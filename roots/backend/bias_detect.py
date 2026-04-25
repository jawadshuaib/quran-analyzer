"""Stage 1 — fast programmatic bias detector.

Uses the canonical renderings derived in term_surveys (Stage 0) as
ground truth. For each verse in scope:

  1. Find which surveyed roots appear in the verse's morphology.
  2. If any, look up each root's canonical English (e.g. Slw → "connect").
  3. Check whether the translation contains any word from that canonical's
     word family — case-insensitive, whole-word match on a hand-curated
     inflection set (see CANONICAL_WORD_FAMILIES).
  4. If not, flag the verse.

No LLM call in this stage. It runs in seconds across the full corpus,
the output is deterministic, and every flag comes with the specific
expected canonical. Stage 2 (Claude adjudicator) can then decide
whether to revise.

Usage:
    python bias_detect.py --surahs 78-114           # Juz Amma
    python bias_detect.py --verses "111:1,2:3,2:43"
    python bias_detect.py --all
    python bias_detect.py --surahs 78-114 --force   # overwrite prior reviews
    python bias_detect.py --surahs 78-114 --config gpt5.1-batch-v2

Output: rows in translation_bias_reviews. flags_json shape per concern:

  {
    "type": "root_mismatch",
    "root_buckwalter": "Slw",
    "root_arabic": "ص-ل-و",
    "arabic_word": "الصَّلَاةَ",
    "expected_canonical": "connect",
    "current_translation_snippet": "...establish the prayer...",
    "reason": "Root ص-ل-و has canonical 'connect' but the translation uses none of its word family."
  }
"""
from __future__ import annotations

import argparse
import json
import re
import sys

from app import get_db

# ------------------------------------------------------------------------
# Canonical word families — hand-curated inflections for each of the 13
# surveyed canonical renderings. If a translation of a verse containing
# the root uses ANY of these tokens, we treat the canonical as honored
# and do not flag. Match is case-insensitive, whole-word (using \b).
# ------------------------------------------------------------------------

CANONICAL_WORD_FAMILIES: dict[str, set[str]] = {
    # Slw → connect
    "connect": {"connect", "connects", "connected", "connecting", "connection",
                "connections", "reconnect", "reconnected", "reconnecting"},
    # zkw → grow
    "grow":    {"grow", "grows", "grew", "grown", "growing", "growth",
                "outgrow", "regrow"},
    # Swm → abstain
    "abstain": {"abstain", "abstains", "abstained", "abstaining", "abstention",
                "abstinence"},
    # Hjj → argue
    "argue":   {"argue", "argues", "argued", "arguing", "argument", "arguments",
                "argumentation"},
    # sjd → submit
    "submit":  {"submit", "submits", "submitted", "submitting", "submission",
                "submissions", "submissive"},
    # rkE → humble
    "humble":  {"humble", "humbles", "humbled", "humbling", "humbly",
                "humility", "humiliate", "humiliated"},
    # snn → pattern
    "pattern": {"pattern", "patterns", "patterned", "patterning"},
    # nsk → devotion
    "devotion": {"devote", "devotes", "devoted", "devoting", "devotion",
                 "devotions", "devotional", "devotedly"},
    # qwm → stand
    "stand":   {"stand", "stands", "stood", "standing", "withstand",
                "withstood", "withstands", "withstanding",
                "upright", "uprightness", "uphold", "upholds", "upheld",
                "upholding"},
    # $Er → perceive
    "perceive": {"perceive", "perceives", "perceived", "perceiving",
                 "perception", "perceptions", "perceptible", "perceptibly",
                 "aware", "awareness"},
    # Emr → cultivate
    "cultivate": {"cultivate", "cultivates", "cultivated", "cultivating",
                  "cultivation", "cultivator", "cultivators"},
    # *kr → remember (also accept invoke/mention since they're commonly used
    # for the same root in the active-devotional contexts)
    "remember": {"remember", "remembers", "remembered", "remembering",
                 "remembrance", "reminder", "reminders", "remind", "reminds",
                 "reminded", "reminding", "mind", "mindful", "mindfulness",
                 "mention", "mentions", "mentioned", "mentioning",
                 "recall", "recalls", "recalled", "recalling",
                 "invoke", "invokes", "invoked", "invocation"},
    # Thr → purify
    "purify":  {"purify", "purifies", "purified", "purifying", "purification",
                "pure", "purity", "impurity", "impure"},
}


def word_family(canonical: str) -> set[str]:
    """Look up the set of surface-form words that count as 'the canonical
    family'. Fall back to a trivial stem-based set if we don't have a
    hand-curated family yet (e.g. if someone surveys a new root)."""
    fam = CANONICAL_WORD_FAMILIES.get(canonical.lower())
    if fam:
        return fam
    # Generic fallback — just the base word + common inflections.
    base = canonical.lower().strip()
    return {base, base + "s", base + "ed", base + "ing"}


