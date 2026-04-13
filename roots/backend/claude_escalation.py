"""Claude-only escalation pass for word gloss alignment.

Instead of re-running every word through Ollama to find mid-confidence items,
this script directly identifies potentially misaligned words by comparing
current glosses against the verse translation, then sends them to Claude
Sonnet in batches for expert review.

Usage:
    python claude_escalation.py --dry-run          # Preview what would be sent
    python claude_escalation.py --apply            # Apply Claude's fixes
    python claude_escalation.py --apply --delay 2  # Slower pace
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

# Import shared utilities from the main pipeline
from fix_word_glosses_ai import (
    CLAUDE_SYSTEM_PROMPT,
    CLAUDE_ESCALATION_MODEL,
    call_claude,
    parse_json_array,
    fetch_verse_words,
    fetch_verse_translation,
    fetch_verse_arabic,
    apply_fix,
    mark_checked,
    get_all_verses_with_ai,
    detect_dedup_candidates,
)

CLAUDE_BATCH_SIZE = 15  # words per Claude call (keep smaller for quality)
MAX_RETRIES = 5
RETRY_BASE_DELAY = 10  # seconds, doubles each retry


def call_claude_with_retry(system_prompt: str, user_prompt: str) -> tuple[str, int]:
    """Call Claude API with exponential backoff retry on 529/5xx errors."""
    for attempt in range(MAX_RETRIES):
        try:
            return call_claude(system_prompt, user_prompt)
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else 0
            if status in (429, 529) or status >= 500:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                print(f" [{status} retry {attempt+1}/{MAX_RETRIES}, "
                      f"waiting {delay}s]", end="", flush=True)
                time.sleep(delay)
            else:
                raise
    # Final attempt — let it raise
    return call_claude(system_prompt, user_prompt)


def find_misaligned_words(words: list[dict], translation: str) -> list[dict]:
    """Identify words whose current gloss looks misaligned with the verse translation.

    Uses heuristic string matching — no LLM needed. Returns words that:
    1. Have a non-trivial gloss (not just particles)
    2. Whose gloss doesn't appear (even partially) in the verse translation
    3. Were NOT already fixed by Claude in a previous run
    """
    if not translation:
        return []

    trans_lower = translation.lower()
    # Build a set of significant words from the translation
    trans_words = set(trans_lower.split())

    # Stop words to ignore
    stop = {"the", "a", "an", "of", "to", "in", "and", "for", "is", "it",
            "on", "not", "who", "that", "those", "which", "with", "from",
            "his", "her", "its", "their", "our", "your", "he", "she", "they",
            "be", "are", "was", "were", "will", "shall", "may", "has", "have",
            "do", "does", "did", "but", "or", "if", "no", "so", "then",
            "them", "him", "we", "you", "i", "my", "me"}

    misaligned = []
    for w in words:
        label = w["current_label"].strip()
        if not label:
            continue

        # Skip if already fixed by Claude
        if w.get("preferred_source") == "align_fix_claude":
            continue

        # Skip pure function words / very short glosses
        gloss_tokens = label.lower().split()
        sig_tokens = [t for t in gloss_tokens if t not in stop]
        if not sig_tokens:
            continue

        # Check if ANY significant gloss word appears in the translation
        found = False
        for token in sig_tokens:
            # Check substring match (e.g., "merciful" matches "Ever-Merciful")
            if token in trans_lower:
                found = True
                break
            # Check stem overlap (first 4+ chars)
            if len(token) >= 4:
                stem = token[:4]
                for tw in trans_words:
                    if stem in tw:
                        found = True
                        break
            if found:
                break

        if not found:
            misaligned.append(w)

    return misaligned


def find_dedup_candidates(words: list[dict]) -> list[dict]:
    """Find words involved in potential meaning bleed that weren't caught before."""
    clusters = detect_dedup_candidates(words)
    dedup_words = []
    seen_pos = set()
    for cluster in clusters:
        for w in cluster:
            if w["pos"] not in seen_pos:
                # Skip if already fixed by Claude
                if w.get("preferred_source") == "align_fix_claude":
                    continue
                dedup_words.append(w)
                seen_pos.add(w["pos"])
    return dedup_words


