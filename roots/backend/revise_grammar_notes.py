"""Revise existing grammar notes (ai_grammar_notes.notes_markdown) to use
the canonical Qur'an-only English from term_surveys instead of the
conventional ritualistic English (prayer, prostration, etc.).

Targets only verses whose grammar note CURRENTLY contains a ritualistic
narrowed English term AND the verse's morphology contains the matching
surveyed root. For each pair we ask Claude Sonnet to rewrite the note
with the canonical word-family — preserving grammatical analysis, all
[[term]] markers (those are grammar-glossary chips), and the readable
flow.

Hard-case verses (per term_surveys.hard_cases_json) get the Arabic
transliteration instead of the canonical.

Original notes are preserved in ai_grammar_notes.notes_markdown_original
(added by this script if missing) so the change can be reverted.

Usage:
    python revise_grammar_notes.py --dry-run             # show what would change
    python revise_grammar_notes.py --verses "55:6"       # one verse
    python revise_grammar_notes.py --all                 # all 172 affected
    python revise_grammar_notes.py --verses "55:6" --force
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

import requests

from app import get_db, _get_claude_api_key

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-6"

# Conventional English terms that signal narrowing for each root,
# paired with the root's Buckwalter form.
RITUALISTIC_PATTERNS: list[tuple[str, str]] = [
    ("Slw",  r"\b(prayer|prayers|praying|prayed|prays)\b"),
    ("zkw",  r"\b(zakat|zakāh|alms|almsgiving|purifying[\s-]?due)\b"),
    ("Swm",  r"\b(fasting|fasts|fasted|Ramadan)\b"),
    ("Hjj",  r"\b(pilgrimage|pilgrim)\b"),
    ("sjd",  r"\b(prostrat\w*)\b"),
    ("rkE",  r"\b(bowed|bowing|bows|bow\s+down)\b"),
    ("snn",  r"\b(Sunnah|Sunna)\b"),
    ("Emr",  r"\b(umrah|ʿumrah)\b"),
    ("Thr",  r"\b(ablution|wudu|wud\u016b\u02be|ritual\s+purification)\b"),
]


SYSTEM_PROMPT = """\
You are revising a Qur'anic grammar note to bring its English vocabulary
in line with the al-nuqta canonical translations for ritualistic-narrowed
roots. The conventional English (prayer, prostration, fasting, etc.)
should be replaced with the broader canonical (connect, submit, abstain,
etc.) — or, for verses listed as hard cases, with the Arabic
transliteration.

