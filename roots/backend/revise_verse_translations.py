"""Revise the verse-level translation_text + departure_notes on ai_translations
to use a surveyed root's canonical English instead of the conventional ritualistic
translation.

Pairs with revise_word_meanings.py and revise_grammar_notes.py; this is the
fourth Phase-2 surface (the verse-page main translation + the Translation
Notes panel below it).

For each verse containing the target root:
  1. Read current translation_text + departure_notes + revised_text.
  2. Ask Claude Sonnet to rewrite ONLY the words/notes about this specific
     root, preserving everything else exactly.
  3. Save the new translation to revised_text (so _best_translation picks
     it up via COALESCE), and the new departure_notes directly to
     departure_notes after backing up the original to departure_notes_original.
  4. Skip hard-case verses — those are handled by
     apply_hard_case_transliterations.py and have a different treatment.

Originals are preserved for revert:
  - translation_text remains untouched (revised_text shadows it). Revert =
    SET revised_text = NULL.
  - departure_notes_original holds the pre-revision value. Revert =
    SET departure_notes = departure_notes_original; SET _original = NULL.

Usage:
    python revise_verse_translations.py --root Sbr --dry-run
    python revise_verse_translations.py --root Sbr
    python revise_verse_translations.py --root Sbr --limit 5 --force
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time

import requests

from app import get_db, _get_claude_api_key

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-6"


SYSTEM_PROMPT = """\
You are revising a Qur'anic verse translation in a study app. The translation
references a root word that has been semantically surveyed across the corpus
and given a canonical Qur'an-only English rendering. Your job is to swap the
conventional ritualistic English (e.g. "patience", "prayer", "prostration")
for the canonical (e.g. "endure", "connect", "submit") in two places:

  1. The verse's main English translation (currently shown to readers).
  2. The verse's Translation Notes — a paragraph or bulleted list explaining
     why each non-conventional choice was made.

CRITICAL preservation rules:

  1. ONLY change wording related to the target root. Other roots in this
     verse have their own surveys (or none); don't touch them.
  2. Preserve everything else in the translation exactly — sentence
     structure, all OTHER root translations, names, particles, syntax.
  3. Use the canonical word family naturally — e.g. for "endure":
     "endurance", "endured", "those who endure", "be enduring". Pick the
     form that fits the morphology and reads cleanly.
  4. Translation Notes: if there's a bullet/paragraph about the target
     root, rewrite it to explain the canonical choice (cite the
     translation_note text we provide as guidance, but paraphrase — don't
     quote it verbatim). Leave bullets about OTHER roots unchanged. If
     there's no bullet for this root, ADD a brief one.
  5. Don't editorialize. Don't apologize for "departing from tradition".
     Just present the canonical reading and a one-sentence reason.

Output ONLY a single JSON object — no preamble, no commentary outside JSON:

{
  "revised_translation": "the full revised English translation, with target-root words swapped",
  "revised_departure_notes": "the full revised translation notes text, with the target-root bullet rewritten and others untouched"
}
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


def ensure_backup_columns(conn):
    """Idempotent ALTER TABLE — adds departure_notes_original if missing.
    translation_text is already preserved by virtue of revised_text shadowing
    it, so no backup column is needed for the translation itself."""
    try:
        conn.execute(
            "ALTER TABLE ai_translations ADD COLUMN departure_notes_original TEXT"
        )
        conn.commit()
    except Exception:
        pass