def build_escalation_prompt(items: list[dict]) -> str:
    """Build a batched prompt for Claude review."""
    item_lines = []
    for item in items:
        item_lines.append(
            f"- Verse {item['chapter']}:{item['verse']} word {item['word_pos']}\n"
            f"  Arabic: {item['arabic']}\n"
            f"  Root: {item.get('root_arabic', '—')}\n"
            f"  POS: {item.get('pos_tag', '—')}, features: {item.get('features', '—')}\n"
            f"  Conventional gloss: \"{item.get('conv_gloss', '')}\"\n"
            f"  AI gloss: \"{item.get('meaning_short', '')}\"\n"
            f"  Current preferred: \"{item.get('current_label', '')}\"\n"
            f"  Verse translation: \"{item.get('verse_translation', '')}\"\n"
            f"  Cognate notes: {item.get('cognate_notes', 'none')}\n"
            f"  Issue: {item.get('issue', 'potential misalignment')}"
        )

    return f"""\
Review each word below. The current word-level gloss may be misaligned with \
the verse-level translation, or may have meaning bleed from adjacent words.

The verse-level AI translation was generated with full Quranic cross-references \
and Semitic cognate analysis. Trust it as the authoritative interpretation.

For each word, provide a corrected 1-3 word tooltip gloss that:
1. Translates ONLY that specific Arabic word/morpheme
2. Uses vocabulary consistent with the verse translation
3. Follows Quran-only methodology (no post-Quranic terminology)

If the current gloss is actually correct, return it unchanged with confidence 1.0.

## Words Needing Review
{chr(10).join(item_lines)}

## Output
JSON array:
[{{"chapter": N, "verse": N, "word_pos": N, "corrected": "1-3 word gloss", \
"confidence": 0.0-1.0, "reason": "brief explanation with cognate evidence if relevant"}}]"""


