"""Fix word-to-word translation alignment and deduplication.

Two problems:
1. Word glosses misaligned with verse-level AI translation
2. Adjacent words duplicating/bleeding meaning into each other

Uses Ollama cloud (gemma4:31b) for bulk processing, Claude Sonnet for
uncertain cases requiring deeper linguistic analysis.

Usage:
    python fix_word_glosses_ai.py --mode align --verses "33:56" --dry-run
    python fix_word_glosses_ai.py --mode dedup --all --dry-run
    python fix_word_glosses_ai.py --mode both --all --apply
    python fix_word_glosses_ai.py --mode both --all --apply --force
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime

import requests

from app import DB_PATH, _strip_bismillah, get_db

# --------------- Configuration ---------------

OLLAMA_CLOUD_URL = "https://ollama.com/api/chat"
OLLAMA_LOCAL_URL = "http://localhost:11434/api/chat"
DEFAULT_OLLAMA_MODEL = "gemma4:31b"
CLAUDE_ESCALATION_MODEL = "claude-sonnet-4-20250514"

# Confidence thresholds
CONF_AUTO_APPLY = 0.75      # >= this: apply directly
CONF_ESCALATE = 0.50        # >= this but < AUTO_APPLY: escalate to Claude
# < CONF_ESCALATE: skip (too uncertain)

CLAUDE_BATCH_SIZE = 20  # max words per Claude escalation call


# --------------- Quran-Only Methodology Prompts ---------------

METHODOLOGY_BLOCK = """\
## Methodology — Quran-Only Analysis
- Derive word meanings from Quranic context only — how this root/word is \
used across the Quran itself.
- Where the root has a broad semantic range, consider Semitic cognates \
(Hebrew, Aramaic, Classical Arabic) to narrow the meaning.
- NEVER use post-Quranic terminology (Islamic, halal, haram, Sunnah, \
Hadith, Shariah, five pillars, etc.) — the Quran predates these concepts.
- When a word's meaning is ambiguous, prefer the sense supported by Quranic \
cross-references and Semitic cognates over conventional/traditional glosses."""

DEDUP_SYSTEM_PROMPT = f"""\
You are fixing word-by-word translations for a Quran study tool that uses \
a Quran-only analytical methodology.

{METHODOLOGY_BLOCK}

You will be given adjacent words in a verse whose translations overlap — \
one word has absorbed meaning that belongs to its neighbor. Your job is to \
correct each word's gloss so it translates ONLY that word.

Respond with ONLY a JSON array. /no_think"""

ALIGN_SYSTEM_PROMPT = f"""\
You are aligning word-by-word translations with a verse-level translation \
for a Quran study tool that uses a Quran-only analytical methodology.

{METHODOLOGY_BLOCK}

The verse translation was produced using Quranic cross-references and \
Semitic cognate analysis. Trust it as authoritative. Word glosses must be \
consistent with this verse translation's vocabulary.

Respond with ONLY a JSON array. /no_think"""

CLAUDE_SYSTEM_PROMPT = f"""\
You are a Quranic Arabic linguist specializing in contextual word analysis.

{METHODOLOGY_BLOCK}

CRITICAL: Do NOT use post-Quranic religious terminology. The Quran predates \
these concepts. Translate words as the original Arabic conveys them.

When the conventional (traditional) gloss reflects later theological \
interpretation rather than the Quranic sense, prefer the Quranic sense. \
Include cognate evidence in your reasoning when it informs your decision."""


# --------------- API helpers ---------------

def get_ollama_config():
    """Determine Ollama API URL and headers."""
    api_key = os.environ.get("OLLAMA_API_KEY")
    if api_key:
        return OLLAMA_CLOUD_URL, {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    print("  (No OLLAMA_API_KEY found, using local Ollama)")
    return OLLAMA_LOCAL_URL, {"Content-Type": "application/json"}


def call_ollama(model: str, system_prompt: str, user_prompt: str,
                temperature: float = 0.2) -> tuple[str, int]:
    """Call Ollama API (cloud or local) with streaming."""
    api_url, headers = get_ollama_config()
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": True,
        "options": {"temperature": temperature, "num_ctx": 32768},
    }
    start = time.time()
    resp = requests.post(api_url, json=payload, headers=headers,
                         stream=True, timeout=1800)
    resp.raise_for_status()

    parts = []
    token_count = 0
    for line in resp.iter_lines():
        if not line:
            continue
        chunk = json.loads(line)
        text = chunk.get("message", {}).get("content", "")
        if text:
            parts.append(text)
            token_count += 1
            if token_count % 40 == 0:
                print(".", end="", flush=True)
        if chunk.get("done"):
            break

    elapsed_ms = int((time.time() - start) * 1000)
    return "".join(parts), elapsed_ms


