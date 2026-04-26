"""Stage 2 of the proper-noun-calque pipeline. Pairs with
proper_noun_detect.py (Stage 0 mechanical + Stage 1 Ollama) and
proper_noun_apply.py (Stage 4 application).

Stage 2 takes Stage-0+1 candidates and asks Claude Sonnet for the final
adjudication. The Sonnet prompt sees:

  - The verse text (Arabic + English)
  - The candidate word and its current English rendering
  - Both Stage-1 LLM verdicts (Qwen + gpt-oss when available) so Sonnet
    can weigh them — the heuristic insight is that **disagreement
    between the cheap models is a signal that Sonnet should be careful**.
  - A wider sample of cross-references where the same root appears,
    with their conventional English translations as evidence.

Sonnet returns:

  {
    "verdict":      "literal" | "name" | "ambiguous",
    "alternatives": [
        {"translation": "...", "rationale": "..."},
        ...   // up to 4, ordered by recommendation
    ],
    "reasoning":   "<paragraph explaining the verdict>",
    "supporting_refs": ["55:6", "77:31", ...]
  }

Usage:
    python proper_noun_adjudicate.py                    # all unadjudicated
    python proper_noun_adjudicate.py --limit 5
    python proper_noun_adjudicate.py --only-disagreement  # only when qwen != gptoss
    python proper_noun_adjudicate.py --refresh          # re-adjudicate all
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time

import requests

from app import get_db, _get_claude_api_key

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-20250514"


SYSTEM_PROMPT = """\
You are an expert in Classical Arabic and Qur'anic philology. Your task
is to adjudicate whether a particular word in an English Qur'an
translation is being treated as a PROPER NAME (a person/place/tribe)
when it might more faithfully be rendered as a literal Arabic
descriptive phrase. The classic example is "Abu Lahab" (111:1) — read
as a name in conventional translations but literally meaning "father
of [burning] flame" with the underlying root used elsewhere as a
common word for fire.

You will receive:
  - Verse reference, Arabic text, and current English translation
  - The specific word + its Arabic root (Buckwalter form)
  - Indefiniteness, compound markers, and root-frequency stats
  - Two PRELIMINARY verdicts from cheap models (Qwen, gpt-oss) — when
    they DISAGREE, treat the case as harder and reason carefully
  - A sample of OTHER verses where the same root appears, with their
    English — to see how the root is used elsewhere

Decide:

  "literal"   — the word is a descriptive phrase being calqued as a
                name. Translation should be revised.
  "name"      — the word really is a person/place/tribe name. Leave it.
  "ambiguous" — genuinely uncertain (rare; reserve for cases where
                evidence is split or interpretive).

For "literal" and "ambiguous" verdicts, propose 2-4 ALTERNATIVE English
renderings, ordered from most-recommended to most-conservative. Each
should reflect different points on the literalness spectrum. Examples
for Abu Lahab might be:
  - "father of [burning] flame"   (most literal, bracketed clarification)
  - "father of flame"             (clean literal)
  - "the inflamed one"            (tighter idiomatic)
  - "Abu Lahab (lit. 'father of flame')"  (preserve traditional reading)

For "name" verdicts, the alternatives array should be empty.

Cite supporting cross-references (verse refs from the input list) that
informed your decision in `supporting_refs`.

Output ONLY a single JSON object — no preamble, no commentary:

