"""AI-powered pipeline to assign thematic tags to every Quran verse.

Uses Ollama cloud API to classify each verse into 1-3 themes from a predefined
set. Processes verses in surah-sized batches for better contextual accuracy.

Usage:
    python assign_themes_ai.py --surah 1                      # Single surah
    python assign_themes_ai.py --surah 1-10                   # Range of surahs
    python assign_themes_ai.py --all                          # All 114 surahs
    python assign_themes_ai.py --surah 1 --dry-run            # Print prompt only
    python assign_themes_ai.py --surah 1 --force              # Re-assign even if exists
    python assign_themes_ai.py --surah 1 --model qwen3:32b    # Override model
"""

import argparse
import json
import os
import re
import sys
import time

import requests

# Import infrastructure from app.py
from app import DB_PATH, _strip_bismillah, get_db

# --------------- Configuration ---------------

OLLAMA_CLOUD_URL = "https://ollama.com/api/chat"
OLLAMA_LOCAL_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "gemma4:31b"

# The 20 predefined themes
THEMES = [
    "Tawhid (Divine Oneness)",
    "The Nature of Allah",
    "Prophethood & Revelation",
    "The Quran as Divine Word",
    "The Day of Judgment",
    "Heaven and Hell",
    "Death and the Afterlife",
    "Human Nature and Free Will",
    "Justice",
    "Gratitude vs. Ingratitude",
    "Arrogance and Humility",
    "Moral Accountability",
    "Worship and Prayer",
    "Repentance and Divine Mercy",
    "Patience and Perseverance",
    "Stories of Previous Nations",
    "The People of the Book",
    "The Signs of God in Creation",
    "Community, Brotherhood & Social Ethics",
    "The Struggle of the Self",
]

SYSTEM_PROMPT = """\
You are a Quranic thematic classifier. Your task is to assign 1 to 3 themes to \
each verse of the Quran from the predefined list below. You may also create a \
NEW theme if none of the predefined themes fit a verse well.

## Predefined Themes
{themes_list}

## Rules

1. Assign 1 to 3 themes per verse — pick the most relevant ones.
2. Use the EXACT theme name from the list above when possible.
3. If a verse genuinely does not fit ANY of the predefined themes, you may create \
a new theme. Use a concise, descriptive name in the same style (e.g. "Covenant \
and Promise", "Warfare and Defense"). Keep new themes rare.
4. For each theme assignment, provide a confidence score from 0.0 to 1.0.
5. Consider the verse's content, context within the surah, and the Arabic text.
6. A verse about multiple topics should get multiple themes.
7. Short verses (e.g. disconnected letters, oaths) should still get the most \
relevant theme based on their traditional and contextual understanding.

## Output Format

Respond with ONLY a JSON array. Each element is an object with:
- "verse": the verse number (integer)
- "themes": array of objects, each with "theme" (string) and "confidence" (float)

Example:
```json
[
  {{"verse": 1, "themes": [{{"theme": "Worship and Prayer", "confidence": 0.95}}]}},
  {{"verse": 2, "themes": [{{"theme": "The Quran as Divine Word", "confidence": 0.9}}, {{"theme": "Prophethood & Revelation", "confidence": 0.7}}]}}
]
```

Do NOT include any text outside the JSON array. /no_think\
"""


def get_api_config():
    """Determine API URL and headers based on available credentials."""
    api_key = os.environ.get("OLLAMA_API_KEY")
    if api_key:
        return OLLAMA_CLOUD_URL, {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    # Fall back to local Ollama
    print("  (No OLLAMA_API_KEY found, using local Ollama)")
    return OLLAMA_LOCAL_URL, {"Content-Type": "application/json"}


def call_ollama(model: str, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> tuple[str, int]:
    """Call Ollama API (cloud or local) with streaming."""
    api_url, headers = get_api_config()

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_ctx": 32768,
        },
    }

    start = time.time()
    resp = requests.post(api_url, json=payload, headers=headers, stream=True, timeout=1800)
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
            if token_count % 40 == 0:
                print(".", end="", flush=True)
        if chunk.get("done"):
            break

    elapsed_ms = int((time.time() - start) * 1000)
    content = "".join(content_parts)
    return content, elapsed_ms


def parse_themes_response(raw: str) -> list[dict]:
    """Parse JSON array of verse theme assignments from model response."""
    # Strip markdown code fences if present
    cleaned = re.sub(r"```json\s*", "", raw)
    cleaned = re.sub(r"```\s*", "", cleaned)
    cleaned = cleaned.strip()

    # Find the JSON array
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON array found in response: {cleaned[:200]}")

    json_str = cleaned[start : end + 1]
    data = json.loads(json_str)

    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array, got {type(data)}")

    return data