def call_claude(system_prompt: str, user_prompt: str,
                temperature: float = 0.2) -> tuple[str, int]:
    """Call Claude API for escalation."""
    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        raise ValueError("CLAUDE_API_KEY not set — cannot escalate to Claude")

    start = time.time()
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        json={
            "model": CLAUDE_ESCALATION_MODEL,
            "max_tokens": 4096,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        },
        timeout=120,
    )
    resp.raise_for_status()
    body = resp.json()
    text = body.get("content", [{}])[0].get("text", "")
    elapsed_ms = int((time.time() - start) * 1000)
    return text, elapsed_ms


def parse_json_array(raw: str) -> list[dict]:
    """Extract a JSON array from model response, handling markdown fences."""
    cleaned = re.sub(r"```json\s*", "", raw)
    cleaned = re.sub(r"```\s*", "", cleaned)
    cleaned = cleaned.strip()
    # Find the array
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON array found in response: {cleaned[:200]}")
    return json.loads(cleaned[start:end + 1])


# --------------- Data fetching ---------------

def fetch_verse_words(conn, chapter: int, verse: int) -> list[dict]:
    """Fetch all words for a verse with morphology, glosses, and AI meanings."""
    # Get morphology (first segment per word gives us the Arabic form)
    morph_rows = conn.execute(
        "SELECT word_pos, form_arabic, root_buckwalter, root_arabic, "
        "       lemma_buckwalter, lemma_arabic, pos, tag, features_raw, "
        "       gender, number, person, case_val, voice, mood, verb_form "
        "FROM morphology WHERE chapter = ? AND verse = ? "
        "ORDER BY word_pos, segment",
        (chapter, verse),
    ).fetchall()

    # Group morphology by word_pos
    # Keep first content segment (non-prefix) for metadata, concatenate all for Arabic
    morph_by_pos = {}
    arabic_parts = {}  # word_pos -> list of Arabic segment forms
    for row in morph_rows:
        wp = row["word_pos"]
        if wp not in arabic_parts:
            arabic_parts[wp] = []
        arabic_parts[wp].append(row["form_arabic"] or "")

        # Use first non-prefix segment for morphological metadata (root, lemma, POS)
        if wp not in morph_by_pos:
            if row["tag"] != "PREFIX":
                morph_by_pos[wp] = dict(row)
        elif morph_by_pos[wp].get("tag") == "PREFIX" and row["tag"] != "PREFIX":
            morph_by_pos[wp] = dict(row)

    # Build full Arabic word from segments
    arabic_by_pos = {wp: "".join(parts) for wp, parts in arabic_parts.items()}

    # Get conventional glosses
    gloss_rows = conn.execute(
        "SELECT word_pos, translation_en FROM word_glosses "
        "WHERE chapter = ? AND verse = ? ORDER BY word_pos",
        (chapter, verse),
    ).fetchall()
    glosses = {r["word_pos"]: r["translation_en"] for r in gloss_rows}

    # Get AI word meanings (latest per word_pos)
    ai_rows = conn.execute(
        "SELECT wm.word_pos, wm.meaning_short, wm.preferred_translation, "
        "       wm.preferred_source, wm.cognate_notes, wm.align_checked_at "
        "FROM ai_word_meanings wm "
        "INNER JOIN ("
        "  SELECT word_pos, MAX(created_at) AS max_created "
        "  FROM ai_word_meanings "
        "  WHERE chapter = ? AND verse = ? "
        "  GROUP BY word_pos"
        ") latest ON wm.word_pos = latest.word_pos "
        "  AND wm.created_at = latest.max_created "
        "WHERE wm.chapter = ? AND wm.verse = ?",
        (chapter, verse, chapter, verse),
    ).fetchall()
    ai_by_pos = {r["word_pos"]: dict(r) for r in ai_rows}

    # Build unified word list from all positions found
    all_positions = sorted(set(morph_by_pos.keys()) | set(glosses.keys()) | set(ai_by_pos.keys()))

    words = []
    for pos in all_positions:
        morph = morph_by_pos.get(pos, {})
        ai = ai_by_pos.get(pos, {})

        # Current display label (same logic as getWordToWordLabel)
        preferred = ai.get("preferred_translation") or ""
        meaning_short = ai.get("meaning_short") or ""
        conv_gloss = glosses.get(pos, "")
        current_label = preferred or meaning_short or conv_gloss

        words.append({
            "pos": pos,
            "arabic": arabic_by_pos.get(pos, ""),
            "conv_gloss": conv_gloss,
            "root_arabic": morph.get("root_arabic", ""),
            "root_bw": morph.get("root_buckwalter", ""),
            "lemma_arabic": morph.get("lemma_arabic", ""),
            "lemma_bw": morph.get("lemma_buckwalter", ""),
            "pos_tag": morph.get("pos") or morph.get("tag", ""),
            "features": morph.get("features_raw", ""),
            "gender": morph.get("gender", ""),
            "number": morph.get("number", ""),
            "voice": morph.get("voice", ""),
            "verb_form": morph.get("verb_form", ""),
            "preferred_translation": preferred,
            "preferred_source": ai.get("preferred_source", ""),
            "meaning_short": meaning_short,
            "cognate_notes": ai.get("cognate_notes", ""),
            "align_checked_at": ai.get("align_checked_at", ""),
            "current_label": current_label,
        })

    return words


