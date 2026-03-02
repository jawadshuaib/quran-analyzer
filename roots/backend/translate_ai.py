"""AI-powered Quranic translation pipeline using Ollama or OpenAI API.

Derives meaning from Quranic cross-references, Semitic cognates, and morphology.

Usage:
    python translate_ai.py --verses "1:1-7,24:41,2:255" --config "quran-only-v1"
    python translate_ai.py --verses "1:1" --dry-run
    python translate_ai.py --verses "1:1" --force
    python translate_ai.py --verses "1:1-7" --model gpt-4.1 --config "gpt4.1-v1"
    python translate_ai.py --verses "1:1-7" --model gpt-4.1-mini --config "gpt4.1mini-v1"
"""

import argparse
import json
import os
import re
import sys
import time

import requests

# Import infrastructure from app.py (builds similarity engine on import, ~2s)
from app import (
    DB_PATH,
    _find_related_verses,
    _get_cognate,
    _root_arabic_map,
    _strip_bismillah,
    get_db,
)

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "qwen3.5:35b"

SYSTEM_PROMPT = """\
You are a Quranic translation engine. Your task is to translate a single Quranic \
verse into English using ONLY the evidence provided below. Do NOT rely on \
conventional translations, tafsir traditions, or external knowledge.

## Your Methodology (follow in this order)

1. **Quranic Self-Reference (primary evidence)**: The Quran is its own best \
interpreter. For each key word, examine how the Quran itself uses that same root \
and lemma across the cross-reference verses provided. Look for patterns: what \
meaning does the Quran CONSISTENTLY give this word through its own usage? If the \
Quran uses a word in 10 other places and the meaning is clear from those contexts, \
that is your strongest evidence. The Quran's internal consistency takes priority \
over all other sources.

2. **Contextual Coherence**: Read the surrounding verses carefully. Your translation \
must flow naturally within the immediate passage. The meaning of each word must \
make sense in its sentence and in the broader narrative or thematic arc. If a \
meaning works in isolation but creates incoherence in context, reject it.

3. **Semitic Cognate Evidence (supplementary guide)**: Use the cognate data to \
INFORM your understanding of a root's semantic range — not to mechanically replace \
conventional meanings. Cognates reveal the original semantic field a root comes \
from, which can illuminate nuances the Quran may be drawing on. But cognates are \
a guide, not a dictionary. A word's meaning in 7th-century Quranic Arabic may \
have specialized or shifted from the proto-Semitic root. Use cognates to: \
(a) confirm a meaning already supported by Quranic cross-references, \
(b) choose between two plausible readings when cross-references are ambiguous, or \
(c) recover a nuance that conventional glosses flatten. Do NOT adopt a cognate \
meaning that contradicts how the Quran itself uses the word.

4. **Morphological Precision**: Respect the exact verb form (I-X), voice \
(active/passive), mood (indicative/subjunctive/jussive), case marking \
(nominative/accusative/genitive), and number/gender. These constrain meaning.

5. **Synthesize and Translate**: Weigh all evidence. Quranic usage comes first, \
context second, cognates third. Produce a translation that is faithful to how the \
Quran uses its own vocabulary. Where the evidence supports a meaning different from \
the conventional translation, follow the evidence — but the evidence must come \
primarily from the Quran itself, with cognates as supporting data.

## Output Format

Respond in EXACTLY this format (no extra text before or after):

TRANSLATION: [Your English translation of the verse]
NOTES: [For each word where your translation departs from the conventional gloss, \
explain what Quranic cross-references, contextual reasoning, and (where relevant) \
cognate evidence led to your choice. Say "None" if your translation aligns with \
the conventional understanding.]\
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
            "Quran-only translation: cross-references, cognates, morphology. No external tafsir.",
        ),
    )
    conn.commit()
    return conn.execute(
        "SELECT id FROM ai_translation_configs WHERE config_name = ?",
        (config_name,),
    ).fetchone()["id"]


def build_prompt(conn, surah: int, ayah: int, config_id: int) -> str:
    """Assemble the full user prompt for a single verse."""

    # 1. Fetch verse text + conventional translation
    verse_row = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
        (surah, ayah),
    ).fetchone()
    if not verse_row:
        raise ValueError(f"Verse {surah}:{ayah} not found in database")

    arabic_text = _strip_bismillah(verse_row["text_uthmani"], surah, ayah)

    trans_row = conn.execute(
        "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
        (surah, ayah),
    ).fetchone()
    conventional = trans_row["text_en"] if trans_row else "(no conventional translation)"

    # 2. Fetch morphology + word glosses
    morph_rows = conn.execute(
        "SELECT word_pos, segment, form_arabic, form_buckwalter, tag, pos, "
        "       root_buckwalter, root_arabic, lemma_buckwalter, lemma_arabic, "
        "       features_raw, gender, number, person, case_val, voice, mood, "
        "       verb_form, state "
        "FROM morphology WHERE chapter = ? AND verse = ? "
        "ORDER BY word_pos, segment",
        (surah, ayah),
    ).fetchall()

    gloss_rows = conn.execute(
        "SELECT word_pos, translation_en FROM word_glosses "
        "WHERE chapter = ? AND verse = ? ORDER BY word_pos",
        (surah, ayah),
    ).fetchall()
    glosses = {r["word_pos"]: r["translation_en"] for r in gloss_rows}

    # Group morphology by word position
    words_morph = {}
    roots_in_verse = set()
    for row in morph_rows:
        wp = row["word_pos"]
        if wp not in words_morph:
            words_morph[wp] = []
        words_morph[wp].append(row)
        if row["root_buckwalter"]:
            roots_in_verse.add(row["root_buckwalter"])

    morph_lines = []
    for wp in sorted(words_morph.keys()):
        segments = words_morph[wp]
        first = segments[0]
        gloss = glosses.get(wp, "")
        features = []
        for key in ("gender", "number", "person", "case_val", "voice", "mood", "verb_form", "state"):
            val = first[key]
            if val:
                features.append(f"{key.replace('_', ' ')}={val}")
        feature_str = ", ".join(features) if features else "none"

        morph_lines.append(
            f"  Word {wp}: {first['form_arabic']} | "
            f"root={first['root_arabic'] or '—'} ({first['root_buckwalter'] or '—'}) | "
            f"lemma={first['lemma_arabic'] or '—'} | "
            f"POS={first['pos'] or first['tag']} | "
            f"features: {feature_str} | "
            f"gloss: \"{gloss}\""
        )

    # 3. Fetch surrounding context
    config_row = conn.execute(
        "SELECT context_verses_before, context_verses_after, related_verses_limit FROM ai_translation_configs WHERE id = ?",
        (config_id,),
    ).fetchone()
    before_n = config_row["context_verses_before"] if config_row else 3
    after_n = config_row["context_verses_after"] if config_row else 3

    context_rows = conn.execute(
        "SELECT v.chapter, v.verse, v.text_uthmani, t.text_en "
        "FROM verses v LEFT JOIN translations t "
        "ON v.chapter = t.chapter AND v.verse = t.verse "
        "WHERE v.chapter = ? AND v.verse BETWEEN ? AND ? AND v.verse != ? "
        "ORDER BY v.verse",
        (surah, max(1, ayah - before_n), ayah + after_n, ayah),
    ).fetchall()

    context_lines = []
    for r in context_rows:
        text = _strip_bismillah(r["text_uthmani"], r["chapter"], r["verse"])
        trans = r["text_en"] or ""
        label = "BEFORE" if r["verse"] < ayah else "AFTER"
        context_lines.append(f"  [{label}] {r['chapter']}:{r['verse']} — {text}\n    Translation: {trans}")

    # 4. Fetch related verses (cross-references)
    related_limit = config_row["related_verses_limit"] if config_row else 7
    related = _find_related_verses(surah, ayah, limit=related_limit)

    xref_lines = []
    for containment, shared_weight, (ch, v), shared_roots in related:
        v_row = conn.execute(
            "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?", (ch, v)
        ).fetchone()
        t_row = conn.execute(
            "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?", (ch, v)
        ).fetchone()
        text = _strip_bismillah(v_row["text_uthmani"], ch, v) if v_row else ""
        trans = t_row["text_en"] if t_row else ""
        shared_arabic = [_root_arabic_map.get(rbw, rbw) for rbw in shared_roots]
        xref_lines.append(
            f"  {ch}:{v} (shared roots: {', '.join(shared_arabic)}) — {text}\n"
            f"    Translation: {trans}"
        )

    # 5. Fetch Semitic cognates for all roots in this verse
    cognate_lines = []
    for rbw in sorted(roots_in_verse):
        cognate = _get_cognate(conn, rbw)
        if not cognate:
            continue
        arabic = _root_arabic_map.get(rbw, rbw)
        cognate_lines.append(f"  Root {arabic} ({rbw}) — Proto-Semitic concept: {cognate['concept']}")
        for d in cognate["derivatives"][:8]:  # limit derivatives per root
            cognate_lines.append(
                f"    [{d['language']}] {d['word']} — {d['meaning']}"
            )

    # Assemble the prompt
    prompt = f"""## Verse to Translate
{surah}:{ayah} — {arabic_text}

