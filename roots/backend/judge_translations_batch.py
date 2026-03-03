"""Batch judge pipeline using OpenAI Batch API (50% cheaper).

Compares conventional vs AI word translations and picks the best tooltip gloss,
processing all words in a single batch via gpt-5-nano.

Usage:
    python judge_translations_batch.py prepare [--verses "96:1-5"] [--force]
    python judge_translations_batch.py submit
    python judge_translations_batch.py status
    python judge_translations_batch.py download
    python judge_translations_batch.py run             # all-in-one
    python judge_translations_batch.py run --verses "96:1-5"  # test subset
"""

import argparse
import json
import os
import sys
import time

import requests

from app import get_db
from judge_translations import (
    SYSTEM_PROMPT,
    build_judge_prompt,
    parse_judge_response,
)
from word_meanings_ai import parse_verse_spec

# ── Constants ──────────────────────────────────────────────────────────────

OPENAI_API = "https://api.openai.com/v1"
STATE_FILE = os.path.join(os.path.dirname(__file__), ".judge_batch_state.json")
BATCH_DIR = os.path.join(os.path.dirname(__file__), "batch_files")

DEFAULT_MODEL = "gpt-5-nano"
DEFAULT_TEMPERATURE = 0.2

# OpenAI Files API limit is 200 MB; use 150 MB for safety margin
MAX_UPLOAD_BYTES = 150 * 1024 * 1024

# ── Helpers ────────────────────────────────────────────────────────────────


def _get_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    return key


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_get_api_key()}",
        "Content-Type": "application/json",
    }


def _save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def _load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE) as f:
        return json.load(f)