def fetch_verse_translation(conn, chapter: int, verse: int) -> str:
    """Get the AI translation for a verse (preferred), falling back to conventional."""
    ai = conn.execute(
        "SELECT translation_text FROM ai_translations "
        "WHERE chapter = ? AND verse = ? ORDER BY created_at DESC LIMIT 1",
        (chapter, verse),
    ).fetchone()
    if ai:
        return ai["translation_text"]
    conv = conn.execute(
        "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
        (chapter, verse),
    ).fetchone()
    return conv["text_en"] if conv else ""


def fetch_verse_arabic(conn, chapter: int, verse: int) -> str:
    """Get the Arabic text of a verse."""
    row = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
        (chapter, verse),
    ).fetchone()
    if not row:
        return ""
    return _strip_bismillah(row["text_uthmani"], chapter, verse)


# --------------- Deduplication (Problem 2) ---------------

def detect_dedup_candidates(words: list[dict]) -> list[list[dict]]:
    """Find clusters of adjacent words with overlapping glosses.

    Returns list of clusters, where each cluster is a list of words
    whose glosses overlap with a neighbor.

    Detection criteria (must meet ALL):
    1. Adjacent words share a significant content word in their glosses
    2. The shared word constitutes a substantial portion of one word's gloss
       (not just incidental vocabulary overlap)
    3. One word's gloss appears to have "absorbed" meaning from its neighbor
       (e.g., "establish prayer" + "the prayer" = word 1 stole "prayer")
    """
    if len(words) < 2:
        return []

    # Common function words to ignore in overlap detection
    stop = {"the", "a", "an", "of", "to", "in", "and", "for", "is", "it",
            "on", "not", "who", "that", "those", "which", "with", "from",
            "his", "her", "its", "their", "our", "your", "he", "she", "they",
            "be", "are", "was", "were", "will", "shall", "may", "has", "have"}

    overlap_pairs = []
    for i in range(len(words) - 1):
        w1 = words[i]
        w2 = words[i + 1]
        label1 = w1["current_label"].lower().strip()
        label2 = w2["current_label"].lower().strip()
        if not label1 or not label2:
            continue

        tokens1 = label1.split()
        tokens2 = label2.split()

        sig1 = set(tokens1) - stop
        sig2 = set(tokens2) - stop

        if not sig1 or not sig2:
            continue

        overlap = sig1 & sig2
        if not overlap:
            continue

        # STRICTER check: the overlap must indicate actual meaning bleed,
        # not just naturally related vocabulary.
        #
        # Heuristic: at least one word's gloss should be a SUBSET or
        # near-subset of the other's. E.g., "establish prayer" + "the prayer"
        # where "prayer" appears in both. But "the Most Merciful" + "the Most
        # Gracious" sharing "most" is just related vocabulary, not bleed.
        #
        # Check: does the overlap constitute >50% of the smaller word's
        # significant content?
        smaller_sig = sig1 if len(sig1) <= len(sig2) else sig2
        if len(overlap) < len(smaller_sig) * 0.5:
            continue  # Overlap is too small relative to the smaller gloss

        # Also skip if both words have the SAME root (genuinely related words)
        root1 = w1.get("root_bw", "")
        root2 = w2.get("root_bw", "")
        if root1 and root2 and root1 == root2:
            continue  # Same root = genuinely related, not meaning bleed

        overlap_pairs.append((i, i + 1, overlap))

    if not overlap_pairs:
        return []

    # Merge overlapping pairs into clusters
    clusters = []
    used = set()
    for i, j, _overlap in overlap_pairs:
        if i in used and j in used:
            # Both already in clusters; merge if different
            continue
        if i in used:
            for c in clusters:
                if any(w["pos"] == words[i]["pos"] for w in c):
                    if not any(w["pos"] == words[j]["pos"] for w in c):
                        c.append(words[j])
                    used.add(j)
                    break
        elif j in used:
            for c in clusters:
                if any(w["pos"] == words[j]["pos"] for w in c):
                    if not any(w["pos"] == words[i]["pos"] for w in c):
                        c.insert(0, words[i])
                    used.add(i)
                    break
        else:
            clusters.append([words[i], words[j]])
            used.add(i)
            used.add(j)

    return clusters