## Conventional Translation (for reference only — do not be bound by it)
{conventional}

## Word-by-Word Morphology
{chr(10).join(morph_lines)}

## Surrounding Context
{chr(10).join(context_lines) if context_lines else "  (none available)"}

## Cross-Reference Verses (same roots used elsewhere in the Quran)
{chr(10).join(xref_lines) if xref_lines else "  (none found)"}

## Semitic Cognate Evidence
{chr(10).join(cognate_lines) if cognate_lines else "  (none available)"}

Now translate verse {surah}:{ayah} following the methodology described in your instructions. /no_think"""

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


def call_openai(model: str, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> tuple[str, int]:
    """Call OpenAI API with streaming and progress dots."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    # Strip /no_think suffix (Ollama-specific)
    clean_prompt = user_prompt.replace(" /no_think", "")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": clean_prompt},
        ],
        "temperature": temperature,
        "stream": True,
    }

    start = time.time()
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        stream=True,
        timeout=300,
    )
    resp.raise_for_status()

    content_parts = []
    token_count = 0
    for line in resp.iter_lines():
        if not line:
            continue
        line_str = line.decode("utf-8")
        if not line_str.startswith("data: "):
            continue
        data_str = line_str[6:]
        if data_str.strip() == "[DONE]":
            break
        try:
            chunk = json.loads(data_str)
            delta = chunk.get("choices", [{}])[0].get("delta", {})
            text = delta.get("content", "")
            if text:
                content_parts.append(text)
                token_count += 1
                if token_count % 20 == 0:
                    print(".", end="", flush=True)
        except json.JSONDecodeError:
            continue

    elapsed_ms = int((time.time() - start) * 1000)
    content = "".join(content_parts)
    return content, elapsed_ms


