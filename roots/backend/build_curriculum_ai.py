"""Build the learning curriculum for the Quranic Concept Web.

Selects the top N roots by frequency, groups them into thematic units,
selects anchor/context verses using IDF weights, and generates root stories
via Ollama.

Usage:
    python build_curriculum_ai.py                          # Build all 50 roots
    python build_curriculum_ai.py --roots 10               # Build top 10 only
    python build_curriculum_ai.py --dry-run                # Preview without saving
    python build_curriculum_ai.py --force                  # Regenerate existing
    python build_curriculum_ai.py --model minimax-m2.5:cloud
    python build_curriculum_ai.py --specific "Slw,sjd,sbH" # Process only these roots
"""

import argparse
import json
import math
import os
import sqlite3
import sys
import time
from collections import defaultdict

import requests

from app import (
    DB_PATH,
    _build_similarity_engine,
    _get_cognate,
    _lemma_inv,
    _root_inv,
    _root_idf,
    _root_arabic_map,
    _verse_lemmas,
    _verse_roots,
    _strip_bismillah,
    _fetch_word_glosses,
    get_db,
)
from translate_ai import call_model

# ── Thematic unit definitions ──
# Each unit is a theological theme with seed roots (buckwalter).
# Roots not in these seeds will be assigned to the best-matching unit.

UNIT_DEFINITIONS = [
    {
        "number": 1,
        "theme": "The Divine Nature",
        "description": "Names, attributes, and nature of God",
        "seed_roots": ["Alh", "rbb", "rHm", "mlk", "qds", "Ebd"],
    },
    {
        "number": 2,
        "theme": "Faith & Belief",
        "description": "Believing, trusting, submitting",
        "seed_roots": ["Amn", "slm", "kfr", "$rk", "nfq"],
    },
    {
        "number": 3,
        "theme": "Guidance & Knowledge",
        "description": "Being guided, knowing, understanding",
        "seed_roots": ["hdy", "Elm", "Eql", "Drb", "fqh", "wHy"],
    },
    {
        "number": 4,
        "theme": "Revelation & Scripture",
        "description": "Books, signs, recitation, revelation",
        "seed_roots": ["ktb", "Ayy", "qrA", "nzl", "klm"],
    },
    {
        "number": 5,
        "theme": "Righteousness & God-consciousness",
        "description": "Piety, good deeds, consciousness of God",
        "seed_roots": ["wqy", "Slw", "SlH", "Hsn", "brr", "zkw"],
    },
    {
        "number": 6,
        "theme": "Creation & Life",
        "description": "Creating, living, dying, returning",
        "seed_roots": ["xlq", "Hyy", "mwt", "bEv", "jEl", "kwn"],
    },
    {
        "number": 7,
        "theme": "Justice & Judgment",
        "description": "Judging, punishing, rewarding, accounting",
        "seed_roots": ["Hkm", "Edb", "jzy", "Hsb", "Zlm", "dyn"],
    },
    {
        "number": 8,
        "theme": "Human & Community",
        "description": "People, nations, prophets, messengers",
        "seed_roots": ["qwm", "nfs", "rsl", "nbA", "Ahl", "nsr"],
    },
    # ── Units 11-20: Second set of 50 roots ──
    {
        "number": 11,
        "theme": "Life, Death & Eternity",
        "description": "Living, dying, eternity, this world vs. the next",
        "seed_roots": ["Hyy", "mwt", "xld", "dnw", "nhr"],
    },
    {
        "number": 12,
        "theme": "Prayer & Devotion",
        "description": "Salat, prostration, glorification, repentance",
        "seed_roots": ["Slw", "sjd", "sbH", "$kr", "twb"],
    },
    {
        "number": 13,
        "theme": "Virtue & Character",
        "description": "Righteousness, truthfulness, patience, obedience, love",
        "seed_roots": ["SlH", "Sdq", "Sbr", "TwE", "Hbb"],
    },
    {
        "number": 14,
        "theme": "Sin & Deviation",
        "description": "Going astray, polytheism, enmity, forbidden acts",
        "seed_roots": ["Dll", "$rk", "Edw", "$Tn", "Hrm"],
    },
    {
        "number": 15,
        "theme": "Perception & Heart",
        "description": "Hearing, seeing, contemplating, the heart, witnessing",
        "seed_roots": ["smE", "bSr", "nZr", "qlb", "$hd"],
    },
    {
        "number": 16,
        "theme": "Community & Family",
        "description": "Nation, family, humankind, children, brotherhood",
        "seed_roots": ["Amm", "Ahl", "Ans", "wld", "Axw"],
    },
    {
        "number": 17,
        "theme": "Divine Power & Provision",
        "description": "God's power, greatness, might, provision, grace",
        "seed_roots": ["qdr", "EZm", "Ezz", "rzq", "fDl"],
    },
    {
        "number": 18,
        "theme": "Prophecy & Recompense",
        "description": "Revelation, prophecy, warning, glad tidings, promises",
        "seed_roots": ["wHy", "nbA", "n*r", "b$r", "wEd"],
    },
    {
        "number": 19,
        "theme": "Actions & Movement",
        "description": "Emerging, entering, following, returning, fighting",
        "seed_roots": ["xrj", "dxl", "tbE", "rjE", "qtl"],
    },
    {
        "number": 20,
        "theme": "Religion & Judgment",
        "description": "Islam, religion, recompense, blessings, fear of God",
        "seed_roots": ["slm", "dyn", "jzy", "nEm", "xwf"],
    },
]

