"""Stage 0 — per-root semantic survey.

For each ritualistic root, pull every Quranic occurrence, feed the full
corpus to Claude Opus with a counter-example-aware prompt, and derive
the single abstract semantic core that fits ALL usages. The result is
the canonical Quran-only English rendering (or a verdict to leave the
term untranslated if no single meaning survives every context).

This is a one-time, low-volume pipeline — maybe 15-20 Claude calls for
the entire seed list. Costs are negligible and the output is stored in
term_surveys for reuse by the bias detector (Stage 1) and adjudicator
(Stage 2).

Usage:
    python term_survey.py --seed-list
    python term_survey.py --root Slw
    python term_survey.py --root Slw --force
    python term_survey.py --root Slw --dry-run
    python term_survey.py --root Slw --model claude-opus-4-20250514

Requires CLAUDE_API_KEY in env or stored in admin_preferences.
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

# ------------------------------------------------------------------------
# Config
# ------------------------------------------------------------------------

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-opus-4-20250514"
DEFAULT_PROMPT_VERSION = "v1"
MAX_TOKENS = 4000
MAX_ATTEMPTS = 3

# Which ai_translation config to use as the "current translation" reference.
# gpt5.1-batch-v2 has full-corpus coverage (6236 verses).
DEFAULT_TRANSLATION_CONFIG = "gpt5.1-batch-v2"

# Seed list of ritualistic / commonly-narrowed roots. Buckwalter forms
# match what's in the morphology table. Paired with a short handle and
# Arabic for logs.
SEED_ROOTS: list[tuple[str, str, str]] = [
    ("Slw",  "ص-ل-و",  "ṣalāh (commonly 'prayer'; cf. 33:56 — God does not pray)"),
    ("zkw",  "ز-ك-و",  "zakāh (commonly 'charity tax')"),
    ("Swm",  "ص-و-م",  "ṣawm (commonly 'fasting during Ramadan')"),
    ("Hjj",  "ح-ج-ج",  "ḥajj (commonly 'pilgrimage'; shares root with ḥujjah=argument)"),
    ("sjd",  "س-ج-د",  "sujūd (commonly 'prostration')"),
    ("rkE",  "ر-ك-ع",  "rukūʿ (commonly 'bowing')"),
    ("snn",  "س-ن-ن",  "sunnah (commonly 'the Prophet's way'; Quran's own usage?)"),
    ("nsk",  "ن-س-ك",  "nusuk (commonly 'ritual sacrifice')"),
    ("qwm",  "ق-و-م",  "qiyām (standing) / qawm (a people) — polysemous, test both"),
    ("$Er",  "ش-ع-ر",  "shaʿāʾir (commonly 'sacred rites')"),
    ("Emr",  "ع-م-ر",  "ʿumra (commonly 'minor pilgrimage')"),
    ("*kr",  "ذ-ك-ر",  "dhikr (commonly 'remembrance' narrowed to devotional formulas)"),
    ("Thr",  "ط-ه-ر",  "ṭahāra (commonly 'ritual purification')"),
]

# ------------------------------------------------------------------------
# Prompt
# ------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a Qur'anic semantics specialist auditing the meaning of a single
Arabic root against the Qur'an's own usage patterns — and ONLY the
Qur'an's own usage patterns. Post-Qur'anic Islamic tradition (hadith,
fiqh schools, tafsir, ritual institutions) is NOT evidence. The Qur'an
is a closed, self-contained corpus for this exercise.

The user will give you EVERY Qur'anic occurrence of a root, with verse
reference, Arabic word form, lemma/morphology, and a conventional
English translation for context.

Your job: derive the SINGLE abstract semantic core that honors every
occurrence. Post-Qur'anic tradition has narrowed many of these roots
to specific ritual forms — you must find a meaning that predates that
narrowing and fits all contexts.

Procedure:

  1. List the contexts. Note the breadth of usages.
  2. Identify counter-examples — occurrences where the common/ritual
     translation fails. (E.g. 33:56: Allah and angels cannot "pray";
     so "prayer" cannot be the semantic core of ṣalāh.)
  3. Propose a single abstract English rendering that fits everywhere.
     The rendering should preserve verbal flexibility so it can act as
     verb, noun, participle, etc. with minor inflection.
  4. Verify: run the proposed rendering through the 3-5 hardest
     counter-examples. Does it still land? If not, iterate.
  5. If no single English rendering honors every usage, set
     leave_untranslated=true. This is acceptable but should be
     uncommon — try hard to find the abstract meaning first.

Output ONLY this JSON object. No preamble, no explanation outside it:

{
  "canonical_english": "<single best English rendering, or the transliteration if leaving untranslated>",
  "reasoning": "<2-4 sentences: the semantic thread through all usages>",
  "counter_examples_checked": [
    {"ref": "CHAPTER:VERSE", "usage": "<Arabic word/form>", "how_canonical_fits": "<one sentence>"},
    ...
  ],
  "alternative_forms": {
    "verb": "<e.g. 'connect'>",
    "noun": "<e.g. 'connection'>",
    "participle": "<e.g. 'connecting'>"
  },
  "translation_note": "<reader-facing note, 3-5 sentences, see below>",
  "leave_untranslated": false,
  "transliteration_fallback": "<what to use if leave_untranslated>",
  "confidence": 0.0 to 1.0
}

TRANSLATION_NOTE (reader-facing, public display on the verse page):

Write a short note that a reader will see as a tooltip or footnote.
Tone should be explanatory, not apologetic. No editorializing about
tradition's history. Structure:

  1. "Conventional translations render <Arabic> as '<conventional>'."
  2. Pivot with "However, upon tracing the root <root> across all N
     occurrences we find <broader semantic core>."
  3. "In <verse_ref>, for instance, <counter-example observation>."
  4. "We translate as '<canonical>', which encompasses <conventional>
     as one form of <canonical> while honoring <range-of-usage-summary>."

Tone rules (CRITICAL):
  - NEVER use the phrases: "Qur'an-only methodology we follow",
    "later ritual institution of", "reflecting the institution",
    "post-Qur'anic", "we propose", "bias", "imposed".
  - Just present the evidence and the finding. No self-labeling.
  - 3-5 sentences, flowing prose. No bullet lists.
  - Never mention sectarian affiliations, fiqh schools, or hadith.

Exact template example for ṣalāh (match this tone precisely):

  "Conventional translations render صَلَاة as 'prayer'. However,
  upon tracing the root ص-ل-و across all 99 occurrences we find a
  broader sense of sustained connection or linking. In 33:56, for
  instance, the Qur'an says Allah and the angels 'yuṣallūna' upon
  the Prophet — a usage that the ritual-prayer reading cannot
  accommodate since God does not pray. We translate as 'connect',
  which encompasses prayer as one form of connection while honoring
  the Qur'an's full range of usage, from divine-human links to
  community bonds."

Include AT LEAST 3 counter-examples that actively stress-test the
proposed meaning. If the root is polysemous, identify that in
reasoning and return a canonical that captures the shared abstract
sense if possible, or leave_untranslated=true otherwise.
"""


