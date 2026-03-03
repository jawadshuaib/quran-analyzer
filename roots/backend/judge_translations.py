"""LLM judge for choosing between conventional and AI word translations.

Compares the hard-coded conventional gloss (from Quran.com) with the
AI-derived meaning_short (from ai_word_meanings) and picks the better
single-word gloss for tooltip display.

Three-tier Zipf optimization:
  Tier 0: Identical translations → auto-skip
  Tier 1: Function words (particles, prepositions, pronouns) → auto-pick conventional
  Tier 2: Zipf-reused meanings (same AI text for all lemma occurrences) →
           judge one representative, replicate to all occurrences
  Tier 3: Context-specific meanings → judge per unique (conv, AI) text pair,
           replicate to all words sharing that pair

Resumable: Ctrl+C any time, re-run to continue where you left off.

Usage:
    python judge_translations.py --all                    # full Quran (Zipf-optimized)
    python judge_translations.py --all --dry-run          # preview stats only
    python judge_translations.py --verses "96:1-5"        # specific verses (per-word)
    python judge_translations.py --verses "96:1" --word-pos 1
    python judge_translations.py --all --force            # re-judge everything
"""

import argparse
import re
import sys
import time

from app import (
    DB_PATH,
    _fetch_word_glosses,
    _strip_bismillah,
    get_db,
)
from translate_ai import call_model
from word_meanings_ai import parse_verse_spec

DEFAULT_MODEL = "qwen3:14b"
DEFAULT_TEMPERATURE = 0.2

# Function word POS tags — auto-pick conventional, no LLM call needed
FUNCTION_POS = {
    "Preposition", "Conjunction", "Subordinating Conjunction",
    "Negative Particle", "Accusative Particle", "Preventive Particle",
    "Prohibition Particle", "Certainty Particle", "Conditional",
    "Amendment Particle", "Answer Particle", "Aversion Particle",
    "Exceptive Particle", "Exhortation Particle", "Explanation Particle",
    "Future Particle", "Inceptive Particle", "Inceptive lam",
    "Interrogative Particle", "Restriction Particle", "Retraction Particle",
    "Surprise Particle", "SUP",
    "Pronoun", "Demonstrative", "Relative Pronoun",
    "Location Adverb", "Time Adverb",
}

SYSTEM_PROMPT = """\
You are a word-translation judge for a Quranic study tool. You will be shown \
two candidate translations for a single Arabic word within a specific verse, \
plus optional departure notes from the AI's full-verse translation analysis \
(these notes discuss the verse as a whole, not this specific word).

Your job: pick the BEST concise (1-3 word) English gloss suitable for a \
word-level tooltip.

## Rules

1. Prefer concise 1-3 word translations. A tooltip gloss must stand alone \
as a word-level label — not leak meaning from neighboring words.
2. Bias toward Translation A (conventional) unless there is strong evidence \
from departure notes that the AI translation (B) captures the word's meaning \
more accurately in context.
3. Penalize Translation B if it appears to anticipate or incorporate meaning \
from surrounding words rather than translating the target word itself.
4. You MAY propose a third alternative (choice C) if neither A nor B is ideal, \
but only if you can justify it briefly.

## Output Format

Respond in EXACTLY this format (no extra text before or after):

CHOICE: A | B | C
TRANSLATION: <chosen or proposed text>
REASONING: <1-2 sentences> /no_think"""