def build_dedup_prompt(chapter: int, verse: int, cluster: list[dict],
                       arabic_text: str, translation: str) -> str:
    """Build user prompt for dedup fix."""
    word_lines = []
    for w in cluster:
        word_lines.append(
            f"  Word {w['pos']}: {w['arabic']} | "
            f"root={w['root_arabic'] or '—'} | "
            f"POS={w['pos_tag']} | "
            f"current_gloss=\"{w['current_label']}\" | "
            f"conventional=\"{w['conv_gloss']}\""
        )

    return f"""\
## Problem
In verse {chapter}:{verse}, adjacent words have overlapping translations — \
one word has absorbed meaning that belongs to its neighbor.

## The Words
{chr(10).join(word_lines)}

## Full Verse
Arabic: {arabic_text}
Translation: {translation}

## Task
For each word listed, provide a corrected 1-3 word gloss that translates \
ONLY that word — do not leak meaning from neighboring words.
Keep glosses consistent with the verse translation above, which was produced \
using Quranic cross-references and Semitic cognate analysis.

Output ONLY a JSON array:
[{{"word_pos": N, "corrected": "...", "confidence": 0.0-1.0}}]

/no_think"""


# --------------- Alignment (Problem 1) ---------------

def build_align_prompt(chapter: int, verse: int, words: list[dict],
                       arabic_text: str, translation: str) -> str:
    """Build user prompt for alignment fix."""
    word_lines = []
    for w in words:
        features = []
        for k in ("gender", "number", "voice", "verb_form"):
            val = w.get(k, "")
            if val:
                features.append(f"{k}={val}")
        feat_str = ", ".join(features) if features else "—"

        word_lines.append(
            f"  Word {w['pos']}: {w['arabic']} | "
            f"root={w['root_arabic'] or '—'} | "
            f"lemma={w['lemma_arabic'] or '—'} | "
            f"POS={w['pos_tag']} | "
            f"features: {feat_str} | "
            f"current_gloss=\"{w['current_label']}\""
        )

    return f"""\
## Verse {chapter}:{verse}
Arabic: {arabic_text}
Verse Translation: {translation}

## Current Word-by-Word Glosses
{chr(10).join(word_lines)}

## Task
Some word glosses don't match the vocabulary used in the verse translation.
For each word, decide:
- KEEP: the current gloss is fine (consistent with the verse translation)
- FIX: provide a corrected 1-3 word gloss derived from how the verse \
translation renders this word

Rules:
- Each word gets 1-3 words max — suitable for a tooltip
- Don't duplicate meaning across adjacent words
- If the verse translation uses a transliteration (e.g. "ṣalāh", "rabb"), \
flag it with confidence < 0.5 so a more powerful model can decide
- Respect morphology: verb forms, voice, case, number/gender
- Prefer Quran-contextual meaning over traditional/conventional glosses \
when they diverge

Output ONLY a JSON array (only include words where action is "FIX"):
[{{"word_pos": N, "action": "FIX", "corrected": "...", "confidence": 0.0-1.0, "reason": "..."}}]

If all words are fine, output an empty array: []

/no_think"""