# Build a lookup from seed root -> unit number
_SEED_TO_UNIT = {}
for udef in UNIT_DEFINITIONS:
    for sr in udef["seed_roots"]:
        _SEED_TO_UNIT[sr] = udef["number"]


def get_root_frequencies(conn):
    """Get root -> occurrence count from morphology table."""
    rows = conn.execute(
        "SELECT root_buckwalter, COUNT(*) as cnt "
        "FROM morphology "
        "WHERE root_buckwalter IS NOT NULL AND root_buckwalter != '' "
        "GROUP BY root_buckwalter "
        "ORDER BY cnt DESC"
    ).fetchall()
    return {r["root_buckwalter"]: r["cnt"] for r in rows}


def get_root_lemmas(conn, root_bw):
    """Get all lemmas for a root with their metadata."""
    rows = conn.execute(
        "SELECT lemma_buckwalter, lemma_arabic, pos, "
        "       COUNT(*) as freq, "
        "       GROUP_CONCAT(DISTINCT features_raw) as all_features "
        "FROM morphology "
        "WHERE root_buckwalter = ? AND lemma_buckwalter IS NOT NULL AND lemma_buckwalter != '' "
        "GROUP BY lemma_buckwalter, pos "
        "ORDER BY freq DESC",
        (root_bw,),
    ).fetchall()

    lemmas = []
    for r in rows:
        # Extract verb form from features if present
        verb_form = None
        feats = r["all_features"] or ""
        for feat_str in feats.split(","):
            for feat in feat_str.split("|"):
                if feat.startswith("(") and feat.endswith(")"):
                    # Roman numeral verb form like (II), (IV), etc.
                    vf = feat.strip("()")
                    if vf in ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"):
                        verb_form = vf
                        break

        lemmas.append({
            "lemma_buckwalter": r["lemma_buckwalter"],
            "lemma_arabic": r["lemma_arabic"],
            "pos": r["pos"],
            "verb_form": verb_form,
            "frequency": r["freq"],
        })
    return lemmas


def get_existing_meanings(conn, root_bw):
    """Get any existing AI word meanings for words with this root."""
    rows = conn.execute(
        "SELECT DISTINCT m.lemma_buckwalter, wm.meaning_short, wm.semantic_field "
        "FROM ai_word_meanings wm "
        "JOIN morphology m ON wm.chapter = m.chapter AND wm.verse = m.verse AND wm.word_pos = m.word_pos "
        "WHERE m.root_buckwalter = ? AND wm.meaning_short IS NOT NULL "
        "GROUP BY m.lemma_buckwalter",
        (root_bw,),
    ).fetchall()
    return {r["lemma_buckwalter"]: {"meaning": r["meaning_short"], "field": r["semantic_field"]} for r in rows}