def build_judge_prompt(conn, surah: int, ayah: int, word_pos: int) -> str | None:
    """Build the prompt for judging a single word. Returns None if word should be skipped."""

    # Get AI meaning
    wm_row = conn.execute(
        "SELECT meaning_short, meaning_detailed, departure_notes "
        "FROM ai_word_meanings "
        "WHERE chapter = ? AND verse = ? AND word_pos = ? "
        "ORDER BY created_at DESC LIMIT 1",
        (surah, ayah, word_pos),
    ).fetchone()

    if not wm_row or not wm_row["meaning_short"]:
        return None

    ai_meaning = wm_row["meaning_short"]
    ai_detailed = wm_row["meaning_detailed"] or ""
    word_departure = wm_row["departure_notes"] or ""

    # Get conventional gloss
    glosses = _fetch_word_glosses(conn, surah, ayah)
    conventional = glosses.get(word_pos, "")

    if not conventional and not ai_meaning:
        return None

    # Skip if both are identical (case-insensitive)
    if conventional.strip().lower() == ai_meaning.strip().lower():
        return None

    # Get morphology for context
    morph_row = conn.execute(
        "SELECT form_arabic, root_arabic, root_buckwalter, "
        "       lemma_arabic, lemma_buckwalter "
        "FROM morphology "
        "WHERE chapter = ? AND verse = ? AND word_pos = ? "
        "ORDER BY segment LIMIT 1",
        (surah, ayah, word_pos),
    ).fetchone()

    arabic_form = morph_row["form_arabic"] if morph_row else ""
    root_ar = morph_row["root_arabic"] if morph_row else ""
    lemma_ar = morph_row["lemma_arabic"] if morph_row else ""

    # Get full verse text + translation
    verse_row = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
        (surah, ayah),
    ).fetchone()
    trans_row = conn.execute(
        "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
        (surah, ayah),
    ).fetchone()

    verse_arabic = _strip_bismillah(verse_row["text_uthmani"], surah, ayah) if verse_row else ""
    verse_trans = trans_row["text_en"] if trans_row else ""

    # Get verse-level departure notes from ai_translations
    verse_departure = ""
    ai_trans_row = conn.execute(
        "SELECT departure_notes FROM ai_translations "
        "WHERE chapter = ? AND verse = ? "
        "ORDER BY created_at DESC LIMIT 1",
        (surah, ayah),
    ).fetchone()
    if ai_trans_row and ai_trans_row["departure_notes"]:
        verse_departure = ai_trans_row["departure_notes"]

    # Build departure section
    departure_section = ""
    if word_departure or verse_departure:
        parts = []
        if word_departure:
            parts.append(f"  Word-level: {word_departure}")
        if verse_departure:
            parts.append(f"  Verse-level: {verse_departure}")
        departure_section = "\n## Departure Notes (from AI's full-verse translation analysis)\n" + "\n".join(parts)

    prompt = f"""## Word Under Review
Position {word_pos} in verse {surah}:{ayah}
Arabic: {arabic_form}
Root: {root_ar or "—"}
Lemma: {lemma_ar or "—"}

## Full Verse
{surah}:{ayah} — {verse_arabic}
Translation: {verse_trans}

## Translation A (conventional)
{conventional or "(empty)"}

## Translation B (AI-derived)
{ai_meaning}

## AI's Reasoning (summary)
{ai_detailed[:500] if ai_detailed else "(none)"}
{departure_section}

Pick the better tooltip gloss for this word. /no_think"""

    return prompt


def parse_judge_response(raw: str) -> dict | None:
    """Parse CHOICE / TRANSLATION / REASONING from judge response."""
    choice_match = re.search(r"CHOICE:\s*([ABC])\b", raw, re.IGNORECASE)
    trans_match = re.search(r"TRANSLATION:\s*(.+?)(?=\nREASONING:|\Z)", raw, re.DOTALL | re.IGNORECASE)
    reason_match = re.search(r"REASONING:\s*(.+?)$", raw, re.DOTALL | re.IGNORECASE)

    if not choice_match or not trans_match:
        return None

    return {
        "choice": choice_match.group(1).upper(),
        "translation": trans_match.group(1).strip().strip('"').strip("'"),
        "reasoning": reason_match.group(1).strip() if reason_match else "",
    }


