#!/usr/bin/env python3
"""Generate AI-powered root meanings from Quranic usage.

For each Arabic root, this script:
1. Gathers all lemmas, word glosses, morphological data, verse samples, and cognates
2. Sends a structured prompt to an LLM
3. Stores a primary meaning (1-5 words) and detailed meaning (paragraph) in the DB

Usage:
    python root_meanings_ai.py --roots "Elm,Hmd,wsm" --dry-run
    python root_meanings_ai.py --all --model minimax-m2.5:cloud
    python root_meanings_ai.py --all --force
"""

import argparse
import re
import sqlite3
import sys
import time
from collections import defaultdict

from app import (
    DB_PATH,
    _get_cognate,
    _root_arabic_map,
    _root_inv,
    get_db,
)
from translate_ai import call_model

DEFAULT_MODEL = "minimax-m2.5:cloud"
DEFAULT_CONFIG = "root-meaning-v1"
MAX_SAMPLE_VERSES = 20
MAX_GLOSSES = 20

SYSTEM_PROMPT = """\
You are a Quranic root analysis engine. Your task is to determine the core \
meaning of an Arabic ROOT as the Quran itself uses it, working ONLY from the \
verse evidence provided below.

## Critical Constraints
- Work EXCLUSIVELY from the Quranic text provided. Do NOT import meanings \
from hadith, tafsir, fiqh, or later Islamic tradition.
- Do NOT use words like "Islamic", "halal", "haram", "sunnah", or any \
terminology that comes from post-Quranic religious tradition. These are \
external frameworks imposed on the text.
- When a root seems related to a ritual or practice, ask: what does the \
Quranic TEXT ITSELF say this word means? Derive the sense from the verse \
context and Semitic cognates, not from how the word is used in later religion.
- Be especially careful with roots that have acquired strong traditional \
religious meanings (prayer, fasting, pilgrimage, slaughter, purity, etc.). \
The Quran may use these roots with a broader or different sense than the \
ritualized meaning they later acquired.

## Methodology
1. Examine how the Quran uses this root across ALL provided verse samples. \
Pay close attention to the RANGE of meanings across different contexts — a \
single root may carry different senses in different verses (e.g., ض ر ب \
may mean "strike" in one verse, "mint/coin" in another, "set forth an example" \
in another). Map out this full semantic range, then triangulate the underlying \
core concept that connects all usages.
2. Consider the morphological variety — how Form I vs Form II vs Form V etc. \
shift the core meaning. The primary meaning should capture what unites all forms.
3. Use Semitic cognate evidence to illuminate the root's original semantic range. \
Note where Quranic usage agrees with, narrows, or extends the cognate meaning.
4. Where relevant, mention physical-world or concrete origins of the root \
(e.g., a root that derives from an animal, body part, or natural phenomenon). \
Many Arabic roots have concrete etymological origins that illuminate their \
abstract Quranic usage.
5. Be objective and descriptive. Do not use devotional language ("praise be", \
"glory to", "the Almighty"). Describe what the text does, not what the reader \
should feel.

## Output Format (EXACTLY this format):
PRIMARY_MEANING: [1-5 word English meaning capturing the root's core semantic]
DETAILED_MEANING: [1-2 paragraphs: how the Quran uses this root across its \
verses, notable morphological patterns, cognate connections, physical-world \
etymology if relevant. Objective linguistic analysis.]
SEMANTIC_FIELD: [comma-separated related concepts, 3-6 items]
EVIDENCE_SUMMARY: [Which verses were most informative and why, 2-3 sentences]
"""


def get_or_create_config(conn, config_name: str, model_name: str) -> int:
    """Get or create a config entry, return config_id."""
    row = conn.execute(
        "SELECT id FROM ai_translation_configs WHERE config_name = ?",
        (config_name,),
    ).fetchone()
    if row:
        return row["id"]

    conn.execute(
        "INSERT INTO ai_translation_configs "
        "(config_name, model_name, system_prompt, temperature, methodology_notes) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            config_name,
            model_name,
            SYSTEM_PROMPT,
            0.2,
            "Root-level meaning derivation from Quranic usage. "
            "Primary (1-5 words) + detailed (paragraph) meanings.",
        ),
    )
    conn.commit()
    return conn.execute(
        "SELECT id FROM ai_translation_configs WHERE config_name = ?",
        (config_name,),
    ).fetchone()["id"]


def _gather_lemmas(conn, root_bw: str) -> list[dict]:
    """Get all distinct lemmas for a root with POS, verb form, and frequency."""
    rows = conn.execute(
        "SELECT lemma_buckwalter, lemma_arabic, pos, verb_form, COUNT(*) as freq "
        "FROM morphology "
        "WHERE root_buckwalter = ? AND lemma_buckwalter IS NOT NULL "
        "GROUP BY lemma_buckwalter, pos, verb_form "
        "ORDER BY freq DESC",
        (root_bw,),
    ).fetchall()
    return [dict(r) for r in rows]