def parse_seed_list() -> list[tuple[str, str, str]]:
    return SEED_ROOTS


def pull_occurrences(conn, root_bw: str, config_name: str) -> list[dict]:
    """Return all Quranic occurrences of a root, deduped per (chapter,
    verse, word_pos), with the canonical (conventional) translation of
    the verse for context.

    The same verse may appear multiple times if multiple words in it
    share the root — we keep each one, because the same word-form might
    appear twice in different syntactic roles.
    """
    config_row = conn.execute(
        "SELECT id FROM ai_translation_configs WHERE config_name = ?",
        (config_name,),
    ).fetchone()
    if not config_row:
        raise SystemExit(f"ERROR: no ai_translation config {config_name!r}")
    config_id = config_row["id"]

    rows = conn.execute(
        """
        SELECT m.chapter, m.verse, m.word_pos, m.form_arabic, m.pos, m.tag,
               m.lemma_arabic, v.text_uthmani,
               t.translation_text
        FROM morphology m
        JOIN verses v ON v.chapter = m.chapter AND v.verse = m.verse
        LEFT JOIN ai_translations t ON t.chapter = m.chapter
                                   AND t.verse = m.verse
                                   AND t.config_id = ?
        WHERE m.root_buckwalter = ?
        GROUP BY m.chapter, m.verse, m.word_pos
        ORDER BY m.chapter, m.verse, m.word_pos
        """,
        (config_id, root_bw),
    ).fetchall()

    return [dict(r) for r in rows]