def _store_judgment(conn, surah, ayah, word_pos, preferred_translation, preferred_source):
    """Write preferred_translation + preferred_source to the most recent ai_word_meanings row."""
    conn.execute(
        "UPDATE ai_word_meanings "
        "SET preferred_translation = ?, preferred_source = ? "
        "WHERE id = ("
        "  SELECT id FROM ai_word_meanings "
        "  WHERE chapter = ? AND verse = ? AND word_pos = ? "
        "  ORDER BY created_at DESC LIMIT 1"
        ")",
        (preferred_translation, preferred_source, surah, ayah, word_pos),
    )


def judge_word(
    conn,
    surah: int,
    ayah: int,
    word_pos: int,
    model: str,
    temperature: float,
    dry_run: bool = False,
    force: bool = False,
) -> bool:
    """Judge a single word via LLM. Returns True if judgment was stored."""

    # Check if already judged
    if not force:
        row = conn.execute(
            "SELECT preferred_translation FROM ai_word_meanings "
            "WHERE chapter = ? AND verse = ? AND word_pos = ? "
            "AND preferred_translation IS NOT NULL "
            "ORDER BY created_at DESC LIMIT 1",
            (surah, ayah, word_pos),
        ).fetchone()
        if row:
            print(f"    word {word_pos} — already judged (use --force to redo)")
            return False

    prompt = build_judge_prompt(conn, surah, ayah, word_pos)
    if prompt is None:
        print(f"    word {word_pos} — skipped (no AI meaning, empty, or identical)")
        return False

    if dry_run:
        print(f"\n{'='*80}")
        print(f"DRY RUN — Judge prompt for {surah}:{ayah} word {word_pos}")
        print(f"{'='*80}")
        print(f"\n[SYSTEM PROMPT]\n{SYSTEM_PROMPT}")
        print(f"\n[USER PROMPT]\n{prompt}")
        print(f"{'='*80}\n")
        return False

    print(f"    word {word_pos} — calling {model}...", end="", flush=True)
    try:
        raw_response, elapsed_ms = call_model(model, SYSTEM_PROMPT, prompt, temperature)
    except Exception as e:
        print(f" ERROR: {e}")
        return False

    print(f" done ({elapsed_ms / 1000:.1f}s)")

    parsed = parse_judge_response(raw_response)
    if not parsed:
        print(f"    word {word_pos} — WARNING: could not parse judge response")
        print(f"      Raw: {raw_response[:200]}")
        return False

    # Map choice to source
    source_map = {"A": "conventional", "B": "ai", "C": "judge"}
    preferred_source = source_map.get(parsed["choice"], "judge")
    preferred_translation = parsed["translation"]

    _store_judgment(conn, surah, ayah, word_pos, preferred_translation, preferred_source)
    conn.commit()

    print(f"      -> [{parsed['choice']}] \"{preferred_translation}\" ({preferred_source})")
    if parsed["reasoning"]:
        print(f"        {parsed['reasoning'][:120]}")
    return True


# ---------------------------------------------------------------------------
#  Zipf-optimized --all mode
# ---------------------------------------------------------------------------


def _load_all_words(conn, verse_set=None):
    """Load all AI word meanings with morphology info for classification.

    Returns list of dicts with keys:
        chapter, verse, word_pos, meaning_short, raw_response, pos, lemma_bw
    """
    rows = conn.execute(
        "SELECT wm.chapter, wm.verse, wm.word_pos, wm.meaning_short, "
        "       wm.raw_response, wm.preferred_translation, "
        "       m.pos, m.lemma_buckwalter "
        "FROM ai_word_meanings wm "
        "INNER JOIN ("
        "  SELECT chapter, verse, word_pos, MAX(created_at) AS max_created "
        "  FROM ai_word_meanings "
        "  GROUP BY chapter, verse, word_pos"
        ") latest ON wm.chapter = latest.chapter AND wm.verse = latest.verse "
        "  AND wm.word_pos = latest.word_pos AND wm.created_at = latest.max_created "
        "LEFT JOIN morphology m ON wm.chapter = m.chapter AND wm.verse = m.verse "
        "  AND wm.word_pos = m.word_pos AND m.pos NOT IN ('Prefix', 'Suffix') "
        "  AND m.lemma_buckwalter IS NOT NULL AND m.lemma_buckwalter != '' "
        "ORDER BY wm.chapter, wm.verse, wm.word_pos"
    ).fetchall()

    result = []
    for r in rows:
        ch, v = r["chapter"], r["verse"]
        if verse_set and (ch, v) not in verse_set:
            continue
        result.append({
            "chapter": ch,
            "verse": v,
            "word_pos": r["word_pos"],
            "meaning_short": (r["meaning_short"] or "").strip(),
            "raw_response": r["raw_response"] or "",
            "already_judged": r["preferred_translation"] is not None,
            "pos": r["pos"] or "",
            "lemma_bw": r["lemma_buckwalter"] or "",
        })
    return result