def select_anchor_verse(conn, root_bw, lemmas):
    """Select the best teaching verse for this root.

    Criteria: contains the most common lemma, is short, has high IDF distinctiveness.
    """
    if not lemmas:
        return None

    # Most frequent lemma
    top_lemma = lemmas[0]["lemma_buckwalter"]

    # All verses containing this root
    verses = list(_root_inv.get(root_bw, set()))
    if not verses:
        return None

    # Score each verse
    scored = []
    for ch, v in verses:
        # Check if top lemma is in this verse
        verse_lems = _verse_lemmas.get((ch, v), set())
        has_top = top_lemma in verse_lems

        # Get verse length
        v_row = conn.execute(
            "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
            (ch, v),
        ).fetchone()
        if not v_row:
            continue
        text = v_row["text_uthmani"]
        word_count = len(text.split())

        # Prefer verses that are 5-20 words (digestible)
        length_score = 1.0
        if word_count < 5:
            length_score = 0.5
        elif word_count > 20:
            length_score = max(0.3, 1.0 - (word_count - 20) * 0.03)

        # IDF distinctiveness of this root in the verse
        verse_roots = _verse_roots.get((ch, v), set())
        root_prominence = 1.0 / max(len(verse_roots), 1)

        # Bonus for having the top lemma
        lemma_bonus = 1.5 if has_top else 0.8

        # Bonus for famous verses (Al-Fatihah, Ayat al-Kursi, etc.)
        fame_bonus = 1.0
        if (ch, v) in [(1, 1), (1, 2), (1, 5), (2, 255), (2, 286), (112, 1)]:
            fame_bonus = 1.3

        score = length_score * root_prominence * lemma_bonus * fame_bonus
        scored.append(((ch, v), score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0] if scored else None


def select_context_verses(conn, root_bw, anchor, lemmas, max_verses=4):
    """Select context verses that show DIFFERENT derivatives of the root."""
    if not lemmas:
        return []

    # Collect lemma -> verses mapping
    lemma_verses = {}
    for lem in lemmas:
        lbw = lem["lemma_buckwalter"]
        v_set = _lemma_inv.get(lbw, set())
        # Also ensure these verses contain the target root
        root_verses = _root_inv.get(root_bw, set())
        lemma_verses[lbw] = v_set & root_verses

    # Try to pick one verse per distinct lemma (different from anchor)
    used_lemmas = set()
    result = []
    anchor_set = {anchor} if anchor else set()

    # First pass: pick the top lemma's verses (skip anchor's lemma if possible)
    top_lemma = lemmas[0]["lemma_buckwalter"]

    for lem in lemmas:
        if len(result) >= max_verses:
            break
        lbw = lem["lemma_buckwalter"]
        if lbw in used_lemmas:
            continue

        # Remove already-picked verses
        picked_keys = {(r[0], r[1]) for r in result}
        candidates = lemma_verses.get(lbw, set()) - anchor_set - picked_keys

        if not candidates:
            continue

        # Pick the shortest verse among candidates
        best = None
        best_len = 9999
        for ch, v in candidates:
            v_row = conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
                (ch, v),
            ).fetchone()
            if v_row:
                wc = len(v_row["text_uthmani"].split())
                if 4 <= wc <= 25 and wc < best_len:
                    best = (ch, v)
                    best_len = wc

        if best:
            role = "contrast" if lbw != top_lemma else "reinforcement"
            result.append((best[0], best[1], lbw, role))
            used_lemmas.add(lbw)

    return result


def assign_unit(root_bw, root_freq, all_roots_in_units):
    """Assign a root to a thematic unit. Seed roots get their defined unit.
    Others get assigned to the unit with the most co-occurring seed roots."""
    if root_bw in _SEED_TO_UNIT:
        return _SEED_TO_UNIT[root_bw]

    # Find which unit's seed roots most often co-occur with this root
    root_verses = _root_inv.get(root_bw, set())
    if not root_verses:
        return 1  # Default

    unit_scores = defaultdict(int)
    for ch, v in root_verses:
        v_roots = _verse_roots.get((ch, v), set())
        for vr in v_roots:
            if vr in _SEED_TO_UNIT:
                unit_scores[_SEED_TO_UNIT[vr]] += 1

    if unit_scores:
        return max(unit_scores, key=unit_scores.get)
    return 1


