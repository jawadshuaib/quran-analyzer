"""Stage 2 — Claude adjudicator for translation bias flags.

Consumes rows from translation_bias_reviews where detector_flagged=1
and decision IS NULL. For each, sends a focused prompt to Claude asking
for a revise/keep/defer verdict. If revise, produces the proposed new
translation text. Results go into the same row (decision, revised_text,
reasoning, confidence). No translations are APPLIED here — that's a
separate step (admin UI or a dedicated apply script), so we can review
the verdicts before shipping any change to readers.

Conservative by design: Claude is told to default to KEEP unless the
case for revising is strong. Stage 1 programmatic scanning has some
false positives (e.g. a translation using a synonym the word-family
match missed); Claude filters those out.

Usage:
    python bias_adjudicate.py --limit 50           # small batch first
    python bias_adjudicate.py --all                # every pending flag
    python bias_adjudicate.py --verses "2:3,87:15" # specific verses
    python bias_adjudicate.py --dry-run
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
DEFAULT_MODEL = "claude-sonnet-4-20250514"
MAX_ATTEMPTS = 3

SYSTEM_PROMPT = """\
You are the adjudicator for al-nuqta's translation bias review pipeline.

A deterministic Stage 1 detector finds verses where the current English
translation does NOT use the canonical Qur'an-only rendering for one or
more roots present in the verse. The canonicals come from a corpus-wide
survey (see term_surveys in the database) — e.g. ṣalāh/Slw → 'connect',
zakāh/zkw → 'grow', dhikr/*kr → 'invoke', sujūd/sjd → 'submit'.

Your job: for each flagged verse, decide one of:

  - "revise": the current translation genuinely uses a post-Qur'anic
    narrowed term or otherwise breaks the canonical. Produce a revised
    translation that uses the canonical word-family while preserving
    the rest of the sentence's meaning.
  - "keep": the current translation actually conveys the canonical sense
    using a synonym the programmatic scanner missed, OR the context is
    idiomatic such that the canonical would distort the meaning.
  - "defer": the decision requires context beyond this verse (e.g. the
    polysemous root qwm could mean "stand" OR "a people" and the verse
    is genuinely ambiguous).

BIAS STRONGLY TOWARD KEEP. Only mark "revise" when the current
rendering clearly uses the conventional ritual/narrowed term
(prayer, fasting, alms, prostration, etc.) where the canonical's
abstract sense should appear. A "revise" verdict should be defensible
to a careful reader; if you're uncertain, keep.

When revising, your revised_text should:
  - Be a complete, natural English sentence
  - Use a form of the canonical word-family in place of the flagged term
  - Preserve every other word/clause of the original translation
  - Remain readable — no stilted phrasing, no caveats, no brackets
  - NOT add commentary; this is a translation not a tafsir

Output ONLY this JSON object:

{
  "decision": "revise" | "keep" | "defer",
  "revised_text": "<full revised English translation, or empty string if decision != revise>",
  "reasoning": "<1-2 sentences explaining the call>",
  "confidence": 0.0 to 1.0
}

If multiple roots were flagged in the same verse, your revised_text
should honor ALL of them if you decide to revise.
"""


def load_pending(conn, limit: int | None, verses: list[tuple[int, int]] | None,
                 detector_model: str) -> list[dict]:
    """Return bias review rows that need adjudication."""
    sql = (
        "SELECT id, chapter, verse, original_text, flags_json "
        "FROM translation_bias_reviews "
        "WHERE detector_flagged = 1 AND decision IS NULL "
        "  AND detector_model = ?"
    )
    params: list = [detector_model]
    if verses:
        placeholders = ",".join(["(?, ?)"] * len(verses))
        sql += f" AND (chapter, verse) IN ({placeholders})"
        for s, a in verses:
            params.extend([s, a])
    sql += " ORDER BY chapter, verse"
    if limit:
        sql += f" LIMIT {int(limit)}"
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def load_survey_context(conn, root_buckwalter: str) -> dict | None:
    row = conn.execute(
        "SELECT root_arabic, canonical_english, reasoning, translation_note "
        "FROM term_surveys WHERE root_buckwalter = ?",
        (root_buckwalter,),
    ).fetchone()
    return dict(row) if row else None


def load_verse_arabic(conn, surah: int, ayah: int) -> str:
    row = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
        (surah, ayah),
    ).fetchone()
    return row["text_uthmani"] if row else ""


def build_prompt(conn, review: dict) -> str:
    try:
        flags = json.loads(review["flags_json"] or "[]")
    except Exception:
        flags = []

    arabic = load_verse_arabic(conn, review["chapter"], review["verse"])

    lines = [
        f"VERSE: {review['chapter']}:{review['verse']}",
        "",
        "ARABIC:",
        arabic,
        "",
        "CURRENT ENGLISH TRANSLATION (under review):",
        review["original_text"] or "",
        "",
        "FLAGGED ROOTS in this verse:",
    ]
    for f in flags:
        root_bw = f.get("root_buckwalter", "")
        ctx = load_survey_context(conn, root_bw) or {}
        lines.append(
            f"  • {f.get('root_arabic', root_bw)} ({root_bw})"
            f" — word in verse: {f.get('arabic_word', '?')}"
        )
        lines.append(
            f"    canonical: '{f.get('expected_canonical', '?')}'"
        )
        note = ctx.get("translation_note") or ""
        if note:
            # Trim excessively long notes
            lines.append(f"    note: {note[:320]}")
    lines.append("")
    lines.append("Return your JSON verdict.")
    return "\n".join(lines)


def call_claude(model: str, system: str, user: str, api_key: str) -> str:
    last_err = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
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
                    "max_tokens": 1200,
                    "temperature": 0.2,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
                timeout=90,
            )
        except requests.RequestException as e:
            last_err = f"request error: {e}"
        else:
            if resp.status_code == 200:
                data = resp.json()
                return "".join(
                    b.get("text", "")
                    for b in data.get("content", [])
                    if b.get("type") == "text"
                )
            last_err = f"HTTP {resp.status_code}: {resp.text[:400]}"

        if attempt < MAX_ATTEMPTS:
            wait = 2 ** attempt
            print(f"  retry {attempt}/{MAX_ATTEMPTS} after {wait}s ({last_err})",
                  file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"Claude failed after {MAX_ATTEMPTS} attempts: {last_err}")


def parse_verdict(raw: str) -> dict:
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"No JSON in response: {text[:300]!r}")
    obj = json.loads(m.group())
    if obj.get("decision") not in ("revise", "keep", "defer"):
        raise ValueError(f"Bad decision: {obj.get('decision')}")
    return obj


def save_verdict(conn, review_id: int, model: str, verdict: dict, raw: str):
    conn.execute(
        "UPDATE translation_bias_reviews SET "
        "  adjudicator_model = ?, adjudicator_run_at = CURRENT_TIMESTAMP, "
        "  decision = ?, revised_text = ?, reasoning = ?, confidence = ?, "
        "  adjudicator_raw_response = ? "
        "WHERE id = ?",
        (
            model,
            verdict["decision"],
            verdict.get("revised_text") or None,
            verdict.get("reasoning") or None,
            float(verdict.get("confidence") or 0.0),
            raw,
            review_id,
        ),
    )
    conn.commit()


def parse_verse_spec(spec: str) -> list[tuple[int, int]]:
    out = []
    for piece in spec.split(","):
        piece = piece.strip()
        if not piece:
            continue
        m = re.match(r"^(\d+):(\d+)(?:-(\d+))?$", piece)
        if not m:
            raise SystemExit(f"bad verse spec: {piece!r}")
        surah, start = int(m.group(1)), int(m.group(2))
        end = int(m.group(3) or start)
        out.extend((surah, v) for v in range(start, end + 1))
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--limit", type=int)
    p.add_argument("--all", action="store_true")
    p.add_argument("--verses", help="e.g. '2:3,87:15'")
    p.add_argument("--detector-model", default="programmatic-canonical-v1")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--api-key")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not (args.all or args.limit or args.verses):
        print("ERROR: pass --all, --limit N, or --verses.", file=sys.stderr)
        return 1

    api_key = args.api_key or _get_claude_api_key()
    if not api_key and not args.dry_run:
        print("ERROR: no CLAUDE_API_KEY.", file=sys.stderr)
        return 1

    conn = get_db()

    verses = parse_verse_spec(args.verses) if args.verses else None
    limit = None if args.all else args.limit

    pending = load_pending(conn, limit, verses, args.detector_model)
    print(f"Adjudicating {len(pending)} pending review(s)")

    stats = {"revise": 0, "keep": 0, "defer": 0, "error": 0}

    for review in pending:
        ref = f"{review['chapter']}:{review['verse']}"
        prompt = build_prompt(conn, review)
        if args.dry_run:
            print(f"\n--- {ref} ---")
            print(prompt[:900])
            continue

        try:
            raw = call_claude(args.model, SYSTEM_PROMPT, prompt, api_key)
            verdict = parse_verdict(raw)
        except Exception as e:
            print(f"  {ref} ERROR: {e}", file=sys.stderr)
            stats["error"] += 1
            continue

        save_verdict(conn, review["id"], args.model, verdict, raw)
        stats[verdict["decision"]] = stats.get(verdict["decision"], 0) + 1
        marker = {"revise": "→", "keep": "·", "defer": "?"}[verdict["decision"]]
        conf = verdict.get("confidence") or 0.0
        print(f"  {marker} {ref} [{verdict['decision']} conf={conf:.2f}] "
              f"{(verdict.get('reasoning') or '')[:100]}")
        if verdict["decision"] == "revise":
            print(f"    was: {review['original_text'][:140]}")
            print(f"    new: {(verdict.get('revised_text') or '')[:140]}")

    print(f"\n=== Summary ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
