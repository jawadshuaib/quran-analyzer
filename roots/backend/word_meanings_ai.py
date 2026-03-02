"""AI-powered per-word meaning pipeline using Ollama or OpenAI.

Derives context-dependent word meanings from Quranic cross-references,
Semitic cognates, and morphology.

Uses Zipf's law to optimize: high-frequency lemmas (>= threshold) are
translated once and reused; low-frequency lemmas get per-occurrence
context-specific translations.

Usage:
    python word_meanings_ai.py --verses "1:1-7,2:255" --config "word-meaning-v1"
    python word_meanings_ai.py --verses "1:1" --dry-run
    python word_meanings_ai.py --verses "1:1" --force
    python word_meanings_ai.py --verses "1:1" --word-pos 3
    python word_meanings_ai.py --verses "2:19" --model gpt-5.1 --freq-threshold 5
"""

import argparse
import json
import os
import re
import sys
import time

import requests

from app import (
    DB_PATH,
    _get_cognate,
    _lemma_inv,
    _root_inv,
    _root_arabic_map,
    _strip_bismillah,
    _fetch_word_glosses,
    get_db,
)
from translate_ai import call_model, _is_openai_model

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "qwen3:14b"
DEFAULT_FREQ_THRESHOLD = 5

# ── Lemma frequency cache (built once) ──
_lemma_freq: dict[str, int] = {}


def _build_lemma_freq(conn):
    """Build a cache of lemma -> occurrence count."""
    global _lemma_freq
    if _lemma_freq:
        return
    rows = conn.execute(
        "SELECT lemma_buckwalter, COUNT(*) as cnt "
        "FROM morphology "
        "WHERE lemma_buckwalter IS NOT NULL AND lemma_buckwalter != '' "
        "GROUP BY lemma_buckwalter"
    ).fetchall()
    _lemma_freq = {r["lemma_buckwalter"]: r["cnt"] for r in rows}


def get_lemma_frequency(lemma_bw: str) -> int:
    """Return how many times this lemma appears in the Quran."""
    return _lemma_freq.get(lemma_bw, 0)


def find_existing_lemma_meaning(conn, lemma_bw: str, config_id: int) -> dict | None:
    """Find an existing AI meaning for this lemma (any occurrence). Returns parsed fields or None."""
    # Join with morphology to find ai_word_meanings for any word with the same lemma
    row = conn.execute(
        "SELECT wm.meaning_short, wm.meaning_detailed, wm.semantic_field, "
        "       wm.cross_ref_notes, wm.cognate_notes, wm.morphology_notes, "
        "       wm.departure_notes, wm.chapter, wm.verse, wm.word_pos "
        "FROM ai_word_meanings wm "
        "JOIN morphology m ON wm.chapter = m.chapter AND wm.verse = m.verse AND wm.word_pos = m.word_pos "
        "WHERE m.lemma_buckwalter = ? AND wm.config_id = ? "
        "LIMIT 1",
        (lemma_bw, config_id),
    ).fetchone()
    if not row:
        return None
    return {
        "meaning_short": row["meaning_short"],
        "meaning_detailed": row["meaning_detailed"],
        "semantic_field": row["semantic_field"],
        "cross_ref_notes": row["cross_ref_notes"],
        "cognate_notes": row["cognate_notes"],
        "morphology_notes": row["morphology_notes"],
        "departure_notes": row["departure_notes"],
        "source": f"{row['chapter']}:{row['verse']} word {row['word_pos']}",
    }