def find_related_roots(root_bw, all_curriculum_roots):
    """Find roots that frequently co-occur in the same verses."""
    root_verses = _root_inv.get(root_bw, set())
    if not root_verses:
        return []

    co_occurrence = defaultdict(int)
    for ch, v in root_verses:
        v_roots = _verse_roots.get((ch, v), set())
        for vr in v_roots:
            if vr != root_bw and vr in all_curriculum_roots:
                co_occurrence[vr] += 1

    # Sort by co-occurrence count, take top 5
    sorted_roots = sorted(co_occurrence.items(), key=lambda x: x[1], reverse=True)
    return [r for r, _ in sorted_roots[:5]]


def generate_root_story(root_bw, root_arabic, lemmas, meanings, cognate, model, dry_run=False):
    """Use LLM to generate a root story connecting all derivatives."""
    deriv_lines = []
    for lem in lemmas[:15]:
        meaning = meanings.get(lem["lemma_buckwalter"], {}).get("meaning", lem.get("meaning_gloss", ""))
        vf = f" (Form {lem['verb_form']})" if lem.get("verb_form") else ""
        deriv_lines.append(
            f"  - {lem['lemma_arabic']} ({lem['lemma_buckwalter']}){vf}: "
            f"{meaning or '?'} — {lem['frequency']}x in Quran"
        )

    cognate_info = ""
    if cognate and cognate.get("derivatives"):
        cog_lines = []
        for d in cognate["derivatives"][:5]:
            cog_lines.append(f"  - {d['language']}: {d.get('displayed_text', d.get('word', ''))} = {d.get('meaning', d.get('concept', ''))}")
        if cog_lines:
            cognate_info = f"\nSemitic cognates:\n" + "\n".join(cog_lines)

    system_prompt = (
        "You are a Quranic Arabic teacher creating learning materials. "
        "Write engaging, accurate explanations that connect linguistic analysis "
        "with theological understanding. Your audience is an English-speaking "
        "adult learner who wants to understand the Quran more deeply."
    )

    user_prompt = f"""Write a "root story" for the Arabic root {root_arabic} ({root_bw}).

This root produces the following words used in the Quran:
{chr(10).join(deriv_lines)}
{cognate_info}

Write a 200-350 word narrative that:
1. Explains the core/original meaning of these three root letters
2. Shows how each derivative connects to that core meaning
3. Highlights any surprising or beautiful semantic connections
4. Mentions the theological significance in the Quran
5. If cognates exist, briefly note how the meaning compares across Semitic languages

Also provide:
- A one-line "meaning_gloss" (3-8 words) for each derivative listed above
- A "semantic_shift" explanation (one sentence) for each derivative showing how it relates to the core root meaning
- A "theological_importance" score from 0.0 to 1.0 (1.0 = central Quranic concept like mercy, guidance; 0.0 = purely functional)
- "teaching_notes": 1-2 sentences of advice for a teacher presenting this root

Respond in this exact JSON format:
{{
  "root_story": "...",
  "theological_importance": 0.85,
  "teaching_notes": "...",
  "derivatives": [
    {{
      "lemma_buckwalter": "...",
      "meaning_gloss": "...",
      "semantic_shift": "..."
    }}
  ]
}}

Return ONLY valid JSON, no markdown fencing, no extra text."""

    if dry_run:
        print(f"\n{'='*60}")
        print(f"ROOT: {root_arabic} ({root_bw})")
        print(f"PROMPT (first 500 chars):\n{user_prompt[:500]}...")
        return None

    raw, elapsed_ms = call_model(model, system_prompt, user_prompt, temperature=0.4)

    # Parse JSON response
    # Strip markdown fencing if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    if cleaned.startswith("json"):
        cleaned = cleaned[4:].strip()

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to extract JSON from the response
        import re

        json_match = re.search(r"\{[\s\S]*\}", cleaned)
        if json_match:
            try:
                result = json.loads(json_match.group())
            except json.JSONDecodeError:
                print(f"  WARNING: Could not parse JSON for {root_bw}. Raw response:\n{raw[:500]}")
                result = {
                    "root_story": raw[:500],
                    "theological_importance": 0.5,
                    "teaching_notes": "",
                    "derivatives": [],
                }
        else:
            print(f"  WARNING: No JSON found for {root_bw}")
            result = {
                "root_story": raw[:500],
                "theological_importance": 0.5,
                "teaching_notes": "",
                "derivatives": [],
            }

    result["_elapsed_ms"] = elapsed_ms
    return result