# --------------- Claude escalation ---------------

def build_claude_prompt(escalation_items: list[dict]) -> str:
    """Build a batched prompt for Claude escalation of uncertain words."""
    item_lines = []
    for item in escalation_items:
        item_lines.append(
            f"- Verse {item['chapter']}:{item['verse']} word {item['word_pos']}\n"
            f"  Arabic: {item['arabic']}\n"
            f"  Root: {item.get('root_arabic', '—')}\n"
            f"  POS: {item.get('pos_tag', '—')}, features: {item.get('features', '—')}\n"
            f"  Conventional gloss: \"{item.get('conv_gloss', '')}\"\n"
            f"  AI gloss: \"{item.get('meaning_short', '')}\"\n"
            f"  Current preferred: \"{item.get('current_label', '')}\"\n"
            f"  Verse translation: \"{item.get('verse_translation', '')}\"\n"
            f"  Ollama suggestion: \"{item.get('ollama_suggestion', '')}\" "
            f"(confidence={item.get('ollama_confidence', 0)})\n"
            f"  Cognate notes: {item.get('cognate_notes', 'none')}"
        )

    return f"""\
The automated system was uncertain about the correct 1-3 word tooltip gloss \
for each word below.

The verse-level AI translation was generated with full Quranic cross-references \
and Semitic cognate analysis. Trust it as the authoritative interpretation.

## Words Needing Review
{chr(10).join(item_lines)}

## Output
JSON array:
[{{"chapter": N, "verse": N, "word_pos": N, "corrected": "1-3 word gloss", \
"confidence": 0.0-1.0, "reason": "..."}}]

Include cognate evidence in the reason when it informs your decision."""


# --------------- Apply updates ---------------

def apply_fix(conn, chapter: int, verse: int, word_pos: int,
              corrected: str, source: str, reason: str):
    """Update preferred_translation for a word in the database."""
    now = datetime.now().isoformat()

    # Update the latest ai_word_meanings row for this word
    row = conn.execute(
        "SELECT id FROM ai_word_meanings "
        "WHERE chapter = ? AND verse = ? AND word_pos = ? "
        "ORDER BY created_at DESC LIMIT 1",
        (chapter, verse, word_pos),
    ).fetchone()

    if row:
        conn.execute(
            "UPDATE ai_word_meanings SET "
            "  preferred_translation = ?, "
            "  preferred_source = ?, "
            "  judge_reasoning = ?, "
            "  align_checked_at = ? "
            "WHERE id = ?",
            (corrected, source, reason, now, row["id"]),
        )
    else:
        print(f"    WARNING: no ai_word_meanings row for {chapter}:{verse} word {word_pos}")


def mark_checked(conn, chapter: int, verse: int, word_pos: int):
    """Mark a word as alignment-checked without changing its translation."""
    now = datetime.now().isoformat()
    row = conn.execute(
        "SELECT id FROM ai_word_meanings "
        "WHERE chapter = ? AND verse = ? AND word_pos = ? "
        "ORDER BY created_at DESC LIMIT 1",
        (chapter, verse, word_pos),
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE ai_word_meanings SET align_checked_at = ? WHERE id = ?",
            (now, row["id"]),
        )


# --------------- Main pipeline ---------------

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


def get_all_verses_with_ai(conn) -> list[tuple[int, int]]:
    """Get all verses that have both AI translations and AI word meanings."""
    rows = conn.execute(
        "SELECT DISTINCT at_.chapter, at_.verse "
        "FROM ai_translations at_ "
        "INNER JOIN ai_word_meanings awm "
        "  ON at_.chapter = awm.chapter AND at_.verse = awm.verse "
        "ORDER BY at_.chapter, at_.verse"
    ).fetchall()
    return [(r["chapter"], r["verse"]) for r in rows]


