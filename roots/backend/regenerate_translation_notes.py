"""Rewrite the translation_note column on existing term_surveys rows
without re-running the full semantic survey. Uses the already-stored
canonical_english + reasoning + counter_examples as input, and has
Claude Sonnet produce a note in the exact tone template — no
apologetic framing, no "methodology we follow", no editorializing.

Usage:
    python regenerate_translation_notes.py                # all rows
    python regenerate_translation_notes.py --root Slw     # single
    python regenerate_translation_notes.py --dry-run
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

DEFAULT_MODEL = "claude-sonnet-4-6"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

PROMPT_TEMPLATE = """\
You will write a short translation note for the al-nuqta Qur'an site.
Follow the tone template EXACTLY. Do not editorialize about tradition's
history. Do not use the phrases "methodology we follow", "later ritual
institution", "post-Qur'anic", "we propose", or "bias". Just present
the evidence and the finding.

TEMPLATE (this is the exact structure and tone to match):

  "Conventional translations render صَلَاة as 'prayer'. However,
  upon tracing the root ص-ل-و across all 99 occurrences we find a
  broader sense of sustained connection or linking. In 33:56, for
  instance, the Qur'an says Allah and the angels 'yuṣallūna' upon
  the Prophet — a usage that the ritual-prayer reading cannot
  accommodate since God does not pray. We translate as 'connect',
  which encompasses prayer as one form of connection while honoring
  the Qur'an's full range of usage, from divine-human links to
  community bonds."

Structure to match:
  1. Sentence 1: "Conventional translations render <ARABIC_TERM> as '<CONVENTIONAL>'."
  2. Sentence 2: "However, upon tracing the root <ROOT> across all <N> occurrences we find <BROADER_MEANING>."
  3. Sentence 3: "In <COUNTER_REF>, for instance, <COUNTER_OBSERVATION>."
  4. Sentence 4 (combining final thought): "We translate as '<CANONICAL>', which encompasses <CONVENTIONAL> as one form of <CANONICAL> while honoring <RANGE_SUMMARY>."

Produce 3-5 sentences total. Output ONLY the note text — no JSON, no
preamble, no quotation marks around it.

--- DATA FOR THIS TERM ---
Root (Arabic): {root_arabic}
Root (Buckwalter): {root_buckwalter}
Occurrence count: {occurrence_count}
Canonical Qur'an-only English: {canonical_english}
Conventional English translation: {conventional_guess}
Semantic reasoning: {reasoning}
Counter-examples: {counter_examples}
A representative Arabic word form from the occurrences: {arabic_sample}
"""

# Conventional translations — hand-mapped so the note can cite the
# mainstream rendering without asking Claude to guess every time.
CONVENTIONAL = {
    "Slw":  ("صَلَاة",   "prayer"),
    "zkw":  ("زَكَاة",    "alms"),
    "Swm":  ("صَوْم",     "fasting"),
    "Hjj":  ("حَجّ",      "pilgrimage"),
    "sjd":  ("سُجُود",    "prostration"),
    "rkE":  ("رُكُوع",    "bowing"),
    "snn":  ("سُنَّة",     "Sunnah / the Prophet's way"),
    "nsk":  ("نُسُك",     "ritual sacrifice"),
    "qwm":  ("قِيَام / قَوْم", "standing / people"),
    "$Er":  ("شَعَائِر",  "sacred rites"),
    "Emr":  ("عُمْرَة",    "minor pilgrimage"),
    "*kr":  ("ذِكْر",      "remembrance"),
    "Thr":  ("طَهَارَة",   "ritual purification"),
}


def fetch_arabic_sample(occurrence_samples: str | None) -> str:
    if not occurrence_samples:
        return ""
    try:
        data = json.loads(occurrence_samples)
    except Exception:
        return ""
    for o in data:
        w = o.get("arabic_word") or ""
        if w:
            return w
    return ""


def call_claude(model: str, prompt: str, api_key: str) -> str:
    resp = requests.post(
        ANTHROPIC_URL,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        json={
            "model": model,
            "max_tokens": 800,
            "temperature": 0.3,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text").strip()


def regenerate_for_row(conn, row: dict, model: str, api_key: str, dry_run: bool) -> None:
    root_bw = row["root_buckwalter"]
    conv = CONVENTIONAL.get(root_bw, (row.get("root_arabic") or "", "(conventional term)"))
    conv_arabic, conv_en = conv

    counter_examples = row.get("counter_examples_json") or "[]"
    try:
        ce = json.loads(counter_examples)
    except Exception:
        ce = []
    ce_text = "; ".join(
        f"{c.get('ref')}: {c.get('how_canonical_fits', '')[:120]}"
        for c in ce[:4]
    )

    arabic_sample = fetch_arabic_sample(row.get("occurrence_samples"))

    prompt = PROMPT_TEMPLATE.format(
        root_arabic=conv_arabic or row.get("root_arabic") or "?",
        root_buckwalter=row.get("root_arabic") or root_bw,  # for the "root <ROOT>" sentence, prefer Arabic
        occurrence_count=row.get("occurrence_count") or "?",
        canonical_english=row.get("canonical_english") or "?",
        conventional_guess=conv_en,
        reasoning=row.get("reasoning") or "",
        counter_examples=ce_text or "(none)",
        arabic_sample=arabic_sample or "?",
    )

    print(f"\n━━━ {root_bw} ({row.get('root_arabic')}) → '{row.get('canonical_english')}' ━━━")

    if dry_run:
        print(prompt[:600])
        print("...")
        return

    try:
        note = call_claude(model, prompt, api_key)
    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return
    # Strip accidental quotes or fences
    note = re.sub(r"^[\"']|[\"']$", "", note.strip())
    print(f"  {note[:300]}{'...' if len(note) > 300 else ''}")
    conn.execute(
        "UPDATE term_surveys SET translation_note = ? WHERE root_buckwalter = ?",
        (note, root_bw),
    )
    conn.commit()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--root", help="just one root (Buckwalter)")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--api-key", default=None)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    api_key = args.api_key or _get_claude_api_key()
    if not api_key and not args.dry_run:
        print("ERROR: no CLAUDE_API_KEY.", file=sys.stderr)
        return 1

    conn = get_db()
    conn.row_factory = __import__("sqlite3").Row
    if args.root:
        rows = conn.execute(
            "SELECT * FROM term_surveys WHERE root_buckwalter = ?",
            (args.root,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM term_surveys ORDER BY root_buckwalter"
        ).fetchall()

    if not rows:
        print("No term_surveys rows found.", file=sys.stderr)
        return 1

    for row in rows:
        regenerate_for_row(conn, dict(row), args.model, api_key, args.dry_run)
        time.sleep(0.3)  # be friendly to the rate limit

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