def build_curriculum(conn, num_roots=50, model="minimax-m2.5:cloud", dry_run=False, force=False, specific_roots=None):
    """Main curriculum building function.

    If specific_roots is provided (list of buckwalter strings), only those
    roots are processed regardless of num_roots.
    """
    print(f"\n{'='*60}")
    print(f"Building Quranic Concept Web Curriculum")
    if specific_roots:
        print(f"Specific roots: {len(specific_roots)} | Model: {model} | Dry run: {dry_run}")
    else:
        print(f"Roots: {num_roots} | Model: {model} | Dry run: {dry_run}")
    print(f"{'='*60}\n")

    # Step 1: Get root frequencies
    freq = get_root_frequencies(conn)
    print(f"Found {len(freq)} distinct roots in morphology table")

    # Step 2: Select roots
    if specific_roots:
        # Use only the specified roots (in the order given)
        sorted_roots = [(rbw, freq.get(rbw, 0)) for rbw in specific_roots if rbw in freq]
        missing = [rbw for rbw in specific_roots if rbw not in freq]
        if missing:
            print(f"WARNING: These roots not found in morphology: {', '.join(missing)}")
    else:
        sorted_roots = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:num_roots]
    selected_roots_set = {r for r, _ in sorted_roots}

    print(f"Selected top {len(sorted_roots)} roots:")
    for i, (rbw, cnt) in enumerate(sorted_roots[:10]):
        ar = _root_arabic_map.get(rbw, "?")
        print(f"  {i+1}. {ar} ({rbw}): {cnt} occurrences")
    if len(sorted_roots) > 10:
        print(f"  ... and {len(sorted_roots) - 10} more")

    # Step 3: Assign units
    unit_assignments = {}
    for rbw, cnt in sorted_roots:
        unit_assignments[rbw] = assign_unit(rbw, cnt, selected_roots_set)

    # Print unit distribution
    unit_counts = defaultdict(int)
    for rbw, un in unit_assignments.items():
        unit_counts[un] += 1
    print(f"\nUnit distribution:")
    for udef in UNIT_DEFINITIONS:
        count = unit_counts.get(udef["number"], 0)
        print(f"  Unit {udef['number']}: {udef['theme']} — {count} roots")

    # Step 4: Process each root
    total = len(sorted_roots)
    for idx, (root_bw, root_freq) in enumerate(sorted_roots):
        root_arabic = _root_arabic_map.get(root_bw, "?")
        unit_num = unit_assignments[root_bw]
        unit_theme = next(
            (u["theme"] for u in UNIT_DEFINITIONS if u["number"] == unit_num),
            "Other",
        )

        print(f"\n[{idx+1}/{total}] {root_arabic} ({root_bw}) — {root_freq}x — Unit {unit_num}: {unit_theme}")

        # Check if already exists
        if not force:
            existing = conn.execute(
                "SELECT id FROM learning_curriculum WHERE root_buckwalter = ?",
                (root_bw,),
            ).fetchone()
            if existing:
                print(f"  Already in curriculum (use --force to regenerate)")
                continue

        # Get lemmas
        lemmas = get_root_lemmas(conn, root_bw)
        print(f"  {len(lemmas)} lemmas found")

        # Get existing AI meanings
        meanings = get_existing_meanings(conn, root_bw)

        # Select anchor verse
        anchor = select_anchor_verse(conn, root_bw, lemmas)
        if not anchor:
            print(f"  WARNING: No suitable anchor verse found, skipping")
            continue
        print(f"  Anchor verse: {anchor[0]}:{anchor[1]}")

        # Select context verses
        ctx_verses = select_context_verses(conn, root_bw, anchor, lemmas)
        print(f"  Context verses: {len(ctx_verses)}")

        # Get cognate data
        cognate = _get_cognate(conn, root_bw)

        # Find related roots
        related = find_related_roots(root_bw, selected_roots_set)

        # Generate root story via LLM
        freq_rank = idx + 1
        result = generate_root_story(
            root_bw, root_arabic, lemmas, meanings, cognate, model, dry_run
        )

        if dry_run:
            print(f"  Would save: unit={unit_num}, anchor={anchor}, ctx={len(ctx_verses)}, related={related[:3]}")
            continue

        if not result:
            print(f"  WARNING: LLM returned no result, skipping")
            continue

        print(f"  LLM response in {result.get('_elapsed_ms', 0)}ms")

        # Save to DB
        theological_imp = float(result.get("theological_importance", 0.5))
        root_story = result.get("root_story", "")
        teaching_notes = result.get("teaching_notes", "")
        llm_derivs = {d["lemma_buckwalter"]: d for d in result.get("derivatives", []) if "lemma_buckwalter" in d}

        # Delete existing if force
        if force:
            conn.execute("DELETE FROM learning_curriculum WHERE root_buckwalter = ?", (root_bw,))
            conn.execute("DELETE FROM learning_derivatives WHERE root_buckwalter = ?", (root_bw,))
            conn.execute("DELETE FROM learning_context_verses WHERE root_buckwalter = ?", (root_bw,))

        # Insert curriculum entry
        conn.execute(
            "INSERT INTO learning_curriculum "
            "(root_buckwalter, root_arabic, unit_number, unit_theme, priority_score, "
            " frequency_rank, theological_importance, derivative_richness, "
            " anchor_verse_chapter, anchor_verse_verse, root_story, teaching_notes, "
            " related_roots) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                root_bw, root_arabic, unit_num, unit_theme,
                root_freq * (0.5 + 0.5 * theological_imp),  # priority = freq weighted by importance
                freq_rank, theological_imp, len(lemmas),
                anchor[0], anchor[1],
                root_story, teaching_notes,
                json.dumps(related),
            ),
        )

        # Insert derivatives
        for di, lem in enumerate(lemmas):
            lbw = lem["lemma_buckwalter"]
            llm_d = llm_derivs.get(lbw, {})
            gloss = llm_d.get("meaning_gloss") or meanings.get(lbw, {}).get("meaning", "")
            shift = llm_d.get("semantic_shift", "")

            conn.execute(
                "INSERT INTO learning_derivatives "
                "(root_buckwalter, lemma_buckwalter, lemma_arabic, pos, verb_form, "
                " frequency, meaning_gloss, semantic_shift, display_order) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    root_bw, lbw, lem["lemma_arabic"], lem["pos"],
                    lem.get("verb_form"), lem["frequency"],
                    gloss or "(no gloss)", shift, di,
                ),
            )

        # Insert anchor verse as context verse
        conn.execute(
            "INSERT INTO learning_context_verses "
            "(root_buckwalter, chapter, verse, target_lemma_buckwalter, verse_role, "
            " teaching_note, display_order) "
            "VALUES (?, ?, ?, ?, 'anchor', ?, 0)",
            (root_bw, anchor[0], anchor[1], lemmas[0]["lemma_buckwalter"] if lemmas else None, ""),
        )

        # Insert context verses
        for ci, (ch, v, lbw, role) in enumerate(ctx_verses):
            conn.execute(
                "INSERT INTO learning_context_verses "
                "(root_buckwalter, chapter, verse, target_lemma_buckwalter, verse_role, "
                " teaching_note, display_order) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (root_bw, ch, v, lbw, role, "", ci + 1),
            )

        conn.commit()
        print(f"  Saved: story={len(root_story)} chars, {len(lemmas)} derivs, {len(ctx_verses)+1} verses")

    print(f"\n{'='*60}")
    print("Curriculum build complete!")
    if not dry_run:
        # Print summary
        count = conn.execute("SELECT COUNT(*) as c FROM learning_curriculum").fetchone()["c"]
        print(f"Total roots in curriculum: {count}")


def main():
    parser = argparse.ArgumentParser(description="Build Quranic Concept Web curriculum")
    parser.add_argument("--roots", type=int, default=50, help="Number of top roots to include (default: 50)")
    parser.add_argument("--specific", type=str, help="Comma-separated buckwalter roots to process (overrides --roots)")
    parser.add_argument("--model", default="minimax-m2.5:cloud", help="LLM model for root stories")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")
    parser.add_argument("--force", action="store_true", help="Regenerate existing entries")
    args = parser.parse_args()

    specific = None
    if args.specific:
        specific = [r.strip() for r in args.specific.split(",") if r.strip()]

    # Build the similarity engine (needed for IDF weights and inverted indexes)
    print("Building similarity engine...")
    _build_similarity_engine()

    conn = get_db()
    try:
        build_curriculum(conn, num_roots=args.roots, model=args.model,
                         dry_run=args.dry_run, force=args.force,
                         specific_roots=specific)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
