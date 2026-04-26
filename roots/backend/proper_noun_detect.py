"""Detect candidates where conventional translations treat descriptive
Arabic phrases as proper nouns (e.g. "Abu Lahab" left untranslated when
the underlying Arabic literally means "father of [burning] flame").

Two-stage pipeline (this script):

  Stage 0 — Mechanical pre-filter, free, full corpus.
            Walks morphology + ai_word_meanings looking for capitalized
            tokens whose underlying Arabic root has descriptive uses
            elsewhere. Indefiniteness, compound-name markers (Abu/Ibn/
            Dhu/etc.), and root-frequency profiles are tallied per row.

  Stage 1 — Ollama cloud detector, cheap. For each Stage-0 candidate
            we ask Qwen 397B and (optionally) gpt-oss 120B:
                "Is this a proper name or a descriptive Arabic phrase?"
            with the verse, word, transliteration, and a sample of
            cross-references where the same root is used non-name-like.
            Both verdicts are stored per-row.

Stage 2 (Sonnet adjudication) lives in proper_noun_adjudicate.py.
Stage 3 (operator review) is the admin UI at /admin/proper-nouns.

Usage:
    python proper_noun_detect.py --stage 0
    python proper_noun_detect.py --stage 1 --models qwen
    python proper_noun_detect.py --stage 1 --models qwen,gptoss --limit 50
    python proper_noun_detect.py --stage 1 --refresh   # re-run on already-stage1 rows
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sqlite3
import sys
import time

import requests

from app import get_db


# ---------------------------------------------------------------------------
# Stage 0 configuration
# ---------------------------------------------------------------------------

# Tokens that are KNOWN proper nouns (real persons, places). Capitalized
# tokens matching these are NOT flagged as candidates. Conservative list —
# unknown capitalized tokens go to the LLMs to adjudicate. Match against
# the lowercased token so case variants are handled uniformly.
KNOWN_NAMES = {
    # Divine
    "allah", "god", "lord",
    # Prophets / persons (English forms)
    "muhammad", "mohammed", "ahmad",
    "moses", "musa", "aaron", "harun",
    "abraham", "ibrahim",
    "ishmael", "ismail",
    "isaac", "ishaq",
    "jacob", "yaqub", "israel", "jacob's",
    "joseph", "yusuf",
    "david", "dawud",
    "solomon", "sulayman",
    "jesus", "isa", "messiah", "christ",
    "mary", "maryam",
    "adam", "eve",
    "noah", "nuh",
    "lot", "lut",
    "job", "ayub",
    "jonah", "yunus", "dhun-nun",
    "zechariah", "zakariyya",
    "john", "yahya",
    "elias", "elijah", "ilyas",
    "elisha", "alyasa",
    "shu'aib", "shuaib", "shoaib",
    "salih",
    "hud",
    "luqman",
    "khidr",
    "imran",
    # Pharaoh / kings
    "pharaoh", "firawn",
    # Locales / tribes
    "mecca", "makka", "bakka",
    "medina", "yathrib",
    "egypt", "misr",
    "babylon", "babil",
    "jerusalem", "bayt",
    # English connectives / articles
    "the", "of", "and", "or", "a", "an", "in", "on", "to", "at", "by",
    "for", "with", "from", "but", "is", "are", "was", "were", "be",
    "as", "if", "so", "no", "not",
    # Common stopwords sometimes fall into translation idiosyncrasies
    "indeed", "truly", "verily",
}

# Compound-name templates worth flagging (the second element is often
# descriptive and translatable). The Buckwalter-form keys handle Arabic;
# the English forms handle the surface translation.
COMPOUND_MARKERS_EN = {"abu", "abi", "ibn", "bin", "umm", "bint", "dhul", "dhu", "dhat", "dhi"}
COMPOUND_MARKERS_AR_LEMMAS = {">abN", "<bn", ">um", "<bn", "*Aw", "*At"}


def _is_capitalized_token(s: str) -> bool:
    """A token is 'capitalized' if it has any uppercase ASCII letter
    AND its leading alphabetic char is uppercase. We use this on per-token
    pieces of preferred_translation to flag possible name-like renderings."""
    if not s:
        return False
    # Strip surrounding punctuation for the test (but keep apostrophes inside)
    core = s.strip(".,;:!?\"'()[]{}<>‘’“”—–-")
    if not core:
        return False
    # Reject tokens that are pure punctuation or numbers
    if not any(c.isalpha() for c in core):
        return False
    first_alpha = next((c for c in core if c.isalpha()), '')
    return first_alpha.isupper()


def _looks_like_proper_noun(translation: str) -> tuple[bool, str | None]:
    """Decide whether a per-word translation looks like a transliterated
    proper noun. Returns (flagged, compound_marker_or_None).

    A translation is flagged when:
      - it has at least one capitalized token NOT in KNOWN_NAMES
      - and the capitalized token isn't a sentence-start English word
        (rough heuristic: tokens after the first that are capitalized are
        more name-like; first-token capitalization is ambiguous)

    Compound markers (Abu/Ibn/etc.) are detected too — those make the
    candidate higher-priority since they're textbook calque sites.
    """
    if not translation:
        return False, None
    text = translation.strip()
    if not text:
        return False, None

    tokens = re.split(r"\s+", text)
    if not tokens:
        return False, None

    compound: str | None = None
    flagged = False
    for i, tok in enumerate(tokens):
        clean = re.sub(r"[^A-Za-z'’\-]", "", tok).strip()
        if not clean:
            continue
        low = clean.lower()
        if low in COMPOUND_MARKERS_EN:
            compound = low
            continue
        # Skip the first token if it's a normal-looking English word — a
        # leading capital is just sentence case.
        if i == 0 and low in KNOWN_NAMES:
            continue
        if _is_capitalized_token(tok) and low not in KNOWN_NAMES:
            flagged = True
    return flagged, compound


def _is_indefinite_morphology_tag(tag: str | None) -> int:
    """Best-effort indefinite detector from morphology.tag string. The
    tagging convention varies; we look for the absence of 'DEF' / 'AL' /
    presence of explicit 'INDEF' as conservative signals."""
    if not tag:
        return 0
    t = tag.upper()
    if "INDEF" in t:
        return 1
    # Many tags include "DEF" for words with al-. Absence is suggestive
    # but not decisive — return 0 in that case so we don't over-claim.
    return 0


# ---------------------------------------------------------------------------
# Stage 0 implementation
# ---------------------------------------------------------------------------

def stage0_detect(conn) -> dict:
    """Run Stage 0 mechanical pre-filter over the entire corpus.
    Inserts new rows into proper_noun_candidates (UNIQUE on chapter,
    verse, word_pos prevents duplicates). Returns counts.
    """
    print("Stage 0: building root-frequency index…")
    root_freq: dict[str, int] = {}
    for r in conn.execute("SELECT root_buckwalter FROM morphology WHERE root_buckwalter IS NOT NULL"):
        root_freq[r["root_buckwalter"]] = root_freq.get(r["root_buckwalter"], 0) + 1
    print(f"  {len(root_freq)} roots in morphology")

    print("Stage 0: scanning translations for capitalized-token candidates…")
    rows = conn.execute(
        "SELECT m.chapter, m.verse, m.word_pos, "
        "       m.form_arabic, m.root_buckwalter, m.lemma_buckwalter, m.tag, "
        "       w.preferred_translation, w.meaning_short "
        "FROM morphology m "
        "LEFT JOIN ai_word_meanings w "
        "  ON w.chapter=m.chapter AND w.verse=m.verse AND w.word_pos=m.word_pos "
        "WHERE m.root_buckwalter IS NOT NULL "
        "ORDER BY m.chapter, m.verse, m.word_pos"
    ).fetchall()
    print(f"  {len(rows)} morphology rows with roots")

    inserted = 0
    skipped_existing = 0
    skipped_no_translation = 0
    candidates_by_type: dict[str, int] = {"compound": 0, "single": 0}

    for row in rows:
        # Prefer judged translation, fall back to meaning_short
        translation = (row["preferred_translation"] or row["meaning_short"] or "").strip()
        if not translation:
            skipped_no_translation += 1
            continue
        flagged, compound = _looks_like_proper_noun(translation)
        if not flagged and not compound:
            continue

        ctype = "compound" if compound else "single"
        rfreq = root_freq.get(row["root_buckwalter"], 0)

        try:
            conn.execute(
                "INSERT INTO proper_noun_candidates ("
                "  chapter, verse, word_pos, "
                "  arabic_word, root_buckwalter, lemma_buckwalter, "
                "  surface_translation, candidate_type, "
                "  is_indefinite, root_quran_frequency, has_compound_marker"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    row["chapter"], row["verse"], row["word_pos"],
                    row["form_arabic"], row["root_buckwalter"], row["lemma_buckwalter"],
                    translation, ctype,
                    _is_indefinite_morphology_tag(row["tag"]),
                    rfreq, compound,
                ),
            )
            inserted += 1
            candidates_by_type[ctype] = candidates_by_type.get(ctype, 0) + 1
        except sqlite3.IntegrityError:
            skipped_existing += 1

    conn.commit()
    print(f"\nStage 0 complete:")
    print(f"  Inserted:           {inserted}")
    print(f"  Already existed:    {skipped_existing}")
    print(f"  No translation:     {skipped_no_translation}")
    print(f"  By type:            {candidates_by_type}")
    return {
        "inserted": inserted,
        "skipped_existing": skipped_existing,
        "skipped_no_translation": skipped_no_translation,
        "by_type": candidates_by_type,
    }


# ---------------------------------------------------------------------------
# Stage 1 — Ollama cloud detector
# ---------------------------------------------------------------------------

OLLAMA_CLOUD_URL = "https://ollama.com/api/chat"
QWEN_MODEL = "qwen3.5:397b-cloud"
GPTOSS_MODEL = "gpt-oss:120b-cloud"  # adjust if exact tag differs

STAGE1_SYSTEM_PROMPT = """\
You are an Arabic-and-Quran expert helping decide whether a particular
translated word in an English Quran translation is being treated as a
PROPER NOUN (an actual person/place name) when it might more
faithfully be rendered as a literal Arabic descriptive phrase.