def process_verse_dedup(conn, chapter: int, verse: int, model: str,
                        apply: bool, force: bool) -> list[dict]:
    """Run dedup detection and fix for a single verse.
    Returns list of escalation items (low-confidence fixes)."""
    words = fetch_verse_words(conn, chapter, verse)
    if not words:
        return []

    clusters = detect_dedup_candidates(words)
    if not clusters:
        return []

    arabic = fetch_verse_arabic(conn, chapter, verse)
    translation = fetch_verse_translation(conn, chapter, verse)
    escalation_items = []

    for cluster in clusters:
        positions = [w["pos"] for w in cluster]

        # Skip if already checked (unless --force)
        if not force:
            if all(w.get("align_checked_at") for w in cluster):
                continue

        overlap_words = []
        for w in cluster:
            overlap_words.append(f"word {w['pos']} \"{w['current_label']}\"")
        print(f"    DEDUP: {' vs '.join(overlap_words)}")

        prompt = build_dedup_prompt(chapter, verse, cluster, arabic, translation)
        print(f"    Calling {model}...", end="", flush=True)

        try:
            raw, ms = call_ollama(model, DEDUP_SYSTEM_PROMPT, prompt)
            print(f" ({ms}ms)")
            fixes = parse_json_array(raw)
        except Exception as e:
            print(f" ERROR: {e}")
            continue

        for fix in fixes:
            wp = fix.get("word_pos")
            corrected = fix.get("corrected", "").strip()
            confidence = fix.get("confidence", 0)

            if not wp or not corrected:
                continue

            # Find the word data for escalation
            word_data = next((w for w in cluster if w["pos"] == wp), None)
            if not word_data:
                continue

            if confidence >= CONF_AUTO_APPLY:
                print(f"      word {wp}: \"{word_data['current_label']}\" -> "
                      f"\"{corrected}\" (conf={confidence}) ✓")
                if apply:
                    apply_fix(conn, chapter, verse, wp, corrected,
                              "align_fix_dedup", f"Dedup fix, confidence={confidence}")
                    mark_checked(conn, chapter, verse, wp)
            elif confidence >= CONF_ESCALATE:
                print(f"      word {wp}: \"{word_data['current_label']}\" -> "
                      f"\"{corrected}\" (conf={confidence}) → ESCALATE")
                escalation_items.append({
                    "chapter": chapter, "verse": verse, "word_pos": wp,
                    "arabic": word_data["arabic"],
                    "root_arabic": word_data["root_arabic"],
                    "pos_tag": word_data["pos_tag"],
                    "features": word_data["features"],
                    "conv_gloss": word_data["conv_gloss"],
                    "meaning_short": word_data["meaning_short"],
                    "current_label": word_data["current_label"],
                    "verse_translation": translation,
                    "ollama_suggestion": corrected,
                    "ollama_confidence": confidence,
                    "cognate_notes": word_data.get("cognate_notes", ""),
                    "fix_type": "dedup",
                })
            else:
                print(f"      word {wp}: conf={confidence} too low, skipping")

        # Mark remaining unchecked words in cluster
        if apply:
            for w in cluster:
                if not any(f.get("word_pos") == w["pos"] for f in fixes
                           if f.get("confidence", 0) >= CONF_AUTO_APPLY):
                    mark_checked(conn, chapter, verse, w["pos"])

    if apply:
        conn.commit()

    return escalation_items


