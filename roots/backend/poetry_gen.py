"""Phase 1 — Qurʾān↔poetry COMPARISON drafting (root-level).

The companion to poetry_corpus.py (Phase 0, which built the corpus and the
poetry_line_roots index). This script drives the agent-driven drafting loop:
for each pilot root it hands Claude Code a brief (the root's Qurʾān profile +
its authenticated poetic occurrences), Claude drafts an objective comparison,
and `add` stores it as a PENDING row in root_poetry_comparisons for admin
review — exactly mirroring the exegesis pipeline (qa_gen.py / exeg_next.py).

NO API calls live here: the reasoning is done by the Claude Code loop itself
(subscription tokens), the same model as the indexing loop.

Usage:
    python poetry_gen.py next --track root [--count N]
    python poetry_gen.py context <root>           # the drafting brief
    python poetry_gen.py add <root> --file <json>  # store a pending draft
    python poetry_gen.py skip <root> --reason "<line>"
    python poetry_gen.py stats
"""
from __future__ import annotations

import argparse
import json
import os
import sys

try:
    from poetry_corpus import get_conn, root_arabic_for, bare
except Exception:  # pragma: no cover
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from poetry_corpus import get_conn, root_arabic_for, bare

PILOT_ROOTS = ["kfr", "wqy", "dhr", "krm", "jnn"]

SHIFT_TYPES = {
    "continuity",          # no real shift — the Qurʾān uses it as the poets did
    "narrowing", "widening",
    "elevation",           # physical → moral/ethical (e.g. wqy → taqwā)
    "theologization",      # worldly → God-centred (e.g. dahr demoted under God)
    "moralization",
    "referential_transfer",# same sense, new referent
    "reassignment",        # agency/ownership reassigned (e.g. ʿizza → God)
}

# Post-Qurʾānic SECTARIAN/jurisprudential terms that must not frame the reading
# (Qurʾān-internal voice). NOTE: unlike the exegesis pipeline we do NOT ban
# "Islamic" — "pre-Islamic poetry" is this feature's own subject matter. We ban
# only terms that would import later doctrine into the interpretation.
POST_QURANIC = [
    "muslim", "hadith", "sunnah", "sharia", "shariah", "fiqh", "caliph",
    "halal", "haram", "madhhab", "scholars say", "ulama", "tafsir",
    "the prophet said", "jurist",
]


# ------------------------------------------------------------------------
# Schema (the 3 Phase-1 tables)
# ------------------------------------------------------------------------

