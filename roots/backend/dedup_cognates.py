#!/usr/bin/env python3
"""Deduplicate and clean Semitic cognate derivatives using an LLM.

For each root where a language appears more than once, an LLM decides whether
to merge entries (same meaning, different transliterations), remove redundant
ones, or keep them all.

Usage:
    python dedup_cognates.py --dry-run              # Preview all, no changes
    python dedup_cognates.py --limit 10              # Process first 10 roots
    python dedup_cognates.py --all                   # Process everything
    python dedup_cognates.py --root "ṣ-b-r"          # Process a single root
    python dedup_cognates.py --all --model qwen3:14b # Use a different model
"""

import argparse
import json
import re
import sqlite3
import sys
import time

from app import DB_PATH
from translate_ai import call_model

DEFAULT_MODEL = "minimax-m2.5:cloud"

SYSTEM_PROMPT = """\
You are a Semitic linguistics data-cleaning engine. You will receive a list of \
cognate entries for a SINGLE language under a SINGLE Semitic root. Some entries \
may be duplicates, near-duplicates, or complementary records from different \
sources.

Your task: decide how to MERGE or REMOVE redundant entries so the final list \
has no repetition, while preserving all unique information.

## Rules
1. If two entries have the same word form (even if transliterated differently) \
AND the same meaning, MERGE them into one. Pick the best displayed_text — \
prefer the one with native script (Arabic/Hebrew/etc.) over plain ASCII. \
Combine meanings if one has extra detail the other lacks.
2. If entries represent genuinely DIFFERENT word forms or different meanings \
from the same root (e.g., a noun vs a verb, or two distinct senses), KEEP \
them as separate entries.
3. If one entry is strictly a subset of another (same word, less detail), \
REMOVE the weaker one.
4. If an entry has NO real meaning (the meaning field just repeats the word \
itself, or is empty/null), it is a low-quality record. REMOVE it if a better \
entry for the same language exists. If it's the ONLY entry for that language, \
keep it but note the issue.
5. Preserve the original language, word, and meaning data faithfully — do NOT \
invent new meanings or change the linguistic content. Only merge/deduplicate.

## Output Format
Return a JSON array of objects, each with these fields:
  - "keep_ids": array of original IDs being merged into this entry
  - "displayed_text": the best displayed_text to use
  - "word": the best word form
  - "meaning": the combined/best meaning
  - "concept": the best concept value (or null if none)

If ALL entries should be kept as-is with no changes, return: []

Return ONLY the JSON array, no other text.\
"""


def get_duplicates(conn: sqlite3.Connection) -> dict:
    """Find all (root_transliteration, language) pairs with >1 entry.

    Groups across multiple root_ids that share the same transliteration,
    since _get_cognate() in app.py merges them for display.
    """
    rows = conn.execute("""
        SELECT r.transliteration, d.language, COUNT(*) as cnt,
               GROUP_CONCAT(DISTINCT r.id) as root_ids
        FROM semitic_derivatives d
        JOIN semitic_roots r ON d.root_id = r.id
        GROUP BY r.transliteration, d.language
        HAVING COUNT(*) > 1
        ORDER BY r.transliteration, d.language
    """).fetchall()

    groups = {}
    for row in rows:
        root_id_list = [int(x) for x in row["root_ids"].split(",")]
        key = (row["transliteration"], tuple(root_id_list), row["language"])
        groups[key] = row["cnt"]
    return groups


def get_entries(conn: sqlite3.Connection, root_ids: tuple, language: str) -> list[dict]:
    """Get all derivative entries for root_id(s) + language."""
    placeholders = ",".join("?" for _ in root_ids)
    rows = conn.execute(
        f"SELECT id, root_id, language, word, displayed_text, concept, meaning "
        f"FROM semitic_derivatives WHERE root_id IN ({placeholders}) AND language = ? ORDER BY id",
        (*root_ids, language),
    ).fetchall()
    return [dict(r) for r in rows]


def build_prompt(root_trans: str, language: str, entries: list[dict]) -> str:
    """Build the user prompt for the LLM."""
    lines = [
        f"Root: {root_trans}",
        f"Language: {language}",
        f"Entries ({len(entries)}):",
        "",
    ]
    for e in entries:
        lines.append(
            f"  ID={e['id']}  word={e['word']!r}  displayed_text={e['displayed_text']!r}  "
            f"concept={e['concept']!r}  meaning={e['meaning']!r}"
        )
    return "\n".join(lines)


def parse_llm_response(raw: str) -> list[dict] | None:
    """Parse the JSON array from the LLM response."""
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
    cleaned = re.sub(r"```\s*$", "", cleaned).strip()

    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            return result
        return None
    except json.JSONDecodeError:
        # Try to find a JSON array in the response
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return None