def _upload_file(path: str) -> str:
    """Upload a single file to OpenAI Files API. Returns file_id."""
    resp = requests.post(
        f"{OPENAI_API}/files",
        headers={"Authorization": f"Bearer {_get_api_key()}"},
        files={"file": open(path, "rb")},
        data={"purpose": "batch"},
        timeout=600,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def _split_jsonl(path: str) -> list[str]:
    """Split a JSONL file into chunks under MAX_UPLOAD_BYTES. Returns list of paths."""
    file_size = os.path.getsize(path)
    if file_size <= MAX_UPLOAD_BYTES:
        return [path]

    base, ext = os.path.splitext(path)
    chunks: list[str] = []
    chunk_idx = 0
    current_size = 0
    current_file = None

    with open(path) as f:
        for line in f:
            line_bytes = len(line.encode("utf-8"))

            if current_file is None or current_size + line_bytes > MAX_UPLOAD_BYTES:
                if current_file:
                    current_file.close()
                chunk_idx += 1
                chunk_path = f"{base}_p{chunk_idx}{ext}"
                chunks.append(chunk_path)
                current_file = open(chunk_path, "w")
                current_size = 0

            current_file.write(line)
            current_size += line_bytes

    if current_file:
        current_file.close()

    return chunks


def _split_and_upload(jsonl_path: str) -> list[dict]:
    """Split a JSONL if needed, upload all chunks. Returns list of batch info dicts."""
    chunks = _split_jsonl(jsonl_path)

    if len(chunks) > 1:
        print(f"  Split into {len(chunks)} chunks (file was "
              f"{os.path.getsize(jsonl_path) / 1024 / 1024:.0f} MB)")

    results: list[dict] = []
    for i, chunk_path in enumerate(chunks):
        count = sum(1 for _ in open(chunk_path))
        suffix = f" chunk {i + 1}/{len(chunks)}" if len(chunks) > 1 else ""
        print(f"  Uploading{suffix} ({count} requests)...")
        file_id = _upload_file(chunk_path)
        print(f"    -> {file_id}")
        results.append({
            "file_id": file_id,
            "batch_id": None,
            "jsonl_path": chunk_path,
            "count": count,
        })

    return results


def _fetch_batch_info(batch_id: str) -> dict:
    """Fetch batch info from OpenAI API."""
    resp = requests.get(
        f"{OPENAI_API}/batches/{batch_id}", headers=_headers(), timeout=30
    )
    resp.raise_for_status()
    return resp.json()


# ── Command: prepare ───────────────────────────────────────────────────────


def cmd_prepare(args):
    """Build judge prompts for all words with AI meanings, write JSONL, upload."""
    os.makedirs(BATCH_DIR, exist_ok=True)

    conn = get_db()
    try:
        # Get all word positions with AI meanings
        if args.verses:
            verse_set = set(parse_verse_spec(args.verses))
        else:
            verse_set = None

        # Fetch all distinct (chapter, verse, word_pos) from ai_word_meanings
        rows = conn.execute(
            "SELECT DISTINCT chapter, verse, word_pos FROM ai_word_meanings "
            "ORDER BY chapter, verse, word_pos"
        ).fetchall()

        candidates = []
        for r in rows:
            ch, v, wp = r["chapter"], r["verse"], r["word_pos"]
            if verse_set and (ch, v) not in verse_set:
                continue
            candidates.append((ch, v, wp))

        print(f"Found {len(candidates)} word positions with AI meanings")

        # Filter out already-judged (unless --force)
        if not args.force:
            judged = conn.execute(
                "SELECT DISTINCT chapter, verse, word_pos FROM ai_word_meanings "
                "WHERE preferred_translation IS NOT NULL"
            ).fetchall()
            judged_set = {(r["chapter"], r["verse"], r["word_pos"]) for r in judged}
            before = len(candidates)
            candidates = [(c, v, w) for c, v, w in candidates if (c, v, w) not in judged_set]
            if before - len(candidates) > 0:
                print(f"Skipping {before - len(candidates)} already-judged words (use --force to redo)")

        if not candidates:
            print("No words to judge — all already done!")
            return

        # Build JSONL
        ts = int(time.time())
        jsonl_path = os.path.join(BATCH_DIR, f"batch_judge_{ts}.jsonl")
        model = args.model

        written = 0
        skipped = 0
        print(f"Generating judge prompts for {len(candidates)} words...")

        with open(jsonl_path, "w") as f:
            for i, (ch, v, wp) in enumerate(candidates):
                prompt = build_judge_prompt(conn, ch, v, wp)
                if prompt is None:
                    skipped += 1
                    continue

                # Strip /no_think for OpenAI
                clean_prompt = prompt.replace(" /no_think", "")
                clean_system = SYSTEM_PROMPT.replace(" /no_think", "")

                body: dict = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": clean_system},
                        {"role": "user", "content": clean_prompt},
                    ],
                }
                # nano doesn't support temperature
                if "nano" not in model:
                    body["temperature"] = args.temperature

                req = {
                    "custom_id": f"{ch}:{v}:{wp}",
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": body,
                }
                f.write(json.dumps(req) + "\n")
                written += 1

                if (i + 1) % 5000 == 0:
                    print(f"  {i + 1}/{len(candidates)} processed...")

        print(f"Wrote {written} requests to {jsonl_path}")
        if skipped:
            print(f"Skipped {skipped} words (identical translations or missing data)")

        # Upload
        print("\nUploading JSONL...")
        all_batches = _split_and_upload(jsonl_path)

        state = {
            "model": model,
            "prepared_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_prompts": written,
            "batches": all_batches,
        }
        if args.verses:
            state["verses"] = args.verses
        _save_state(state)

        print(f"\n{len(all_batches)} file(s) uploaded. Run: python judge_translations_batch.py submit")

    finally:
        conn.close()


# ── Command: submit ────────────────────────────────────────────────────────


