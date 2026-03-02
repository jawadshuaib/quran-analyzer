"""OpenAI Batch API for Quranic verse translation — 50% cheaper than streaming.

Workflow:
  1. prepare  — Generate prompts for all verses, write JSONL, upload to OpenAI
  2. submit   — Create the batch job
  3. status   — Check batch job progress
  4. download — Download results and store in database

Usage:
    # Full pipeline (prepare + submit):
    python translate_ai_batch.py prepare --model gpt-5.1 --config "gpt5.1-batch-v2"
    python translate_ai_batch.py submit

    # Check progress:
    python translate_ai_batch.py status

    # Download and store results when done:
    python translate_ai_batch.py download

    # Or do it all at once (prepare, submit, poll, download):
    python translate_ai_batch.py run --model gpt-5.1 --config "gpt5.1-batch-v2"

    # Translate only specific verses:
    python translate_ai_batch.py prepare --verses "1:1-7,2:1-5" --model gpt-5.1

    # Re-translate verses already in DB (normally auto-skipped):
    python translate_ai_batch.py prepare --model gpt-5.1 --config "gpt5.1-batch-v2" --include-existing
"""

import argparse
import json
import os
import sys
import time

import requests

from app import get_db
from translate_ai import (
    SYSTEM_PROMPT,
    build_prompt,
    get_or_create_config,
    parse_response,
    parse_verse_spec,
)

OPENAI_API = "https://api.openai.com/v1"
STATE_FILE = os.path.join(os.path.dirname(__file__), ".batch_state.json")
BATCH_DIR = os.path.join(os.path.dirname(__file__), "batch_files")


def get_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    return key


def headers() -> dict:
    return {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE) as f:
        return json.load(f)


def get_all_verses(conn) -> list[tuple[int, int]]:
    """Get all verse references in the Quran."""
    rows = conn.execute(
        "SELECT chapter, verse FROM verses ORDER BY chapter, verse"
    ).fetchall()
    return [(r["chapter"], r["verse"]) for r in rows]


def get_existing_verses(conn, config_id: int) -> set[tuple[int, int]]:
    """Get verses already translated for this config."""
    rows = conn.execute(
        "SELECT chapter, verse FROM ai_translations WHERE config_id = ?",
        (config_id,),
    ).fetchall()
    return {(r["chapter"], r["verse"]) for r in rows}


# ── Command: prepare ──


def _check_active_batches(config: str) -> bool:
    """Check OpenAI for any active batches matching this config. Returns True if one is active."""
    state = load_state()
    if "batch_id" not in state:
        return False
    if state.get("config") != config:
        return False
    if state.get("status") in ("completed", "failed", "expired", "cancelled", "downloaded"):
        return False

    # Live-check with OpenAI in case state file is stale
    try:
        resp = requests.get(
            f"{OPENAI_API}/batches/{state['batch_id']}",
            headers=headers(),
            timeout=30,
        )
        if resp.ok:
            live_status = resp.json().get("status")
            state["status"] = live_status
            save_state(state)
            if live_status not in ("completed", "failed", "expired", "cancelled"):
                return True
    except Exception:
        pass
    return False