def find_target_verses(conn, root_bw: str, exclude_hard_cases: bool = True) -> list[tuple[int, int]]:
    """Verses containing this root that have an ai_translations row.
    Optionally excludes hard-case verses (those are handled by
    apply_hard_case_transliterations.py)."""
    sql = (
        "SELECT DISTINCT t.chapter, t.verse "
        "FROM ai_translations t "
        "JOIN morphology m ON m.chapter = t.chapter AND m.verse = t.verse "
        "WHERE m.root_buckwalter = ? "
        "  AND t.translation_text IS NOT NULL"
    )
    rows = conn.execute(sql, (root_bw,)).fetchall()
    candidates = [(r["chapter"], r["verse"]) for r in rows]

    if exclude_hard_cases:
        # Pull hard-case refs for this root from term_surveys.
        survey_row = conn.execute(
            "SELECT hard_cases_json FROM term_surveys WHERE root_buckwalter = ?",
            (root_bw,),
        ).fetchone()
        hard_refs: set[tuple[int, int]] = set()
        if survey_row and survey_row["hard_cases_json"]:
            try:
                cases = json.loads(survey_row["hard_cases_json"]) or []
            except Exception:
                cases = []
            for hc in cases:
                ref = hc.get("ref", "")
                m = re.match(r"^(\d+):(\d+)$", ref)
                if m:
                    hard_refs.add((int(m.group(1)), int(m.group(2))))
        candidates = [v for v in candidates if v not in hard_refs]

    candidates.sort()
    return candidates


def collect_targets(conn, root_bw: str, force: bool) -> list[tuple[int, int]]:
    """Verses to revise: contain this root, have a translation, not a hard
    case, and (unless force) not already revised. Already revised =
    departure_notes_original is set."""
    candidates = find_target_verses(conn, root_bw, exclude_hard_cases=True)
    if force:
        return candidates
    out = []
    for ch, vs in candidates:
        row = conn.execute(
            "SELECT departure_notes_original FROM ai_translations "
            "WHERE chapter = ? AND verse = ?",
            (ch, vs),
        ).fetchone()
        already = row and row["departure_notes_original"] is not None and row["departure_notes_original"] != ""
        if not already:
            out.append((ch, vs))
    return out


def build_prompt(
    ch: int, vs: int,
    arabic_text: str,
    current_translation: str,
    current_notes: str,
    root_arabic: str, root_bw: str, canonical: str, translation_note: str,
) -> str:
    parts = [
        f"VERSE: {ch}:{vs}",
        f"ARABIC: {arabic_text or '(unavailable)'}",
        "",
        f"TARGET ROOT: {root_arabic} ({root_bw}) → canonical English '{canonical}'",
        f"WHY THIS CANONICAL (paraphrase, don't quote): {translation_note or '(no note saved)'}",
        "",
        "CURRENT TRANSLATION:",
        current_translation or "(empty — generate one using the canonical for the target root)",
        "",
        "CURRENT TRANSLATION NOTES:",
        current_notes or "(empty — add a brief one for the target root)",
        "",
        "Output the JSON object now. Preserve everything not related to the target root.",
    ]
    return "\n".join(parts)


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
                    "max_tokens": 3000,
                    "temperature": 0.2,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
                timeout=90,
            )
        except requests.RequestException as e:
            last_err = f"request: {e}"
        else:
            if resp.status_code == 200:
                return "".join(
                    b.get("text", "")
                    for b in resp.json().get("content", [])
                    if b.get("type") == "text"
                ).strip()
            last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"
        if attempt < 3:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Claude failed: {last_err}")


def _repair_json_quotes(s: str) -> str:
    """Same heuristic as revise_word_meanings._repair_json_quotes:
    escape unescaped " inside JSON string values."""
    out: list[str] = []
    i = 0
    n = len(s)
    in_string = False
    while i < n:
        c = s[i]
        if not in_string:
            out.append(c)
            if c == '"':
                in_string = True
            i += 1
            continue
        if c == '\\' and i + 1 < n:
            out.append(c)
            out.append(s[i + 1])
            i += 2
            continue
        if c == '"':
            j = i + 1
            while j < n and s[j] in ' \t\r\n':
                j += 1
            if j >= n or s[j] in ',}]:':
                out.append('"')
                in_string = False
            else:
                out.append('\\"')
            i += 1
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def parse_response(raw: str) -> dict:
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"no JSON: {text[:300]!r}")
    json_text = m.group()
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        return json.loads(_repair_json_quotes(json_text))


