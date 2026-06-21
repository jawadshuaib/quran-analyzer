"""Apply transliteration to the 27 hard-case verses identified in
term_surveys.hard_cases_json.

For each (root, verse) hard case, ask Claude to perform a minimal-edit
revision of the existing AI translation: swap the conventional English
token for the Arabic transliteration. Other words are kept exactly.

The revised text goes into ai_translations.revised_text; the original
translation_text remains untouched. The /api/verse/<s>:<a>/ai-translation
endpoint prefers revised_text when present.

Usage:
    python apply_hard_case_transliterations.py --dry-run
    python apply_hard_case_transliterations.py --root Slw     # one root
    python apply_hard_case_transliterations.py --all
    python apply_hard_case_transliterations.py --verse "33:56" --force
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
DEFAULT_TRANSLATION_CONFIG = "gpt5.1-batch-v2"

SYSTEM_PROMPT = """\
You will perform a MINIMAL-EDIT revision of an existing English Qur'anic
translation. The verse contains a specific Arabic word (a "hard case")
where conventional English translations introduce a noun or phrase not
present in the Arabic — and where any single canonical English word
would also distort the verse. The right move is to leave the Arabic
word in place as a transliteration, with a glossary tooltip carrying
the explanation.

Your job: take the existing English translation and replace the
conventional English token(s) for THIS hard-case word with the Arabic
transliteration provided. Wrap the transliteration in italics in
markdown — `*ṣalli*`, `*yuṣallūna*`, etc. — so the frontend can
recognize it for the glossary tooltip layer.

Rules:
  1. Change only the words tied to the hard-case Arabic word. Every
     other word in the translation remains EXACTLY as-is — same
     spelling, same punctuation, same capitalization, same brackets.
  2. The transliteration goes in italics: `*xxxxx*`.
  3. If the conventional English required adding a preposition or
     object that the Arabic doesn't have ("send blessings UPON",
     "pray FOR them"), drop the invented words too. The Arabic verb
     governs its own preposition; the transliteration carries that.
  4. Read naturally as English. If swap creates a grammatical break,
     adjust ONLY the immediate surrounding clause, not the whole
     translation.
  5. Preserve directional quotes (" "), em-dashes, em-dashes, etc.