def process_verse_align(conn, chapter: int, verse: int, model: str,
                        apply: bool, force: bool) -> list[dict]:
    """Run alignment detection and fix for a single verse.
    Returns list of escalation items (low-confidence fixes)."""
    words = fetch_verse_words(conn, chapter, verse)
    if not words:
        return []

    # Skip if all words already checked (unless --force)
    if not force:
        if all(w.get("align_checked_at") for w in words):
            return []

    arabic = fetch_verse_arabic(conn, chapter, verse)
    translation = fetch_verse_translation(conn, chapter, verse)

    if not translation:
        return []

    # Filter to unchecked words (unless --force)
    words_to_check = words if force else [
        w for w in words if not w.get("align_checked_at")
    ]

    if not words_to_check:
        return []

    prompt = build_align_prompt(chapter, verse, words_to_check, arabic, translation)
    print(f"    Calling {model} for alignment ({len(words_to_check)} words)...",
          end="", flush=True)

    try:
        raw, ms = call_ollama(model, ALIGN_SYSTEM_PROMPT, prompt)
        print(f" ({ms}ms)")
        fixes = parse_json_array(raw)
    except Exception as e:
        print(f" ERROR: {e}")
        return []

    escalation_items = []

    for fix in fixes:
        wp = fix.get("word_pos")
        corrected = fix.get("corrected", "").strip()
        confidence = fix.get("confidence", 0)
        reason = fix.get("reason", "")

        if not wp or not corrected:
            continue

        word_data = next((w for w in words if w["pos"] == wp), None)
        if not word_data:
            continue

        # Skip if corrected is same as current
        if corrected.lower().strip() == word_data["current_label"].lower().strip():
            if apply:
                mark_checked(conn, chapter, verse, wp)
            continue

        if confidence >= CONF_AUTO_APPLY:
            print(f"      word {wp}: \"{word_data['current_label']}\" -> "
                  f"\"{corrected}\" (conf={confidence}) ✓ — {reason[:80]}")
            if apply:
                apply_fix(conn, chapter, verse, wp, corrected,
                          "align_fix", f"Alignment fix: {reason}")
                mark_checked(conn, chapter, verse, wp)
        elif confidence >= CONF_ESCALATE:
            print(f"      word {wp}: \"{word_data['current_label']}\" -> "
                  f"\"{corrected}\" (conf={confidence}) → ESCALATE — {reason[:80]}")
            escalation_items.append({
                "chapter": chapter, "verse": verse, "word_pos": wp,
                "arabic": word_data["arabic"],
                "root_arabic": word_data["root_arabic"],
                "pos_tag": word_data["pos_tag"],
                "features": word_data["features"],
                "conv_gloss": word_data["conv_gloss"],
                "meaning_short": word_data["meaning_short"],
                "current_label": word_data["current_label"],
                "verse_translation": translation,
                "ollama_suggestion": corrected,
                "ollama_confidence": confidence,
                "cognate_notes": word_data.get("cognate_notes", ""),
                "fix_type": "align",
            })
        else:
            print(f"      word {wp}: conf={confidence} too low, skipping")

    # Mark all checked words that weren't fixed
    if apply:
        fixed_positions = {f.get("word_pos") for f in fixes
                          if f.get("confidence", 0) >= CONF_AUTO_APPLY}
        for w in words_to_check:
            if w["pos"] not in fixed_positions:
                mark_checked(conn, chapter, verse, w["pos"])
        conn.commit()

    return escalation_items


