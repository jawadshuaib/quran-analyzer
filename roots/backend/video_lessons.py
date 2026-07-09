#!/usr/bin/env python3
"""Studio lessons ledger — the system's learned editorial doctrine.

Every operator verdict, operator edit, and panel finding can become a
LESSON: one paragraph of binding guidance with the evidence that taught
it. Active lessons are injected into every drafting context and into the
calibration-judge's checklist, so the system compounds: today's
rejection is tomorrow's pre-draft constraint.

    active  -> print the injection block (loop pastes this into drafting
               and judge prompts)
    add     -> distiller writes a lesson (evidence REQUIRED; prefers
               strengthening an existing lesson over minting a new one)
    flag    -> mark a lesson contradicted by a new verdict (operator
               reviews it in the Studio panel)
    retire / reactivate / list

Guardrails: at most MAX_ACTIVE active lessons — `add` fails beyond the
cap so the distiller must consolidate, not accumulate. Prod is truth for
text+status of existing keys (operator edits/retires there); the loop
only creates new keys.
"""

from __future__ import annotations

import argparse
import json
import sys

import qa_video_common as C
import qa_video_pipeline as PL

MAX_ACTIVE = 15


def cmd_active(args) -> int:
    conn = C.get_conn()
    try:
        PL.ensure_tables(conn)
        rows = conn.execute(
            "SELECT lesson_key, lesson FROM studio_lessons "
            "WHERE status='active' ORDER BY id"
        ).fetchall()
        if not rows:
            print("(no active lessons)")
            return 0
        print("LEARNED LESSONS (binding — from operator verdicts, operator "
              "edits, and panel findings):")
        for i, r in enumerate(rows, 1):
            print(f"{i}. [{r['lesson_key']}] {r['lesson']}")
        return 0
    finally:
        conn.close()


def cmd_add(args) -> int:
    if not (args.evidence or "").strip():
        print("ERROR: --evidence is required — a lesson without the verdict/"
              "edit/finding that taught it is an opinion, not a lesson",
              file=sys.stderr)
        return 2
    conn = C.get_conn()
    try:
        PL.ensure_tables(conn)
        n_active = conn.execute(
            "SELECT COUNT(*) FROM studio_lessons WHERE status='active'"
        ).fetchone()[0]
        exists = conn.execute(
            "SELECT id FROM studio_lessons WHERE lesson_key=?",
            (args.key,)).fetchone()
        if not exists and n_active >= MAX_ACTIVE:
            print(f"ERROR: {MAX_ACTIVE} active lessons already — consolidate "
                  f"(strengthen an existing lesson) instead of adding",
                  file=sys.stderr)
            return 3
        conn.execute(
            "INSERT INTO studio_lessons (lesson_key, lesson, source, evidence, "
            "  status, updated_at) VALUES (?,?,?,?, 'active', datetime('now')) "
            "ON CONFLICT(lesson_key) DO UPDATE SET "
            "  lesson=excluded.lesson, source=excluded.source, "
            "  evidence=excluded.evidence, updated_at=datetime('now')",
            (args.key, args.lesson, args.source, args.evidence))
        conn.commit()
        print(json.dumps({"ok": True, "key": args.key,
                          "updated": bool(exists)}))
        return 0
    finally:
        conn.close()


def _set_status(key: str, status: str, note: str | None = None) -> int:
    conn = C.get_conn()
    try:
        PL.ensure_tables(conn)
        row = conn.execute(
            "SELECT id, evidence FROM studio_lessons WHERE lesson_key=?",
            (key,)).fetchone()
        if not row:
            print(f"ERROR: no lesson {key!r}", file=sys.stderr)
            return 2
        ev = row["evidence"] or ""
        if note:
            ev = f"{ev}\n[{status}] {note}".strip()
        conn.execute(
            "UPDATE studio_lessons SET status=?, evidence=?, "
            "updated_at=datetime('now') WHERE lesson_key=?",
            (status, ev, key))
        conn.commit()
        print(json.dumps({"ok": True, "key": key, "status": status}))
        return 0
    finally:
        conn.close()


def cmd_flag(args) -> int:
    return _set_status(args.key, "flagged", args.reason)


def cmd_retire(args) -> int:
    return _set_status(args.key, "retired", args.reason)


def cmd_reactivate(args) -> int:
    return _set_status(args.key, "active", args.reason)


def cmd_list(args) -> int:
    conn = C.get_conn()
    try:
        PL.ensure_tables(conn)
        for r in conn.execute(
            "SELECT lesson_key, status, source, lesson FROM studio_lessons "
            "ORDER BY (status='active') DESC, id"
        ).fetchall():
            print(f"[{r['status']:<8}] {r['lesson_key']:<28} ({r['source']}) "
                  f"{r['lesson'][:90]}")
        return 0
    finally:
        conn.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("active", help="print the injection block")
    p.set_defaults(fn=cmd_active)

    p = sub.add_parser("add", help="add or strengthen a lesson")
    p.add_argument("--key", required=True, help="short-kebab-slug, stable")
    p.add_argument("--lesson", required=True)
    p.add_argument("--source", required=True,
                   choices=["operator_reject", "operator_edit", "panel",
                            "seed", "manual"])
    p.add_argument("--evidence", required=True)
    p.set_defaults(fn=cmd_add)

    for name, fn in (("flag", cmd_flag), ("retire", cmd_retire),
                     ("reactivate", cmd_reactivate)):
        p = sub.add_parser(name)
        p.add_argument("key")
        p.add_argument("--reason")
        p.set_defaults(fn=fn)

    p = sub.add_parser("list")
    p.set_defaults(fn=cmd_list)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
