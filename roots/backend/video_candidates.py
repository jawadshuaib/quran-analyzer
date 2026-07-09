#!/usr/bin/env python3
"""Studio idea layer — mine, record, and submit video candidates.

The Studio funnel puts a cheap IDEA stage in front of the expensive
script stage:

    mine  -> print rateable material per source (Claude rates per
             video_rubric.md — rationale first, kill < 8)
    record -> persist the rated candidate (including kills, so the
             loop never re-proposes a dead idea)
    context -> everything needed to draft one candidate: verse token
             dumps + enrichment + the full source material
    submit -> gate a drafted script (same fail-closed gates as every
             other bank entry) and upsert it into qa_videos

Sources: qa (rated-5 Q&A) | exegesis (approved verse notes) |
root (lexicon shift stories + judge-divergent words) | poetry
(pre-Islamic comparisons with quotable bayts).

Dedup is structural: video_candidates.source_key is UNIQUE, and
qa_videos.source_key is UNIQUE — an idea exists once, a script exists
once, regardless of who mined it or when.
"""

from __future__ import annotations

import argparse
import json
import sys

import qa_video_common as C
import qa_video_pipeline as PL
import qa_video_script as SC


def _known_keys(conn) -> set[str]:
    keys = {r[0] for r in conn.execute(
        "SELECT source_key FROM video_candidates").fetchall()}
    keys |= {r[0] for r in conn.execute(
        "SELECT source_key FROM qa_videos WHERE source_key IS NOT NULL").fetchall()}
    return keys


# ---------------------------------------------------------------------------
#  Miners — each returns [{source_key, anchor_ref, material...}] for rating.
# ---------------------------------------------------------------------------

def mine_qa(conn, limit: int, known: set[str]) -> list[dict]:
    out = []
    for r in conn.execute(
        "SELECT id, question, answer, page_key FROM assistant_conversations "
        "WHERE quality_score=5 ORDER BY id DESC"
    ).fetchall():
        key = f"qa:{r['id']}"
        if key in known:
            continue
        out.append({
            "source_key": key,
            "anchor_ref": r["page_key"],
            "question": r["question"],
            "answer": (r["answer"] or "")[:600],
        })
        if len(out) >= limit:
            break
    return out


def mine_exegesis(conn, limit: int, known: set[str]) -> list[dict]:
    out = []
    for r in conn.execute(
        "SELECT id, chapter, verse, exegesis_markdown FROM verse_exegesis "
        "WHERE review_status='approved' AND COALESCE(hidden,0)=0 "
        "ORDER BY id DESC"
    ).fetchall():
        key = f"exegesis:{r['id']}"
        if key in known:
            continue
        md = r["exegesis_markdown"] or ""
        # Concreteness pre-filter: the note must anchor to visible Arabic
        # (script or *transliteration*) or it cannot survive the match gate.
        if not (any("؀" <= ch <= "ۿ" for ch in md) or "*" in md):
            continue
        out.append({
            "source_key": key,
            "anchor_ref": f"{r['chapter']}:{r['verse']}",
            "note": md[:900],
        })
        if len(out) >= limit:
            break
    return out


def mine_root(conn, limit: int, known: set[str]) -> list[dict]:
    """Lexicon entries with a shift story, garnished with the verses where
    the judge preferred the root-based meaning over the conventional gloss
    — the places the divergence bites."""
    out = []
    for r in conn.execute(
        "SELECT root_buckwalter, root_arabic, relation_to_quran, "
        "       quran_internal_summary, lexicon_markdown "
        "FROM root_poetic_lexicon WHERE review_status='approved' "
        "AND relation_to_quran IN ('narrowing','specialization','reassignment','widening') "
        "ORDER BY rowid"
    ).fetchall():
        key = f"root:{r['root_buckwalter']}"
        if key in known:
            continue
        bites = [dict(x) for x in conn.execute(
            "SELECT w.chapter, w.verse, w.preferred_translation, w.meaning_short "
            "FROM ai_word_meanings w "
            "JOIN morphology m ON m.chapter=w.chapter AND m.verse=w.verse "
            "  AND m.word_pos=w.word_pos "
            "WHERE m.root_buckwalter=? AND w.preferred_source='ai' "
            "LIMIT 4", (r["root_buckwalter"],)).fetchall()]
        out.append({
            "source_key": key,
            "anchor_ref": (f"{bites[0]['chapter']}:{bites[0]['verse']}" if bites else None),
            "root_arabic": r["root_arabic"],
            "relation": r["relation_to_quran"],
            "summary": (r["quran_internal_summary"] or "")[:500],
            "lexicon": (r["lexicon_markdown"] or "")[:700],
            "divergent_words": bites,
        })
        if len(out) >= limit:
            break
    return out