SYSTEM_PROMPT = """\
You are a Quranic word meaning engine. Your task is to determine the precise \
meaning of a SINGLE Arabic word in its specific Quranic context using ONLY the \
evidence provided below. Do NOT rely on conventional translations, tafsir \
traditions, or external knowledge. Treat the conventional gloss as a HYPOTHESIS \
to be tested against the evidence, not as a default to fall back on.

## Your Methodology (follow in this order)

1. **Semitic Cognate Evidence (start here)**: The cognate data reveals the \
ORIGINAL semantic core of the root before later theological traditions narrowed \
or shifted its meaning. You MUST engage with the cognate evidence directly and \
substantively. If cognates across multiple Semitic languages converge on a meaning \
that differs from the conventional gloss, this is strong evidence that the \
conventional gloss may be a later semantic drift. Explain concretely how the \
cognate meanings relate to or challenge the conventional gloss. Never dismiss \
cognate evidence as irrelevant — if the data is provided, it is relevant.

2. **Cross-Reference Analysis**: Examine how the same lemma and root appear in \
other Quranic verses. Look for patterns: does the Quran use this word in ways \
that align with the cognate meaning or with the conventional gloss? If cross-references \
show the word functioning in a way consistent with the cognate meaning, this \
strengthens the case for departing from convention.

3. **Morphological Precision**: Respect the exact verb form (I-X), voice \
(active/passive), mood (indicative/subjunctive/jussive), case marking \
(nominative/accusative/genitive), and number/gender. These constrain meaning. \
Consider how the morphological form interacts with the semantic range established \
by cognates and cross-references.

4. **Contextual Coherence**: The surrounding verses provide the immediate narrative \
or thematic flow. Test whether the cognate-informed meaning fits the context \
BETTER than the conventional gloss. Often it does.

5. **Synthesize and Decide**: Weigh all evidence. If the cognates, cross-references, \
and morphology converge on a meaning different from the conventional gloss, you \
MUST follow the evidence and note the departure. Do not default to convention \
out of caution — the whole purpose of this analysis is to surface meanings that \
conventional glosses may have obscured.

## Output Format

Respond in EXACTLY this format (no extra text before or after):

MEANING_SHORT: [2-5 word English meaning for this word in this context]
MEANING_DETAILED: [1-3 paragraphs explaining why this meaning is correct, \
citing specific cross-references and cognate evidence]
SEMANTIC_FIELD: [comma-separated related concepts, e.g. "mercy, compassion, womb"]
CROSS_REF_NOTES: [Which cross-reference verses were most informative and why]
COGNATE_NOTES: [How the cognate data informed or challenged your understanding \
of this word. Address the cognate evidence directly — what do the cognates suggest, \
and how does that compare to the conventional gloss?]
MORPHOLOGY_NOTES: [How the grammatical form constrains or specifies the meaning]
DEPARTURE: [How and why this differs from the conventional gloss, or "None" \
ONLY if cognates, cross-refs, and morphology all genuinely support the conventional gloss]\
"""


def parse_verse_spec(spec: str) -> list[tuple[int, int]]:
    """Parse verse specification like '1:1-7,24:41,2:255' into (surah, ayah) pairs."""
    verses = []
    for part in spec.split(","):
        part = part.strip()
        match = re.match(r"(\d+):(\d+)-(\d+)$", part)
        if match:
            surah, start, end = int(match.group(1)), int(match.group(2)), int(match.group(3))
            for ayah in range(start, end + 1):
                verses.append((surah, ayah))
        else:
            match = re.match(r"(\d+):(\d+)$", part)
            if match:
                verses.append((int(match.group(1)), int(match.group(2))))
            else:
                print(f"Warning: skipping invalid verse spec '{part}'")
    return verses


def get_or_create_config(conn, config_name: str, model_name: str) -> int:
    """Get or create an AI translation config, returning its ID."""
    row = conn.execute(
        "SELECT id FROM ai_translation_configs WHERE config_name = ?",
        (config_name,),
    ).fetchone()
    if row:
        return row["id"]

    conn.execute(
        "INSERT INTO ai_translation_configs "
        "(config_name, model_name, system_prompt, methodology_notes) "
        "VALUES (?, ?, ?, ?)",
        (
            config_name,
            model_name,
            SYSTEM_PROMPT,
            "Per-word meaning: cross-references, cognates, morphology. No external tafsir.",
        ),
    )
    conn.commit()
    return conn.execute(
        "SELECT id FROM ai_translation_configs WHERE config_name = ?",
        (config_name,),
    ).fetchone()["id"]