def fetch_surah_verses(conn, surah: int) -> list[dict]:
    """Fetch all verses for a surah with Arabic text and English translation."""
    rows = conn.execute(
        "SELECT v.verse, v.text_uthmani, t.text_en "
        "FROM verses v "
        "LEFT JOIN translations t ON v.chapter = t.chapter AND v.verse = t.verse "
        "WHERE v.chapter = ? ORDER BY v.verse",
        (surah,),
    ).fetchall()

    verses = []
    for r in rows:
        arabic = _strip_bismillah(r["text_uthmani"], surah, r["verse"])
        verses.append({
            "verse": r["verse"],
            "arabic": arabic,
            "english": r["text_en"] or "",
        })
    return verses


def build_surah_prompt(surah: int, surah_name: str, verses: list[dict]) -> str:
    """Build the user prompt for a full surah."""
    verse_lines = []
    for v in verses:
        verse_lines.append(
            f"Verse {v['verse']}:\n"
            f"  Arabic: {v['arabic']}\n"
            f"  English: {v['english']}"
        )

    return (
        f"## Surah {surah}: {surah_name}\n"
        f"Total verses: {len(verses)}\n\n"
        f"Assign themes to each verse below.\n\n"
        + "\n\n".join(verse_lines)
    )


def get_existing_themes(conn, surah: int) -> set[int]:
    """Get verse numbers that already have themes assigned in this surah."""
    rows = conn.execute(
        "SELECT DISTINCT verse FROM verse_themes WHERE chapter = ?",
        (surah,),
    ).fetchall()
    return {r["verse"] for r in rows}


def process_surah(
    conn,
    surah: int,
    surah_name: str,
    model: str,
    temperature: float,
    dry_run: bool = False,
    force: bool = False,
) -> int:
    """Process a single surah. Returns number of verses themed."""

    verses = fetch_surah_verses(conn, surah)
    if not verses:
        print(f"  Surah {surah} — no verses found, skipping")
        return 0

    # Check existing
    if not force:
        existing = get_existing_themes(conn, surah)
        if len(existing) == len(verses):
            print(f"  Surah {surah} ({surah_name}) — all {len(verses)} verses already themed (use --force)")
            return 0
        if existing:
            print(f"  Surah {surah} ({surah_name}) — {len(existing)}/{len(verses)} already themed, processing remaining")
            verses = [v for v in verses if v["verse"] not in existing]

    # Build prompt
    themes_list = "\n".join(f"  {i+1}. {t}" for i, t in enumerate(THEMES))
    system = SYSTEM_PROMPT.format(themes_list=themes_list)
    user_prompt = build_surah_prompt(surah, surah_name, verses)

    if dry_run:
        print(f"\n{'='*80}")
        print(f"DRY RUN — Surah {surah}: {surah_name} ({len(verses)} verses)")
        print(f"{'='*80}")
        print(f"\n[SYSTEM PROMPT]\n{system}")
        print(f"\n[USER PROMPT]\n{user_prompt[:3000]}...")
        print(f"{'='*80}\n")
        return 0

    # Call model
    print(f"  Surah {surah} ({surah_name}) — {len(verses)} verses, calling {model}...", end="", flush=True)
    try:
        raw_response, elapsed_ms = call_ollama(model, system, user_prompt, temperature)
    except Exception as e:
        print(f" ERROR: {e}")
        return 0

    print(f" done ({elapsed_ms / 1000:.1f}s)")

    # Parse response
    try:
        theme_data = parse_themes_response(raw_response)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"    PARSE ERROR: {e}")
        print(f"    Raw response (first 500 chars): {raw_response[:500]}")
        return 0

    # Validate and store
    verse_nums = {v["verse"] for v in verses}
    stored = 0

    for entry in theme_data:
        v_num = entry.get("verse")
        if v_num not in verse_nums:
            continue

        themes = entry.get("themes", [])
        if not themes:
            continue

        for t in themes[:3]:  # Max 3 themes per verse
            theme_name = t.get("theme", "").strip()
            confidence = t.get("confidence", 0.5)

            if not theme_name:
                continue

            # Clamp confidence
            confidence = max(0.0, min(1.0, float(confidence)))

            try:
                if force:
                    conn.execute(
                        "DELETE FROM verse_themes WHERE chapter = ? AND verse = ? AND theme = ?",
                        (surah, v_num, theme_name),
                    )
                conn.execute(
                    "INSERT OR IGNORE INTO verse_themes (chapter, verse, theme, confidence, model_used) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (surah, v_num, theme_name, confidence, model),
                )
            except Exception as e:
                print(f"    DB error for {surah}:{v_num} theme '{theme_name}': {e}")
                continue

        stored += 1

    conn.commit()

    # Summary
    assigned_themes = conn.execute(
        "SELECT COUNT(DISTINCT verse) FROM verse_themes WHERE chapter = ?",
        (surah,),
    ).fetchone()[0]
    total_entries = conn.execute(
        "SELECT COUNT(*) FROM verse_themes WHERE chapter = ?",
        (surah,),
    ).fetchone()[0]
    print(f"    Stored themes for {stored} verses ({total_entries} total theme entries, {assigned_themes} verses covered)")

    return stored