def _is_openai_model(model: str) -> bool:
    """Check if the model name is an OpenAI model."""
    return model.startswith("gpt-") or model.startswith("o1") or model.startswith("o3")


def call_model(model: str, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> tuple[str, int]:
    """Route to the appropriate API based on model name."""
    if _is_openai_model(model):
        return call_openai(model, system_prompt, user_prompt, temperature)
    return call_ollama(model, system_prompt, user_prompt, temperature)


def parse_response(raw: str) -> tuple[str, str]:
    """Parse TRANSLATION: ... NOTES: ... format from model response.

    Handles both plain format and markdown-wrapped variants like:
      **Translation:** "text"
      TRANSLATION: text
    """
    translation = ""
    notes = ""

    # Try standard format first: TRANSLATION: ... NOTES: ...
    trans_match = re.search(r"TRANSLATION:\s*(.+?)(?=\nNOTES:|$)", raw, re.DOTALL | re.IGNORECASE)
    if trans_match:
        translation = trans_match.group(1).strip()

    # Try markdown variant: **Translation:** ...
    if not translation:
        trans_match = re.search(r"\*\*Translation:?\*\*:?\s*(.+?)(?=\n\*\*Notes?|$)", raw, re.DOTALL | re.IGNORECASE)
        if trans_match:
            translation = trans_match.group(1).strip()

    # Extract notes (both formats)
    notes_match = re.search(r"(?:NOTES|\*\*Notes?:?\*\*):?\s*(.+?)$", raw, re.DOTALL | re.IGNORECASE)
    if notes_match:
        notes = notes_match.group(1).strip()
        if notes.lower() == "none":
            notes = ""

    # Clean up: remove surrounding quotes and markdown artifacts
    for q in ('"', '\u201c', '\u201d'):
        if translation.startswith(q) and translation.endswith(q):
            translation = translation[1:-1].strip()
    # Remove numbered list prefixes from notes (e.g. "1. **Word..." -> clean text)
    notes = re.sub(r"^\d+\.\s*", "", notes)
    # Strip leftover markdown bold
    translation = re.sub(r"\*\*", "", translation)
    notes = re.sub(r"\*\*", "", notes)

    # Fallback: if nothing matched, use the whole response
    if not translation:
        translation = raw.strip()

    return translation, notes


def translate_verse(
    conn,
    surah: int,
    ayah: int,
    config_id: int,
    model: str,
    temperature: float,
    dry_run: bool = False,
    force: bool = False,
) -> bool:
    """Translate a single verse. Returns True if translation was performed."""

    # Check if already translated
    if not force:
        existing = conn.execute(
            "SELECT id FROM ai_translations WHERE chapter = ? AND verse = ? AND config_id = ?",
            (surah, ayah, config_id),
        ).fetchone()
        if existing:
            print(f"  {surah}:{ayah} — already translated (use --force to redo)")
            return False

    # Build the prompt
    prompt = build_prompt(conn, surah, ayah, config_id)

    if dry_run:
        print(f"\n{'='*80}")
        print(f"DRY RUN — Prompt for {surah}:{ayah}")
        print(f"{'='*80}")
        print(f"\n[SYSTEM PROMPT]\n{SYSTEM_PROMPT}")
        print(f"\n[USER PROMPT]\n{prompt}")
        print(f"{'='*80}\n")
        return False

    # Call model
    print(f"  {surah}:{ayah} — calling {model}...", end="", flush=True)
    try:
        raw_response, elapsed_ms = call_model(model, SYSTEM_PROMPT, prompt, temperature)
    except Exception as e:
        print(f" ERROR: {e}")
        return False

    print(f" done ({elapsed_ms / 1000:.1f}s)")

    # Parse response
    translation, notes = parse_response(raw_response)

    if not translation:
        print(f"  {surah}:{ayah} — WARNING: empty translation from model")
        return False

    # Store in database
    if force:
        conn.execute(
            "DELETE FROM ai_translations WHERE chapter = ? AND verse = ? AND config_id = ?",
            (surah, ayah, config_id),
        )

    conn.execute(
        "INSERT INTO ai_translations "
        "(chapter, verse, config_id, translation_text, departure_notes, "
        " full_prompt, raw_response, model_response_time_ms) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (surah, ayah, config_id, translation, notes or None, prompt, raw_response, elapsed_ms),
    )
    conn.commit()

    # Print result
    print(f"    Translation: {translation[:120]}{'...' if len(translation) > 120 else ''}")
    if notes:
        print(f"    Notes: {notes[:120]}{'...' if len(notes) > 120 else ''}")

    return True


def main():
    parser = argparse.ArgumentParser(description="AI Quranic Translation Pipeline")
    parser.add_argument("--verses", required=True, help="Verse specification, e.g. '1:1-7,24:41,2:255'")
    parser.add_argument("--config", default="quran-only-v1", help="Config name (default: quran-only-v1)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model (default: {DEFAULT_MODEL})")
    parser.add_argument("--temperature", type=float, default=0.3, help="Temperature (default: 0.3)")
    parser.add_argument("--dry-run", action="store_true", help="Print prompt without calling model")
    parser.add_argument("--force", action="store_true", help="Re-translate even if already exists")
    args = parser.parse_args()

    verses = parse_verse_spec(args.verses)
    if not verses:
        print("No valid verses specified")
        sys.exit(1)

    print(f"Translating {len(verses)} verse(s) with config '{args.config}', model '{args.model}'")

    conn = get_db()
    try:
        config_id = get_or_create_config(conn, args.config, args.model)
        translated = 0
        for surah, ayah in verses:
            if translate_verse(conn, surah, ayah, config_id, args.model, args.temperature, args.dry_run, args.force):
                translated += 1

        if not args.dry_run:
            print(f"\nDone: {translated}/{len(verses)} verses translated")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