def build_word_prompt(conn, surah: int, ayah: int, word_pos: int) -> str | None:
    """Assemble the full prompt for a single word. Returns None if word should be skipped."""

    # 1. Get morphology for this word
    morph_rows = conn.execute(
        "SELECT word_pos, segment, form_arabic, form_buckwalter, tag, pos, "
        "       root_buckwalter, root_arabic, lemma_buckwalter, lemma_arabic, "
        "       features_raw, gender, number, person, case_val, voice, mood, "
        "       verb_form, state "
        "FROM morphology WHERE chapter = ? AND verse = ? AND word_pos = ? "
        "ORDER BY segment",
        (surah, ayah, word_pos),
    ).fetchall()

    if not morph_rows:
        return None

    # Skip words where all segments are Prefix/Suffix with no root or lemma
    has_content = any(
        (row["root_buckwalter"] or row["lemma_buckwalter"])
        and row["pos"] not in ("Prefix", "Suffix")
        for row in morph_rows
    )
    if not has_content:
        return None

    # Find main segment info
    main = morph_rows[0]
    root_bw = None
    root_ar = None
    lemma_bw = None
    lemma_ar = None
    main_pos = None
    for row in morph_rows:
        if row["root_buckwalter"] and not root_bw:
            root_bw = row["root_buckwalter"]
            root_ar = row["root_arabic"]
        if row["lemma_buckwalter"] and not lemma_bw:
            lemma_bw = row["lemma_buckwalter"]
            lemma_ar = row["lemma_arabic"]
        if row["pos"] and row["pos"] not in ("Prefix", "Suffix") and not main_pos:
            main_pos = row["pos"]
            main = row

    features = []
    for key in ("gender", "number", "person", "case_val", "voice", "mood", "verb_form", "state"):
        val = main[key]
        if val:
            features.append(f"{key.replace('_', ' ')}={val}")
    feature_str = ", ".join(features) if features else "none"

    # Get conventional gloss
    glosses = _fetch_word_glosses(conn, surah, ayah)
    conventional_gloss = glosses.get(word_pos, "")

    # 2. Get verse text + translation
    verse_row = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
        (surah, ayah),
    ).fetchone()
    if not verse_row:
        return None

    arabic_text = _strip_bismillah(verse_row["text_uthmani"], surah, ayah)

    trans_row = conn.execute(
        "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
        (surah, ayah),
    ).fetchone()
    conventional_trans = trans_row["text_en"] if trans_row else "(no translation)"

    # 3. Surrounding context (3 before + 3 after)
    context_rows = conn.execute(
        "SELECT v.chapter, v.verse, v.text_uthmani, t.text_en "
        "FROM verses v LEFT JOIN translations t "
        "ON v.chapter = t.chapter AND v.verse = t.verse "
        "WHERE v.chapter = ? AND v.verse BETWEEN ? AND ? AND v.verse != ? "
        "ORDER BY v.verse",
        (surah, max(1, ayah - 3), ayah + 3, ayah),
    ).fetchall()

    context_lines = []
    for r in context_rows:
        text = _strip_bismillah(r["text_uthmani"], r["chapter"], r["verse"])
        trans = r["text_en"] or ""
        label = "BEFORE" if r["verse"] < ayah else "AFTER"
        context_lines.append(f"  [{label}] {r['chapter']}:{r['verse']} — {text}\n    Translation: {trans}")

    # 4. Same-lemma cross-references (primary evidence)
    lemma_xref_lines = []
    if lemma_bw:
        lemma_verses = sorted(_lemma_inv.get(lemma_bw, set()))
        count = 0
        for ch, v in lemma_verses:
            if ch == surah and v == ayah:
                continue
            if count >= 10:
                break

            v_row = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?", (ch, v)
            ).fetchone()
            t_row = conn.execute(
                "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?", (ch, v)
            ).fetchone()
            text = _strip_bismillah(v_row["text_uthmani"], ch, v) if v_row else ""
            trans = t_row["text_en"] if t_row else ""

            # Get the word gloss for the matching word position in this verse
            occ_morph = conn.execute(
                "SELECT DISTINCT word_pos FROM morphology "
                "WHERE chapter = ? AND verse = ? AND lemma_buckwalter = ?",
                (ch, v, lemma_bw),
            ).fetchall()
            occ_glosses = _fetch_word_glosses(conn, ch, v)
            word_glosses_str = ", ".join(
                f"word {r['word_pos']}: \"{occ_glosses.get(r['word_pos'], '')}\""
                for r in occ_morph
            )

            lemma_xref_lines.append(
                f"  {ch}:{v} — {text}\n"
                f"    Translation: {trans}\n"
                f"    Word glosses: {word_glosses_str}"
            )
            count += 1

    # 5. Same-root cross-references (excluding lemma hits, up to 5)
    root_xref_lines = []
    if root_bw:
        lemma_verse_set = _lemma_inv.get(lemma_bw, set()) if lemma_bw else set()
        root_verses = sorted(_root_inv.get(root_bw, set()))
        count = 0
        for ch, v in root_verses:
            if ch == surah and v == ayah:
                continue
            if (ch, v) in lemma_verse_set:
                continue
            if count >= 5:
                break

            v_row = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?", (ch, v)
            ).fetchone()
            t_row = conn.execute(
                "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?", (ch, v)
            ).fetchone()
            text = _strip_bismillah(v_row["text_uthmani"], ch, v) if v_row else ""
            trans = t_row["text_en"] if t_row else ""

            root_xref_lines.append(
                f"  {ch}:{v} (same root, different lemma) — {text}\n"
                f"    Translation: {trans}"
            )
            count += 1

    # 6. Semitic cognate data
    cognate_lines = []
    if root_bw:
        cognate = _get_cognate(conn, root_bw)
        if cognate:
            cognate_lines.append(f"  Root {root_ar} ({root_bw}) — Proto-Semitic concept: {cognate['concept']}")
            for d in cognate["derivatives"][:8]:
                cognate_lines.append(
                    f"    [{d['language']}] {d['word']} — {d['meaning']}"
                )

    # Assemble the prompt
    prompt = f"""## Target Word
Position {word_pos} in verse {surah}:{ayah}
Arabic form: {main["form_arabic"]}
Root: {root_ar or "—"} ({root_bw or "—"})
Lemma: {lemma_ar or "—"} ({lemma_bw or "—"})
POS: {main_pos or main["tag"]}
Morphological features: {feature_str}
Conventional gloss: "{conventional_gloss}"

## Full Verse
{surah}:{ayah} — {arabic_text}
Translation: {conventional_trans}

## Surrounding Context
{chr(10).join(context_lines) if context_lines else "  (none available)"}

## Same-Lemma Cross-References (primary evidence — same lemma in other verses)
{chr(10).join(lemma_xref_lines) if lemma_xref_lines else "  (none found)"}

## Same-Root Cross-References (different lemmas from the same root)
{chr(10).join(root_xref_lines) if root_xref_lines else "  (none found)"}

## Semitic Cognate Evidence
{chr(10).join(cognate_lines) if cognate_lines else "  (none available)"}

Now determine the meaning of this word (position {word_pos}: {main["form_arabic"]}) in this specific context. Follow the methodology in your instructions. /no_think"""

    return prompt