def cmd_submit(args):
    """Submit batch jobs for all uploaded files."""
    DELAY_BETWEEN = 10
    MAX_RETRIES = 5

    state = _load_state()
    batches = state.get("batches", [])
    if not batches:
        print("ERROR: No prepared batch found. Run 'prepare' first.")
        sys.exit(1)

    pending = [b for b in batches if not b.get("batch_id")]
    already = [b for b in batches if b.get("batch_id")]

    if not pending:
        if already:
            print(f"All {len(already)} batch(es) already submitted. Use 'status' to check.")
        return

    print(f"{len(pending)} batch(es) to submit ({len(already)} already submitted)...\n")

    submitted = 0
    for i, b in enumerate(pending):
        for attempt in range(MAX_RETRIES):
            print(f"Submitting batch ({b['count']} requests)...")

            file_id = b["file_id"]
            resp = requests.post(
                f"{OPENAI_API}/batches",
                headers=_headers(),
                json={
                    "input_file_id": file_id,
                    "endpoint": "/v1/chat/completions",
                    "completion_window": "24h",
                },
                timeout=60,
            )

            # If file expired, re-upload and retry
            if resp.status_code == 400:
                err_msg = resp.json().get("error", {}).get("message", "")
                if "file" in err_msg.lower() or "invalid" in err_msg.lower():
                    print(f"  File may have expired, re-uploading...")
                    file_id = _upload_file(b["jsonl_path"])
                    b["file_id"] = file_id
                    print(f"  New file_id: {file_id}")
                    resp = requests.post(
                        f"{OPENAI_API}/batches",
                        headers=_headers(),
                        json={
                            "input_file_id": file_id,
                            "endpoint": "/v1/chat/completions",
                            "completion_window": "24h",
                        },
                        timeout=60,
                    )

            if resp.ok:
                batch_data = resp.json()
                b["batch_id"] = batch_data["id"]
                print(f"  Batch: {batch_data['id']} ({batch_data['status']})")
                submitted += 1
                _save_state(state)
                break

            err = resp.json().get("error", {}).get("message", resp.text)
            wait = DELAY_BETWEEN * (2 ** attempt)
            print(f"  Rejected: {err}")
            if attempt < MAX_RETRIES - 1:
                print(f"  Retrying in {wait}s (attempt {attempt + 2}/{MAX_RETRIES})...")
                time.sleep(wait)
            else:
                print(f"  Failed after {MAX_RETRIES} attempts.")

        if i < len(pending) - 1:
            time.sleep(DELAY_BETWEEN)

    state["status"] = "submitted"
    state["submitted_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _save_state(state)

    print(f"\n{submitted} submitted. Check progress: python judge_translations_batch.py status")


# ── Command: status ────────────────────────────────────────────────────────


def cmd_status(args):
    """Check progress of all batch jobs."""
    state = _load_state()
    batches = state.get("batches", [])
    if not batches or not any(b.get("batch_id") for b in batches):
        print("No batch jobs found. Run 'prepare' and 'submit' first.")
        return

    print(f"Model:     {state.get('model', '?')}")
    print(f"Submitted: {state.get('submitted_at', '?')}")
    print(f"Batches:   {len(batches)}")
    print()

    all_done = True
    any_failed = False
    total_completed = 0
    total_failed = 0
    total_requests = 0

    for b in batches:
        bid = b.get("batch_id")
        if not bid:
            print(f"  Not submitted yet")
            all_done = False
            continue

        batch = _fetch_batch_info(bid)
        rc = batch.get("request_counts", {})
        completed = rc.get("completed", 0)
        failed = rc.get("failed", 0)
        total = rc.get("total", 0) or b.get("count", "?")

        total_completed += completed
        total_failed += failed
        if isinstance(total, int):
            total_requests += total

        if batch.get("output_file_id"):
            b["output_file_id"] = batch["output_file_id"]
        if batch.get("error_file_id"):
            b["error_file_id"] = batch["error_file_id"]

        status_str = batch["status"]
        if batch["status"] != "completed":
            all_done = False
        if batch["status"] in ("failed", "expired", "cancelled"):
            any_failed = True

        pct = (completed * 100 // total) if isinstance(total, int) and total > 0 else "?"
        print(f"  {bid}  {status_str:12s}  {completed}/{total} ({pct}%)")

    print(f"\n  Total: {total_completed}/{total_requests} completed, {total_failed} failed")

    if all_done and not any_failed:
        state["status"] = "completed"
        print("\nAll batches complete! Run: python judge_translations_batch.py download")
    elif any_failed:
        state["status"] = "failed"

    _save_state(state)


# ── Command: download ──────────────────────────────────────────────────────


def cmd_download(args):
    """Download results from all batches and store judgments in database."""
    state = _load_state()
    batches = state.get("batches", [])
    if not batches or not any(b.get("batch_id") for b in batches):
        print("No batch jobs found.")
        sys.exit(1)

    os.makedirs(BATCH_DIR, exist_ok=True)

    # Download all result files
    result_files: list[str] = []
    for b in batches:
        bid = b.get("batch_id")
        if not bid:
            continue

        batch = _fetch_batch_info(bid)
        if batch["status"] != "completed":
            rc = batch.get("request_counts", {})
            print(f"  {bid}: not complete ({batch['status']}, "
                  f"{rc.get('completed', 0)}/{rc.get('total', '?')})")
            continue

        output_file_id = batch.get("output_file_id")
        if not output_file_id:
            print(f"  {bid}: no output file")
            continue

        print(f"  Downloading results for {bid}...")
        resp = requests.get(
            f"{OPENAI_API}/files/{output_file_id}/content",
            headers={"Authorization": f"Bearer {_get_api_key()}"},
            timeout=600,
        )
        resp.raise_for_status()

        results_path = os.path.join(BATCH_DIR, f"results_judge_{bid[-8:]}.jsonl")
        with open(results_path, "wb") as f:
            f.write(resp.content)
        result_files.append(results_path)

        # Download errors if any
        error_file_id = batch.get("error_file_id")
        if error_file_id:
            try:
                resp_err = requests.get(
                    f"{OPENAI_API}/files/{error_file_id}/content",
                    headers={"Authorization": f"Bearer {_get_api_key()}"},
                    timeout=300,
                )
                if resp_err.ok and resp_err.content.strip():
                    err_path = os.path.join(BATCH_DIR, f"errors_judge_{bid[-8:]}.jsonl")
                    with open(err_path, "wb") as f:
                        f.write(resp_err.content)
                    print(f"    Errors saved to {err_path}")
            except Exception:
                pass

    if not result_files:
        print("No results ready to download.")
        return

    # Parse and store judgments
    print(f"\nStoring judgments from {len(result_files)} result file(s)...")
    conn = get_db()
    try:
        stored = 0
        skipped = 0
        errors = 0
        source_counts = {"conventional": 0, "ai": 0, "judge": 0}
        source_map = {"A": "conventional", "B": "ai", "C": "judge"}

        for results_path in result_files:
            with open(results_path) as f:
                for line in f:
                    result = json.loads(line.strip())
                    custom_id = result["custom_id"]

                    # Extract response content
                    response = result.get("response", {})
                    if response.get("status_code") != 200:
                        errors += 1
                        continue

                    choices = response.get("body", {}).get("choices", [])
                    if not choices:
                        errors += 1
                        continue

                    raw = choices[0].get("message", {}).get("content", "")
                    if not raw:
                        errors += 1
                        continue

                    # Parse the judge response
                    parsed = parse_judge_response(raw)
                    if not parsed:
                        print(f"    {custom_id} — could not parse response")
                        errors += 1
                        continue

                    # Parse custom_id -> chapter:verse:word_pos
                    parts = custom_id.split(":")
                    ch, v, wp = int(parts[0]), int(parts[1]), int(parts[2])

                    preferred_source = source_map.get(parsed["choice"], "judge")
                    preferred_translation = parsed["translation"]

                    # Update the most recent ai_word_meanings row
                    cursor = conn.execute(
                        "UPDATE ai_word_meanings "
                        "SET preferred_translation = ?, preferred_source = ? "
                        "WHERE id = ("
                        "  SELECT id FROM ai_word_meanings "
                        "  WHERE chapter = ? AND verse = ? AND word_pos = ? "
                        "  ORDER BY created_at DESC LIMIT 1"
                        ")",
                        (preferred_translation, preferred_source, ch, v, wp),
                    )

                    if cursor.rowcount > 0:
                        stored += 1
                        source_counts[preferred_source] += 1
                    else:
                        skipped += 1

                    if stored % 500 == 0 and stored > 0:
                        conn.commit()
                        if stored % 5000 == 0:
                            print(f"    {stored} judgments stored...")

        conn.commit()

        print(f"\nDone: {stored} stored, {skipped} skipped, {errors} errors")
        print(f"  Conventional (A): {source_counts['conventional']}")
        print(f"  AI (B):           {source_counts['ai']}")
        print(f"  Judge alt (C):    {source_counts['judge']}")

        state["status"] = "downloaded"
        state["stored"] = stored
        state["source_counts"] = source_counts
        state["downloaded_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        _save_state(state)

    finally:
        conn.close()


# ── Command: run ───────────────────────────────────────────────────────────


def cmd_run(args):
    """Full pipeline: prepare -> submit -> poll -> download."""
    cmd_prepare(args)
    cmd_submit(args)

    print("\nPolling for completion (Ctrl+C to stop — resume with 'status' / 'download')...")
    state = _load_state()
    batches = state.get("batches", [])
    poll_interval = 60

    while True:
        try:
            time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("\nStopped polling. Resume with:")
            print("  python judge_translations_batch.py status")
            print("  python judge_translations_batch.py download")
            return

        all_done = True
        any_failed = False
        total_completed = 0
        total_requests = 0

        for b in batches:
            bid = b.get("batch_id")
            if not bid:
                all_done = False
                continue

            try:
                batch = _fetch_batch_info(bid)
            except Exception as e:
                print(f"  [{time.strftime('%H:%M:%S')}] check failed ({e})")
                all_done = False
                continue

            rc = batch.get("request_counts", {})
            completed = rc.get("completed", 0)
            failed = rc.get("failed", 0)
            total = rc.get("total", 0) or b.get("count", "?")

            total_completed += completed
            if isinstance(total, int):
                total_requests += total

            pct = (completed * 100 // total) if isinstance(total, int) and total > 0 else "?"
            print(f"  [{time.strftime('%H:%M:%S')}] {batch['status']:12s} "
                  f"{completed}/{total} ({pct}%) done, {failed} failed")

            if batch["status"] != "completed":
                all_done = False
            if batch["status"] in ("failed", "expired", "cancelled"):
                any_failed = True

            if batch.get("output_file_id"):
                b["output_file_id"] = batch["output_file_id"]

        _save_state(state)

        if all_done and not any_failed:
            state["status"] = "completed"
            _save_state(state)
            print("\nAll batches complete! Downloading results...")
            cmd_download(args)
            return

        if any_failed and all_done:
            print("\nSome batches failed. Downloading available results...")
            cmd_download(args)
            return

        poll_interval = min(poll_interval + 30, 300)


# ── CLI ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Batch Judge — OpenAI Batch API"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # prepare
    p = sub.add_parser("prepare", help="Build judge prompts, upload JSONL")
    p.add_argument("--verses", help="Verse spec, e.g. '96:1-5' (default: all with AI meanings)")
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"Model (default: {DEFAULT_MODEL})")
    p.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    p.add_argument("--force", action="store_true", help="Re-judge already-judged words")

    # submit
    sub.add_parser("submit", help="Submit prepared batch job to OpenAI")

    # status
    sub.add_parser("status", help="Check batch job progress")

    # download
    sub.add_parser("download", help="Download results and store judgments in DB")

    # run (all-in-one)
    p = sub.add_parser("run", help="Full pipeline: prepare + submit + poll + download")
    p.add_argument("--verses", help="Verse spec (default: all with AI meanings)")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    p.add_argument("--force", action="store_true", help="Re-judge already-judged words")

    args = parser.parse_args()

    {
        "prepare": cmd_prepare,
        "submit": cmd_submit,
        "status": cmd_status,
        "download": cmd_download,
        "run": cmd_run,
    }[args.command](args)


if __name__ == "__main__":
    main()