def ensure_compare_schema(conn) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS poetry_compare_configs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            config_name   TEXT NOT NULL UNIQUE,
            model_name    TEXT NOT NULL,
            prompt_version TEXT NOT NULL,
            methodology_notes TEXT,
            created_at    TEXT DEFAULT (datetime('now'))
        );

        -- ROOT-LEVEL comparison (twin of term_surveys). One row per root.
        CREATE TABLE IF NOT EXISTS root_poetry_comparisons (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            root_buckwalter  TEXT NOT NULL UNIQUE,
            root_arabic      TEXT,
            config_id        INTEGER REFERENCES poetry_compare_configs(id),
            shift_type       TEXT,
            comparison_markdown  TEXT,
            quran_usage_summary  TEXT,
            poetry_usage_summary TEXT,
            quoted_lines_json    TEXT,   -- enriched: poet, bayt, tier, english…
            collocations_json    TEXT,   -- {"quran":[…],"poetry":[…]}
            continuity       INTEGER DEFAULT 0,
            counter_search_json  TEXT,   -- the adversarial counter-search trace
            adversarial_report   TEXT,
            lexical_basis    TEXT,       -- dictionary/cognate grounding (Lane/Lisān/Semitic)
            confidence       REAL,
            auth_tier_max    TEXT,       -- best tier among quoted lines
            review_status    TEXT DEFAULT 'pending',
            hidden           INTEGER DEFAULT 0,
            raw_response     TEXT,
            created_at       TEXT DEFAULT CURRENT_TIMESTAMP,
            edited_at        TEXT
        );

        -- VERSE-LEVEL note (twin of verse_exegesis). Phase 1b.
        CREATE TABLE IF NOT EXISTS verse_poetry_notes (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter          INTEGER NOT NULL,
            verse            INTEGER NOT NULL,
            page_key         TEXT NOT NULL,
            focus_root_buckwalter TEXT,
            note_markdown    TEXT NOT NULL,
            quoted_lines_json TEXT,
            continuity       INTEGER DEFAULT 0,
            confidence       REAL,
            auth_tier_max    TEXT,
            config_id        INTEGER REFERENCES poetry_compare_configs(id),
            adversarial_report TEXT,
            review_status    TEXT DEFAULT 'pending',
            hidden           INTEGER DEFAULT 0,
            raw_response     TEXT,
            created_at       TEXT DEFAULT CURRENT_TIMESTAMP,
            edited_at        TEXT,
            UNIQUE(chapter, verse)
        );
        """
    )
    have = {r[1] for r in conn.execute("PRAGMA table_info(root_poetry_comparisons)")}
    if "lexical_basis" not in have:
        conn.execute("ALTER TABLE root_poetry_comparisons ADD COLUMN lexical_basis TEXT")
    conn.commit()


# ------------------------------------------------------------------------
# Data assembly
# ------------------------------------------------------------------------

def quran_profile(conn, root_bw: str) -> dict:
    root_ar = root_arabic_for(conn, root_bw)
    total = conn.execute(
        "SELECT COUNT(DISTINCT chapter||':'||verse) n FROM morphology WHERE root_buckwalter=?",
        (root_bw,)).fetchone()["n"]
    meaning = conn.execute(
        """SELECT primary_meaning, detailed_meaning, semantic_field, evidence_summary
           FROM ai_root_meanings WHERE root_buckwalter=? ORDER BY id DESC LIMIT 1""",
        (root_bw,)).fetchone()
    lemmas = [dict(r) for r in conn.execute(
        """SELECT DISTINCT lemma_arabic, lemma_buckwalter FROM morphology
           WHERE root_buckwalter=? AND lemma_arabic IS NOT NULL LIMIT 12""",
        (root_bw,))]
    # a spread of Qurʾānic occurrences with the base English translation
    refs = [dict(r) for r in conn.execute(
        """SELECT DISTINCT m.chapter, m.verse, t.text_en
           FROM morphology m LEFT JOIN translations t
             ON t.chapter=m.chapter AND t.verse=m.verse
           WHERE m.root_buckwalter=? ORDER BY m.chapter, m.verse""",
        (root_bw,))]
    sample = refs[:: max(1, len(refs) // 10)][:10] if refs else []
    return {"root_arabic": root_ar, "total": total, "meaning": dict(meaning) if meaning else None,
            "lemmas": lemmas, "sample_verses": sample}


def poetry_occurrences(conn, root_bw: str) -> list[dict]:
    rows = conn.execute(
        """SELECT plr.id line_root_id, plr.surface_word, plr.sense_hint, plr.confidence,
                  pp.poet, pp.auth_tier, pp.title, pl.text_plain, pl.hemistich1, pl.hemistich2
           FROM poetry_line_roots plr
           JOIN poetry_lines pl ON pl.id = plr.line_id
           JOIN poetry_poems pp ON pp.id = pl.poem_id
           WHERE plr.root_buckwalter = ?
           ORDER BY pp.auth_tier ASC, plr.confidence DESC""",
        (root_bw,)).fetchall()
    return [dict(r) for r in rows]


# ------------------------------------------------------------------------
# next
# ------------------------------------------------------------------------

def cmd_next(args) -> int:
    conn = get_conn(); ensure_compare_schema(conn)
    try:
        done = {r["root_buckwalter"] for r in conn.execute(
            "SELECT root_buckwalter FROM root_poetry_comparisons")}
        todo = [r for r in PILOT_ROOTS if r not in done]
        batch = todo[: args.count]
        out = {"track": args.track, "remaining": len(todo),
               "roots": [{"root": r, "root_arabic": root_arabic_for(conn, r),
                          "poetry_lines": len(poetry_occurrences(conn, r))} for r in batch]}
        print(json.dumps(out, ensure_ascii=False, indent=2))
    finally:
        conn.close()
    return 0


# ------------------------------------------------------------------------
# context  (the drafting brief)
# ------------------------------------------------------------------------

def cmd_context(args) -> int:
    conn = get_conn(); ensure_compare_schema(conn)
    try:
        root_bw = args.root
        prof = quran_profile(conn, root_bw)
        occ = poetry_occurrences(conn, root_bw)
        L = []
        L.append(f"# Drafting brief — root {prof['root_arabic']}  ({root_bw})\n")
        L.append("## Qurʾānic side")
        L.append(f"Total Qurʾānic occurrences: {prof['total']} verses")
        if prof["meaning"]:
            m = prof["meaning"]
            L.append(f"AI root meaning (primary): {m.get('primary_meaning')}")
            if m.get("detailed_meaning"):
                L.append(f"Detailed: {m['detailed_meaning']}")
            if m.get("semantic_field"):
                L.append(f"Semantic field: {m['semantic_field']}")
        if prof["lemmas"]:
            L.append("Lemmas: " + ", ".join(
                f"{l['lemma_arabic']} ({l['lemma_buckwalter']})" for l in prof["lemmas"]))
        L.append("\nSample Qurʾānic occurrences (ref — base translation):")
        for v in prof["sample_verses"]:
            tr = (v.get("text_en") or "").strip()
            if len(tr) > 200:
                tr = tr[:197] + "…"
            L.append(f"  {v['chapter']}:{v['verse']} — {tr}")

        L.append(f"\n## Pre-Islamic poetry side — {len(occ)} indexed occurrence(s)")
        L.append("(Quote ONLY by line_root_id. Tier A/B are quotable for contrasts; "
                 "Tier C is for statistics/illustration only.)")
        cur_tier = None
        for o in occ:
            if o["auth_tier"] != cur_tier:
                cur_tier = o["auth_tier"]
                L.append(f"\n-- Tier {cur_tier} --")
            bayt = o["text_plain"] or " / ".join(
                x for x in [o["hemistich1"], o["hemistich2"]] if x)
            L.append(f"  [lr:{o['line_root_id']}] «{o['surface_word']}» "
                     f"({o.get('sense_hint')}) — {o['poet']}: {bayt}")
        print("\n".join(L))
    finally:
        conn.close()
    return 0


# ------------------------------------------------------------------------
# add  (store a pending draft + validate)
# ------------------------------------------------------------------------

def cmd_add(args) -> int:
    with open(args.file, encoding="utf-8") as f:
        payload = json.load(f)
    conn = get_conn(); ensure_compare_schema(conn)
    try:
        root_bw = args.root
        root_ar = root_arabic_for(conn, root_bw)
        flags = []

        shift = (payload.get("shift_type") or "").strip()
        if shift not in SHIFT_TYPES:
            print(f"ERROR: shift_type {shift!r} not in {sorted(SHIFT_TYPES)}", file=sys.stderr)
            return 1
        continuity = 1 if payload.get("continuity") else 0
        md = (payload.get("comparison_markdown") or "").strip()
        if len(md) < 80:
            print("ERROR: comparison_markdown too short / missing.", file=sys.stderr)
            return 1

        # validate + enrich quoted lines against the index
        quoted_in = payload.get("quoted_lines") or []
        enriched, tiers = [], []
        for q in quoted_in:
            lrid = q.get("line_root_id")
            row = conn.execute(
                """SELECT plr.id, plr.surface_word, pp.poet, pp.auth_tier, pp.title,
                          pl.text_plain, pl.hemistich1, pl.hemistich2
                   FROM poetry_line_roots plr
                   JOIN poetry_lines pl ON pl.id=plr.line_id
                   JOIN poetry_poems pp ON pp.id=pl.poem_id
                   WHERE plr.id=? AND plr.root_buckwalter=?""",
                (lrid, root_bw)).fetchone()
            if not row:
                print(f"ERROR: quoted line_root_id {lrid} not found for root {root_bw}.",
                      file=sys.stderr)
                return 1
            tiers.append(row["auth_tier"])
            enriched.append({
                "line_root_id": lrid, "poet": row["poet"], "auth_tier": row["auth_tier"],
                "arabic": row["text_plain"], "surface_word": row["surface_word"],
                "english": q.get("english"), "translit": q.get("translit"),
                "note": q.get("note"),
            })
        rank = {"A": 3, "B": 2, "C": 1, "D": 0}
        auth_tier_max = max(tiers, key=lambda t: rank.get(t, 0)) if tiers else None

        # OBJECTIVITY GATE: a contrast may not rest SOLELY on unauthenticated
        # (Tier-C) poetry. It must be grounded in EITHER authenticated (A/B)
        # poetic evidence OR an explicit lexical_basis (the dictionaries /
        # Semitic cognates — Tier-A-equivalent for a lexical claim), with the
        # Tier-C lines serving as illustration. (Research doc §2.2, §7.)
        lexical_basis = (payload.get("lexical_basis") or "").strip()
        if not continuity and auth_tier_max not in ("A", "B") and not lexical_basis:
            print("ERROR: a contrast (continuity=0) must EITHER quote >=1 Tier-A/B line "
                  f"(got auth_tier_max={auth_tier_max!r}) OR supply a 'lexical_basis' "
                  "(dictionary/cognate grounding). Otherwise set continuity=1.", file=sys.stderr)
            return 1
        if lexical_basis and auth_tier_max not in ("A", "B"):
            flags.append("contrast_rests_on_lexical_basis (Tier-C poetry = illustration only)")

        low = md.lower()
        hits = [w for w in POST_QURANIC if w in low]
        if hits:
            flags.append(f"post_quranic_terms: {hits}")

        conn.execute("DELETE FROM root_poetry_comparisons WHERE root_buckwalter=?", (root_bw,))
        conn.execute(
            """INSERT INTO root_poetry_comparisons
               (root_buckwalter, root_arabic, shift_type, comparison_markdown,
                quran_usage_summary, poetry_usage_summary, quoted_lines_json,
                collocations_json, continuity, counter_search_json, adversarial_report,
                lexical_basis, confidence, auth_tier_max, review_status, raw_response)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,'pending',?)""",
            (root_bw, root_ar, shift, md,
             payload.get("quran_usage_summary"), payload.get("poetry_usage_summary"),
             json.dumps(enriched, ensure_ascii=False),
             json.dumps(payload.get("collocations") or {}, ensure_ascii=False),
             continuity,
             json.dumps(payload.get("counter_search") or "", ensure_ascii=False),
             payload.get("adversarial_report"), lexical_basis or None,
             float(payload.get("confidence") or 0.0), auth_tier_max,
             json.dumps(payload, ensure_ascii=False)))
        conn.commit()
        verdict = "continuity" if continuity else f"contrast ({shift})"
        print(f"add {root_bw}: stored pending — {verdict}, {len(enriched)} quoted line(s), "
              f"tier_max={auth_tier_max}, conf={payload.get('confidence')}."
              + (f"  FLAGS: {flags}" if flags else ""))
    finally:
        conn.close()
    return 0


# ------------------------------------------------------------------------
# skip / stats
# ------------------------------------------------------------------------

def cmd_skip(args) -> int:
    conn = get_conn(); ensure_compare_schema(conn)
    try:
        root_ar = root_arabic_for(conn, args.root)
        conn.execute("DELETE FROM root_poetry_comparisons WHERE root_buckwalter=?", (args.root,))
        conn.execute(
            """INSERT INTO root_poetry_comparisons
               (root_buckwalter, root_arabic, comparison_markdown, review_status)
               VALUES (?,?,?,'skipped')""",
            (args.root, root_ar, f"SKIPPED: {args.reason}"))
        conn.commit()
        print(f"skip {args.root}: {args.reason}")
    finally:
        conn.close()
    return 0


def cmd_stats(args) -> int:
    conn = get_conn(); ensure_compare_schema(conn)
    try:
        print("━━━━━ root comparisons ━━━━━")
        for rb in PILOT_ROOTS:
            row = conn.execute(
                "SELECT shift_type, continuity, review_status, auth_tier_max, confidence "
                "FROM root_poetry_comparisons WHERE root_buckwalter=?", (rb,)).fetchone()
            ar = root_arabic_for(conn, rb)
            npoetry = len(poetry_occurrences(conn, rb))
            if not row:
                print(f"  {rb:<5} {ar:<10} poetry={npoetry:<4} — NOT DRAFTED")
            else:
                verdict = "continuity" if row["continuity"] else (row["shift_type"] or "?")
                print(f"  {rb:<5} {ar:<10} poetry={npoetry:<4} — {row['review_status']}"
                      f" / {verdict} / tier={row['auth_tier_max']} / conf={row['confidence']}")
        q = conn.execute(
            "SELECT review_status, COUNT(*) n FROM root_poetry_comparisons GROUP BY review_status"
        ).fetchall()
        print("\nreview queue:", {r["review_status"]: r["n"] for r in q})
    finally:
        conn.close()
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("next", help="next roots needing a comparison")
    sp.add_argument("--track", choices=["root", "verse"], default="root")
    sp.add_argument("--count", type=int, default=1)

    sp = sub.add_parser("context", help="the drafting brief for a root")
    sp.add_argument("root")

    sp = sub.add_parser("add", help="store a pending draft")
    sp.add_argument("root")
    sp.add_argument("--file", required=True)

    sp = sub.add_parser("skip", help="mark a root intentionally skipped")
    sp.add_argument("root")
    sp.add_argument("--reason", required=True)

    sub.add_parser("stats", help="drafting progress + review queue")

    args = p.parse_args()
    return {
        "next": cmd_next, "context": cmd_context, "add": cmd_add,
        "skip": cmd_skip, "stats": cmd_stats,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