def call_ollama(model: str, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> tuple[str, int]:
    """Call Ollama API using streaming to avoid timeout, with progress dots."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_ctx": 8192,
        },
    }

    start = time.time()
    resp = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=1800)
    resp.raise_for_status()

    content_parts = []
    token_count = 0
    for line in resp.iter_lines():
        if not line:
            continue
        chunk = json.loads(line)
        text = chunk.get("message", {}).get("content", "")
        if text:
            content_parts.append(text)
            token_count += 1
            if token_count % 20 == 0:
                print(".", end="", flush=True)
        if chunk.get("done"):
            break

    elapsed_ms = int((time.time() - start) * 1000)
    content = "".join(content_parts)
    return content, elapsed_ms


def parse_response(raw: str) -> dict:
    """Parse the structured response format into a dictionary."""
    result = {
        "meaning_short": "",
        "meaning_detailed": "",
        "semantic_field": "",
        "cross_ref_notes": "",
        "cognate_notes": "",
        "morphology_notes": "",
        "departure_notes": "",
    }

    field_map = {
        "MEANING_SHORT": "meaning_short",
        "MEANING_DETAILED": "meaning_detailed",
        "SEMANTIC_FIELD": "semantic_field",
        "CROSS_REF_NOTES": "cross_ref_notes",
        "COGNATE_NOTES": "cognate_notes",
        "MORPHOLOGY_NOTES": "morphology_notes",
        "DEPARTURE": "departure_notes",
    }

    # Split by field headers
    fields = list(field_map.keys())
    for i, field in enumerate(fields):
        # Build regex: capture from this field header to the next one (or end)
        if i < len(fields) - 1:
            next_fields = "|".join(fields[i + 1:])
            pattern = rf"{field}:\s*(.+?)(?=\n(?:{next_fields}):|\Z)"
        else:
            pattern = rf"{field}:\s*(.+?)$"

        match = re.search(pattern, raw, re.DOTALL | re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            # Clean up markdown artifacts
            value = re.sub(r"\*\*", "", value)
            if value.lower() == "none":
                value = ""
            result[field_map[field]] = value

    # Fallback: if nothing matched, use the whole response as meaning_detailed
    if not result["meaning_short"] and not result["meaning_detailed"]:
        result["meaning_detailed"] = raw.strip()

    return result


def _get_word_lemma(conn, surah: int, ayah: int, word_pos: int) -> str | None:
    """Get the primary lemma for a word position."""
    rows = conn.execute(
        "SELECT lemma_buckwalter FROM morphology "
        "WHERE chapter = ? AND verse = ? AND word_pos = ? "
        "AND lemma_buckwalter IS NOT NULL AND lemma_buckwalter != '' "
        "AND pos NOT IN ('Prefix', 'Suffix') "
        "ORDER BY segment LIMIT 1",
        (surah, ayah, word_pos),
    ).fetchone()
    return rows["lemma_buckwalter"] if rows else None


def _store_word_meaning(conn, surah, ayah, word_pos, config_id, parsed, prompt, raw_response, elapsed_ms, force=False):
    """Store a word meaning in the database."""
    if force:
        conn.execute(
            "DELETE FROM ai_word_meanings "
            "WHERE chapter = ? AND verse = ? AND word_pos = ? AND config_id = ?",
            (surah, ayah, word_pos, config_id),
        )

    conn.execute(
        "INSERT INTO ai_word_meanings "
        "(chapter, verse, word_pos, config_id, meaning_short, meaning_detailed, "
        " semantic_field, cross_ref_notes, cognate_notes, morphology_notes, "
        " departure_notes, full_prompt, raw_response, model_response_time_ms) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            surah, ayah, word_pos, config_id,
            parsed["meaning_short"],
            parsed["meaning_detailed"],
            parsed.get("semantic_field") or None,
            parsed.get("cross_ref_notes") or None,
            parsed.get("cognate_notes") or None,
            parsed.get("morphology_notes") or None,
            parsed.get("departure_notes") or None,
            prompt, raw_response, elapsed_ms,
        ),
    )
    conn.commit()


def process_word(
    conn,
    surah: int,
    ayah: int,
    word_pos: int,
    config_id: int,
    model: str,
    temperature: float,
    dry_run: bool = False,
    force: bool = False,
    freq_threshold: int = DEFAULT_FREQ_THRESHOLD,
) -> bool:
    """Process a single word. Returns True if meaning was stored.

    Uses Zipf-based hybrid approach:
    - High-freq lemmas (>= freq_threshold): reuse existing meaning if available
    - Low-freq lemmas (< freq_threshold): always generate with full context
    """

    # Check if already processed for this exact position
    if not force:
        existing = conn.execute(
            "SELECT id FROM ai_word_meanings "
            "WHERE chapter = ? AND verse = ? AND word_pos = ? AND config_id = ?",
            (surah, ayah, word_pos, config_id),
        ).fetchone()
        if existing:
            print(f"    word {word_pos} — already processed (use --force to redo)")
            return False

    # Build the prompt (also checks if word should be skipped)
    prompt = build_word_prompt(conn, surah, ayah, word_pos)
    if prompt is None:
        print(f"    word {word_pos} — skipped (prefix/suffix only)")
        return False

    # ── Zipf check: can we reuse an existing meaning for this lemma? ──
    lemma_bw = _get_word_lemma(conn, surah, ayah, word_pos)
    if lemma_bw and not force:
        freq = get_lemma_frequency(lemma_bw)
        if freq >= freq_threshold:
            existing_meaning = find_existing_lemma_meaning(conn, lemma_bw, config_id)
            if existing_meaning:
                source = existing_meaning.pop("source")
                _store_word_meaning(
                    conn, surah, ayah, word_pos, config_id,
                    existing_meaning, "", f"[reused from {source}]", 0, force,
                )
                print(f"    word {word_pos} — reused ({freq}x lemma, from {source}): {existing_meaning['meaning_short']}")
                return True

    if dry_run:
        freq_info = ""
        if lemma_bw:
            freq = get_lemma_frequency(lemma_bw)
            freq_info = f" [lemma freq: {freq}, {'REUSE' if freq >= freq_threshold else 'PER-OCC'}]"
        print(f"\n{'='*80}")
        print(f"DRY RUN — Prompt for {surah}:{ayah} word {word_pos}{freq_info}")
        print(f"{'='*80}")
        print(f"\n[SYSTEM PROMPT]\n{SYSTEM_PROMPT}")
        print(f"\n[USER PROMPT]\n{prompt}")
        print(f"{'='*80}\n")
        return False

    # ── Call model (Ollama or OpenAI) ──
    print(f"    word {word_pos} — calling {model}...", end="", flush=True)
    try:
        raw_response, elapsed_ms = call_model(model, SYSTEM_PROMPT, prompt, temperature)
    except Exception as e:
        print(f" ERROR: {e}")
        return False

    print(f" done ({elapsed_ms / 1000:.1f}s)")

    # Parse response
    parsed = parse_response(raw_response)

    if not parsed["meaning_short"]:
        print(f"    word {word_pos} — WARNING: empty meaning_short from model")
        return False

    # Store in database
    _store_word_meaning(
        conn, surah, ayah, word_pos, config_id,
        parsed, prompt, raw_response, elapsed_ms, force,
    )

    freq_label = ""
    if lemma_bw:
        freq = get_lemma_frequency(lemma_bw)
        if freq >= freq_threshold:
            freq_label = f" [first for {freq}x lemma — will be reused]"
        else:
            freq_label = f" [rare lemma, {freq}x]"

    print(f"      → {parsed['meaning_short']}{freq_label}")
    return True


def main():
    parser = argparse.ArgumentParser(description="AI Per-Word Meaning Pipeline")
    parser.add_argument("--verses", required=True, help="Verse specification, e.g. '1:1-7,24:41'")
    parser.add_argument("--config", default="word-meaning-v1", help="Config name (default: word-meaning-v1)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--temperature", type=float, default=0.3, help="Temperature (default: 0.3)")
    parser.add_argument("--dry-run", action="store_true", help="Print prompt without calling model")
    parser.add_argument("--force", action="store_true", help="Re-generate even if already exists")
    parser.add_argument("--word-pos", type=int, default=None, help="Process only this word position")
    parser.add_argument(
        "--freq-threshold", type=int, default=DEFAULT_FREQ_THRESHOLD,
        help=f"Lemmas appearing >= this many times are translated once and reused (default: {DEFAULT_FREQ_THRESHOLD})"
    )
    args = parser.parse_args()

    verses = parse_verse_spec(args.verses)
    if not verses:
        print("No valid verses specified")
        sys.exit(1)

    print(f"Processing words in {len(verses)} verse(s) with config '{args.config}', model '{args.model}'")
    print(f"Zipf threshold: {args.freq_threshold} (lemmas with >= {args.freq_threshold} occurrences translated once)")

    conn = get_db()
    try:
        # Build lemma frequency cache
        _build_lemma_freq(conn)
        config_id = get_or_create_config(conn, args.config, args.model)

        total_generated = 0
        total_reused = 0

        for surah, ayah in verses:
            print(f"\n  {surah}:{ayah}:")

            if args.word_pos is not None:
                # Process a single word
                if process_word(conn, surah, ayah, args.word_pos, config_id,
                                args.model, args.temperature, args.dry_run, args.force,
                                args.freq_threshold):
                    total_generated += 1
            else:
                # Find all word positions in this verse
                pos_rows = conn.execute(
                    "SELECT DISTINCT word_pos FROM morphology "
                    "WHERE chapter = ? AND verse = ? ORDER BY word_pos",
                    (surah, ayah),
                ).fetchall()

                for row in pos_rows:
                    before = conn.execute(
                        "SELECT COUNT(*) FROM ai_word_meanings WHERE config_id = ?",
                        (config_id,),
                    ).fetchone()[0]

                    if process_word(conn, surah, ayah, row["word_pos"], config_id,
                                    args.model, args.temperature, args.dry_run, args.force,
                                    args.freq_threshold):
                        # Check if it was a reuse (no raw_response) or a fresh generation
                        after_row = conn.execute(
                            "SELECT raw_response FROM ai_word_meanings "
                            "WHERE chapter = ? AND verse = ? AND word_pos = ? AND config_id = ?",
                            (surah, ayah, row["word_pos"], config_id),
                        ).fetchone()
                        if after_row and after_row["raw_response"] and after_row["raw_response"].startswith("[reused"):
                            total_reused += 1
                        else:
                            total_generated += 1

        if not args.dry_run:
            print(f"\nDone: {total_generated} generated, {total_reused} reused from high-freq lemmas")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