def run_all(args):
    """Run the Zipf-optimized judge across all AI word meanings."""
    conn = get_db()
    try:
        verse_set = set(parse_verse_spec(args.verses)) if args.verses else None

        print("Loading word data...")
        words = _load_all_words(conn, verse_set)
        print(f"Total word positions with AI meanings: {len(words)}")

        # Preload all glosses
        gloss_cache = {}
        for w in words:
            key = (w["chapter"], w["verse"])
            if key not in gloss_cache:
                gloss_cache[key] = _fetch_word_glosses(conn, w["chapter"], w["verse"])

        # ── Classify into tiers ──
        tier0_identical = []    # auto-skip
        tier1_function = []     # auto-conventional
        tier2_reused = {}       # (lemma, ai_lower) -> [word, ...]
        tier3_context = {}      # (conv_lower, ai_lower) -> [word, ...]

        for w in words:
            conv = (gloss_cache[(w["chapter"], w["verse"])].get(w["word_pos"], "") or "").strip()
            ai = w["meaning_short"]
            w["_conv"] = conv  # stash for later

            if not conv or not ai:
                tier0_identical.append(w)
                continue
            if conv.lower() == ai.lower():
                tier0_identical.append(w)
                continue

            if w["pos"] in FUNCTION_POS:
                tier1_function.append(w)
                continue

            # Zipf-reused: raw_response starts with [reused or [tier1
            # Group by (lemma, ai_meaning) only — conv varies with prefixes
            # but the AI meaning is identical for all reused occurrences,
            # so the judgment should be consistent across all of them.
            raw = w["raw_response"]
            if raw.startswith("[reused") or raw.startswith("[tier1"):
                key = (w["lemma_bw"], ai.lower())
                tier2_reused.setdefault(key, []).append(w)
                continue

            # Context-specific: group by text pair
            key = (conv.lower(), ai.lower())
            tier3_context.setdefault(key, []).append(w)

        tier2_total = sum(len(v) for v in tier2_reused.values())
        tier3_total = sum(len(v) for v in tier3_context.values())

        print(f"\n=== Zipf Judge Strategy ===")
        print(f"  Tier 0 - Identical (auto-skip):         {len(tier0_identical):>6,} words ->       0 calls")
        print(f"  Tier 1 - Function words (auto-conv):    {len(tier1_function):>6,} words ->       0 calls")
        print(f"  Tier 2 - Zipf-reused (judge 1, copy):   {tier2_total:>6,} words -> {len(tier2_reused):>7,} calls")
        print(f"  Tier 3 - Context-specific (per pair):   {tier3_total:>6,} words -> {len(tier3_context):>7,} calls")
        total_calls = len(tier2_reused) + len(tier3_context)
        est_hours = total_calls * 20 / 3600
        print(f"  TOTAL LLM CALLS: {total_calls:,}  (est. {est_hours:.1f} hours at ~20s each)")

        if args.dry_run:
            print("\n[DRY RUN] No changes made.")
            return

        # ── Tier 1: auto-pick conventional for function words ──
        t1_stored = 0
        for w in tier1_function:
            if w["already_judged"] and not args.force:
                continue
            _store_judgment(conn, w["chapter"], w["verse"], w["word_pos"],
                           w["_conv"], "conventional")
            t1_stored += 1
            if t1_stored % 500 == 0:
                conn.commit()
        conn.commit()
        print(f"\nTier 1: {t1_stored} function words set to conventional")

        # ── Tier 2: judge one representative per group, replicate ──
        t2_judged = 0
        t2_replicated = 0
        source_counts = {"conventional": 0, "ai": 0, "judge": 0}

        for (lemma, ai_l), group in tier2_reused.items():
            # Check if any in group is already judged (use as cached result)
            cached = None
            if not args.force:
                for w in group:
                    if w["already_judged"]:
                        row = conn.execute(
                            "SELECT preferred_translation, preferred_source "
                            "FROM ai_word_meanings "
                            "WHERE chapter = ? AND verse = ? AND word_pos = ? "
                            "AND preferred_translation IS NOT NULL "
                            "ORDER BY created_at DESC LIMIT 1",
                            (w["chapter"], w["verse"], w["word_pos"]),
                        ).fetchone()
                        if row:
                            cached = (row["preferred_translation"], row["preferred_source"])
                            break

            if cached:
                # Replicate to unjudged members
                for w in group:
                    if not w["already_judged"]:
                        _store_judgment(conn, w["chapter"], w["verse"], w["word_pos"],
                                        cached[0], cached[1])
                        t2_replicated += 1
                conn.commit()
                continue

            # Judge the first word in the group
            rep = group[0]
            prompt = build_judge_prompt(conn, rep["chapter"], rep["verse"], rep["word_pos"])
            if prompt is None:
                continue

            print(f"  T2 [{lemma}] {rep['chapter']}:{rep['verse']} w{rep['word_pos']} "
                  f"({len(group)} occ) — calling {args.model}...", end="", flush=True)
            try:
                raw_response, elapsed_ms = call_model(args.model, SYSTEM_PROMPT, prompt, args.temperature)
            except Exception as e:
                print(f" ERROR: {e}")
                continue

            print(f" done ({elapsed_ms / 1000:.1f}s)")

            parsed = parse_judge_response(raw_response)
            if not parsed:
                print(f"    WARNING: could not parse response")
                continue

            source_map = {"A": "conventional", "B": "ai", "C": "judge"}
            pref_source = source_map.get(parsed["choice"], "judge")
            pref_trans = parsed["translation"]
            source_counts[pref_source] += 1

            print(f"    -> [{parsed['choice']}] \"{pref_trans}\" -> {len(group)} words")

            # Store for all words in the group
            for w in group:
                _store_judgment(conn, w["chapter"], w["verse"], w["word_pos"],
                                pref_trans, pref_source)
            conn.commit()

            t2_judged += 1
            t2_replicated += len(group) - 1

        print(f"\nTier 2: {t2_judged} judged, {t2_replicated} replicated")

        # ── Tier 3: judge one representative per unique text pair ──
        t3_judged = 0
        t3_replicated = 0

        # Sort by pair count descending so most-frequent pairs are judged first
        sorted_pairs = sorted(tier3_context.items(), key=lambda x: -len(x[1]))

        for (conv_l, ai_l), group in sorted_pairs:
            # Check if any in group is already judged
            cached = None
            if not args.force:
                for w in group:
                    if w["already_judged"]:
                        row = conn.execute(
                            "SELECT preferred_translation, preferred_source "
                            "FROM ai_word_meanings "
                            "WHERE chapter = ? AND verse = ? AND word_pos = ? "
                            "AND preferred_translation IS NOT NULL "
                            "ORDER BY created_at DESC LIMIT 1",
                            (w["chapter"], w["verse"], w["word_pos"]),
                        ).fetchone()
                        if row:
                            cached = (row["preferred_translation"], row["preferred_source"])
                            break

            if cached:
                for w in group:
                    if not w["already_judged"]:
                        _store_judgment(conn, w["chapter"], w["verse"], w["word_pos"],
                                        cached[0], cached[1])
                        t3_replicated += 1
                conn.commit()
                continue

            # Judge the first word
            rep = group[0]
            prompt = build_judge_prompt(conn, rep["chapter"], rep["verse"], rep["word_pos"])
            if prompt is None:
                continue

            occ_label = f"({len(group)} occ) " if len(group) > 1 else ""
            print(f"  T3 {rep['chapter']}:{rep['verse']} w{rep['word_pos']} {occ_label}"
                  f"— calling {args.model}...", end="", flush=True)
            try:
                raw_response, elapsed_ms = call_model(args.model, SYSTEM_PROMPT, prompt, args.temperature)
            except Exception as e:
                print(f" ERROR: {e}")
                continue

            print(f" done ({elapsed_ms / 1000:.1f}s)")

            parsed = parse_judge_response(raw_response)
            if not parsed:
                print(f"    WARNING: could not parse response")
                continue

            source_map = {"A": "conventional", "B": "ai", "C": "judge"}
            pref_source = source_map.get(parsed["choice"], "judge")
            pref_trans = parsed["translation"]
            source_counts[pref_source] += 1

            if len(group) > 1:
                print(f"    -> [{parsed['choice']}] \"{pref_trans}\" -> {len(group)} words")
            else:
                print(f"    -> [{parsed['choice']}] \"{pref_trans}\"")

            for w in group:
                _store_judgment(conn, w["chapter"], w["verse"], w["word_pos"],
                                pref_trans, pref_source)
            conn.commit()

            t3_judged += 1
            t3_replicated += len(group) - 1

            # Progress report every 100 calls
            total_done = t2_judged + t3_judged
            if total_done % 100 == 0 and total_done > 0:
                elapsed_pct = total_done / total_calls * 100 if total_calls else 0
                print(f"\n  --- Progress: {total_done}/{total_calls} calls ({elapsed_pct:.0f}%) ---\n")

        total_stored = t1_stored + t2_judged + t2_replicated + t3_judged + t3_replicated
        print(f"\nTier 3: {t3_judged} judged, {t3_replicated} replicated")
        print(f"\n=== Summary ===")
        print(f"  Total words updated: {total_stored:,}")
        print(f"  LLM calls made:     {t2_judged + t3_judged:,}")
        print(f"  Conventional (A):   {source_counts['conventional']}")
        print(f"  AI (B):             {source_counts['ai']}")
        print(f"  Judge alt (C):      {source_counts['judge']}")

    finally:
        conn.close()