def apply_merges(conn: sqlite3.Connection, merges: list[dict], dry_run: bool = False) -> tuple[int, int]:
    """Apply merge decisions. Returns (merged_count, deleted_count)."""
    merged = 0
    deleted = 0

    for merge in merges:
        keep_ids = merge.get("keep_ids", [])
        if not keep_ids or len(keep_ids) < 2:
            continue

        # Keep the first ID, update it with merged data, delete the rest
        primary_id = keep_ids[0]
        delete_ids = keep_ids[1:]

        if dry_run:
            print(f"    MERGE: keep ID {primary_id}, delete IDs {delete_ids}")
            print(f"      → displayed_text: {merge.get('displayed_text', '?')}")
            print(f"      → meaning: {merge.get('meaning', '?')[:80]}")
            merged += 1
            deleted += len(delete_ids)
            continue

        # Update the primary entry
        conn.execute(
            "UPDATE semitic_derivatives SET displayed_text=?, word=?, meaning=?, concept=? WHERE id=?",
            (
                merge.get("displayed_text", ""),
                merge.get("word", ""),
                merge.get("meaning", ""),
                merge.get("concept"),
                primary_id,
            ),
        )

        # Delete the redundant entries
        for did in delete_ids:
            conn.execute("DELETE FROM semitic_derivatives WHERE id=?", (did,))

        merged += 1
        deleted += len(delete_ids)

    return merged, deleted


def process_group(
    conn: sqlite3.Connection,
    root_trans: str,
    root_ids: tuple,
    language: str,
    model: str,
    dry_run: bool,
) -> tuple[int, int]:
    """Process one (root, language) group. Returns (merged, deleted)."""
    entries = get_entries(conn, root_ids, language)
    if len(entries) < 2:
        return 0, 0

    prompt = build_prompt(root_trans, language, entries)

    if dry_run:
        print(f"\n{'='*60}")
        print(f"Root: {root_trans} | Language: {language} | Entries: {len(entries)}")
        for e in entries:
            print(f"  [{e['id']}] {e['displayed_text']}  →  {(e['meaning'] or '')[:60]}")

    try:
        raw_response, tokens = call_model(model, SYSTEM_PROMPT, prompt, temperature=0.1)
    except Exception as exc:
        print(f"  ⚠ LLM error for {root_trans}/{language}: {exc}", file=sys.stderr)
        return 0, 0

    merges = parse_llm_response(raw_response)
    if merges is None:
        print(f"  ⚠ Could not parse LLM response for {root_trans}/{language}", file=sys.stderr)
        if dry_run:
            print(f"    Raw: {raw_response[:200]}")
        return 0, 0

    if not merges:
        if dry_run:
            print(f"  → LLM says: keep all as-is (no duplicates)")
            print(f"    Raw response: {raw_response[:300]}")
        return 0, 0

    merged, deleted = apply_merges(conn, merges, dry_run)

    if dry_run:
        print(f"  → Would merge {merged} groups, delete {deleted} rows")
    else:
        conn.commit()

    return merged, deleted


def main():
    parser = argparse.ArgumentParser(description="Deduplicate Semitic cognate entries using LLM")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying DB")
    parser.add_argument("--all", action="store_true", help="Process all roots with duplicates")
    parser.add_argument("--root", type=str, help="Process a single root (e.g., 'ṣ-b-r')")
    parser.add_argument("--limit", type=int, default=0, help="Max number of groups to process")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help=f"Model (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    if not args.all and not args.root:
        print("Specify --all or --root <transliteration>. Use --dry-run to preview.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    groups = get_duplicates(conn)
    print(f"Found {len(groups)} (root, language) groups with duplicates")

    # Filter to specific root if requested
    if args.root:
        groups = {k: v for k, v in groups.items() if k[0] == args.root}
        if not groups:
            print(f"No duplicates found for root '{args.root}'")
            sys.exit(0)

    if args.limit:
        items = list(groups.items())[:args.limit]
        groups = dict(items)

    total_merged = 0
    total_deleted = 0
    processed = 0

    for (root_trans, root_ids, language), cnt in groups.items():
        merged, deleted = process_group(
            conn, root_trans, root_ids, language, args.model, args.dry_run,
        )
        total_merged += merged
        total_deleted += deleted
        processed += 1

        if not args.dry_run and processed % 20 == 0:
            print(f"  ... processed {processed}/{len(groups)}, merged {total_merged}, deleted {total_deleted}")

    print(f"\nDone. Processed {processed} groups.")
    print(f"  Merged: {total_merged} groups")
    print(f"  Deleted: {total_deleted} redundant rows")
    if args.dry_run:
        print("  (dry-run — no changes made)")

    conn.close()


if __name__ == "__main__":
    main()
