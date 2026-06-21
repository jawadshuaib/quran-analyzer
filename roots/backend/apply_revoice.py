#!/usr/bin/env python3
"""Apply old-voice -> v2 voice rewrites to the flagged AI drafts.

Reads batch files, each a JSON list of {"id": int, "answer": str,
"question": str?}. For each draft it does exactly what `qa_gen.py revise`
does — re-validate banned terms / refs, refresh cited_refs+flags, set
meta.voice='v2', clear needs_voice_revision, stamp edited_at — with two
deliberate differences:

  * quality_score is PRESERVED (the honest re-grade stays; re-voicing is
    not a re-grade).
  * Only drafts still carrying needs_voice_revision are touched (a safety
    gate: the already-v2 corpus is never rewritten).

The honest-grade audit (prev_score / score_honest / regraded_honest) is
left intact.

Usage:  python apply_revoice.py /tmp/revoice/batch_*.json
"""
import glob
import json
import os
import sys

import qa_gen  # reuse get_conn, _find_refs, _banned_hits, now_iso, ALLOWED_CATEGORIES


def main(patterns):
    files = []
    for p in patterns:
        files.extend(sorted(glob.glob(p)))
    if not files:
        sys.exit("no batch files matched")

    payload = {}
    for f in files:
        with open(f) as fh:
            for it in json.load(fh):
                payload[int(it["id"])] = it

    conn = qa_gen.get_conn()
    applied = flagged_out = missing = not_flagged = empty_answer = 0
    with_flags = []
    for gid, it in payload.items():
        row = conn.execute(
            "SELECT page_key, question, category, quality_score, generation_meta "
            "FROM assistant_conversations WHERE id=? AND source='ai'", (gid,)
        ).fetchone()
        if not row:
            missing += 1
            continue
        try:
            meta = json.loads(row["generation_meta"]) if row["generation_meta"] else {}
        except Exception:
            meta = {}
        if not meta.get("needs_voice_revision"):
            not_flagged += 1
            continue
        q = (it.get("question") or row["question"] or "").strip()
        a = (it.get("answer") or "").strip()
        if not a:
            empty_answer += 1
            continue
        cat = (row["category"] or "other").strip().lower()
        if cat not in qa_gen.ALLOWED_CATEGORIES:
            cat = "other"

        flags = []
        bad = qa_gen._banned_hits(q + " " + a)
        if bad:
            flags.append("post_quranic_terms:" + ",".join(bad))
        valid_refs, invalid_refs = qa_gen._find_refs(conn, q + " " + a)
        if invalid_refs:
            flags.append("invalid_refs:" + ",".join(invalid_refs))

        meta["cited_refs"] = valid_refs
        meta["flags"] = flags
        meta["voice"] = "v2"
        meta.pop("needs_voice_revision", None)  # rewritten -> now new-voice

        conn.execute(
            "UPDATE assistant_conversations SET question=?, answer=?, category=?, "
            "generation_meta=?, edited_at=? WHERE id=?",
            (q[:500], a[:50000], cat, json.dumps(meta, ensure_ascii=False),
             qa_gen.now_iso(), gid),  # quality_score intentionally NOT updated
        )
        applied += 1
        flagged_out += 1 if flags else 0
        if flags:
            with_flags.append({"id": gid, "ref": row["page_key"], "flags": flags})
    conn.commit()
    conn.close()
    print(json.dumps({
        "files": len(files), "in_payload": len(payload), "applied": applied,
        "with_flags": flagged_out, "missing_id": missing,
        "skipped_not_flagged": not_flagged, "skipped_empty_answer": empty_answer,
        "flagged_detail": with_flags[:40],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:] or ["/tmp/revoice/batch_*.json"])