def _gather_glosses(conn, root_bw: str) -> list[dict]:
    """Get word glosses grouped by frequency for this root."""
    rows = conn.execute(
        "SELECT wg.translation_en, COUNT(*) as freq "
        "FROM morphology m "
        "JOIN word_glosses wg ON m.chapter = wg.chapter AND m.verse = wg.verse AND m.word_pos = wg.word_pos "
        "WHERE m.root_buckwalter = ? AND wg.translation_en IS NOT NULL AND wg.translation_en != '' "
        "GROUP BY wg.translation_en "
        "ORDER BY freq DESC "
        f"LIMIT {MAX_GLOSSES}",
        (root_bw,),
    ).fetchall()
    return [dict(r) for r in rows]


def _gather_morph_stats(conn, root_bw: str) -> dict:
    """Get morphological variety stats (POS distribution, verb forms)."""
    pos_rows = conn.execute(
        "SELECT pos, COUNT(*) as cnt FROM morphology "
        "WHERE root_buckwalter = ? AND pos IS NOT NULL "
        "GROUP BY pos ORDER BY cnt DESC",
        (root_bw,),
    ).fetchall()

    vf_rows = conn.execute(
        "SELECT verb_form, COUNT(*) as cnt FROM morphology "
        "WHERE root_buckwalter = ? AND verb_form IS NOT NULL AND verb_form != '' "
        "GROUP BY verb_form ORDER BY cnt DESC",
        (root_bw,),
    ).fetchall()

    return {
        "pos_dist": [(r["pos"], r["cnt"]) for r in pos_rows],
        "verb_forms": [(r["verb_form"], r["cnt"]) for r in vf_rows],
    }