_SHIFT_PRIORITY = {"theologization": 0, "reassignment": 1, "elevation": 2,
                   "narrowing": 3, "continuity": 4}


def mine_poetry(conn, limit: int, known: set[str]) -> list[dict]:
    rows = conn.execute(
        "SELECT id, root_buckwalter, root_arabic, shift_type, "
        "       comparison_markdown, quoted_lines_json "
        "FROM root_poetry_comparisons "
        "WHERE review_status='approved' AND COALESCE(hidden,0)=0"
    ).fetchall()
    rows = sorted(rows, key=lambda r: _SHIFT_PRIORITY.get(r["shift_type"], 9))
    out = []
    for r in rows:
        key = f"poetry:{r['root_buckwalter']}"
        if key in known:
            continue
        bayt = None
        try:
            for x in json.loads(r["quoted_lines_json"] or "[]"):
                if isinstance(x, dict) and (x.get("bayt") or x.get("arabic")) \
                        and (x.get("english") or x.get("translation")):
                    bayt = {"arabic": x.get("bayt") or x.get("arabic"),
                            "english": x.get("english") or x.get("translation"),
                            "poet": x.get("poet")}
                    break
        except Exception:
            pass
        if not bayt:
            continue
        # A verse note for this root gives the anchor verse when present.
        note = conn.execute(
            "SELECT chapter, verse FROM verse_poetry_notes "
            "WHERE focus_root_buckwalter=? AND review_status='approved' "
            "AND COALESCE(hidden,0)=0 LIMIT 1", (r["root_buckwalter"],)).fetchone()
        out.append({
            "source_key": key,
            "anchor_ref": (f"{note['chapter']}:{note['verse']}" if note else None),
            "root_arabic": r["root_arabic"],
            "shift_type": r["shift_type"],
            "comparison": (r["comparison_markdown"] or "")[:800],
            "bayt": bayt,
        })
        if len(out) >= limit:
            break
    return out


MINERS = {"qa": mine_qa, "exegesis": mine_exegesis,
          "root": mine_root, "poetry": mine_poetry}


# ---------------------------------------------------------------------------
#  CLI commands
# ---------------------------------------------------------------------------

def cmd_mine(args) -> int:
    conn = C.get_conn()
    try:
        PL.ensure_tables(conn)
        known = _known_keys(conn)
        cands = MINERS[args.source](conn, args.limit, known)
        print(json.dumps({"source": args.source, "candidates": cands},
                         ensure_ascii=False, indent=1))
        return 0
    finally:
        conn.close()


def cmd_record(args) -> int:
    """Persist a rated candidate (or update its status later)."""
    conn = C.get_conn()
    try:
        PL.ensure_tables(conn)
        conn.execute(
            "INSERT INTO video_candidates "
            "  (source_type, source_key, anchor_ref, angle, hook_sketch, "
            "   self_score, rationale, status, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,datetime('now')) "
            "ON CONFLICT(source_key) DO UPDATE SET "
            "  angle=excluded.angle, hook_sketch=excluded.hook_sketch, "
            "  self_score=excluded.self_score, rationale=excluded.rationale, "
            "  status=excluded.status, updated_at=datetime('now')",
            (args.source_key.split(":", 1)[0], args.source_key,
             args.anchor_ref, args.angle, args.hook, args.score,
             args.rationale, args.status),
        )
        conn.commit()
        print(json.dumps({"ok": True, "source_key": args.source_key,
                          "status": args.status}))
        return 0
    finally:
        conn.close()


def cmd_context(args) -> int:
    """Drafting context for one candidate: verse tokens + enrichment +
    the full source material."""
    conn = C.get_conn()
    try:
        PL.ensure_tables(conn)
        row = conn.execute(
            "SELECT * FROM video_candidates WHERE source_key=?",
            (args.source_key,)).fetchone()
        anchor = args.anchor_ref or (row["anchor_ref"] if row else None)
        if not anchor:
            print("no anchor_ref known — pass --anchor-ref", file=sys.stderr)
            return 2
        ctx = SC.build_context(conn, anchor, args.refs or [])
        enr = SC.build_enrichment(conn, anchor)
        out = {"source_key": args.source_key, "anchor_ref": anchor,
               "candidate": dict(row) if row else None,
               "verses": ctx["verses"], "enrichment": enr}
        # Full (untruncated) source material by type
        st = args.source_key.split(":", 1)[0]
        sid = args.source_key.split(":", 1)[1]
        if st == "exegesis":
            r = conn.execute("SELECT exegesis_markdown FROM verse_exegesis WHERE id=?",
                             (int(sid),)).fetchone()
            out["source_material"] = r["exegesis_markdown"] if r else None
        elif st == "root":
            r = conn.execute("SELECT * FROM root_poetic_lexicon WHERE root_buckwalter=?",
                             (sid,)).fetchone()
            out["source_material"] = dict(r) if r else None
        elif st == "poetry":
            r = conn.execute("SELECT * FROM root_poetry_comparisons WHERE root_buckwalter=?",
                             (sid,)).fetchone()
            out["source_material"] = dict(r) if r else None
        elif st == "qa":
            r = conn.execute("SELECT question, answer FROM assistant_conversations WHERE id=?",
                             (int(sid),)).fetchone()
            out["source_material"] = dict(r) if r else None
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0
    finally:
        conn.close()