def translation_contains_family(translation: str, family: set[str]) -> bool:
    """Case-insensitive whole-word scan."""
    tl = translation.lower()
    for w in family:
        if re.search(rf"\b{re.escape(w)}\b", tl):
            return True
    return False


def parse_verse_spec(spec: str) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for piece in spec.split(","):
        piece = piece.strip()
        if not piece:
            continue
        m = re.match(r"^(\d+):(\d+)(?:-(\d+))?$", piece)
        if not m:
            raise SystemExit(f"bad verse spec: {piece!r}")
        surah, start = int(m.group(1)), int(m.group(2))
        end = int(m.group(3) or start)
        out.extend((surah, v) for v in range(start, end + 1))
    return out


def parse_surahs_spec(spec: str) -> list[int]:
    out: list[int] = []
    for piece in spec.split(","):
        piece = piece.strip()
        if "-" in piece:
            a, b = piece.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        elif piece:
            out.append(int(piece))
    return out


def verses_in_surahs(conn, surahs: list[int]) -> list[tuple[int, int]]:
    placeholders = ",".join(["?"] * len(surahs))
    rows = conn.execute(
        f"SELECT chapter, verse FROM verses WHERE chapter IN ({placeholders}) "
        f"ORDER BY chapter, verse",
        surahs,
    ).fetchall()
    return [(r["chapter"], r["verse"]) for r in rows]


def load_surveys(conn) -> dict[str, dict]:
    """Return a mapping from root_buckwalter to its survey row."""
    rows = conn.execute(
        "SELECT root_buckwalter, root_arabic, canonical_english, "
        "       leave_untranslated, confidence "
        "FROM term_surveys"
    ).fetchall()
    return {r["root_buckwalter"]: dict(r) for r in rows}


def load_config_id(conn, name: str) -> int:
    row = conn.execute(
        "SELECT id FROM ai_translation_configs WHERE config_name = ?",
        (name,),
    ).fetchone()
    if not row:
        raise SystemExit(f"unknown ai_translation config {name!r}")
    return row["id"]


def find_surveyed_roots_in_verse(
    conn, surah: int, ayah: int, surveys: dict[str, dict],
) -> list[dict]:
    """Return a list of {root_buckwalter, root_arabic, arabic_word,
    word_pos} for each surveyed root that occurs in this verse (dedup
    per word_pos — if one word has multiple segments with the same root,
    we record it once)."""
    rows = conn.execute(
        "SELECT word_pos, form_arabic, root_buckwalter, root_arabic "
        "FROM morphology "
        "WHERE chapter = ? AND verse = ? "
        "  AND root_buckwalter IS NOT NULL "
        "ORDER BY word_pos, segment",
        (surah, ayah),
    ).fetchall()
    out = []
    seen = set()
    for r in rows:
        root = r["root_buckwalter"]
        if root not in surveys:
            continue
        key = (root, r["word_pos"])
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "root_buckwalter": root,
            "root_arabic": r["root_arabic"] or surveys[root].get("root_arabic"),
            "arabic_word": r["form_arabic"],
            "word_pos": r["word_pos"],
        })
    return out


def detect_flags_for_verse(
    translation: str,
    surveyed_occurrences: list[dict],
    surveys: dict[str, dict],
) -> list[dict]:
    """Return a list of concern dicts for this verse — one per surveyed
    root occurrence whose canonical word family is absent from the
    translation. Multiple occurrences of the same root collapse into one
    concern (we don't need to flag each inflection separately)."""
    flags = []
    already_flagged_roots: set[str] = set()

    for occ in surveyed_occurrences:
        root = occ["root_buckwalter"]
        if root in already_flagged_roots:
            continue
        survey = surveys[root]
        if survey.get("leave_untranslated"):
            continue  # policy: leave as transliteration, don't flag
        canonical = survey.get("canonical_english") or ""
        if not canonical:
            continue
        family = word_family(canonical)
        if translation_contains_family(translation, family):
            continue  # honored
        # Deviation detected. Record the concern.
        flags.append({
            "type": "root_mismatch",
            "root_buckwalter": root,
            "root_arabic": occ["root_arabic"],
            "arabic_word": occ["arabic_word"],
            "word_pos": occ["word_pos"],
            "expected_canonical": canonical,
            "expected_word_family_sample": sorted(family)[:5],
            "reason": (
                f"Root {occ['root_arabic']} ({root}) has canonical "
                f"'{canonical}' per Qur'an-only survey, but the current "
                f"translation contains no form of that word family."
            ),
        })
        already_flagged_roots.add(root)
    return flags


