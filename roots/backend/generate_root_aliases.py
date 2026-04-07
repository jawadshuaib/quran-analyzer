"""Generate search aliases for Quranic roots using Ollama cloud.

Creates a root_search_aliases table mapping alternative transliterations,
romanizations, and common misspellings to canonical Buckwalter roots.

Usage:
    python generate_root_aliases.py                    # Process all roots
    python generate_root_aliases.py --limit 50         # Process first 50
    python generate_root_aliases.py --force             # Regenerate all
    python generate_root_aliases.py --model qwen3:14b   # Use local model
"""

import argparse
import json
import re
import sqlite3
import time

import requests

DB_PATH = "data/quran.db"
OLLAMA_URL = "http://localhost:11434/api/chat"

# ── Static Buckwalter-to-phonetic mapping ──
# These are deterministic and don't need LLM
BUCKWALTER_PHONETIC = {
    "A": ["a", "alif"],
    "b": ["b", "ba"],
    "t": ["t", "ta"],
    "v": ["th", "tha"],
    "j": ["j", "ja", "jim"],
    "H": ["h", "ha", "haa"],
    "x": ["kh", "kha"],
    "d": ["d", "da", "dal"],
    "*": ["dh", "dha", "thal", "z"],
    "r": ["r", "ra"],
    "z": ["z", "za", "zay"],
    "s": ["s", "sa", "sin"],
    "$": ["sh", "sha", "shin"],
    "S": ["s", "sa", "sad"],
    "D": ["d", "da", "dad", "dh", "dha"],
    "T": ["t", "ta", "taa"],
    "Z": ["z", "za", "dh", "dha", "zha"],
    "E": ["a", "aa", "ain", "ayn", "3"],
    "g": ["gh", "gha", "ghain"],
    "f": ["f", "fa"],
    "q": ["q", "qa", "k"],
    "k": ["k", "ka", "kaf"],
    "l": ["l", "la", "lam"],
    "m": ["m", "ma", "mim"],
    "n": ["n", "na", "nun"],
    "h": ["h", "ha"],
    "w": ["w", "wa", "waw"],
    "y": ["y", "ya"],
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS root_search_aliases (
            root_buckwalter TEXT NOT NULL,
            alias TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'ai',
            PRIMARY KEY (root_buckwalter, alias)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_alias_lookup
        ON root_search_aliases(alias)
    """)
    conn.commit()


def generate_static_aliases(root_bw):
    """Generate deterministic phonetic aliases from Buckwalter encoding."""
    aliases = set()
    letters = list(root_bw)

    # Generate hyphenated and concatenated phonetic forms
    # e.g., xlq -> kh-l-q, khlq, khalq
    phonetic_parts = []
    for letter in letters:
        phonetic_parts.append(BUCKWALTER_PHONETIC.get(letter, [letter]))

    # Build combinations (limit to avoid explosion)
    def build_combos(parts, sep):
        if not parts:
            return [""]
        result = []
        for prefix in parts[0]:
            for suffix in build_combos(parts[1:], sep):
                result.append(prefix + sep + suffix if suffix else prefix)
        return result

    # Only take first 2 variants per letter to keep it manageable
    limited_parts = [p[:2] for p in phonetic_parts]

    for sep in ["", "-"]:
        combos = build_combos(limited_parts, sep)
        for c in combos:
            if c.lower() != root_bw.lower():
                aliases.add(c.lower())

    # Also add the plain buckwalter lowercase
    aliases.add(root_bw.lower())

    return aliases


def call_ollama(model, prompt, max_tokens=1000):
    """Call Ollama API and return response text."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": 0.3},
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()


def generate_ai_aliases(root_bw, root_arabic, top_meaning, model):
    """Use LLM to generate search aliases a user might type."""
    prompt = f"""Given this Arabic root: {root_arabic} (Buckwalter: {root_bw})
Meaning: {top_meaning}

Generate a JSON array of 10-15 search strings that English-speaking users might type when looking for this root. Include:
1. Romanizations with hyphens between letters (e.g., "kh-l-q", "i-l-m", "r-h-m")
2. Romanizations without hyphens (e.g., "khlq", "ilm", "rhm")
3. Simplified spellings where emphatic Arabic letters are replaced with plain ones (ع→a/i, ح→h, ص→s, ض→d, ط→t, ظ→z, ث→th/s, خ→kh/x, غ→gh/g, ش→sh)
4. Common misspellings an English speaker might make (e.g., "ism" for إثم, "ilm" for علم)
5. English meaning keywords and close synonyms (e.g., "mercy", "compassion", "merciful" for رحم)

Return ONLY a JSON array of lowercase strings, nothing else. Example:
["kh-l-q", "khalaq", "khlq", "kalaq", "create", "creation", "creator"]"""

    try:
        raw = call_ollama(model, prompt)
        # Extract JSON array from response
        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        if match:
            aliases = json.loads(match.group())
            return [str(a).lower().strip() for a in aliases if isinstance(a, str) and a.strip()]
    except Exception as e:
        print(f"  WARNING: LLM error for {root_bw}: {e}")
    return []


def main():
    parser = argparse.ArgumentParser(description="Generate root search aliases")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of roots (0=all)")
    parser.add_argument("--model", default="minimax-m2.5:cloud", help="Ollama model")
    parser.add_argument("--force", action="store_true", help="Regenerate existing")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")
    args = parser.parse_args()

    conn = get_db()
    ensure_table(conn)

    # Get all roots with frequency
    roots = conn.execute("""
        SELECT root_buckwalter, root_arabic, COUNT(*) as freq
        FROM morphology
        WHERE root_buckwalter IS NOT NULL AND root_buckwalter != ''
        GROUP BY root_buckwalter
        ORDER BY freq DESC
    """).fetchall()

    if args.limit > 0:
        roots = roots[:args.limit]

    # Get existing aliases if not forcing
    existing = set()
    if not args.force:
        rows = conn.execute("SELECT DISTINCT root_buckwalter FROM root_search_aliases WHERE source = 'ai'").fetchall()
        existing = {r["root_buckwalter"] for r in rows}

    # Get meanings: ai_root_meanings > learning_derivatives > word_glosses
    meanings = {}
    try:
        for r in conn.execute("""
            SELECT root_buckwalter, primary_meaning FROM ai_root_meanings
            ORDER BY config_id DESC
        """).fetchall():
            if r["root_buckwalter"] not in meanings:
                meanings[r["root_buckwalter"]] = r["primary_meaning"]
    except sqlite3.OperationalError:
        pass  # table may not exist yet

    for r in conn.execute("""
        SELECT root_buckwalter, meaning_gloss FROM learning_derivatives
        ORDER BY frequency DESC
    """).fetchall():
        if r["root_buckwalter"] not in meanings:
            meanings[r["root_buckwalter"]] = r["meaning_gloss"]

    # Also get glosses from word_glosses for roots not in curriculum
    for r in conn.execute("""
        SELECT DISTINCT m.root_buckwalter, wg.translation_en
        FROM morphology m
        JOIN word_glosses wg ON m.chapter = wg.chapter AND m.verse = wg.verse AND m.word_pos = wg.word_pos
        WHERE m.root_buckwalter IS NOT NULL AND m.root_buckwalter != ''
        AND wg.translation_en IS NOT NULL AND wg.translation_en != ''
    """).fetchall():
        if r["root_buckwalter"] not in meanings and r["translation_en"]:
            meanings[r["root_buckwalter"]] = r["translation_en"]

    print(f"Processing {len(roots)} roots (model: {args.model})")
    print(f"Already have AI aliases for {len(existing)} roots")

    total_aliases = 0
    for i, root in enumerate(roots):
        root_bw = root["root_buckwalter"]
        root_ar = root["root_arabic"]
        freq = root["freq"]
        meaning = meanings.get(root_bw, "")

        # Generate static aliases always
        static_aliases = generate_static_aliases(root_bw)

        # Generate AI aliases if not already done
        ai_aliases = []
        if root_bw not in existing:
            ai_aliases = generate_ai_aliases(root_bw, root_ar, meaning, args.model)
            # Brief pause to avoid rate limiting
            if (i + 1) % 20 == 0:
                time.sleep(1)

        all_aliases = static_aliases | set(ai_aliases)
        # Remove the exact buckwalter match (it's searched directly)
        all_aliases.discard(root_bw)

        if args.dry_run:
            if (i < 5) or (i % 100 == 0):
                print(f"  [{i+1}/{len(roots)}] {root_bw} ({root_ar}) {freq}x: {len(all_aliases)} aliases")
                if ai_aliases:
                    print(f"    AI: {ai_aliases[:8]}")
            continue

        # Insert aliases
        for alias in all_aliases:
            if not alias or len(alias) > 50:
                continue
            source = "ai" if alias in set(ai_aliases) else "static"
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO root_search_aliases (root_buckwalter, alias, source) VALUES (?, ?, ?)",
                    (root_bw, alias, source),
                )
            except sqlite3.IntegrityError:
                pass

        total_aliases += len(all_aliases)

        if (i + 1) % 50 == 0 or i < 5:
            print(f"  [{i+1}/{len(roots)}] {root_bw} ({root_ar}): {len(all_aliases)} aliases (AI: {len(ai_aliases)})")
            conn.commit()

    if not args.dry_run:
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM root_search_aliases").fetchone()[0]
        distinct = conn.execute("SELECT COUNT(DISTINCT root_buckwalter) FROM root_search_aliases").fetchone()[0]
        print(f"\nDone! Total aliases: {count}, covering {distinct} roots")

    conn.close()


if __name__ == "__main__":
    main()
