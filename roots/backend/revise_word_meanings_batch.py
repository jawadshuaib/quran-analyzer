"""Batch-mode word-meanings revisor — half-cost equivalent of
revise_word_meanings.py.

Same revision logic; same backup columns; same prompt. The difference
is the API path: this script bundles every pending entry into a single
Anthropic Message Batch (50% off, async). State is persisted to /tmp
so the script can be interrupted and resumed.

Usage:
    python revise_word_meanings_batch.py --hard-cases-only
    python revise_word_meanings_batch.py --all-surveyed
    python revise_word_meanings_batch.py --status     # check pending batch
    python revise_word_meanings_batch.py --reset      # cancel local state

The script does:
  1. Collect pending entries (same logic as the synchronous script).
  2. Build an Anthropic batch payload — one request per entry,
     custom_id = "wm_<row_id>" so we can route results back.
  3. Submit (or skip if a batch is already in flight per saved state).
  4. Poll every 30 s until the batch ends.
  5. Stream results, parse each, and write back to ai_word_meanings.

Re-running before the batch ends just continues polling. Re-running
after results have been processed clears the state so the next call
treats it as a fresh job.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from typing import Any

from app import get_db, _get_claude_api_key
from revise_word_meanings import (
    SURVEYED_ROOTS,
    SYSTEM_PROMPT,
    build_prompt,
    collect_targets,
    load_canonical_index,
    load_hard_cases_index,
    parse_response,
)
from anthropic_batch import (
    submit_batch,
    wait_for_batch,
    fetch_results,
    load_batch_state,
    save_batch_state,
    clear_batch_state,
    get_batch_status,
)

DEFAULT_MODEL = "claude-sonnet-4-6"
LABEL_PREFIX = "word_meanings"


def label_for(mode: str) -> str:
    return f"{LABEL_PREFIX}_{mode}"


def build_request(
    row: dict,
    hc: dict | None,
    canon: dict,
    model: str,
) -> dict:
    user = build_prompt(row, hc, canon)
    return {
        "custom_id": f"wm_{row['id']}",
        "params": {
            "model": model,
            "max_tokens": 2000,
            "temperature": 0.2,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user}],
        },
    }


def apply_result_to_db(conn, row_id: int, result: dict) -> str:
    """Apply one batch result to the corresponding ai_word_meanings row.
    Returns 'revised' / 'errored' / 'parse-error'."""
    rtype = result.get("type")
    if rtype != "succeeded":
        return f"failed-{rtype}"
    message = result.get("message") or {}
    text = "".join(
        b.get("text", "") for b in message.get("content", [])
        if b.get("type") == "text"
    )
    try:
        verdict = parse_response(text)
    except Exception:
        return "parse-error"

    new_short = (verdict.get("meaning_short") or "").strip()
    new_detailed = (verdict.get("meaning_detailed") or "").strip()
    new_preferred = (verdict.get("preferred_translation") or "").strip()
    if not (new_short and new_detailed and new_preferred):
        return "missing-fields"

    # Save originals on first revision
    cur = conn.execute(
        "SELECT meaning_short, meaning_detailed, preferred_translation, "
        "       meaning_short_original "
        "FROM ai_word_meanings WHERE id = ?",
        (row_id,),
    ).fetchone()
    if not cur:
        return "row-missing"
    if not cur["meaning_short_original"]:
        conn.execute(
            "UPDATE ai_word_meanings SET "
            "  meaning_short_original = ?, "
            "  meaning_detailed_original = ?, "
            "  preferred_translation_original = ? "
            "WHERE id = ?",
            (cur["meaning_short"], cur["meaning_detailed"],
             cur["preferred_translation"], row_id),
        )

    conn.execute(
        "UPDATE ai_word_meanings SET "
        "  meaning_short = ?, meaning_detailed = ?, "
        "  preferred_translation = ? "
        "WHERE id = ?",
        (new_short, new_detailed, new_preferred, row_id),
    )
    conn.commit()
    return "revised"


def parse_verse_arg(spec: str) -> tuple[int, int] | None:
    if not spec:
        return None
    m = re.match(r"^(\d+):(\d+)$", spec.strip())
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--hard-cases-only", action="store_true")
    p.add_argument("--all-surveyed", action="store_true")
    p.add_argument("--verse", help="limit to one verse 'X:Y'")
    p.add_argument("--limit", type=int)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--api-key")
    p.add_argument("--status", action="store_true",
                   help="check the in-flight batch's status (no submit)")
    p.add_argument("--reset", action="store_true",
                   help="discard saved batch state for the chosen mode")
    p.add_argument("--force", action="store_true",
                   help="re-submit even if a previous batch was processed")
    args = p.parse_args()

    api_key = args.api_key or _get_claude_api_key()
    if not api_key:
        print("ERROR: no CLAUDE_API_KEY", file=sys.stderr)
        return 1

    if args.hard_cases_only:
        mode = "hard-cases-only"
    elif args.all_surveyed:
        mode = "all-surveyed"
    else:
        print("ERROR: pass --hard-cases-only or --all-surveyed", file=sys.stderr)
        return 1

    label = label_for(mode)

    if args.reset:
        clear_batch_state(label)
        print(f"Cleared local batch state for '{label}'.")
        return 0

    state = load_batch_state(label)

    if args.status:
        if not state:
            print(f"No saved batch for '{label}'.")
            return 0
        info = get_batch_status(api_key, state["batch_id"])
        print(json.dumps({
            "batch_id": state["batch_id"],
            "processing_status": info.get("processing_status"),
            "request_counts": info.get("request_counts"),
            "ended_at": info.get("ended_at"),
            "results_url": info.get("results_url"),
        }, indent=2))
        return 0

    conn = get_db()
    conn.row_factory = sqlite3.Row

    # ---- Submit phase ----
    if not state or args.force:
        verse_filter = parse_verse_arg(args.verse) if args.verse else None
        rows = collect_targets(conn, mode, verse_filter, args.force)
        if args.limit:
            rows = rows[: args.limit]
        if not rows:
            print(f"Nothing pending in mode '{mode}' (already revised or empty).")
            return 0

        hc_index = load_hard_cases_index(conn)
        canon_index = load_canonical_index(conn)

        requests_list = []
        for row in rows:
            row_d = dict(row)
            canon = canon_index.get(row_d["root_buckwalter"])
            if not canon:
                continue
            hc = hc_index.get((row_d["root_buckwalter"], row_d["chapter"], row_d["verse"]))
            requests_list.append(build_request(row_d, hc, canon, args.model))

        print(f"Submitting batch ({len(requests_list)} requests, mode={mode})…")
        batch_id = submit_batch(api_key, requests_list, label)
        print(f"  batch_id: {batch_id}")
        state = load_batch_state(label)

    # ---- Wait phase ----
    print(f"Polling batch {state['batch_id']} every 30 s…")
    info = wait_for_batch(api_key, state["batch_id"], poll_every=30)
    results_url = info.get("results_url")
    if not results_url:
        print("ERROR: batch ended without results_url:", json.dumps(info)[:400],
              file=sys.stderr)
        return 2

    # ---- Apply phase ----
    print("Streaming results…")
    stats: dict[str, int] = {}
    for record in fetch_results(api_key, results_url):
        cid = record.get("custom_id") or ""
        if not cid.startswith("wm_"):
            continue
        try:
            row_id = int(cid.split("_", 1)[1])
        except ValueError:
            continue
        result = record.get("result") or {}
        outcome = apply_result_to_db(conn, row_id, result)
        stats[outcome] = stats.get(outcome, 0) + 1

    print("\n=== Apply summary ===")
    for k, v in sorted(stats.items(), key=lambda kv: -kv[1]):
        print(f"  {k}: {v}")

    # Done — clear state so a re-run starts fresh
    clear_batch_state(label)
    print(f"\nCleared batch state for '{label}'. Done.")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
