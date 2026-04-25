"""Per-root hard-case detector — Stage 0.5 of the bias pipeline.

For each surveyed root, identify the small set of verses where the
conventional English translation MUST INVENT a word that is not in
the Arabic — and where any single English canonical (including ours)
would also distort the verse.

Example: 33:56 for ṣ-l-w. The Arabic verb يُصَلُّونَ is performed by
Allah, the angels, and the believers in the same sentence. Conventional
translations invent "send blessings upon" to make the act distinguishable
across actors. A faithful rendering refuses to fill the gap. The right
move is to leave the Arabic word transliterated in place, and let a
glossary tooltip carry the explanation.

This script asks Claude to surface those verses per root. Output goes
into term_surveys.hard_cases_json as:

  [
    {
      "ref": "33:56",
      "arabic_word": "يُصَلُّونَ",
      "transliteration": "yuṣallūna",
      "reason": "Same verb performed by God, angels, and believers in
                 the same sentence — conventional 'send blessings upon'
                 is invented to mask the unity"
    },
    ...
  ]

Usage:
    python hard_cases_detect.py --root Slw
    python hard_cases_detect.py --all-surveyed
    python hard_cases_detect.py --root Slw --force
    python hard_cases_detect.py --root Slw --dry-run
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
DEFAULT_MODEL = "claude-opus-4-20250514"
DEFAULT_TRANSLATION_CONFIG = "gpt5.1-batch-v2"

SYSTEM_PROMPT = """\
You are auditing a single Arabic root's Qur'anic occurrences to identify
HARD CASES — verses where the conventional English translation MUST
INVENT a word or phrase that is not in the Arabic to make the rendering
work, and where any single English canonical (including the one we've
derived) would also distort the verse.

For each hard case you identify, the recommended action is to leave the
Arabic word in the translation as a transliteration, and let a glossary
tooltip carry the explanation.

Be CONSERVATIVE. Only mark a verse hard if:
  (a) Conventional translations introduce a noun or phrase that has no
      morphological basis in the Arabic of this verse, AND
  (b) Replacing the conventional rendering with our derived canonical
      would also distort the meaning, AND
  (c) The verse benefits from the reader seeing the Arabic word
      directly with a gloss, rather than ANY English substitution.

Counter-examples in the survey data are a strong signal of hard cases —
those are the verses that broke the conventional reading in the first
place.

Output ONLY this JSON:

{
  "hard_cases": [
    {
      "ref": "CHAPTER:VERSE",
      "arabic_word": "<exact Arabic form from the verse>",
      "transliteration": "<ALA-LC transliteration with macrons / dots, e.g. 'yuṣallūna', 'ṣalāh'>",
      "reason": "<one sentence: what the conventional translation invents and why our canonical also distorts>"
    },
    ...
  ]
}

Most roots will have 0–3 hard cases. Some may have none — return an
empty hard_cases list and don't manufacture entries. The classic
exemplar is 33:56 for ṣ-l-w (Allah and angels and believers all
performing the same verb on the Prophet — conventional 'send blessings'
is invented; our 'connect' also strains).

No preamble, no explanation outside the JSON.
"""


def fetch_root_data(conn, root_bw: str, config_name: str) -> dict | None:
    """Pull canonical, reasoning, counter-examples, and ALL occurrences
    of this root with their current translations. Returns None if the
    root hasn't been surveyed yet."""
    survey = conn.execute(
        "SELECT root_buckwalter, root_arabic, canonical_english, reasoning, "
        "       counter_examples_json, occurrence_count, occurrence_samples "
        "FROM term_surveys WHERE root_buckwalter = ?",
        (root_bw,),
    ).fetchone()
    if not survey:
        return None
    return dict(survey)


def build_user_prompt(survey: dict) -> str:
    samples = json.loads(survey.get("occurrence_samples") or "[]")
    counter_examples = json.loads(survey.get("counter_examples_json") or "[]")

    lines = [
        f"ROOT: {survey['root_buckwalter']} ({survey['root_arabic']})",
        f"DERIVED CANONICAL: '{survey['canonical_english']}'",
        f"OCCURRENCE COUNT: {survey['occurrence_count']}",
        "",
        "REASONING (semantic thread through all usages):",
        survey.get("reasoning") or "(none)",
        "",
        "COUNTER-EXAMPLES previously identified (verses that strained the conventional reading):",
    ]
    for ce in counter_examples:
        lines.append(f"  • {ce.get('ref')}: {ce.get('how_canonical_fits', '')}")

    lines += [
        "",
        "ALL OCCURRENCES (compact form: ref · Arabic word · current English translation):",
    ]
    for s in samples:
        ref = f"{s['chapter']}:{s['verse']}"
        word = s.get("arabic_word") or "?"
        trans = (s.get("translation") or "").strip()
        if len(trans) > 160:
            trans = trans[:157] + "…"
        lines.append(f"  {ref} · {word} — {trans}")

    lines += [
        "",
        "Identify the hard cases — verses where conventional English INVENTS",
        "a word and where our canonical would also distort. Return only the",
        "JSON object.",
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
                    "max_tokens": 4000,
                    "temperature": 0.2,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
                timeout=300,
            )
        except requests.RequestException as e:
            last_err = f"request error: {e}"
        else:
            if resp.status_code == 200:
                data = resp.json()
                return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
            last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"
        if attempt < 3:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Claude failed after 3 attempts: {last_err}")


