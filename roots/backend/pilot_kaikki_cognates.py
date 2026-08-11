#!/usr/bin/env python3
"""Evaluate explicit Wiktionary cognates for uncovered Quranic roots.

This is deliberately a non-destructive pilot: it reads quran.db and the
Kaikki English-Wiktionary Arabic JSONL dump, then writes a JSON report and a
CSV review queue.  It never changes the production cognate tables.

Usage:
    python pilot_kaikki_cognates.py
    python pilot_kaikki_cognates.py --limit 100 --force-download
    python pilot_kaikki_cognates.py --review-csv data/kaikki_review.csv

Reviewers may set the CSV ``decision`` column to ``accept`` or ``reject`` and
rerun the command to have the report calculate the adjudication rate.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

import requests

from scrape_semitic_roots import bw_root_to_sr


HERE = Path(__file__).resolve().parent
DEFAULT_DB = HERE / "data" / "quran.db"
DEFAULT_DUMP = HERE / "data" / "kaikki.org-dictionary-Arabic.jsonl"
DEFAULT_REPORT = HERE / "data" / "kaikki_cognate_pilot.json"
DEFAULT_REVIEW = HERE / "data" / "kaikki_cognate_review.csv"
DUMP_URL = (
    "https://kaikki.org/dictionary/Arabic/"
    "kaikki.org-dictionary-Arabic.jsonl"
)

# Wiktionary language codes for Semitic languages useful to the cognate panel.
# Arabic varieties are excluded: they are descendants/varieties, not external
# comparative evidence for an Arabic Quranic root.
SEMITIC_LANGUAGES = {
    "sem-pro": "Proto-Semitic",
    "akk": "Akkadian",
    "uga": "Ugaritic",
    "xpu": "Punic",
    "phn": "Phoenician",
    "he": "Hebrew",
    "hbo": "Biblical Hebrew",
    "arc": "Aramaic",
    "tmr": "Jewish Babylonian Aramaic",
    "sam": "Samaritan Aramaic",
    "syc": "Classical Syriac",
    "syr": "Syriac",
    "myz": "Classical Mandaic",
    "gez": "Ge'ez",
    "am": "Amharic",
    "ti": "Tigrinya",
    "tig": "Tigre",
    "har": "Harari",
    "sqt": "Soqotri",
    "meh": "Mehri",
    "hss": "Harsusi",
    "mt": "Maltese",
    "sba": "Sabaic",
    "xsa": "Sabaic",
    "axb": "Abishira",
}

ARABIC_MARKS_RE = re.compile(
    "[\u0610-\u061a\u0640\u064b-\u065f\u0670\u06d6-\u06ed^#]"
)


def arabic_key(text: str, *, loose: bool = False) -> str:
    """Normalize Arabic orthography for lemma-to-headword matching."""
    text = unicodedata.normalize("NFC", text or "")
    text = ARABIC_MARKS_RE.sub("", text)
    text = text.replace("ٱ", "ا").replace("ى", "ي")
    if loose:
        text = re.sub("[أإآءؤئ]", "ا", text)
        # Quranic Corpus sometimes spells a seated/standalone hamza followed
        # by its carrier alif (e.g. ءَايَة), where dictionary Arabic uses آية.
        text = re.sub("ا+", "ا", text)
    return text


def entry_gloss(entry: dict) -> str:
    glosses: list[str] = []
    for sense in entry.get("senses") or []:
        for gloss in sense.get("glosses") or []:
            if gloss and gloss not in glosses:
                glosses.append(gloss)
    return "; ".join(glosses[:3])


def explicit_relations(entry: dict) -> list[dict]:
    """Return only structured ``cog`` and ``inh`` Semitic relations."""
    out = []
    seen = set()
    for template in entry.get("etymology_templates") or []:
        relation = template.get("name")
        args = template.get("args") or {}
        if relation == "cog":
            code, word = args.get("1"), args.get("2")
        elif relation == "inh":
            code, word = args.get("2"), args.get("3")
        else:
            continue
        if code not in SEMITIC_LANGUAGES or not word:
            continue
        roman = args.get("tr") or ""
        meaning = args.get("t") or args.get("gloss") or ""
        key = (relation, code, word, roman, meaning)
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "relation": "cognate" if relation == "cog" else "inherited",
            "language_code": code,
            "language": SEMITIC_LANGUAGES[code],
            "word": word,
            "romanization": roman,
            "meaning": meaning,
        })
    return out


def download_dump(path: Path, force: bool = False) -> None:
    if path.exists() and not force:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".partial")
    print(f"Downloading {DUMP_URL}")
    with requests.get(DUMP_URL, stream=True, timeout=60) as response:
        response.raise_for_status()
        with partial.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    partial.replace(path)


def target_roots(conn: sqlite3.Connection, limit: int) -> tuple[list[dict], set[str]]:
    known = {
        row[0] for row in conn.execute(
            "SELECT DISTINCT transliteration FROM semitic_roots"
        )
    }
    rows = conn.execute(
        """
        SELECT root_buckwalter,
               MIN(root_arabic) AS root_arabic,
               COUNT(DISTINCT chapter || ':' || verse) AS verse_count,
               COUNT(*) AS segment_count
        FROM morphology
        WHERE COALESCE(root_buckwalter, '') <> ''
        GROUP BY root_buckwalter
        ORDER BY verse_count DESC, segment_count DESC, root_buckwalter
        """
    ).fetchall()
    uncovered = [
        dict(row) for row in rows
        if bw_root_to_sr(row["root_buckwalter"]) not in known
    ]
    return uncovered[:limit], known


def root_headwords(conn: sqlite3.Connection, roots: list[dict]) -> dict[str, dict[str, set[str]]]:
    """Collect Arabic lemmas and lexical forms for each target root."""
    result: dict[str, dict[str, set[str]]] = {}
    for root in roots:
        bw = root["root_buckwalter"]
        values = conn.execute(
            """
            SELECT DISTINCT lemma_arabic FROM morphology
            WHERE root_buckwalter=? AND COALESCE(lemma_arabic, '') <> ''
            """,
            (bw,),
        ).fetchall()
        strict = {arabic_key(row[0]) for row in values if arabic_key(row[0])}
        loose = {arabic_key(row[0], loose=True) for row in values if arabic_key(row[0], loose=True)}
        result[bw] = {"strict": strict, "loose": loose}
    return result


def build_indexes(headwords: dict[str, dict[str, set[str]]]):
    strict_index: dict[str, set[str]] = defaultdict(set)
    loose_index: dict[str, set[str]] = defaultdict(set)
    for root, keys in headwords.items():
        for key in keys["strict"]:
            strict_index[key].add(root)
        for key in keys["loose"]:
            loose_index[key].add(root)
    return strict_index, loose_index


def scan_dump(path: Path, headwords: dict[str, dict[str, set[str]]]) -> tuple[list[dict], dict]:
    strict_index, loose_index = build_indexes(headwords)
    candidates = []
    stats = {"lines_scanned": 0, "arabic_entries_matched": 0, "ambiguous_entries": 0}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            stats["lines_scanned"] += 1
            entry = json.loads(line)
            if entry.get("lang_code") != "ar" or entry.get("source") == "thesaurus":
                continue
            word = entry.get("word") or ""
            strict_roots = strict_index.get(arabic_key(word), set())
            roots = strict_roots or loose_index.get(arabic_key(word, loose=True), set())
            if not roots:
                continue
            relations = explicit_relations(entry)
            if not relations:
                continue
            stats["arabic_entries_matched"] += 1
            if len(roots) != 1:
                stats["ambiguous_entries"] += 1
            confidence = "explicit" if strict_roots and len(roots) == 1 else "review"
            for root in sorted(roots):
                for relation in relations:
                    candidates.append({
                        "root_buckwalter": root,
                        "arabic_headword": word,
                        "headword_gloss": entry_gloss(entry),
                        "match_type": "strict_lemma" if strict_roots else "loose_lemma",
                        "confidence": confidence,
                        "source": "enwiktionary_kaikki",
                        "source_url": "https://en.wiktionary.org/wiki/" + quote(word) + "#Arabic",
                        **relation,
                    })
    # Identical relations can recur across parts of speech/etymology sections.
    unique = {}
    for row in candidates:
        key = (
            row["root_buckwalter"], row["arabic_headword"], row["relation"],
            row["language_code"], row["word"], row["romanization"],
        )
        unique.setdefault(key, row)
    return list(unique.values()), stats


def existing_comparison(conn: sqlite3.Connection, candidates: list[dict]) -> dict:
    """Measure overlaps/conflicts, even though targets start uncovered."""
    exact = 0
    language_conflicts = 0
    for candidate in candidates:
        sr = bw_root_to_sr(candidate["root_buckwalter"])
        rows = conn.execute(
            """
            SELECT d.language, d.word FROM semitic_derivatives d
            JOIN semitic_roots r ON r.id=d.root_id
            WHERE r.transliteration=?
            """,
            (sr,),
        ).fetchall()
        same_language = [row for row in rows if (row["language"] or "").casefold() == candidate["language"].casefold()]
        if any((row["word"] or "").casefold() == candidate["word"].casefold() for row in same_language):
            exact += 1
        elif same_language:
            language_conflicts += 1
    return {"exact_existing_relations": exact, "same_language_different_form": language_conflicts}


REVIEW_FIELDS = [
    "decision", "review_notes", "root_buckwalter", "root_arabic",
    "verse_count", "arabic_headword", "headword_gloss", "match_type",
    "confidence", "relation", "language", "word", "romanization",
    "meaning", "language_code", "source", "source_url",
]


def previous_decisions(path: Path) -> dict[tuple[str, ...], tuple[str, str]]:
    if not path.exists():
        return {}
    decisions = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["root_buckwalter"], row["arabic_headword"], row["relation"], row["language"], row["word"])
            decisions[key] = (row.get("decision", ""), row.get("review_notes", ""))
    return decisions


def write_review(path: Path, roots_by_bw: dict[str, dict], candidates: list[dict]) -> dict:
    old = previous_decisions(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    counts = defaultdict(int)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        for candidate in sorted(candidates, key=lambda row: (-roots_by_bw[row["root_buckwalter"]]["verse_count"], row["root_buckwalter"], row["language"], row["word"])):
            key = (candidate["root_buckwalter"], candidate["arabic_headword"], candidate["relation"], candidate["language"], candidate["word"])
            decision, notes = old.get(key, ("", ""))
            decision = decision.strip().lower()
            if decision in {"accept", "reject"}:
                counts[decision] += 1
            else:
                decision = ""
                counts["pending"] += 1
            root = roots_by_bw[candidate["root_buckwalter"]]
            writer.writerow({
                "decision": decision,
                "review_notes": notes,
                "root_arabic": root["root_arabic"],
                "verse_count": root["verse_count"],
                **candidate,
            })
    reviewed = counts["accept"] + counts["reject"]
    return {
        "accepted": counts["accept"], "rejected": counts["reject"],
        "pending": counts["pending"], "reviewed": reviewed,
        "acceptance_rate": (counts["accept"] / reviewed) if reviewed else None,
    }


def run(args) -> dict:
    download_dump(args.dump, args.force_download)
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    roots, _known = target_roots(conn, args.limit)
    roots_by_bw = {row["root_buckwalter"]: row for row in roots}
    headwords = root_headwords(conn, roots)
    candidates, scan_stats = scan_dump(args.dump, headwords)
    comparison = existing_comparison(conn, candidates)
    conn.close()

    review = write_review(args.review_csv, roots_by_bw, candidates)
    covered = {row["root_buckwalter"] for row in candidates}
    explicit_covered = {row["root_buckwalter"] for row in candidates if row["confidence"] == "explicit"}
    report = {
        "pilot": {
            "source": "English Wiktionary via Kaikki",
            "dump_url": DUMP_URL,
            "target": "highest-frequency Quranic roots lacking SemiticRoots/Starling exact matches",
            "target_root_count": len(roots),
        },
        "results": {
            **scan_stats,
            "candidate_relations": len(candidates),
            "newly_covered_roots": len(covered),
            "explicit_strictly_matched_roots": len(explicit_covered),
            "coverage_rate_in_pilot": len(covered) / len(roots) if roots else 0,
            "languages": sorted({row["language"] for row in candidates}),
            "relation_types": dict(sorted((kind, sum(row["relation"] == kind for row in candidates)) for kind in {row["relation"] for row in candidates})),
            "existing_data_comparison": comparison,
            "manual_review": review,
        },
        "target_roots": [
            {**root, "lemma_headwords": sorted(headwords[root["root_buckwalter"]]["strict"]), "has_candidate": root["root_buckwalter"] in covered}
            for root in roots
        ],
        "candidates": candidates,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--dump", type=Path, default=DEFAULT_DUMP)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--review-csv", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--force-download", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    report = run(args)
    result = report["results"]
    print(f"Pilot roots: {report['pilot']['target_root_count']}")
    print(f"Newly covered: {result['newly_covered_roots']} ({result['coverage_rate_in_pilot']:.1%})")
    print(f"Candidate relations: {result['candidate_relations']}")
    print(f"Review: {args.review_csv}")
    print(f"Report: {args.report}")


if __name__ == "__main__":
    main()