CRITICAL preservation rules:

  1. Keep ALL [[term]] markers exactly as-is. Those are grammar-glossary
     chips (terms like [[dual]], [[imperfect]], [[nominative]]). Never
     remove or rename them.
  2. Keep ALL grammatical analysis intact — the part-of-speech tags,
     verb-form descriptions, syntactic role explanations.
  3. Only swap the ritualistic conventional English (prayer / prostrate
     / fast / pilgrimage / etc.) for the canonical or transliteration.
     Do not rewrite for style; minimal-edit is the goal.
  4. The note should still read naturally. If the swap creates an
     awkward sentence, rephrase the immediate surrounding clause —
     but keep the substantive content unchanged.
  5. If the note discusses the verb-form of the root (e.g. "the verb
     'prostrate' is in the dual"), the verb you reference should be the
     canonical or transliteration too.

Output ONLY the revised notes_markdown text. No JSON, no preamble, no
quotation marks around it.
"""


def parse_verses(spec: str) -> list[tuple[int, int]]:
    out = []
    for piece in spec.split(","):
        piece = piece.strip()
        if not piece:
            continue
        m = re.match(r"^(\d+):(\d+)(?:-(\d+))?$", piece)
        if not m:
            raise SystemExit(f"bad verse spec: {piece!r}")
        s, a = int(m.group(1)), int(m.group(2))
        e = int(m.group(3) or a)
        out.extend((s, v) for v in range(a, e + 1))
    return out


def find_affected_verses(conn) -> list[tuple[int, int, list[str]]]:
    """Return (chapter, verse, [matching root_buckwalter list]) for every
    grammar note whose markdown contains a ritualistic English term
    matching a surveyed root that's also present in the verse."""
    # Pull all grammar notes
    notes = list(conn.execute(
        "SELECT chapter, verse, notes_markdown FROM ai_grammar_notes "
        "WHERE notes_markdown IS NOT NULL"
    ))
    # Pull verse->root index
    verse_roots: dict[tuple[int, int], set[str]] = {}
    for r in conn.execute(
        "SELECT chapter, verse, root_buckwalter FROM morphology "
        "WHERE root_buckwalter IS NOT NULL"
    ):
        key = (r["chapter"], r["verse"])
        verse_roots.setdefault(key, set()).add(r["root_buckwalter"])

    out = []
    for n in notes:
        text = n["notes_markdown"] or ""
        ch, vs = n["chapter"], n["verse"]
        verse_root_set = verse_roots.get((ch, vs), set())
        matched_roots: list[str] = []
        for root, pat in RITUALISTIC_PATTERNS:
            if root not in verse_root_set:
                continue
            if re.search(pat, text, re.IGNORECASE):
                matched_roots.append(root)
        if matched_roots:
            out.append((ch, vs, matched_roots))
    return out


def load_canonicals(conn, roots: list[str]) -> list[dict]:
    """Return canonical info for each root: canonical_english,
    hard_cases_json (parsed)."""
    out = []
    for root in roots:
        row = conn.execute(
            "SELECT root_buckwalter, root_arabic, canonical_english, "
            "       hard_cases_json "
            "FROM term_surveys WHERE root_buckwalter = ?",
            (root,),
        ).fetchone()
        if not row:
            continue
        hc = json.loads(row["hard_cases_json"] or "[]")
        out.append({
            "root_bw": row["root_buckwalter"],
            "root_arabic": row["root_arabic"],
            "canonical": row["canonical_english"],
            "hard_cases": hc,
        })
    return out


def build_prompt(ch: int, vs: int, original: str, canonicals: list[dict]) -> str:
    lines = [
        f"VERSE: {ch}:{vs}",
        "",
        "ROOT(S) IN THIS VERSE WITH CANONICAL RENDERINGS:",
    ]
    for c in canonicals:
        lines.append(f"  • {c['root_arabic']} ({c['root_bw']}) → '{c['canonical']}'")
        # If this verse is a hard case for this root, surface the transliteration
        for hc in c.get("hard_cases", []):
            if hc.get("ref") == f"{ch}:{vs}":
                lines.append(
                    f"    HARD CASE here — use transliteration "
                    f"'{hc.get('transliteration')}' instead of '{c['canonical']}'"
                )
    lines += [
        "",
        "ORIGINAL GRAMMAR NOTE (rewrite the ritualistic vocabulary in this):",
        "─" * 70,
        original,
        "─" * 70,
        "",
        "Output only the revised note. Preserve all [[term]] markers and the",
        "grammatical analysis. Minimal edits — just swap the ritualistic",
        "vocabulary for the canonical (or transliteration if hard case).",
    ]
    return "\n".join(lines)


def call_claude(model: str, system: str, user: str, api_key: str) -> str:
    last_err = None
    for attempt in range(1, 4):
        try:
            resp = requests.post(
                ANTHROPIC_URL,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": model,
                    "max_tokens": 2000,
                    "temperature": 0.2,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
                timeout=60,
            )
        except requests.RequestException as e:
            last_err = f"request: {e}"
        else:
            if resp.status_code == 200:
                data = resp.json()
                return "".join(
                    b.get("text", "")
                    for b in data.get("content", [])
                    if b.get("type") == "text"
                ).strip()
            last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"
        if attempt < 3:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Claude failed: {last_err}")


def ensure_backup_column(conn):
    try:
        conn.execute("ALTER TABLE ai_grammar_notes ADD COLUMN notes_markdown_original TEXT")
        conn.commit()
    except Exception:
        pass


def revise_one(conn, ch: int, vs: int, roots: list[str],
               model: str, api_key: str, dry_run: bool, force: bool) -> str:
    row = conn.execute(
        "SELECT notes_markdown, notes_markdown_original "
        "FROM ai_grammar_notes WHERE chapter=? AND verse=?",
        (ch, vs),
    ).fetchone()
    if not row:
        return "skip-no-note"
    original = row["notes_markdown"]
    if row["notes_markdown_original"] and not force:
        return "skip-already-revised"
    canonicals = load_canonicals(conn, roots)
    if not canonicals:
        return "skip-no-canonicals"

    prompt = build_prompt(ch, vs, original, canonicals)

    if dry_run:
        print(f"\n--- {ch}:{vs} would revise (roots: {','.join(roots)}) ---")
        print(prompt[:1200])
        return "dry-run"

    try:
        revised = call_claude(model, SYSTEM_PROMPT, prompt, api_key)
    except Exception as e:
        print(f"  {ch}:{vs} ERROR: {e}", file=sys.stderr)
        return "error"

    # Save with backup
    if not row["notes_markdown_original"]:
        conn.execute(
            "UPDATE ai_grammar_notes SET notes_markdown_original = ? "
            "WHERE chapter=? AND verse=?",
            (original, ch, vs),
        )
    conn.execute(
        "UPDATE ai_grammar_notes SET notes_markdown = ? WHERE chapter=? AND verse=?",
        (revised, ch, vs),
    )
    conn.commit()
    return "revised"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--verses", help="e.g. '55:6,2:43'")
    p.add_argument("--all", action="store_true",
                   help="all verses where grammar note has ritualistic terms")
    p.add_argument("--limit", type=int)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--api-key")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true",
                   help="re-revise even if notes_markdown_original is present")
    args = p.parse_args()

    api_key = args.api_key or _get_claude_api_key()
    if not api_key and not args.dry_run:
        print("ERROR: no CLAUDE_API_KEY", file=sys.stderr)
        return 1

    conn = get_db()
    ensure_backup_column(conn)

    if args.verses:
        targets = parse_verses(args.verses)
        # need to compute roots per verse
        verse_roots: dict[tuple[int, int], set[str]] = {}
        for r in conn.execute(
            "SELECT chapter, verse, root_buckwalter FROM morphology "
            "WHERE root_buckwalter IS NOT NULL"
        ):
            verse_roots.setdefault((r["chapter"], r["verse"]), set()).add(r["root_buckwalter"])
        affected = []
        for ch, vs in targets:
            note = conn.execute(
                "SELECT notes_markdown FROM ai_grammar_notes WHERE chapter=? AND verse=?",
                (ch, vs),
            ).fetchone()
            if not note or not note["notes_markdown"]:
                affected.append((ch, vs, []))
                continue
            roots = []
            for root, pat in RITUALISTIC_PATTERNS:
                if root not in verse_roots.get((ch, vs), set()):
                    continue
                if re.search(pat, note["notes_markdown"], re.IGNORECASE):
                    roots.append(root)
            affected.append((ch, vs, roots))
        affected = [a for a in affected if a[2]]
    elif args.all:
        affected = find_affected_verses(conn)
    else:
        print("ERROR: pass --verses or --all", file=sys.stderr)
        return 1

    if args.limit:
        affected = affected[: args.limit]

    print(f"Revising {len(affected)} grammar note(s)")

    stats = {"revised": 0, "skip-already-revised": 0, "skip-no-note": 0,
             "skip-no-canonicals": 0, "error": 0, "dry-run": 0}

    for ch, vs, roots in affected:
        result = revise_one(conn, ch, vs, roots, args.model, api_key,
                           args.dry_run, args.force)
        stats[result] = stats.get(result, 0) + 1
        if not args.dry_run:
            mark = {"revised": "→", "error": "✗"}.get(result, "·")
            print(f"  {mark} {ch}:{vs} [{result}]")

    print("\n=== Summary ===")
    for k, v in stats.items():
        if v:
            print(f"  {k}: {v}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