def build_user_prompt(root_bw: str, root_arabic: str, note: str, occurrences: list[dict],
                      extra_constraint: str = "") -> str:
    """Format every occurrence for the surveyor prompt. We include the
    Arabic word, its lemma, part of speech, and the verse's current
    English translation. We keep each verse line compact — the total
    corpus for a common root is ~80-100 verses, so we need to stay
    under a reasonable token budget."""
    lines = [
        f"ROOT: {root_bw}  ({root_arabic})",
        f"CONTEXT NOTE: {note}",
        f"TOTAL OCCURRENCES: {len(occurrences)}",
        "",
        "OCCURRENCES (chapter:verse · Arabic form · lemma · pos · conventional English translation):",
    ]
    for o in occurrences:
        ref = f"{o['chapter']}:{o['verse']}"
        form = o.get("form_arabic") or "?"
        lemma = o.get("lemma_arabic") or ""
        pos = o.get("pos") or "?"
        trans = (o.get("translation_text") or "").strip()
        # Trim very long translations so the prompt stays within budget
        if len(trans) > 180:
            trans = trans[:177] + "…"
        lemma_part = f" [lemma: {lemma}]" if lemma else ""
        lines.append(f"  {ref} · {form}{lemma_part} · {pos} — {trans}")
    if extra_constraint:
        lines.append("")
        lines.append("ADDITIONAL CONSTRAINT FOR THIS SURVEY:")
        lines.append(extra_constraint)
    lines.append("")
    lines.append(
        "Derive the canonical Qur'an-only English rendering that honors "
        "every one of these usages. Return only the JSON object."
    )
    return "\n".join(lines)


def call_claude(model: str, system: str, user: str, api_key: str) -> tuple[str, float]:
    """Call Claude with retries. Returns (text_response, elapsed_ms)."""
    last_err = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        t0 = time.time()
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
                    "max_tokens": MAX_TOKENS,
                    "temperature": 0.2,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
                timeout=300,
            )
        except requests.RequestException as e:
            last_err = f"request error: {e}"
        else:
            elapsed = (time.time() - t0) * 1000
            if resp.status_code == 200:
                data = resp.json()
                content_blocks = data.get("content") or []
                text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
                return text, elapsed
            last_err = f"HTTP {resp.status_code}: {resp.text[:400]}"

        if attempt < MAX_ATTEMPTS:
            wait = (2 ** attempt) + 1
            print(f"  retry {attempt}/{MAX_ATTEMPTS} after {wait}s ({last_err})", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"Claude failed after {MAX_ATTEMPTS} attempts: {last_err}")


def parse_response(raw: str) -> dict:
    """Extract the JSON object from Claude's response."""
    text = (raw or "").strip()
    # Strip fences if present
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    # Find the first balanced JSON object
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"No JSON object: {text[:400]!r}")
    return json.loads(m.group())