You will see:
  - The verse reference (e.g. 111:1)
  - The Arabic word (with diacritics)
  - The Arabic root (Buckwalter-transliterated) and lemma
  - The current English rendering
  - A short list of OTHER verses where the same root appears, with
    their conventional English translations — to show how the root is
    used elsewhere in the corpus

Your job is to deliver ONE verdict from this set:
  - "literal"   - the word looks more like a descriptive Arabic phrase
                  that the translator calqued as a name (e.g. "Abu Lahab"
                  for "father of flame", "Dhul-Qarnayn" for "the two-horned
                  one"). Translation should likely be revised.
  - "name"      - the word really is a proper name (person, place,
                  tribe). Leave it as-is.
  - "ambiguous" - genuinely uncertain — reasonable translators could
                  go either way.

Output ONLY a single JSON object, no preamble, no commentary:

{
  "verdict": "literal" | "name" | "ambiguous",
  "confidence": <float 0.0 to 1.0>,
  "reasoning": "<2-4 sentences citing concrete evidence — frequency,
                indefiniteness, cross-references, compound structure>"
}
"""


def _gather_cross_references(conn, root_bw: str, exclude_chapter: int, exclude_verse: int, n: int = 6) -> list[dict]:
    """Pick up to N other verses where this root appears, with English
    translation. Used as evidence for the LLM."""
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
    # Sample evenly across the corpus: take every Nth so we get diverse
    # examples rather than just the first N (which tend to cluster early).
    if len(rows) > n:
        step = max(1, len(rows) // n)
        rows = rows[::step][:n]
    return [
        {"ref": f"{r['chapter']}:{r['verse']}", "translation": (r["translation_text"] or "")[:300]}
        for r in rows
    ]


def _build_stage1_prompt(conn, candidate: dict) -> str:
    refs = _gather_cross_references(
        conn, candidate["root_buckwalter"], candidate["chapter"], candidate["verse"], n=6,
    )
    parts = [
        f"VERSE: {candidate['chapter']}:{candidate['verse']}",
        f"ARABIC WORD: {candidate['arabic_word']}",
        f"ROOT (Buckwalter): {candidate['root_buckwalter']}",
        f"LEMMA: {candidate.get('lemma_buckwalter') or '(unknown)'}",
        f"CURRENT ENGLISH: {candidate['surface_translation']}",
        "",
        f"COMPOUND MARKER PRESENT: {candidate.get('has_compound_marker') or '(none)'}",
        f"ROOT INDEFINITE IN ARABIC: {'yes' if candidate.get('is_indefinite') else 'unknown'}",
        f"ROOT FREQUENCY IN CORPUS: {candidate.get('root_quran_frequency')}",
        "",
        "OTHER VERSES USING THIS ROOT (for context):",
    ]
    if refs:
        for r in refs:
            parts.append(f"  - {r['ref']}: {r['translation']}")
    else:
        parts.append("  (none with translations)")
    parts += [
        "",
        "Decide whether the current English rendering is a proper name or a"
        " descriptive phrase being calqued as a name. Output JSON only.",
    ]
    return "\n".join(parts)


def call_ollama(model: str, system: str, user: str, api_key: str, timeout: int = 120) -> tuple[str, int]:
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": 0.2},
    }
    t0 = time.time()
    last_err = None
    for attempt in range(1, 4):
        try:
            resp = requests.post(OLLAMA_CLOUD_URL, headers=headers, json=payload, timeout=timeout)
            if resp.status_code == 200:
                content = resp.json().get("message", {}).get("content", "")
                return content, int((time.time() - t0) * 1000)
            if 400 <= resp.status_code < 500 and resp.status_code != 429:
                raise RuntimeError(f"Ollama {resp.status_code}: {resp.text[:300]}")
            last_err = f"HTTP {resp.status_code}"
        except requests.RequestException as e:
            last_err = f"req: {e}"
        if attempt < 3:
            time.sleep(random.uniform(2, 6) * attempt)
    raise RuntimeError(f"Ollama failed: {last_err}")


def _parse_stage1_response(raw: str) -> dict:
    """Extract { verdict, confidence, reasoning } from model output.
    Tolerant of code fences and surrounding text."""
    text = (raw or "").strip()
    # Strip <think>...</think> blocks Qwen sometimes emits
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"no JSON found: {text[:300]!r}")
    obj = json.loads(m.group())
    verdict = (obj.get("verdict") or "").strip().lower()
    if verdict not in ("literal", "name", "ambiguous"):
        raise ValueError(f"bad verdict: {verdict!r}")
    confidence = float(obj.get("confidence", 0.5))
    confidence = max(0.0, min(1.0, confidence))
    return {
        "verdict": verdict,
        "confidence": confidence,
        "reasoning": (obj.get("reasoning") or "").strip()[:2000],
    }


def stage1_run(conn, api_key: str, models: list[str], limit: int | None, refresh: bool) -> dict:
    """Run Stage 1 detector on candidates without stage1_run_at (or all
    if refresh). One row updated per (candidate, model)."""
    where = "WHERE stage1_run_at IS NULL" if not refresh else ""
    sql = (
        "SELECT id, chapter, verse, word_pos, arabic_word, "
        "       root_buckwalter, lemma_buckwalter, surface_translation, "
        "       candidate_type, is_indefinite, root_quran_frequency, "
        "       has_compound_marker "
        f"FROM proper_noun_candidates {where} "
        "ORDER BY id"
    )
    candidates = [dict(r) for r in conn.execute(sql).fetchall()]
    if limit:
        candidates = candidates[:limit]

    print(f"Stage 1: processing {len(candidates)} candidates with models: {models}")
    stats = {"qwen_ok": 0, "qwen_err": 0, "gptoss_ok": 0, "gptoss_err": 0, "total": len(candidates)}

    for i, c in enumerate(candidates, 1):
        prompt = _build_stage1_prompt(conn, c)
        ref = f"{c['chapter']}:{c['verse']}/p{c['word_pos']}"
        print(f"\n[{i}/{len(candidates)}] {ref}  '{c['surface_translation']}'  (root={c['root_buckwalter']})")

        if "qwen" in models:
            try:
                raw, ms = call_ollama(QWEN_MODEL, STAGE1_SYSTEM_PROMPT, prompt, api_key)
                parsed = _parse_stage1_response(raw)
                conn.execute(
                    "UPDATE proper_noun_candidates SET "
                    "  qwen_verdict = ?, qwen_confidence = ?, qwen_reasoning = ?, "
                    "  stage1_run_at = COALESCE(stage1_run_at, datetime('now')) "
                    "WHERE id = ?",
                    (parsed["verdict"], parsed["confidence"], parsed["reasoning"], c["id"]),
                )
                conn.commit()
                stats["qwen_ok"] += 1
                print(f"  qwen: {parsed['verdict']} ({parsed['confidence']:.2f}) [{ms} ms]")
            except Exception as e:
                stats["qwen_err"] += 1
                print(f"  qwen ERROR: {e}", file=sys.stderr)

        if "gptoss" in models:
            try:
                raw, ms = call_ollama(GPTOSS_MODEL, STAGE1_SYSTEM_PROMPT, prompt, api_key)
                parsed = _parse_stage1_response(raw)
                conn.execute(
                    "UPDATE proper_noun_candidates SET "
                    "  gptoss_verdict = ?, gptoss_confidence = ?, gptoss_reasoning = ?, "
                    "  stage1_run_at = COALESCE(stage1_run_at, datetime('now')) "
                    "WHERE id = ?",
                    (parsed["verdict"], parsed["confidence"], parsed["reasoning"], c["id"]),
                )
                conn.commit()
                stats["gptoss_ok"] += 1
                print(f"  gptoss: {parsed['verdict']} ({parsed['confidence']:.2f}) [{ms} ms]")
            except Exception as e:
                stats["gptoss_err"] += 1
                print(f"  gptoss ERROR: {e}", file=sys.stderr)

    print(f"\nStage 1 complete: {stats}")
    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _get_ollama_api_key(conn) -> str:
    row = conn.execute(
        "SELECT value FROM admin_preferences WHERE key='ollama_api_key'"
    ).fetchone()
    return (row["value"] if row else "") or ""


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--stage", type=int, choices=[0, 1], required=True)
    p.add_argument("--models", default="qwen", help="comma-separated: qwen,gptoss")
    p.add_argument("--limit", type=int)
    p.add_argument("--refresh", action="store_true",
                   help="(stage 1) re-run on already-completed candidates")
    args = p.parse_args()

    conn = get_db()
    conn.row_factory = sqlite3.Row

    if args.stage == 0:
        stage0_detect(conn)
    else:
        api_key = _get_ollama_api_key(conn)
        if not api_key:
            print("ERROR: no ollama_api_key in admin_preferences.", file=sys.stderr)
            return 1
        models = [m.strip() for m in args.models.split(",") if m.strip()]
        if not models:
            print("ERROR: --models cannot be empty", file=sys.stderr)
            return 1
        stage1_run(conn, api_key, models, args.limit, args.refresh)

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