def _select_representative_verses(conn, root_bw: str, lemmas: list[dict]) -> list[dict]:
    """Select diverse representative verses for this root.

    Strategy:
    1. One verse per distinct lemma (covers all word forms)
    2. One verse per verb form
    3. Fill remaining slots with diverse surahs
    4. Cap at MAX_SAMPLE_VERSES
    """
    verse_keys = sorted(_root_inv.get(root_bw, set()))
    if len(verse_keys) <= MAX_SAMPLE_VERSES:
        # Include all verses for small roots
        selected_keys = verse_keys
    else:
        selected = set()
        remaining = list(verse_keys)

        # 1. Cover each lemma
        lemma_bws = {l["lemma_buckwalter"] for l in lemmas}
        for lbw in lemma_bws:
            if len(selected) >= MAX_SAMPLE_VERSES:
                break
            for ch, v in remaining:
                row = conn.execute(
                    "SELECT 1 FROM morphology WHERE chapter = ? AND verse = ? "
                    "AND root_buckwalter = ? AND lemma_buckwalter = ? LIMIT 1",
                    (ch, v, root_bw, lbw),
                ).fetchone()
                if row and (ch, v) not in selected:
                    selected.add((ch, v))
                    break

        # 2. Cover each verb form
        vf_rows = conn.execute(
            "SELECT DISTINCT verb_form FROM morphology "
            "WHERE root_buckwalter = ? AND verb_form IS NOT NULL AND verb_form != ''",
            (root_bw,),
        ).fetchall()
        for vf_row in vf_rows:
            if len(selected) >= MAX_SAMPLE_VERSES:
                break
            vf = vf_row["verb_form"]
            for ch, v in remaining:
                if (ch, v) in selected:
                    continue
                row = conn.execute(
                    "SELECT 1 FROM morphology WHERE chapter = ? AND verse = ? "
                    "AND root_buckwalter = ? AND verb_form = ? LIMIT 1",
                    (ch, v, root_bw, vf),
                ).fetchone()
                if row:
                    selected.add((ch, v))
                    break

        # 3. Fill with evenly spaced verses for surah diversity
        if len(selected) < MAX_SAMPLE_VERSES:
            unselected = [k for k in remaining if k not in selected]
            step = max(1, len(unselected) // (MAX_SAMPLE_VERSES - len(selected)))
            for i in range(0, len(unselected), step):
                if len(selected) >= MAX_SAMPLE_VERSES:
                    break
                selected.add(unselected[i])

        selected_keys = sorted(selected)

    # Fetch verse data
    verses = []
    for ch, v in selected_keys:
        vrow = conn.execute(
            "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
            (ch, v),
        ).fetchone()
        trow = conn.execute(
            "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
            (ch, v),
        ).fetchone()
        if vrow:
            verses.append({
                "ref": f"{ch}:{v}",
                "arabic": vrow["text_uthmani"],
                "translation": trow["text_en"] if trow else "",
            })

    return verses


def build_prompt(conn, root_bw: str) -> str:
    """Build the user prompt for a root meaning generation."""
    root_arabic = _root_arabic_map.get(root_bw, root_bw)
    verse_count = len(_root_inv.get(root_bw, set()))

    # 1. Lemmas
    lemmas = _gather_lemmas(conn, root_bw)
    lemma_lines = []
    for l in lemmas:
        vf = f", Form {l['verb_form']}" if l.get("verb_form") else ""
        lemma_lines.append(
            f"- {l['lemma_arabic']} ({l['lemma_buckwalter']}): "
            f"{l['pos'] or 'unknown POS'}{vf}, {l['freq']}x"
        )

    # 2. Word glosses
    glosses = _gather_glosses(conn, root_bw)
    gloss_lines = [f"- \"{g['translation_en']}\" ({g['freq']}x)" for g in glosses]

    # 3. Morphological stats
    stats = _gather_morph_stats(conn, root_bw)
    pos_lines = [f"- {pos}: {cnt}x" for pos, cnt in stats["pos_dist"]]
    vf_lines = [f"- Form {vf}: {cnt}x" for vf, cnt in stats["verb_forms"]]

    # 4. Verse samples
    verses = _select_representative_verses(conn, root_bw, lemmas)
    verse_lines = []
    for v in verses:
        verse_lines.append(f"[{v['ref']}] {v['arabic']}")
        if v["translation"]:
            verse_lines.append(f"  Translation: {v['translation']}")
        verse_lines.append("")

    # 5. Cognate data
    cognate = _get_cognate(conn, root_bw)
    cognate_section = ""
    if cognate and cognate.get("derivatives"):
        cog_lines = [f"Core concept: {cognate['concept']}"]
        cog_lines.append(f"Transliteration: {cognate['transliteration']}")
        cog_lines.append("Cognates by language:")
        for d in cognate["derivatives"]:
            meaning = d.get("meaning") or d.get("concept", "")
            cog_lines.append(f"- {d['language']}: {d['displayed_text']} — {meaning}")
        cognate_section = "\n".join(cog_lines)

    # Assemble prompt
    sections = [
        f"## Root: {root_arabic} ({root_bw})",
        f"Total Quranic occurrences: {verse_count} verses",
        "",
        "## Lemmas Derived from This Root",
        "\n".join(lemma_lines) if lemma_lines else "(no lemma data)",
        "",
        "## Word Glosses (conventional per-word translations, by frequency)",
        "\n".join(gloss_lines) if gloss_lines else "(no gloss data)",
        "",
        "## Morphological Variety",
        "Part-of-speech distribution:",
        "\n".join(pos_lines) if pos_lines else "(none)",
    ]

    if vf_lines:
        sections.append("Verb forms used:")
        sections.append("\n".join(vf_lines))

    sections.extend([
        "",
        f"## Verse Samples ({len(verses)} representative verses)",
        "\n".join(verse_lines),
    ])

    if cognate_section:
        sections.extend([
            "## Semitic Cognate Evidence",
            cognate_section,
        ])

    sections.append("")
    sections.append("Determine the root meaning following your methodology. /no_think")

    return "\n".join(sections)


def parse_response(raw: str) -> dict:
    """Parse PRIMARY_MEANING / DETAILED_MEANING / SEMANTIC_FIELD / EVIDENCE_SUMMARY."""
    result = {
        "primary_meaning": "",
        "detailed_meaning": "",
        "semantic_field": "",
        "evidence_summary": "",
    }

    # PRIMARY_MEANING
    m = re.search(r"PRIMARY_MEANING:\s*(.+?)(?:\n|$)", raw, re.IGNORECASE)
    if m:
        result["primary_meaning"] = m.group(1).strip().strip('"').strip("'")

    # DETAILED_MEANING — may be multi-line/multi-paragraph
    m = re.search(
        r"DETAILED_MEANING:\s*(.+?)(?=\nSEMANTIC_FIELD:|\nEVIDENCE_SUMMARY:|\Z)",
        raw, re.IGNORECASE | re.DOTALL,
    )
    if m:
        result["detailed_meaning"] = m.group(1).strip()

    # SEMANTIC_FIELD
    m = re.search(r"SEMANTIC_FIELD:\s*(.+?)(?:\n|$)", raw, re.IGNORECASE)
    if m:
        result["semantic_field"] = m.group(1).strip()

    # EVIDENCE_SUMMARY — may be multi-line
    m = re.search(
        r"EVIDENCE_SUMMARY:\s*(.+?)(?=\n[A-Z_]+:|\Z)",
        raw, re.IGNORECASE | re.DOTALL,
    )
    if m:
        result["evidence_summary"] = m.group(1).strip()

    return result


def process_root(
    conn, root_bw: str, config_id: int, model: str,
    temperature: float, dry_run: bool, force: bool,
) -> bool:
    """Process a single root. Returns True if processed, False if skipped."""
    root_arabic = _root_arabic_map.get(root_bw, root_bw)

    # Check if already done
    if not force:
        existing = conn.execute(
            "SELECT id FROM ai_root_meanings WHERE root_buckwalter = ? AND config_id = ?",
            (root_bw, config_id),
        ).fetchone()
        if existing:
            return False

    # Build prompt
    prompt = build_prompt(conn, root_bw)

    if dry_run:
        print(f"\n{'='*60}")
        print(f"ROOT: {root_arabic} ({root_bw})")
        print(f"{'='*60}")
        print(f"Prompt length: {len(prompt)} chars")
        print(prompt[:2000])
        if len(prompt) > 2000:
            print(f"... [{len(prompt) - 2000} more chars]")
        return True

    # Call model
    print(f"  {root_arabic} ({root_bw})", end="", flush=True)
    try:
        raw_response, elapsed_ms = call_model(model, SYSTEM_PROMPT, prompt, temperature)
    except Exception as e:
        print(f" — ERROR: {e}")
        return False

    print(f" ({elapsed_ms / 1000:.1f}s)")

    # Parse response
    parsed = parse_response(raw_response)

    if not parsed["primary_meaning"]:
        print(f"    WARNING: No PRIMARY_MEANING parsed for {root_bw}")
        # Use first line of response as fallback
        first_line = raw_response.strip().split("\n")[0][:100]
        parsed["primary_meaning"] = first_line

    # Store (retry with fresh connection on DB lock from concurrent writers)
    values = (
        root_bw, config_id,
        parsed["primary_meaning"],
        parsed["detailed_meaning"],
        parsed["semantic_field"],
        parsed["evidence_summary"],
        prompt, raw_response, elapsed_ms,
    )
    for attempt in range(20):
        try:
            write_conn = sqlite3.connect(DB_PATH, timeout=120)
            try:
                if force:
                    write_conn.execute(
                        "DELETE FROM ai_root_meanings WHERE root_buckwalter = ? AND config_id = ?",
                        (root_bw, config_id),
                    )
                write_conn.execute(
                    "INSERT INTO ai_root_meanings "
                    "(root_buckwalter, config_id, primary_meaning, detailed_meaning, "
                    " semantic_field, evidence_summary, full_prompt, raw_response, "
                    " model_response_time_ms) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    values,
                )
                write_conn.commit()
            finally:
                write_conn.close()
            break
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < 19:
                time.sleep(2 + attempt * 2)
                print(f"    (DB locked, retry {attempt + 1})", flush=True)
            else:
                raise
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate AI root meanings from Quranic usage")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--roots", help="Comma-separated Buckwalter roots (e.g. Elm,Hmd,wsm)")
    group.add_argument("--all", action="store_true", help="Process all roots")
    parser.add_argument("--config", default=DEFAULT_CONFIG, help=f"Config name (default: {DEFAULT_CONFIG})")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--temperature", type=float, default=0.2, help="Temperature (default: 0.2)")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts without calling API")
    parser.add_argument("--force", action="store_true", help="Re-generate even if already exists")
    args = parser.parse_args()

    # Build root list
    if args.all:
        root_list = sorted(_root_arabic_map.keys())
    else:
        root_list = [r.strip() for r in args.roots.split(",") if r.strip()]

    # Validate roots
    invalid = [r for r in root_list if r not in _root_arabic_map]
    if invalid:
        print(f"WARNING: Unknown roots (not in morphology): {', '.join(invalid[:10])}")
        root_list = [r for r in root_list if r in _root_arabic_map]

    if not root_list:
        print("No valid roots to process.")
        sys.exit(1)

    print(f"Roots to process: {len(root_list)}")
    print(f"Model: {args.model}")
    print(f"Config: {args.config}")
    print(f"Dry run: {args.dry_run}")
    print()

    conn = get_db()
    try:
        config_id = get_or_create_config(conn, args.config, args.model)
        processed = 0
        skipped = 0

        for i, root_bw in enumerate(root_list, 1):
            prefix = f"[{i}/{len(root_list)}]"
            if not args.dry_run:
                print(prefix, end="", flush=True)

            result = process_root(
                conn, root_bw, config_id, args.model,
                args.temperature, args.dry_run, args.force,
            )

            if result:
                processed += 1
            else:
                skipped += 1
                if not args.dry_run:
                    root_ar = _root_arabic_map.get(root_bw, "")
                    print(f"  {root_ar} ({root_bw}) — already done, skipping")

        print(f"\nDone! Processed: {processed}, Skipped: {skipped}, Total: {len(root_list)}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