def save_survey(
    conn, root_bw: str, root_arabic: str, occurrences: list[dict],
    model: str, prompt_version: str, parsed: dict, raw: str,
    force: bool,
) -> bool:
    existing = conn.execute(
        "SELECT id FROM term_surveys WHERE root_buckwalter = ?", (root_bw,),
    ).fetchone()
    if existing and not force:
        return False
    if existing:
        conn.execute("DELETE FROM term_surveys WHERE id = ?", (existing["id"],))

    samples = [
        {
            "chapter": o["chapter"], "verse": o["verse"],
            "arabic_word": o.get("form_arabic"),
            "lemma": o.get("lemma_arabic"),
            "translation": o.get("translation_text"),
        }
        for o in occurrences
    ]

    conn.execute(
        """
        INSERT INTO term_surveys (
            root_buckwalter, root_arabic,
            occurrence_count, occurrence_samples,
            surveyor_model, surveyor_prompt_version,
            canonical_english, reasoning, counter_examples_json,
            translation_note,
            leave_untranslated, confidence, raw_response
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            root_bw, root_arabic,
            len(occurrences), json.dumps(samples, ensure_ascii=False),
            model, prompt_version,
            parsed.get("canonical_english"),
            parsed.get("reasoning"),
            json.dumps(parsed.get("counter_examples_checked") or [], ensure_ascii=False),
            parsed.get("translation_note"),
            1 if parsed.get("leave_untranslated") else 0,
            float(parsed.get("confidence") or 0.0),
            raw,
        ),
    )
    conn.commit()
    return True


def survey_one(
    conn, root_bw: str, root_arabic: str, note: str,
    model: str, prompt_version: str, config_name: str,
    api_key: str, force: bool, dry_run: bool,
    extra_constraint: str = "",
) -> None:
    print(f"\n━━━━━ {root_bw}  ({root_arabic}) ━━━━━")
    occurrences = pull_occurrences(conn, root_bw, config_name)
    if not occurrences:
        print(f"  no occurrences in morphology — skipping")
        return
    print(f"  {len(occurrences)} occurrences")

    user_prompt = build_user_prompt(root_bw, root_arabic, note, occurrences, extra_constraint)

    if dry_run:
        print(f"  (dry-run) prompt length: {len(user_prompt)} chars")
        print("  --- prompt head ---")
        print(user_prompt[:800])
        print("  ...")
        return

    try:
        raw, ms = call_claude(model, SYSTEM_PROMPT, user_prompt, api_key)
        print(f"  Claude responded in {ms:.0f}ms")
    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return

    try:
        parsed = parse_response(raw)
    except Exception as e:
        print(f"  ERROR parsing: {e}", file=sys.stderr)
        print(f"  raw: {raw[:400]!r}", file=sys.stderr)
        return

    wrote = save_survey(
        conn, root_bw, root_arabic, occurrences,
        model, prompt_version, parsed, raw, force,
    )
    if not wrote:
        print(f"  already surveyed (skip — pass --force to overwrite)")
        return

    canonical = parsed.get("canonical_english") or "(none)"
    confidence = parsed.get("confidence") or 0.0
    leave_ut = bool(parsed.get("leave_untranslated"))
    print(f"  → canonical: {canonical!r}  (confidence {confidence:.2f}"
          f"{', leave_untranslated' if leave_ut else ''})")
    reasoning = (parsed.get("reasoning") or "").strip()
    if reasoning:
        print(f"  reasoning: {reasoning[:220]}")
    cex = parsed.get("counter_examples_checked") or []
    if cex:
        print(f"  counter-examples ({len(cex)}):")
        for c in cex[:3]:
            print(f"    {c.get('ref')}: {str(c.get('how_canonical_fits'))[:160]}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--root", help="single Buckwalter root, e.g. Slw")
    p.add_argument("--seed-list", action="store_true", help="survey all default ritualistic roots")
    p.add_argument("--config", default=DEFAULT_TRANSLATION_CONFIG,
                   help="ai_translation config to use as current-translation reference")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--prompt-version", default=DEFAULT_PROMPT_VERSION)
    p.add_argument("--api-key", default=None)
    p.add_argument("--force", action="store_true", help="overwrite existing survey rows")
    p.add_argument("--dry-run", action="store_true", help="print prompts, don't call Claude")
    p.add_argument("--note",
                   help="extra constraint appended to the user prompt — useful for "
                        "collision handling or nudging toward a specific rendering")
    args = p.parse_args()

    api_key = args.api_key or _get_claude_api_key()
    if not api_key and not args.dry_run:
        print("ERROR: no CLAUDE_API_KEY (env, admin_preferences, or --api-key).", file=sys.stderr)
        return 1

    if not args.root and not args.seed_list:
        print("ERROR: pass --root <buckwalter> or --seed-list.", file=sys.stderr)
        return 1

    conn = get_db()
    try:
        if args.seed_list:
            targets = parse_seed_list()
        else:
            targets = [(args.root, args.root, "")]

        for root_bw, root_arabic, note in targets:
            survey_one(
                conn, root_bw, root_arabic, note,
                args.model, args.prompt_version, args.config,
                api_key, args.force, args.dry_run,
                extra_constraint=args.note or "",
            )

        # Quick summary table
        if not args.dry_run:
            print("\n━━━━━ Survey summary ━━━━━")
            rows = conn.execute(
                "SELECT root_buckwalter, root_arabic, canonical_english, "
                "       leave_untranslated, confidence, occurrence_count "
                "FROM term_surveys ORDER BY root_buckwalter"
            ).fetchall()
            for r in rows:
                flag = " [untranslated]" if r["leave_untranslated"] else ""
                print(f"  {r['root_buckwalter']:<5} ({r['root_arabic']})  "
                      f"n={r['occurrence_count']:>4}  "
                      f"conf={r['confidence']:.2f}  "
                      f"→ {r['canonical_english']!r}{flag}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