def cmd_prepare(args):
    """Generate prompts for all verses, write JSONL, upload to OpenAI."""
    os.makedirs(BATCH_DIR, exist_ok=True)

    # Guard: block if there's already an in-flight batch for this config
    if _check_active_batches(args.config):
        state = load_state()
        print(f"ERROR: Batch {state['batch_id']} is already in-flight for config '{args.config}' (status: {state['status']})")
        print("Use 'status' to check progress, or 'download' when complete.")
        print("To start over, delete .batch_state.json first.")
        sys.exit(1)

    conn = get_db()
    try:
        config_id = get_or_create_config(conn, args.config, args.model)

        # Determine which verses to process
        if args.verses:
            verses = parse_verse_spec(args.verses)
        else:
            verses = get_all_verses(conn)

        # Deduplicate verse list (e.g. overlapping ranges like "1:1-7,1:5-10")
        seen = set()
        unique_verses = []
        for s, a in verses:
            if (s, a) not in seen:
                seen.add((s, a))
                unique_verses.append((s, a))
        if len(verses) != len(unique_verses):
            print(f"Removed {len(verses) - len(unique_verses)} duplicate verse(s) from input")
        verses = unique_verses

        # Skip verses already in DB (default behavior; use --include-existing to override)
        if not args.include_existing:
            existing = get_existing_verses(conn, config_id)
            before = len(verses)
            verses = [(s, a) for s, a in verses if (s, a) not in existing]
            skipped = before - len(verses)
            if skipped:
                print(f"Skipping {skipped} already-translated verses (use --include-existing to override)")

        if not verses:
            print("No verses to process — all already translated!")
            return

        print(f"Generating prompts for {len(verses)} verses...")

        # Build JSONL
        jsonl_path = os.path.join(BATCH_DIR, f"batch_{args.config}_{int(time.time())}.jsonl")
        count = 0
        with open(jsonl_path, "w") as f:
            for i, (surah, ayah) in enumerate(verses):
                try:
                    prompt = build_prompt(conn, surah, ayah, config_id)
                except ValueError as e:
                    print(f"  Skipping {surah}:{ayah}: {e}")
                    continue

                request_obj = {
                    "custom_id": f"{surah}:{ayah}",
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": args.model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt.replace(" /no_think", "")},
                        ],
                        "temperature": args.temperature,
                    },
                }
                f.write(json.dumps(request_obj) + "\n")
                count += 1

                if (i + 1) % 500 == 0:
                    print(f"  {i + 1}/{len(verses)} prompts generated...")

        print(f"Wrote {count} requests to {jsonl_path}")

        # Upload to OpenAI
        print("Uploading to OpenAI Files API...")
        resp = requests.post(
            f"{OPENAI_API}/files",
            headers={"Authorization": f"Bearer {get_api_key()}"},
            files={"file": open(jsonl_path, "rb")},
            data={"purpose": "batch"},
            timeout=300,
        )
        resp.raise_for_status()
        file_data = resp.json()
        file_id = file_data["id"]
        print(f"Uploaded: file_id = {file_id}")

        # Save state
        save_state({
            "file_id": file_id,
            "jsonl_path": jsonl_path,
            "model": args.model,
            "config": args.config,
            "config_id": config_id,
            "verse_count": count,
            "prepared_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

        print(f"\nReady! Run: python translate_ai_batch.py submit")

    finally:
        conn.close()


# ── Command: submit ──


def cmd_submit(args):
    """Create the batch job from the uploaded file."""
    state = load_state()
    if "file_id" not in state:
        print("ERROR: No prepared batch found. Run 'prepare' first.")
        sys.exit(1)

    if "batch_id" in state and state.get("status") not in ("completed", "failed", "expired", "cancelled"):
        print(f"WARNING: Batch {state['batch_id']} already submitted (status: {state.get('status', 'unknown')})")
        print("Use 'status' to check progress, or delete .batch_state.json to start over.")
        return

    print(f"Submitting batch job for {state['verse_count']} verses...")
    resp = requests.post(
        f"{OPENAI_API}/batches",
        headers=headers(),
        json={
            "input_file_id": state["file_id"],
            "endpoint": "/v1/chat/completions",
            "completion_window": "24h",
        },
        timeout=60,
    )
    resp.raise_for_status()
    batch_data = resp.json()
    batch_id = batch_data["id"]

    state["batch_id"] = batch_id
    state["status"] = batch_data["status"]
    state["submitted_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_state(state)

    print(f"Batch submitted: {batch_id}")
    print(f"Status: {batch_data['status']}")
    print(f"\nCheck progress: python translate_ai_batch.py status")


# ── Command: status ──


def cmd_status(args):
    """Check batch job progress."""
    state = load_state()
    if "batch_id" not in state:
        print("No batch job found. Run 'prepare' and 'submit' first.")
        return

    resp = requests.get(
        f"{OPENAI_API}/batches/{state['batch_id']}",
        headers=headers(),
        timeout=30,
    )
    resp.raise_for_status()
    batch = resp.json()

    state["status"] = batch["status"]
    if batch.get("output_file_id"):
        state["output_file_id"] = batch["output_file_id"]
    if batch.get("error_file_id"):
        state["error_file_id"] = batch["error_file_id"]
    save_state(state)

    completed = batch.get("request_counts", {}).get("completed", 0)
    failed = batch.get("request_counts", {}).get("failed", 0)
    total = batch.get("request_counts", {}).get("total", state.get("verse_count", "?"))

    print(f"Batch:     {state['batch_id']}")
    print(f"Model:     {state.get('model', '?')}")
    print(f"Config:    {state.get('config', '?')}")
    print(f"Status:    {batch['status']}")
    print(f"Progress:  {completed}/{total} completed, {failed} failed")
    print(f"Submitted: {state.get('submitted_at', '?')}")

    if batch["status"] == "completed":
        print(f"\nBatch complete! Run: python translate_ai_batch.py download")
    elif batch["status"] in ("failed", "expired", "cancelled"):
        print(f"\nBatch {batch['status']}.")
        if batch.get("errors"):
            for err in batch["errors"].get("data", []):
                print(f"  Error: {err.get('message', err)}")


# ── Command: download ──


def cmd_download(args):
    """Download results and store in database."""
    state = load_state()
    if "batch_id" not in state:
        print("No batch job found.")
        sys.exit(1)

    # Check status first
    resp = requests.get(
        f"{OPENAI_API}/batches/{state['batch_id']}",
        headers=headers(),
        timeout=30,
    )
    resp.raise_for_status()
    batch = resp.json()

    if batch["status"] != "completed":
        print(f"Batch not yet complete. Status: {batch['status']}")
        completed = batch.get("request_counts", {}).get("completed", 0)
        total = batch.get("request_counts", {}).get("total", "?")
        print(f"Progress: {completed}/{total}")
        return

    output_file_id = batch.get("output_file_id")
    if not output_file_id:
        print("ERROR: No output file available")
        sys.exit(1)

    # Download results
    print("Downloading results...")
    resp = requests.get(
        f"{OPENAI_API}/files/{output_file_id}/content",
        headers={"Authorization": f"Bearer {get_api_key()}"},
        timeout=300,
    )
    resp.raise_for_status()

    results_path = os.path.join(BATCH_DIR, f"results_{state['batch_id']}.jsonl")
    with open(results_path, "wb") as f:
        f.write(resp.content)
    print(f"Saved results to {results_path}")

    # Download errors if any
    error_file_id = batch.get("error_file_id")
    if error_file_id:
        resp_err = requests.get(
            f"{OPENAI_API}/files/{error_file_id}/content",
            headers={"Authorization": f"Bearer {get_api_key()}"},
            timeout=300,
        )
        if resp_err.ok and resp_err.content.strip():
            errors_path = os.path.join(BATCH_DIR, f"errors_{state['batch_id']}.jsonl")
            with open(errors_path, "wb") as f:
                f.write(resp_err.content)
            print(f"Saved errors to {errors_path}")

    # Parse and store in DB
    print("Storing translations in database...")
    conn = get_db()
    try:
        config_id = get_or_create_config(conn, state["config"], state["model"])

        stored = 0
        skipped = 0
        errors = 0
        seen_in_results = set()

        with open(results_path) as f:
            for line in f:
                result = json.loads(line.strip())
                custom_id = result["custom_id"]

                # Guard: skip duplicate custom_ids within the results file
                if custom_id in seen_in_results:
                    print(f"  {custom_id} — duplicate in results file, skipping")
                    skipped += 1
                    continue
                seen_in_results.add(custom_id)

                # Parse surah:ayah from custom_id
                parts = custom_id.split(":")
                surah, ayah = int(parts[0]), int(parts[1])

                # Check for API error
                response = result.get("response", {})
                if response.get("status_code") != 200:
                    print(f"  {surah}:{ayah} — API error: {response.get('status_code')}")
                    errors += 1
                    continue

                # Extract content
                body = response.get("body", {})
                choices = body.get("choices", [])
                if not choices:
                    print(f"  {surah}:{ayah} — no choices in response")
                    errors += 1
                    continue

                raw_response = choices[0].get("message", {}).get("content", "")
                if not raw_response:
                    print(f"  {surah}:{ayah} — empty response")
                    errors += 1
                    continue

                # Parse translation + notes
                translation, notes = parse_response(raw_response)
                if not translation:
                    print(f"  {surah}:{ayah} — could not parse translation")
                    errors += 1
                    continue

                # Check if already exists
                existing = conn.execute(
                    "SELECT id FROM ai_translations WHERE chapter = ? AND verse = ? AND config_id = ?",
                    (surah, ayah, config_id),
                ).fetchone()

                if existing and not args.force:
                    skipped += 1
                    continue

                if existing:
                    conn.execute(
                        "DELETE FROM ai_translations WHERE chapter = ? AND verse = ? AND config_id = ?",
                        (surah, ayah, config_id),
                    )

                # Rebuild the prompt for storage (or use empty string to save space)
                prompt_text = ""
                if args.store_prompts:
                    try:
                        prompt_text = build_prompt(conn, surah, ayah, config_id)
                    except Exception:
                        prompt_text = ""

                conn.execute(
                    "INSERT INTO ai_translations "
                    "(chapter, verse, config_id, translation_text, departure_notes, "
                    " full_prompt, raw_response, model_response_time_ms) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (surah, ayah, config_id, translation, notes or None,
                     prompt_text, raw_response, 0),
                )
                stored += 1

                if stored % 500 == 0:
                    conn.commit()
                    print(f"  {stored} translations stored...")

        conn.commit()
        print(f"\nDone: {stored} stored, {skipped} skipped, {errors} errors")

        state["status"] = "downloaded"
        state["stored"] = stored
        state["downloaded_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        save_state(state)

    finally:
        conn.close()


# ── Command: run ──


def cmd_run(args):
    """Full pipeline: prepare, submit, poll, download."""
    # Prepare
    cmd_prepare(args)

    # Submit
    cmd_submit(args)

    # Poll
    print("\nPolling for completion (Ctrl+C to stop — you can resume with 'status' / 'download')...")
    state = load_state()
    poll_interval = 60  # start at 60s

    while True:
        try:
            time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("\nStopped polling. Resume with:")
            print("  python translate_ai_batch.py status")
            print("  python translate_ai_batch.py download")
            return

        resp = requests.get(
            f"{OPENAI_API}/batches/{state['batch_id']}",
            headers=headers(),
            timeout=30,
        )
        resp.raise_for_status()
        batch = resp.json()

        completed = batch.get("request_counts", {}).get("completed", 0)
        failed = batch.get("request_counts", {}).get("failed", 0)
        total = batch.get("request_counts", {}).get("total", "?")
        pct = (completed * 100 // total) if isinstance(total, int) and total > 0 else "?"

        print(f"  [{time.strftime('%H:%M:%S')}] {batch['status']} — {completed}/{total} ({pct}%) done, {failed} failed")

        if batch["status"] == "completed":
            state["output_file_id"] = batch.get("output_file_id")
            state["error_file_id"] = batch.get("error_file_id")
            state["status"] = "completed"
            save_state(state)
            print("\nBatch complete! Downloading results...")
            cmd_download(args)
            return

        if batch["status"] in ("failed", "expired", "cancelled"):
            print(f"\nBatch {batch['status']}.")
            if batch.get("errors"):
                for err in batch["errors"].get("data", []):
                    print(f"  Error: {err.get('message', err)}")
            return

        # Increase poll interval gradually (max 5 min)
        poll_interval = min(poll_interval + 30, 300)


def main():
    parser = argparse.ArgumentParser(description="OpenAI Batch API for Quranic Translation")
    sub = parser.add_subparsers(dest="command", required=True)

    # prepare
    p_prepare = sub.add_parser("prepare", help="Generate prompts and upload JSONL")
    p_prepare.add_argument("--verses", help="Verse spec (default: all Quran)")
    p_prepare.add_argument("--model", default="gpt-5.1", help="OpenAI model (default: gpt-5.1)")
    p_prepare.add_argument("--config", default="gpt5.1-batch-v2", help="Config name")
    p_prepare.add_argument("--temperature", type=float, default=0.3)
    p_prepare.add_argument("--include-existing", action="store_true", help="Include verses already in DB (default: skip them)")

    # submit
    sub.add_parser("submit", help="Submit the prepared batch job")

    # status
    sub.add_parser("status", help="Check batch job progress")

    # download
    p_download = sub.add_parser("download", help="Download results and store in DB")
    p_download.add_argument("--force", action="store_true", help="Overwrite existing translations")
    p_download.add_argument("--store-prompts", action="store_true", help="Store full prompts (uses more DB space)")

    # run (all-in-one)
    p_run = sub.add_parser("run", help="Full pipeline: prepare + submit + poll + download")
    p_run.add_argument("--verses", help="Verse spec (default: all Quran)")
    p_run.add_argument("--model", default="gpt-5.1", help="OpenAI model (default: gpt-5.1)")
    p_run.add_argument("--config", default="gpt5.1-batch-v2", help="Config name")
    p_run.add_argument("--temperature", type=float, default=0.3)
    p_run.add_argument("--include-existing", action="store_true", help="Include verses already in DB (default: skip them)")
    p_run.add_argument("--force", action="store_true", help="Overwrite existing translations on download")
    p_run.add_argument("--store-prompts", action="store_true")

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
