"""One-off cleanup: collapse duplicate assistant_conversations rows.

Groups rows by (session_id, page_type, page_key) within a 1-hour window.
For each group with more than one row, synthesizes the questions, keeps the
newest answer, updates the oldest row, and deletes the rest.

Usage:
    python cleanup_duplicate_qa.py              # dry-run (default)
    python cleanup_duplicate_qa.py --apply      # actually modify the database
"""

import argparse
import sqlite3
import sys

from app import DB_PATH, _synthesize_questions


def find_duplicate_groups(conn):
    """Find groups of rows that share (session_id, page_type, page_key) within 1 hour."""
    rows = conn.execute(
        "SELECT id, session_id, page_type, page_key, question, answer, created_at "
        "FROM assistant_conversations ORDER BY session_id, page_type, page_key, id"
    ).fetchall()

    groups = {}
    for r in rows:
        key = (r["session_id"], r["page_type"], r["page_key"])
        if key not in groups:
            groups[key] = []
        groups[key].append(dict(r))

    # Filter to groups with duplicates, split by 1-hour windows
    duplicate_groups = []
    for key, entries in groups.items():
        if len(entries) < 2:
            continue
        # Split into 1-hour windows based on created_at
        windows = []
        current_window = [entries[0]]
        for e in entries[1:]:
            # Simple comparison: if same hour-ish, group together
            # Use the first entry's time as anchor
            first_ts = current_window[0]["created_at"]
            cur_ts = e["created_at"]
            # SQLite datetime strings are ISO format, comparable as strings for same day
            # For robust 1-hour check, parse them
            from datetime import datetime
            try:
                t0 = datetime.fromisoformat(first_ts)
                t1 = datetime.fromisoformat(cur_ts)
                if (t1 - t0).total_seconds() <= 3600:
                    current_window.append(e)
                else:
                    if len(current_window) > 1:
                        windows.append(current_window)
                    current_window = [e]
            except (ValueError, TypeError):
                # If timestamps are unparseable, group conservatively
                current_window.append(e)
        if len(current_window) > 1:
            windows.append(current_window)

        duplicate_groups.extend(windows)

    return duplicate_groups


def main():
    parser = argparse.ArgumentParser(description="Collapse duplicate assistant Q&A rows")
    parser.add_argument("--apply", action="store_true", help="Actually modify the database (default is dry-run)")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row

    groups = find_duplicate_groups(conn)

    if not groups:
        print("No duplicate groups found. Nothing to do.")
        conn.close()
        return

    print(f"Found {len(groups)} duplicate group(s):\n")

    collapsed = 0
    deleted_total = 0

    for group in groups:
        oldest = group[0]
        newest = group[-1]
        questions = [e["question"] for e in group]
        ids = [e["id"] for e in group]
        keep_id = oldest["id"]
        delete_ids = [e["id"] for e in group[1:]]

        print(f"  Group: session={oldest['session_id'][:12]}... "
              f"page={oldest['page_type']}:{oldest['page_key']} "
              f"({len(group)} rows, ids={ids})")
        for e in group:
            print(f"    #{e['id']}: {e['question'][:80]}")

        # Synthesize questions
        synthesized = _synthesize_questions(questions)
        print(f"    -> Synthesized: {synthesized[:100]}")
        print(f"    -> Keep #{keep_id}, delete {delete_ids}")

        if args.apply:
            conn.execute(
                "UPDATE assistant_conversations SET question = ?, answer = ? WHERE id = ?",
                (synthesized, newest["answer"], keep_id),
            )
            conn.execute(
                f"DELETE FROM assistant_conversations WHERE id IN ({','.join('?' * len(delete_ids))})",
                delete_ids,
            )
            conn.commit()
            print(f"    APPLIED")

        collapsed += 1
        deleted_total += len(delete_ids)
        print()

    mode = "APPLIED" if args.apply else "DRY RUN"
    print(f"\n{mode}: {collapsed} group(s) collapsed, {deleted_total} row(s) {'deleted' if args.apply else 'would be deleted'}")

    conn.close()


if __name__ == "__main__":
    main()