Output ONLY the revised translation text. No JSON, no preamble, no
quotation marks around the whole string.
"""


def parse_verse_arg(spec: str) -> tuple[int, int] | None:
    if not spec:
        return None
    m = re.match(r"^(\d+):(\d+)$", spec.strip())
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def gather_hard_cases(conn, root_filter: str | None,
                      verse_filter: tuple[int, int] | None) -> list[dict]:
    """Flatten term_surveys.hard_cases_json into a list of (root, verse,
    arabic_word, transliteration, reason)."""
    rows = conn.execute(
        "SELECT root_buckwalter, root_arabic, canonical_english, hard_cases_json "
        "FROM term_surveys WHERE hard_cases_json IS NOT NULL"
    ).fetchall()
    out = []
    for r in rows:
        if root_filter and r["root_buckwalter"] != root_filter:
            continue
        try:
            cases = json.loads(r["hard_cases_json"]) or []
        except Exception:
            continue
        for hc in cases:
            ref = hc.get("ref", "")
            m = re.match(r"^(\d+):(\d+)$", ref)
            if not m:
                continue
            ch, vs = int(m.group(1)), int(m.group(2))
            if verse_filter and (ch, vs) != verse_filter:
                continue
            out.append({
                "chapter": ch,
                "verse": vs,
                "root_bw": r["root_buckwalter"],
                "root_arabic": r["root_arabic"],
                "canonical_english": r["canonical_english"],
                "arabic_word": hc.get("arabic_word"),
                "transliteration": hc.get("transliteration"),
                "reason": hc.get("reason"),
            })
    return out


def load_translation(conn, ch: int, vs: int, config_name: str) -> dict | None:
    config_row = conn.execute(
        "SELECT id FROM ai_translation_configs WHERE config_name = ?",
        (config_name,),
    ).fetchone()
    if not config_row:
        return None
    row = conn.execute(
        "SELECT id, translation_text, revised_text "
        "FROM ai_translations "
        "WHERE chapter = ? AND verse = ? AND config_id = ?",
        (ch, vs, config_row["id"]),
    ).fetchone()
    return dict(row) if row else None


def build_prompt(case: dict, current_text: str) -> str:
    return (
        f"VERSE: {case['chapter']}:{case['verse']}\n"
        f"ROOT: {case['root_arabic']} ({case['root_bw']})\n"
        f"CANONICAL (for reference): '{case['canonical_english']}'\n\n"
        f"HARD-CASE ARABIC WORD: {case['arabic_word']}\n"
        f"TRANSLITERATION TO INSERT: {case['transliteration']}\n"
        f"WHY THIS IS A HARD CASE: {case['reason']}\n\n"
        f"CURRENT ENGLISH TRANSLATION (to revise minimally):\n"
        f"{current_text}\n\n"
        f"Output the revised translation only. Wrap the transliteration in "
        f"markdown italics: *{case['transliteration']}*. Drop any preposition/"
        f"object the conventional English invents that the Arabic doesn't have. "
        f"Every other word remains exactly as-is."
    )


def call_claude(model: str, system: str, user: str, api_key: str) -> str:
    last_err = None
    for attempt in range(1, 4):
        try:
            resp = requests.post(
                ANTHROPIC_URL,
                headers={"Content-Type": "application/json",
                         "x-api-key": api_key,
                         "anthropic-version": "2023-06-01"},
                json={"model": model, "max_tokens": 1500, "temperature": 0.1,
                      "system": system,
                      "messages": [{"role": "user", "content": user}]},
                timeout=60,
            )
        except requests.RequestException as e:
            last_err = f"request: {e}"
        else:
            if resp.status_code == 200:
                return "".join(b.get("text", "") for b in resp.json().get("content", [])
                               if b.get("type") == "text").strip()
            last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"
        if attempt < 3:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Claude failed: {last_err}")


def apply_one(conn, case: dict, model: str, api_key: str,
              config_name: str, dry_run: bool, force: bool) -> str:
    ref = f"{case['chapter']}:{case['verse']}"
    tr = load_translation(conn, case["chapter"], case["verse"], config_name)
    if not tr:
        print(f"  {ref}: no translation in '{config_name}', skipping")
        return "skip-no-translation"
    if tr["revised_text"] and not force:
        print(f"  {ref}: already has revised_text (use --force to redo)")
        return "skip-already-revised"

    current = tr["revised_text"] or tr["translation_text"]
    prompt = build_prompt(case, current)

    if dry_run:
        print(f"\n--- {ref} ({case['root_arabic']} {case['arabic_word']} → "
              f"*{case['transliteration']}*) ---")
        print(f"  WAS: {current}")
        return "dry-run"

    try:
        revised = call_claude(model, SYSTEM_PROMPT, prompt, api_key)
    except Exception as e:
        print(f"  {ref} ERROR: {e}", file=sys.stderr)
        return "error"

    revised = re.sub(r"^[\"'`]+|[\"'`]+$", "", revised.strip())

    conn.execute(
        "UPDATE ai_translations SET revised_text = ? WHERE id = ?",
        (revised, tr["id"]),
    )
    conn.commit()

    print(f"  → {ref}")
    print(f"    was: {current[:140]}")
    print(f"    new: {revised[:140]}")
    return "applied"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--all", action="store_true")
    p.add_argument("--root", help="apply only for this root (Buckwalter)")
    p.add_argument("--verse", help="single verse 'X:Y'")
    p.add_argument("--config", default=DEFAULT_TRANSLATION_CONFIG)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--api-key")
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not (args.all or args.root or args.verse):
        print("ERROR: pass --all, --root, or --verse.", file=sys.stderr)
        return 1

    api_key = args.api_key or _get_claude_api_key()
    if not api_key and not args.dry_run:
        print("ERROR: no CLAUDE_API_KEY", file=sys.stderr)
        return 1

    conn = get_db()
    verse_filter = parse_verse_arg(args.verse) if args.verse else None
    cases = gather_hard_cases(conn, args.root, verse_filter)

    if not cases:
        print("No hard cases match.", file=sys.stderr)
        return 1

    print(f"Applying transliteration to {len(cases)} hard case(s)")

    stats = {}
    for case in cases:
        result = apply_one(conn, case, args.model, api_key,
                          args.config, args.dry_run, args.force)
        stats[result] = stats.get(result, 0) + 1

    print(f"\n=== Summary ===")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
