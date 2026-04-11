"""Backfill: evaluate all past assistant conversations for insights.

Finds conversations in assistant_conversations that have never been evaluated
(no matching conversation_id in insight_evolution_log) and runs _evaluate_insight
on each one. Processes them sequentially to avoid hammering the API.

Usage:
    python backfill_insights.py                     # dry-run (default)
    python backfill_insights.py --apply             # actually call Claude and evaluate
    python backfill_insights.py --apply --verse 1:2 # only backfill for a specific verse
"""

import argparse
import os
import sys
import time

from app import DB_PATH, _evaluate_insight, _CLAUDE_API_KEY, get_db


def find_unevaluated(conn, verse_filter=None):
    """Find conversations that have never been evaluated."""
    query = """
        SELECT ac.id, ac.page_type, ac.page_key, ac.question, ac.answer, ac.created_at
        FROM assistant_conversations ac
        LEFT JOIN insight_evolution_log iel ON ac.id = iel.conversation_id
        WHERE iel.id IS NULL
          AND ac.page_type = 'verse'
    """
    params = []

    if verse_filter:
        query += " AND ac.page_key = ?"
        params.append(verse_filter)

    query += " ORDER BY ac.id"
    return conn.execute(query, params).fetchall()


def parse_verse_key(page_key):
    """Parse '1:2' into (1, 2)."""
    parts = page_key.split(":")
    if len(parts) != 2:
        return None, None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None, None


def main():
    parser = argparse.ArgumentParser(description="Backfill insight evaluations for past Q&A conversations")
    parser.add_argument("--apply", action="store_true", help="Actually run evaluations (default is dry-run)")
    parser.add_argument("--verse", help="Only backfill for a specific verse (e.g. '1:2')")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between API calls (default: 2.0)")
    args = parser.parse_args()

    if args.apply and not _CLAUDE_API_KEY:
        print("ERROR: CLAUDE_API_KEY environment variable not set.")
        print("Set it with: export CLAUDE_API_KEY=sk-ant-...")
        sys.exit(1)

    conn = get_db()
    rows = find_unevaluated(conn, args.verse)
    conn.close()

    if not rows:
        print("No unevaluated conversations found. Nothing to do.")
        return

    print(f"Found {len(rows)} unevaluated conversation(s):\n")

    evaluated = 0
    for r in rows:
        chapter, verse = parse_verse_key(r["page_key"])
        if chapter is None:
            print(f"  #{r['id']} — skipping, invalid page_key: {r['page_key']}")
            continue

        q_preview = r["question"][:80]
        a_preview = r["answer"][:80]
        print(f"  #{r['id']} verse {chapter}:{verse}")
        print(f"    Q: {q_preview}")
        print(f"    A: {a_preview}")

        if args.apply:
            print(f"    Evaluating...", end="", flush=True)
            try:
                _evaluate_insight(r["id"], chapter, verse, r["question"], r["answer"])
                print(" done")
                evaluated += 1
            except Exception as e:
                print(f" ERROR: {e}")

            # Check what happened
            check_conn = get_db()
            log = check_conn.execute(
                "SELECT status, confidence_score, evaluation_reasoning "
                "FROM insight_evolution_log WHERE conversation_id = ? ORDER BY id DESC LIMIT 1",
                (r["id"],),
            ).fetchone()
            check_conn.close()

            if log:
                status = log["status"]
                conf = log["confidence_score"]
                reason = (log["evaluation_reasoning"] or "")[:150]
                print(f"    Result: {status} (confidence={conf})")
                print(f"    Reasoning: {reason}")
            else:
                print(f"    Result: no log entry created (API key missing or error)")

            if args.delay > 0 and r != rows[-1]:
                time.sleep(args.delay)
        else:
            print(f"    (dry-run — would evaluate)")

        print()

    mode = "EVALUATED" if args.apply else "DRY RUN"
    print(f"\n{mode}: {evaluated if args.apply else 0}/{len(rows)} conversations processed")

    if args.apply:
        # Print summary
        conn = get_db()
        stats = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM insight_evolution_log GROUP BY status"
        ).fetchall()
        conn.close()
        print("\nInsight evolution log summary:")
        for s in stats:
            print(f"  {s['status']}: {s['cnt']}")


if __name__ == "__main__":
    main()