{
  "verdict": "literal" | "name" | "ambiguous",
  "alternatives": [
    {"translation": "...", "rationale": "..."},
    ...
  ],
  "reasoning": "<2-4 sentences>",
  "supporting_refs": ["X:Y", ...]
}
"""


def _gather_cross_references(conn, root_bw: str, exclude_chapter: int, exclude_verse: int, n: int = 10) -> list[dict]:
    """Wider net than Stage 1 — Sonnet handles more context well."""
    rows = conn.execute(
        "SELECT m.chapter, m.verse, t.translation_text "
        "FROM morphology m "
        "LEFT JOIN ai_translations t ON t.chapter=m.chapter AND t.verse=m.verse "
        "WHERE m.root_buckwalter = ? "
        "  AND NOT (m.chapter = ? AND m.verse = ?) "
        "  AND t.translation_text IS NOT NULL "
        "GROUP BY m.chapter, m.verse "
        "ORDER BY m.chapter, m.verse",
        (root_bw, exclude_chapter, exclude_verse),
    ).fetchall()
    if len(rows) > n:
        step = max(1, len(rows) // n)
        rows = rows[::step][:n]
    return [
        {"ref": f"{r['chapter']}:{r['verse']}", "translation": (r["translation_text"] or "")[:300]}
        for r in rows
    ]


def _verse_arabic(conn, ch: int, vs: int) -> str:
    row = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter=? AND verse=?", (ch, vs),
    ).fetchone()
    return row["text_uthmani"] if row and row["text_uthmani"] else ""


def _verse_english(conn, ch: int, vs: int) -> str:
    row = conn.execute(
        "SELECT translation_text, revised_text FROM ai_translations "
        "WHERE chapter=? AND verse=?", (ch, vs),
    ).fetchone()
    if not row:
        return ""
    return (row["revised_text"] or row["translation_text"] or "")


def build_prompt(conn, candidate: dict) -> str:
    arabic = _verse_arabic(conn, candidate["chapter"], candidate["verse"])
    english = _verse_english(conn, candidate["chapter"], candidate["verse"])
    refs = _gather_cross_references(
        conn, candidate["root_buckwalter"], candidate["chapter"], candidate["verse"], n=10,
    )

    parts = [
        f"VERSE: {candidate['chapter']}:{candidate['verse']}",
        f"ARABIC: {arabic or '(unavailable)'}",
        f"ENGLISH: {english or '(unavailable)'}",
        "",
        f"WORD IN QUESTION: {candidate.get('arabic_word') or '(?)'}",
        f"ROOT (Buckwalter): {candidate['root_buckwalter']}",
        f"LEMMA: {candidate.get('lemma_buckwalter') or '(?)'}",
        f"CURRENT ENGLISH RENDERING: {candidate['surface_translation']}",
        "",
        f"COMPOUND MARKER: {candidate.get('has_compound_marker') or '(none)'}",
        f"ARABIC INDEFINITE: {'yes' if candidate.get('is_indefinite') else 'unknown'}",
        f"ROOT FREQUENCY: {candidate.get('root_quran_frequency')} occurrences in the Qur'an",
        "",
        "STAGE-1 PRELIMINARY VERDICTS:",
    ]
    qv = candidate.get("qwen_verdict")
    if qv:
        parts.append(
            f"  - Qwen 397B: {qv} (confidence {candidate.get('qwen_confidence', 0):.2f})"
        )
        if candidate.get("qwen_reasoning"):
            parts.append(f"    reasoning: {candidate['qwen_reasoning'][:400]}")
    gv = candidate.get("gptoss_verdict")
    if gv:
        parts.append(
            f"  - gpt-oss 120B: {gv} (confidence {candidate.get('gptoss_confidence', 0):.2f})"
        )
        if candidate.get("gptoss_reasoning"):
            parts.append(f"    reasoning: {candidate['gptoss_reasoning'][:400]}")
    if qv and gv and qv != gv:
        parts.append("  *** MODELS DISAGREE — reason carefully. ***")

    parts += [
        "",
        "OTHER VERSES USING THIS ROOT (evidence — note any descriptive uses):",
    ]
    if refs:
        for r in refs:
            parts.append(f"  - {r['ref']}: {r['translation']}")
    else:
        parts.append("  (none with translations)")

    parts += [
        "",
        "Adjudicate. Output the JSON object only.",
    ]
    return "\n".join(parts)


def call_claude(model: str, system: str, user: str, api_key: str) -> str:
    """Single-attempt Sonnet call with a 45s timeout. The frontend
    retry-with-backoff loop handles transient failures; doing multi-
    attempt retries here just stretches a slow chunk past the proxy
    timeout in front of the API."""
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
                "max_tokens": 2500,
                "temperature": 0.2,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
            timeout=45,
        )
    except requests.RequestException as e:
        raise RuntimeError(f"Claude request failed: {e}") from e
    if resp.status_code != 200:
        raise RuntimeError(f"Claude HTTP {resp.status_code}: {resp.text[:300]}")
    return "".join(
        b.get("text", "")
        for b in resp.json().get("content", [])
        if b.get("type") == "text"
    ).strip()


def parse_response(raw: str) -> dict:
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"no JSON: {text[:300]!r}")
    obj = json.loads(m.group())
    verdict = (obj.get("verdict") or "").strip().lower()
    if verdict not in ("literal", "name", "ambiguous"):
        raise ValueError(f"bad verdict: {verdict!r}")
    alts = obj.get("alternatives") or []
    if not isinstance(alts, list):
        alts = []
    cleaned_alts = []
    for a in alts:
        if isinstance(a, dict) and a.get("translation"):
            cleaned_alts.append({
                "translation": str(a["translation"]).strip(),
                "rationale": str(a.get("rationale", "")).strip(),
            })
    refs = obj.get("supporting_refs") or []
    if not isinstance(refs, list):
        refs = []
    cleaned_refs = [str(r).strip() for r in refs if r]
    return {
        "verdict": verdict,
        "alternatives": cleaned_alts,
        "reasoning": (obj.get("reasoning") or "").strip()[:3000],
        "supporting_refs": cleaned_refs,
    }


def adjudicate_one(conn, candidate: dict, model: str, api_key: str, dry_run: bool) -> str:
    ref = f"{candidate['chapter']}:{candidate['verse']}/p{candidate['word_pos']}"
    prompt = build_prompt(conn, candidate)
    if dry_run:
        print(f"\n--- {ref} would adjudicate ---")
        print(prompt[:1500])
        return "dry-run"
    try:
        raw = call_claude(model, SYSTEM_PROMPT, prompt, api_key)
        parsed = parse_response(raw)
    except Exception as e:
        print(f"  {ref} ERROR: {e}", file=sys.stderr)
        return "error"

    conn.execute(
        "UPDATE proper_noun_candidates SET "
        "  sonnet_verdict = ?, "
        "  sonnet_alternatives_json = ?, "
        "  sonnet_reasoning = ?, "
        "  sonnet_supporting_refs_json = ?, "
        "  stage2_run_at = datetime('now') "
        "WHERE id = ?",
        (
            parsed["verdict"],
            json.dumps(parsed["alternatives"]),
            parsed["reasoning"],
            json.dumps(parsed["supporting_refs"]),
            candidate["id"],
        ),
    )
    conn.commit()
    print(f"  → {ref}: {parsed['verdict']} (alts: {len(parsed['alternatives'])})")
    return "adjudicated"


def collect_targets(conn, refresh: bool, only_disagreement: bool) -> list[dict]:
    """Candidates needing Stage 2. Default: stage1 done, stage2 missing."""
    sql = (
        "SELECT id, chapter, verse, word_pos, arabic_word, "
        "       root_buckwalter, lemma_buckwalter, surface_translation, "
        "       candidate_type, is_indefinite, root_quran_frequency, "
        "       has_compound_marker, "
        "       qwen_verdict, qwen_confidence, qwen_reasoning, "
        "       gptoss_verdict, gptoss_confidence, gptoss_reasoning "
        "FROM proper_noun_candidates "
        "WHERE stage1_run_at IS NOT NULL "
    )
    if not refresh:
        sql += "  AND stage2_run_at IS NULL "
    sql += "ORDER BY id"

    rows = [dict(r) for r in conn.execute(sql).fetchall()]
    if only_disagreement:
        rows = [
            r for r in rows
            if r.get("qwen_verdict") and r.get("gptoss_verdict")
            and r["qwen_verdict"] != r["gptoss_verdict"]
        ]
    return rows


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--limit", type=int)
    p.add_argument("--refresh", action="store_true",
                   help="re-adjudicate already-adjudicated rows")
    p.add_argument("--only-disagreement", action="store_true",
                   help="only adjudicate rows where qwen and gptoss disagreed")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    api_key = _get_claude_api_key()
    if not api_key and not args.dry_run:
        print("ERROR: no CLAUDE_API_KEY", file=sys.stderr)
        return 1

    conn = get_db()
    conn.row_factory = sqlite3.Row

    targets = collect_targets(conn, args.refresh, args.only_disagreement)
    if args.limit:
        targets = targets[: args.limit]

    print(f"Adjudicating {len(targets)} candidates with {args.model}")

    stats = {"adjudicated": 0, "error": 0, "dry-run": 0}
    for c in targets:
        result = adjudicate_one(conn, c, args.model, api_key, args.dry_run)
        stats[result] = stats.get(result, 0) + 1

    print(f"\nDone: {stats}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