def run_claude_escalation(conn, items: list[dict], apply: bool) -> dict:
    """Send uncertain words to Claude for expert review. Returns stats."""
    if not items:
        return {"escalated": 0, "fixed": 0, "skipped": 0}

    stats = {"escalated": len(items), "fixed": 0, "skipped": 0}

    # Process in batches
    for i in range(0, len(items), CLAUDE_BATCH_SIZE):
        batch = items[i:i + CLAUDE_BATCH_SIZE]
        print(f"\n  Claude escalation batch {i // CLAUDE_BATCH_SIZE + 1} "
              f"({len(batch)} words)...", end="", flush=True)

        prompt = build_claude_prompt(batch)
        try:
            raw, ms = call_claude(CLAUDE_SYSTEM_PROMPT, prompt)
            print(f" ({ms}ms)")
            fixes = parse_json_array(raw)
        except Exception as e:
            print(f" ERROR: {e}")
            stats["skipped"] += len(batch)
            continue

        for fix in fixes:
            ch = fix.get("chapter")
            vs = fix.get("verse")
            wp = fix.get("word_pos")
            corrected = fix.get("corrected", "").strip()
            confidence = fix.get("confidence", 0)
            reason = fix.get("reason", "")

            if not ch or not vs or not wp or not corrected:
                continue

            if confidence >= CONF_ESCALATE:
                # Find original item for context
                orig = next((it for it in batch
                             if it["chapter"] == ch and it["verse"] == vs
                             and it["word_pos"] == wp), None)
                old_label = orig["current_label"] if orig else "?"

                print(f"    Claude: {ch}:{vs} word {wp}: "
                      f"\"{old_label}\" -> \"{corrected}\" "
                      f"(conf={confidence}) — {reason[:80]}")

                if apply:
                    apply_fix(conn, ch, vs, wp, corrected,
                              "align_fix_claude",
                              f"Claude escalation: {reason}")
                    mark_checked(conn, ch, vs, wp)
                stats["fixed"] += 1
            else:
                stats["skipped"] += 1

        if apply:
            conn.commit()

        # Small delay between batches
        if i + CLAUDE_BATCH_SIZE < len(items):
            time.sleep(1)

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Fix word-to-word translation alignment and deduplication"
    )
    parser.add_argument("--mode", choices=["align", "dedup", "both"],
                        default="both", help="Which fix mode to run")
    parser.add_argument("--verses", help="Verse specs, e.g. '1:1-7,33:56'")
    parser.add_argument("--all", action="store_true",
                        help="Process all verses with AI translations")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print proposed changes without applying (this is the default)")
    parser.add_argument("--apply", action="store_true",
                        help="Actually write changes (default is dry-run)")
    parser.add_argument("--force", action="store_true",
                        help="Re-evaluate already-checked words")
    parser.add_argument("--model", default=DEFAULT_OLLAMA_MODEL,
                        help=f"Ollama model (default: {DEFAULT_OLLAMA_MODEL})")
    parser.add_argument("--no-escalate", action="store_true",
                        help="Skip Claude escalation for uncertain cases")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Seconds between verse API calls (default: 1.0)")
    args = parser.parse_args()

    if not args.verses and not args.all:
        print("ERROR: specify --verses or --all")
        sys.exit(1)

    # Check API keys
    if not os.environ.get("OLLAMA_API_KEY"):
        print("WARNING: No OLLAMA_API_KEY set, will try local Ollama")

    if not args.no_escalate and not os.environ.get("CLAUDE_API_KEY"):
        print("WARNING: No CLAUDE_API_KEY set, Claude escalation will be skipped")

    conn = get_db()

    # Build verse list
    if args.all:
        verses = get_all_verses_with_ai(conn)
        print(f"Found {len(verses)} verses with AI translations + word meanings")
    else:
        verses = parse_verse_spec(args.verses)
        print(f"Processing {len(verses)} specified verse(s)")

    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"Mode: {args.mode} | {mode} | Model: {args.model}\n")

    all_escalation_items = []
    stats = {
        "verses_processed": 0,
        "dedup_fixes": 0,
        "align_fixes": 0,
        "escalated": 0,
        "errors": 0,
    }

    for i, (chapter, verse) in enumerate(verses):
        print(f"[{i + 1}/{len(verses)}] Verse {chapter}:{verse}")
        stats["verses_processed"] += 1

        try:
            if args.mode in ("dedup", "both"):
                escalations = process_verse_dedup(
                    conn, chapter, verse, args.model, args.apply, args.force
                )
                all_escalation_items.extend(escalations)

            if args.mode in ("align", "both"):
                escalations = process_verse_align(
                    conn, chapter, verse, args.model, args.apply, args.force
                )
                all_escalation_items.extend(escalations)

        except Exception as e:
            print(f"  ERROR: {e}")
            stats["errors"] += 1

        if args.delay > 0 and i < len(verses) - 1:
            time.sleep(args.delay)

    # Claude escalation phase
    if all_escalation_items and not args.no_escalate:
        print(f"\n{'='*60}")
        print(f"CLAUDE ESCALATION: {len(all_escalation_items)} uncertain word(s)")
        print(f"{'='*60}")

        claude_stats = run_claude_escalation(
            conn, all_escalation_items, args.apply
        )
        stats["escalated"] = claude_stats["escalated"]
        stats["dedup_fixes"] += sum(
            1 for it in all_escalation_items if it["fix_type"] == "dedup"
        )
        stats["align_fixes"] += sum(
            1 for it in all_escalation_items if it["fix_type"] == "align"
        )
    elif all_escalation_items:
        print(f"\n  Skipped Claude escalation for {len(all_escalation_items)} "
              f"uncertain word(s) (--no-escalate)")

    conn.close()

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY ({mode})")
    print(f"{'='*60}")
    print(f"  Verses processed: {stats['verses_processed']}")
    print(f"  Escalated to Claude: {len(all_escalation_items)}")
    print(f"  Errors: {stats['errors']}")

    if not args.apply:
        print("\n  This was a DRY RUN. Use --apply to write changes.")


if __name__ == "__main__":
    main()