# ---------------------------------------------------------------------------
#  --fix-tier2: re-judge only Zipf-reused groups for consistency
# ---------------------------------------------------------------------------


def fix_tier2(args):
    """Re-judge Tier 2 (Zipf-reused) lemma groups and overwrite all members."""
    conn = get_db()
    try:
        print("Loading Tier 2 words...")
        words = _load_all_words(conn)

        gloss_cache = {}
        for w in words:
            key = (w["chapter"], w["verse"])
            if key not in gloss_cache:
                gloss_cache[key] = _fetch_word_glosses(conn, w["chapter"], w["verse"])

        # Collect only Tier 2 groups
        tier2_reused = {}
        for w in words:
            conv = (gloss_cache[(w["chapter"], w["verse"])].get(w["word_pos"], "") or "").strip()
            ai = w["meaning_short"]
            w["_conv"] = conv
            if not conv or not ai or conv.lower() == ai.lower():
                continue
            if w["pos"] in FUNCTION_POS:
                continue
            raw = w["raw_response"]
            if raw.startswith("[reused") or raw.startswith("[tier1"):
                key = (w["lemma_bw"], ai.lower())
                tier2_reused.setdefault(key, []).append(w)

        total_words = sum(len(g) for g in tier2_reused.values())
        print(f"Found {len(tier2_reused)} Tier 2 groups covering {total_words} words")
        print(f"Will make {len(tier2_reused)} LLM calls\n")

        if args.dry_run:
            for (lemma, ai_l), group in tier2_reused.items():
                print(f"  [{lemma}] {len(group)} words — AI: {ai_l[:60]}")
            print("\n[DRY RUN] No changes made.")
            return

        judged = 0
        replicated = 0
        source_counts = {"conventional": 0, "ai": 0, "judge": 0}

        for (lemma, ai_l), group in tier2_reused.items():
            rep = group[0]
            prompt = build_judge_prompt(conn, rep["chapter"], rep["verse"], rep["word_pos"])
            if prompt is None:
                continue

            print(f"  [{lemma}] {rep['chapter']}:{rep['verse']} w{rep['word_pos']} "
                  f"({len(group)} occ) — calling {args.model}...", end="", flush=True)
            try:
                raw_response, elapsed_ms = call_model(args.model, SYSTEM_PROMPT, prompt, args.temperature)
            except Exception as e:
                print(f" ERROR: {e}")
                continue

            print(f" done ({elapsed_ms / 1000:.1f}s)")

            parsed = parse_judge_response(raw_response)
            if not parsed:
                print(f"    WARNING: could not parse response")
                continue

            source_map = {"A": "conventional", "B": "ai", "C": "judge"}
            pref_source = source_map.get(parsed["choice"], "judge")
            pref_trans = parsed["translation"]
            source_counts[pref_source] += 1

            print(f"    -> [{parsed['choice']}] \"{pref_trans}\" -> {len(group)} words")

            for w in group:
                _store_judgment(conn, w["chapter"], w["verse"], w["word_pos"],
                                pref_trans, pref_source)
            conn.commit()

            judged += 1
            replicated += len(group) - 1

        print(f"\nDone: {judged} groups judged, {replicated} words replicated")
        print(f"  Conventional (A): {source_counts['conventional']}")
        print(f"  AI (B):           {source_counts['ai']}")
        print(f"  Judge alt (C):    {source_counts['judge']}")

    finally:
        conn.close()


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="LLM Judge for Word Translations")
    parser.add_argument("--verses", default=None, help="Verse specification, e.g. '1:1-7,96:1-5'")
    parser.add_argument("--all", action="store_true", help="Run Zipf-optimized judge on all AI word meanings")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE, help="Temperature (default: 0.2)")
    parser.add_argument("--dry-run", action="store_true", help="Print stats/prompts without calling model")
    parser.add_argument("--force", action="store_true", help="Re-judge already-judged words")
    parser.add_argument("--word-pos", type=int, default=None, help="Judge only this word position (with --verses)")
    parser.add_argument("--fix-tier2", action="store_true",
                        help="Re-judge only Tier 2 (Zipf-reused) groups for consistency")
    args = parser.parse_args()

    if args.fix_tier2:
        fix_tier2(args)
        return

    if args.all:
        run_all(args)
        return

    if not args.verses:
        print("ERROR: specify --verses or --all")
        sys.exit(1)

    verses = parse_verse_spec(args.verses)
    if not verses:
        print("No valid verses specified")
        sys.exit(1)

    print(f"Judging words in {len(verses)} verse(s) with model '{args.model}'")

    conn = get_db()
    try:
        total_judged = 0

        for surah, ayah in verses:
            print(f"\n  {surah}:{ayah}:")

            if args.word_pos is not None:
                if judge_word(conn, surah, ayah, args.word_pos, args.model,
                              args.temperature, args.dry_run, args.force):
                    total_judged += 1
            else:
                # Find all word positions that have AI meanings
                pos_rows = conn.execute(
                    "SELECT DISTINCT word_pos FROM ai_word_meanings "
                    "WHERE chapter = ? AND verse = ? ORDER BY word_pos",
                    (surah, ayah),
                ).fetchall()

                for row in pos_rows:
                    if judge_word(conn, surah, ayah, row["word_pos"], args.model,
                                  args.temperature, args.dry_run, args.force):
                        total_judged += 1

        if not args.dry_run:
            print(f"\nDone: {total_judged} word(s) judged")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