def cmd_submit(args) -> int:
    """Gate a drafted script through the SAME fail-closed gates as every
    bank entry, persist it, and link the candidate."""
    import qa_video_gen as QG
    script = json.load(open(args.file, encoding="utf-8"))
    conn = C.get_conn()
    try:
        PL.ensure_tables(conn)
        result = QG.gate_script(conn, script)
        source_type = args.source_key.split(":", 1)[0]
        status = "gate_passed" if result["ok"] else "rejected_match"
        fields = {
            "title": script.get("title"),
            "theme": script.get("theme"),
            "angle": args.angle,
            "self_score": args.score,
            "script_json": json.dumps(script, ensure_ascii=False),
            "status": status,
            "triggered_by": "studio",
            "punch_ok": 1 if (result["gate_a"] or {}).get("ok") else 0,
            "match_ok": 1 if (result["gate_b"] or {}).get("ok") else 0,
            "error_message": ("; ".join(result["issues"])[:800] or None),
        }
        if result["ok"]:
            fields["payload_json"] = json.dumps(result["payload"], ensure_ascii=False)
            fields["match_snapshot"] = json.dumps(result["match_snapshot"], ensure_ascii=False)
        if source_type == "qa" and str(script.get("qa_id") or "").isdigit():
            fields["qa_id"] = int(script["qa_id"])
        if args.quality_report:
            fields["quality_report"] = open(args.quality_report, encoding="utf-8").read()
        vid = PL.upsert_by_source(conn, source_type, args.source_key,
                                  script.get("anchor_ref"), **fields)
        conn.execute(
            "UPDATE video_candidates SET status=?, video_id=?, updated_at=datetime('now') "
            "WHERE source_key=?",
            ("drafted" if result["ok"] else "rejected_gate", vid, args.source_key))
        conn.commit()
        print(json.dumps({"ok": result["ok"], "video_id": vid,
                          "status": status, "issues": result["issues"]},
                         ensure_ascii=False))
        return 0 if result["ok"] else 1
    finally:
        conn.close()


def cmd_list(args) -> int:
    conn = C.get_conn()
    try:
        PL.ensure_tables(conn)
        rows = conn.execute(
            "SELECT source_key, anchor_ref, self_score, status, angle "
            "FROM video_candidates ORDER BY self_score DESC, id DESC LIMIT ?",
            (args.limit,)).fetchall()
        for r in rows:
            print(f"{r['self_score'] or '-':>4} {r['status']:<14} "
                  f"{r['source_key']:<18} {r['anchor_ref'] or '-':<8} {r['angle'] or ''}")
        return 0
    finally:
        conn.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("mine", help="print rateable candidates for a source")
    p.add_argument("source", choices=list(MINERS))
    p.add_argument("--limit", type=int, default=5)
    p.set_defaults(fn=cmd_mine)

    p = sub.add_parser("record", help="persist a rated candidate")
    p.add_argument("--source-key", required=True)
    p.add_argument("--anchor-ref")
    p.add_argument("--angle")
    p.add_argument("--hook")
    p.add_argument("--score", type=float)
    p.add_argument("--rationale")
    p.add_argument("--status", default="proposed",
                   choices=["proposed", "rejected_score", "starred"])
    p.set_defaults(fn=cmd_record)

    p = sub.add_parser("context", help="drafting context for one candidate")
    p.add_argument("source_key")
    p.add_argument("--anchor-ref")
    p.add_argument("--refs", nargs="*")
    p.set_defaults(fn=cmd_context)

    p = sub.add_parser("submit", help="gate + bank a drafted script")
    p.add_argument("--source-key", required=True)
    p.add_argument("--file", required=True)
    p.add_argument("--angle")
    p.add_argument("--score", type=float)
    p.add_argument("--quality-report", help="JSON file with the quality panel verdicts")
    p.set_defaults(fn=cmd_submit)

    p = sub.add_parser("list", help="show recorded candidates")
    p.add_argument("--limit", type=int, default=30)
    p.set_defaults(fn=cmd_list)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