def revise_one(
    conn, ch: int, vs: int,
    root_bw: str, root_arabic: str, canonical: str, translation_note: str,
    model: str, api_key: str, dry_run: bool, force: bool,
) -> str:
    row = conn.execute(
        "SELECT translation_text, revised_text, departure_notes, "
        "       departure_notes_original "
        "FROM ai_translations WHERE chapter = ? AND verse = ?",
        (ch, vs),
    ).fetchone()
    if not row:
        return "skip-no-row"
    if row["departure_notes_original"] and not force:
        return "skip-already-revised"

    # The visible translation is whatever _best_translation would render.
    current_translation = row["revised_text"] or row["translation_text"] or ""
    current_notes = row["departure_notes"] or ""

    arabic = ""
    av = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
        (ch, vs),
    ).fetchone()
    if av and av["text_uthmani"]:
        arabic = av["text_uthmani"]

    prompt = build_prompt(
        ch, vs, arabic, current_translation, current_notes,
        root_arabic, root_bw, canonical, translation_note,
    )

    if dry_run:
        print(f"\n--- {ch}:{vs} would revise ---")
        print(prompt[:1200])
        return "dry-run"

    try:
        raw = call_claude(model, SYSTEM_PROMPT, prompt, api_key)
        verdict = parse_response(raw)
    except Exception as e:
        print(f"  {ch}:{vs} ERROR: {e}", file=sys.stderr)
        return "error"

    new_trans = (verdict.get("revised_translation") or "").strip()
    new_notes = (verdict.get("revised_departure_notes") or "").strip()
    if not (new_trans and new_notes):
        print(
            f"  {ch}:{vs} ERROR: missing fields in response (got "
            f"trans={bool(new_trans)} notes={bool(new_notes)})",
            file=sys.stderr,
        )
        return "error"

    # Back up departure_notes if first revision (idempotent)
    if not row["departure_notes_original"]:
        conn.execute(
            "UPDATE ai_translations SET departure_notes_original = ? "
            "WHERE chapter = ? AND verse = ?",
            (current_notes, ch, vs),
        )
    conn.execute(
        "UPDATE ai_translations SET revised_text = ?, departure_notes = ? "
        "WHERE chapter = ? AND verse = ?",
        (new_trans, new_notes, ch, vs),
    )
    conn.commit()
    print(f"  → {ch}:{vs} revised")
    return "revised"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--root", required=True, help="Buckwalter root, e.g. Sbr")
    p.add_argument("--verses", help="optional: comma-separated verses, e.g. '2:153,2:155'")
    p.add_argument("--limit", type=int)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--api-key")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    api_key = args.api_key or _get_claude_api_key()
    if not api_key and not args.dry_run:
        print("ERROR: no CLAUDE_API_KEY", file=sys.stderr)
        return 1

    conn = get_db()
    conn.row_factory = __import__("sqlite3").Row
    ensure_backup_columns(conn)

    survey = conn.execute(
        "SELECT root_buckwalter, root_arabic, canonical_english, translation_note "
        "FROM term_surveys WHERE root_buckwalter = ?",
        (args.root,),
    ).fetchone()
    if not survey or not survey["canonical_english"]:
        print(f"ERROR: no surveyed canonical for root {args.root!r}", file=sys.stderr)
        return 1

    if args.verses:
        verse_filter = set(parse_verses(args.verses))
        targets = [v for v in collect_targets(conn, args.root, args.force) if v in verse_filter]
    else:
        targets = collect_targets(conn, args.root, args.force)
    if args.limit:
        targets = targets[: args.limit]

    print(f"Revising {len(targets)} verses for root {args.root} ('{survey['canonical_english']}')")

    stats = {"revised": 0, "error": 0, "skip-already-revised": 0,
             "skip-no-row": 0, "dry-run": 0}
    for ch, vs in targets:
        result = revise_one(
            conn, ch, vs,
            survey["root_buckwalter"], survey["root_arabic"],
            survey["canonical_english"], survey["translation_note"] or "",
            args.model, api_key, args.dry_run, args.force,
        )
        stats[result] = stats.get(result, 0) + 1

    print(f"\nDone: {stats}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