def upsert_review(
    conn, surah: int, ayah: int, config_id: int, original_text: str,
    flagged: bool, flags: list[dict], force: bool,
    detector_model: str = "programmatic-canonical-v1",
    prompt_version: str = "v1",
) -> str:
    """Insert or replace the translation_bias_reviews row.
    Returns 'inserted' / 'replaced' / 'skipped_exists'."""
    existing = conn.execute(
        "SELECT id FROM translation_bias_reviews "
        "WHERE chapter = ? AND verse = ? "
        "  AND detector_model = ? AND detector_prompt_version = ? "
        "  AND ai_translation_config_id = ?",
        (surah, ayah, detector_model, prompt_version, config_id),
    ).fetchone()
    if existing and not force:
        return "skipped_exists"
    if existing:
        conn.execute("DELETE FROM translation_bias_reviews WHERE id = ?",
                     (existing["id"],))
    conn.execute(
        "INSERT INTO translation_bias_reviews ("
        "  chapter, verse, ai_translation_config_id, original_text,"
        "  detector_model, detector_prompt_version, detector_flagged,"
        "  flags_json"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            surah, ayah, config_id, original_text,
            detector_model, prompt_version, 1 if flagged else 0,
            json.dumps(flags, ensure_ascii=False) if flags else None,
        ),
    )
    conn.commit()
    return "replaced" if existing else "inserted"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--verses", help="e.g. '111:1-5,112:1-4'")
    p.add_argument("--surahs", help="e.g. '78-114'")
    p.add_argument("--all", action="store_true")
    p.add_argument("--config", default="gpt5.1-batch-v2",
                   help="ai_translation config_name to audit")
    p.add_argument("--force", action="store_true",
                   help="overwrite existing review rows")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="print each verse's verdict")
    args = p.parse_args()

    conn = get_db()
    config_id = load_config_id(conn, args.config)
    surveys = load_surveys(conn)

    if not surveys:
        print("ERROR: term_surveys is empty. Run term_survey.py --seed-list first.",
              file=sys.stderr)
        return 1

    print(f"Loaded {len(surveys)} canonical renderings: "
          f"{', '.join(sorted(s['canonical_english'] for s in surveys.values()))}")

    # Resolve verse list
    if args.verses:
        verse_list = parse_verse_spec(args.verses)
    elif args.surahs:
        verse_list = verses_in_surahs(conn, parse_surahs_spec(args.surahs))
    elif args.all:
        verse_list = [(r["chapter"], r["verse"]) for r in conn.execute(
            "SELECT chapter, verse FROM verses ORDER BY chapter, verse")]
    else:
        print("ERROR: pass --verses, --surahs, or --all.", file=sys.stderr)
        return 1

    stats = {
        "total": len(verse_list),
        "no_translation": 0,
        "no_surveyed_roots": 0,
        "flagged": 0,
        "clean": 0,
        "skipped_exists": 0,
    }
    concern_counts_by_root: dict[str, int] = {}

    for surah, ayah in verse_list:
        tr = conn.execute(
            "SELECT translation_text FROM ai_translations "
            "WHERE chapter = ? AND verse = ? AND config_id = ?",
            (surah, ayah, config_id),
        ).fetchone()
        if not tr or not tr["translation_text"]:
            stats["no_translation"] += 1
            continue
        translation = tr["translation_text"]

        occurrences = find_surveyed_roots_in_verse(conn, surah, ayah, surveys)
        if not occurrences:
            stats["no_surveyed_roots"] += 1
            if args.verbose:
                print(f"  {surah}:{ayah} — no surveyed roots present")
            continue

        flags = detect_flags_for_verse(translation, occurrences, surveys)
        flagged = bool(flags)
        result = upsert_review(
            conn, surah, ayah, config_id, translation,
            flagged, flags, args.force,
        )
        if result == "skipped_exists":
            stats["skipped_exists"] += 1
            continue
        if flagged:
            stats["flagged"] += 1
            for f in flags:
                r = f["root_buckwalter"]
                concern_counts_by_root[r] = concern_counts_by_root.get(r, 0) + 1
            if args.verbose:
                roots = ", ".join(
                    f"{f['root_arabic']}→'{f['expected_canonical']}'"
                    for f in flags
                )
                print(f"  {surah}:{ayah} FLAGGED — {roots}")
        else:
            stats["clean"] += 1
            if args.verbose:
                print(f"  {surah}:{ayah} clean")

    print(f"\n=== Summary (config '{args.config}', {stats['total']} verses) ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    if concern_counts_by_root:
        print("\nFlags by root:")
        for root, n in sorted(concern_counts_by_root.items(), key=lambda kv: -kv[1]):
            survey = surveys[root]
            print(f"  {root:<5} ({survey['root_arabic']}) → '{survey['canonical_english']}': "
                  f"{n} flags")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