def main():
    parser = argparse.ArgumentParser(
        description="Claude-only escalation pass for word gloss alignment"
    )
    parser.add_argument("--apply", action="store_true",
                        help="Apply Claude's fixes to DB")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without applying (default)")
    parser.add_argument("--delay", type=float, default=1.5,
                        help="Seconds between Claude API calls (default: 1.5)")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max words to send to Claude (0 = all)")
    args = parser.parse_args()

    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        print("ERROR: CLAUDE_API_KEY not set")
        sys.exit(1)

    conn = get_db()
    verses = get_all_verses_with_ai(conn)
    print(f"Scanning {len(verses)} verses for misaligned/dedup words...")

    # Phase 1: Identify candidates (no LLM calls, pure heuristics)
    all_candidates = []

    for i, (chapter, verse) in enumerate(verses):
        words = fetch_verse_words(conn, chapter, verse)
        if not words:
            continue

        translation = fetch_verse_translation(conn, chapter, verse)

        # Find alignment issues
        misaligned = find_misaligned_words(words, translation)
        for w in misaligned:
            all_candidates.append({
                "chapter": chapter,
                "verse": verse,
                "word_pos": w["pos"],
                "arabic": w["arabic"],
                "root_arabic": w.get("root_arabic", ""),
                "pos_tag": w.get("pos_tag", ""),
                "features": w.get("features", ""),
                "conv_gloss": w.get("conv_gloss", ""),
                "meaning_short": w.get("meaning_short", ""),
                "current_label": w.get("current_label", ""),
                "verse_translation": translation,
                "cognate_notes": w.get("cognate_notes", ""),
                "issue": "gloss not reflected in verse translation",
                "fix_type": "align",
            })

        # Find dedup issues
        dedup_words = find_dedup_candidates(words)
        for w in dedup_words:
            # Avoid duplicating if already in misaligned list
            key = (chapter, verse, w["pos"])
            if any((c["chapter"], c["verse"], c["word_pos"]) == key for c in all_candidates):
                continue
            all_candidates.append({
                "chapter": chapter,
                "verse": verse,
                "word_pos": w["pos"],
                "arabic": w["arabic"],
                "root_arabic": w.get("root_arabic", ""),
                "pos_tag": w.get("pos_tag", ""),
                "features": w.get("features", ""),
                "conv_gloss": w.get("conv_gloss", ""),
                "meaning_short": w.get("meaning_short", ""),
                "current_label": w.get("current_label", ""),
                "verse_translation": translation,
                "cognate_notes": w.get("cognate_notes", ""),
                "issue": "potential meaning bleed with adjacent word",
                "fix_type": "dedup",
            })

        if (i + 1) % 500 == 0:
            print(f"  Scanned {i + 1}/{len(verses)} verses, "
                  f"{len(all_candidates)} candidates so far...")

    print(f"\nFound {len(all_candidates)} candidate words for Claude review")
    align_count = sum(1 for c in all_candidates if c["fix_type"] == "align")
    dedup_count = sum(1 for c in all_candidates if c["fix_type"] == "dedup")
    print(f"  Alignment issues: {align_count}")
    print(f"  Dedup issues: {dedup_count}")

    if not all_candidates:
        print("Nothing to escalate!")
        conn.close()
        return

    if args.limit > 0:
        all_candidates = all_candidates[:args.limit]
        print(f"  Limited to first {args.limit} candidates")

    if not args.apply:
        # Show sample
        print(f"\nSample candidates (first 10):")
        for c in all_candidates[:10]:
            print(f"  {c['chapter']}:{c['verse']} word {c['word_pos']}: "
                  f"\"{c['current_label']}\" — {c['issue']}")
        print(f"\nThis was a DRY RUN. Use --apply to send to Claude and write fixes.")
        conn.close()
        return

    # Phase 2: Send to Claude in batches
    mode = "APPLY"
    print(f"\n{'='*60}")
    print(f"CLAUDE ESCALATION: {len(all_candidates)} words")
    print(f"{'='*60}")

    stats = {"sent": 0, "fixed": 0, "unchanged": 0, "errors": 0}

    for i in range(0, len(all_candidates), CLAUDE_BATCH_SIZE):
        batch = all_candidates[i:i + CLAUDE_BATCH_SIZE]
        batch_num = i // CLAUDE_BATCH_SIZE + 1
        total_batches = (len(all_candidates) + CLAUDE_BATCH_SIZE - 1) // CLAUDE_BATCH_SIZE

        print(f"\n  Batch {batch_num}/{total_batches} ({len(batch)} words)...",
              end="", flush=True)
        stats["sent"] += len(batch)

        prompt = build_escalation_prompt(batch)
        try:
            raw, ms = call_claude_with_retry(CLAUDE_SYSTEM_PROMPT, prompt)
            print(f" ({ms}ms)")
            fixes = parse_json_array(raw)
        except Exception as e:
            print(f" ERROR: {e}")
            stats["errors"] += len(batch)
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

            # Find the original item
            orig = next((it for it in batch
                         if it["chapter"] == ch and it["verse"] == vs
                         and it["word_pos"] == wp), None)
            old_label = orig["current_label"] if orig else "?"

            if corrected.lower() == old_label.lower():
                # Claude says current is fine
                print(f"    {ch}:{vs} word {wp}: \"{old_label}\" — unchanged (conf={confidence})")
                stats["unchanged"] += 1
                mark_checked(conn, ch, vs, wp)
            elif confidence >= 0.50:
                print(f"    {ch}:{vs} word {wp}: \"{old_label}\" -> "
                      f"\"{corrected}\" (conf={confidence}) — {reason[:80]}")
                apply_fix(conn, ch, vs, wp, corrected,
                          "align_fix_claude",
                          f"Claude escalation: {reason}")
                stats["fixed"] += 1
            else:
                print(f"    {ch}:{vs} word {wp}: conf={confidence} too low, skipping")

        conn.commit()

        if args.delay > 0 and i + CLAUDE_BATCH_SIZE < len(all_candidates):
            time.sleep(args.delay)

    conn.close()

    # Summary
    print(f"\n{'='*60}")
    print(f"CLAUDE ESCALATION SUMMARY ({mode})")
    print(f"{'='*60}")
    print(f"  Words sent to Claude: {stats['sent']}")
    print(f"  Fixed: {stats['fixed']}")
    print(f"  Unchanged: {stats['unchanged']}")
    print(f"  Errors: {stats['errors']}")


if __name__ == "__main__":
    main()