def parse_response(raw: str) -> list[dict]:
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"No JSON: {text[:300]!r}")
    obj = json.loads(m.group())
    cases = obj.get("hard_cases") or []
    if not isinstance(cases, list):
        return []
    return cases


def detect_for_root(conn, root_bw: str, model: str, api_key: str,
                    config_name: str, force: bool, dry_run: bool) -> None:
    survey = fetch_root_data(conn, root_bw, config_name)
    if not survey:
        print(f"  {root_bw} — not in term_surveys, skip")
        return

    existing = json.loads(survey.get("hard_cases_json") or "null")
    if existing is not None and not force:
        print(f"  {root_bw} ({survey['root_arabic']}) — already has "
              f"{len(existing)} hard cases (pass --force to redo)")
        return

    prompt = build_user_prompt(survey)
    print(f"\n━━━ {root_bw} ({survey['root_arabic']}) → '{survey['canonical_english']}' ━━━")

    if dry_run:
        print(f"  (dry-run) prompt length: {len(prompt)} chars")
        print(prompt[:600])
        print("  ...")
        return

    try:
        raw = call_claude(model, SYSTEM_PROMPT, prompt, api_key)
    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return

    try:
        cases = parse_response(raw)
    except Exception as e:
        print(f"  ERROR parsing: {e}", file=sys.stderr)
        print(f"  raw: {raw[:300]!r}", file=sys.stderr)
        return

    print(f"  → {len(cases)} hard case(s) identified")
    for c in cases:
        print(f"    {c.get('ref')}: {c.get('arabic_word')} ({c.get('transliteration')})")
        print(f"      reason: {(c.get('reason') or '')[:200]}")

    conn.execute(
        "UPDATE term_surveys SET hard_cases_json = ? WHERE root_buckwalter = ?",
        (json.dumps(cases, ensure_ascii=False), root_bw),
    )
    conn.commit()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--root", help="single Buckwalter root, e.g. Slw")
    p.add_argument("--all-surveyed", action="store_true",
                   help="run for every row in term_surveys")
    p.add_argument("--config", default=DEFAULT_TRANSLATION_CONFIG)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--api-key")
    p.add_argument("--force", action="store_true",
                   help="redo even if hard_cases_json is already populated")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    api_key = args.api_key or _get_claude_api_key()
    if not api_key and not args.dry_run:
        print("ERROR: no CLAUDE_API_KEY.", file=sys.stderr)
        return 1

    conn = get_db()
    if args.all_surveyed:
        targets = [r["root_buckwalter"] for r in conn.execute(
            "SELECT root_buckwalter FROM term_surveys ORDER BY root_buckwalter")]
    elif args.root:
        targets = [args.root]
    else:
        print("ERROR: pass --root <bw> or --all-surveyed.", file=sys.stderr)
        return 1

    for root_bw in targets:
        detect_for_root(
            conn, root_bw, args.model, api_key,
            args.config, args.force, args.dry_run,
        )

    if not args.dry_run:
        print("\n━━━ Hard-case summary ━━━")
        rows = conn.execute(
            "SELECT root_buckwalter, root_arabic, canonical_english, hard_cases_json "
            "FROM term_surveys WHERE hard_cases_json IS NOT NULL "
            "ORDER BY root_buckwalter"
        ).fetchall()
        total_cases = 0
        for r in rows:
            cases = json.loads(r["hard_cases_json"])
            total_cases += len(cases)
            refs = ", ".join(c.get("ref", "?") for c in cases) or "(none)"
            print(f"  {r['root_buckwalter']:<5} ({r['root_arabic']}) → "
                  f"'{r['canonical_english']}': {len(cases)} hard cases — {refs}")
        print(f"\n  Total hard cases across roots: {total_cases}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