# Surah names for display
SURAH_NAMES = [
    "", "Al-Fatihah", "Al-Baqarah", "Ali 'Imran", "An-Nisa", "Al-Ma'idah",
    "Al-An'am", "Al-A'raf", "Al-Anfal", "At-Tawbah", "Yunus",
    "Hud", "Yusuf", "Ar-Ra'd", "Ibrahim", "Al-Hijr",
    "An-Nahl", "Al-Isra", "Al-Kahf", "Maryam", "Taha",
    "Al-Anbya", "Al-Hajj", "Al-Mu'minun", "An-Nur", "Al-Furqan",
    "Ash-Shu'ara", "An-Naml", "Al-Qasas", "Al-'Ankabut", "Ar-Rum",
    "Luqman", "As-Sajdah", "Al-Ahzab", "Saba", "Fatir",
    "Ya-Sin", "As-Saffat", "Sad", "Az-Zumar", "Ghafir",
    "Fussilat", "Ash-Shura", "Az-Zukhruf", "Ad-Dukhan", "Al-Jathiyah",
    "Al-Ahqaf", "Muhammad", "Al-Fath", "Al-Hujurat", "Qaf",
    "Adh-Dhariyat", "At-Tur", "An-Najm", "Al-Qamar", "Ar-Rahman",
    "Al-Waqi'ah", "Al-Hadid", "Al-Mujadila", "Al-Hashr", "Al-Mumtahanah",
    "As-Saf", "Al-Jumu'ah", "Al-Munafiqun", "At-Taghabun", "At-Talaq",
    "At-Tahrim", "Al-Mulk", "Al-Qalam", "Al-Haqqah", "Al-Ma'arij",
    "Nuh", "Al-Jinn", "Al-Muzzammil", "Al-Muddaththir", "Al-Qiyamah",
    "Al-Insan", "Al-Mursalat", "An-Naba", "An-Nazi'at", "Abasa",
    "At-Takwir", "Al-Infitar", "Al-Mutaffifin", "Al-Inshiqaq", "Al-Buruj",
    "At-Tariq", "Al-A'la", "Al-Ghashiyah", "Al-Fajr", "Al-Balad",
    "Ash-Shams", "Al-Layl", "Ad-Duha", "Ash-Sharh", "At-Tin",
    "Al-Alaq", "Al-Qadr", "Al-Bayyinah", "Az-Zalzalah", "Al-Adiyat",
    "Al-Qari'ah", "At-Takathur", "Al-Asr", "Al-Humazah", "Al-Fil",
    "Quraysh", "Al-Ma'un", "Al-Kawthar", "Al-Kafirun", "An-Nasr",
    "Al-Masad", "Al-Ikhlas", "Al-Falaq", "An-Nas",
]


def main():
    parser = argparse.ArgumentParser(description="Assign thematic tags to Quran verses via Ollama")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--surah", help="Surah number or range (e.g. '1', '1-10')")
    group.add_argument("--all", action="store_true", help="Process all 114 surahs")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--temperature", type=float, default=0.2, help="Temperature (default: 0.2)")
    parser.add_argument("--dry-run", action="store_true", help="Print prompt without calling model")
    parser.add_argument("--force", action="store_true", help="Re-assign themes even if already exist")
    parser.add_argument("--api-key", help="Ollama API key (overrides OLLAMA_API_KEY env var)")
    args = parser.parse_args()

    # Set API key from arg if provided
    if args.api_key:
        os.environ["OLLAMA_API_KEY"] = args.api_key

    # Parse surah range
    if args.all:
        surahs = list(range(1, 115))
    else:
        match = re.match(r"(\d+)-(\d+)$", args.surah)
        if match:
            start, end = int(match.group(1)), int(match.group(2))
            surahs = list(range(start, end + 1))
        else:
            surahs = [int(args.surah)]

    # Validate
    for s in surahs:
        if s < 1 or s > 114:
            print(f"Invalid surah number: {s}")
            sys.exit(1)

    api_url, _ = get_api_config()
    print(f"Assigning themes to {len(surahs)} surah(s) with model '{args.model}'")
    print(f"API: {api_url}")
    print(f"Themes: {len(THEMES)} predefined + auto-generated if needed")
    print()

    conn = get_db()
    try:
        total_themed = 0
        for surah in surahs:
            name = SURAH_NAMES[surah] if surah < len(SURAH_NAMES) else f"Surah {surah}"
            themed = process_surah(
                conn, surah, name, args.model, args.temperature,
                args.dry_run, args.force,
            )
            total_themed += themed

        if not args.dry_run:
            # Final stats
            total_entries = conn.execute("SELECT COUNT(*) FROM verse_themes").fetchone()[0]
            total_verses = conn.execute("SELECT COUNT(DISTINCT chapter || ':' || verse) FROM verse_themes").fetchone()[0]
            distinct_themes = conn.execute("SELECT COUNT(DISTINCT theme) FROM verse_themes").fetchone()[0]
            print(f"\nDone: {total_themed} verses processed this run")
            print(f"Total: {total_entries} theme entries across {total_verses} verses, {distinct_themes} distinct themes")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
