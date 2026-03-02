"""Tiered batch word-meanings pipeline using OpenAI Batch API (50% cheaper).

Three tiers based on Zipf's law and POS classification:
  Tier 1: Stable/function lemmas (freq >= threshold & stable POS)
          — one prompt per unique lemma via gpt-5.1, replicated to all occurrences
  Tier 2: Content lemmas (freq >= threshold, non-stable POS)
          — per-occurrence via nano
  Tier 3: Rare lemmas (freq < threshold)
          — per-occurrence via gpt-5.1

Large JSONL files are automatically split into chunks under 150 MB for upload.

Usage:
    python word_meanings_ai_batch.py prepare [--config word-v2-batch] [--freq-threshold 5]
    python word_meanings_ai_batch.py submit
    python word_meanings_ai_batch.py status
    python word_meanings_ai_batch.py download [--force]
    python word_meanings_ai_batch.py run  # all-in-one

    # Test on a small verse range first:
    python word_meanings_ai_batch.py prepare --verses "2:19-20"
"""

import argparse
import json
import os
import sys
import time

import requests

from app import get_db
from word_meanings_ai import (
    SYSTEM_PROMPT,
    build_word_prompt,
    parse_response,
    get_or_create_config,
    _build_lemma_freq,
    get_lemma_frequency,
    parse_verse_spec,
)

# ── Constants ──────────────────────────────────────────────────────────────

OPENAI_API = "https://api.openai.com/v1"
STATE_FILE = os.path.join(os.path.dirname(__file__), ".word_batch_state.json")
BATCH_DIR = os.path.join(os.path.dirname(__file__), "batch_files")

DEFAULT_NANO_MODEL = "gpt-5-nano"
DEFAULT_SMART_MODEL = "gpt-5.1"
DEFAULT_CONFIG = "word-v2-batch"
DEFAULT_FREQ_THRESHOLD = 5

# OpenAI Files API limit is 200 MB; use 150 MB for safety margin
MAX_UPLOAD_BYTES = 150 * 1024 * 1024

STABLE_POS = {
    "Preposition",
    "Conjunction",
    "Subordinating Conjunction",
    "Negative Particle",
    "Accusative Particle",
    "Preventive Particle",
    "Prohibition Particle",
    "Certainty Particle",
    "Conditional",
    "Amendment Particle",
    "Answer Particle",
    "Aversion Particle",
    "Exceptive Particle",
    "Exhortation Particle",
    "Explanation Particle",
    "Future Particle",
    "Inceptive Particle",
    "Inceptive lam",
    "Interrogative Particle",
    "Restriction Particle",
    "Retraction Particle",
    "Surprise Particle",
    "SUP",
    "Pronoun",
    "Demonstrative",
    "Relative Pronoun",
    "Location Adverb",
    "Time Adverb",
    "Proper Noun",
}

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


# ── File upload helpers (chunked) ──────────────────────────────────────────


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


def _split_and_upload(jsonl_path: str, label: str) -> list[dict]:
    """Split a JSONL if needed, upload all chunks. Returns list of batch info dicts."""
    chunks = _split_jsonl(jsonl_path)

    if len(chunks) > 1:
        print(f"  Split into {len(chunks)} chunks (file was "
              f"{os.path.getsize(jsonl_path) / 1024 / 1024:.0f} MB)")

    results: list[dict] = []
    for i, chunk_path in enumerate(chunks):
        count = sum(1 for _ in open(chunk_path))
        suffix = f" chunk {i + 1}/{len(chunks)}" if len(chunks) > 1 else ""
        print(f"  Uploading {label}{suffix} ({count} requests)...")
        file_id = _upload_file(chunk_path)
        print(f"    -> {file_id}")
        results.append({
            "label": label,
            "file_id": file_id,
            "batch_id": None,
            "jsonl_path": chunk_path,
            "count": count,
        })

    return results


# ── Classification helpers ─────────────────────────────────────────────────


def _build_lemma_pos_map(conn) -> dict[str, str]:
    """Build lemma_bw -> dominant POS (most frequent non-prefix/suffix POS)."""
    rows = conn.execute(
        "SELECT lemma_buckwalter, pos, COUNT(*) as cnt "
        "FROM morphology "
        "WHERE lemma_buckwalter IS NOT NULL AND lemma_buckwalter != '' "
        "AND pos NOT IN ('Prefix', 'Suffix') "
        "GROUP BY lemma_buckwalter, pos "
        "ORDER BY lemma_buckwalter, cnt DESC"
    ).fetchall()
    pos_map: dict[str, str] = {}
    for row in rows:
        lemma = row["lemma_buckwalter"]
        if lemma not in pos_map:
            pos_map[lemma] = row["pos"]
    return pos_map


def classify_word(freq: int, dominant_pos: str, freq_threshold: int = DEFAULT_FREQ_THRESHOLD) -> int:
    """Return tier 1, 2, or 3."""
    if freq >= freq_threshold and dominant_pos in STABLE_POS:
        return 1
    elif freq >= freq_threshold:
        return 2
    else:
        return 3


def _get_content_words(conn, verse_set: set | None = None) -> list[tuple[int, int, int, str]]:
    """Return [(ch, v, wp, lemma_bw), ...] for all content words in Quran order."""
    rows = conn.execute(
        "SELECT chapter, verse, word_pos, segment, "
        "       lemma_buckwalter, root_buckwalter, pos "
        "FROM morphology "
        "ORDER BY chapter, verse, word_pos, segment"
    ).fetchall()

    result: list[tuple[int, int, int, str]] = []
    prev_key: tuple | None = None
    lemma_bw: str | None = None
    has_content = False

    def _emit():
        if prev_key and has_content and lemma_bw:
            if verse_set is None or (prev_key[0], prev_key[1]) in verse_set:
                result.append((prev_key[0], prev_key[1], prev_key[2], lemma_bw))

    for row in rows:
        key = (row["chapter"], row["verse"], row["word_pos"])
        if key != prev_key:
            _emit()
            prev_key = key
            lemma_bw = None
            has_content = False

        if (
            (row["root_buckwalter"] or row["lemma_buckwalter"])
            and row["pos"] not in ("Prefix", "Suffix", None)
        ):
            has_content = True
            if not lemma_bw and row["lemma_buckwalter"]:
                lemma_bw = row["lemma_buckwalter"]

    _emit()
    return result


# ── Active-batch guard ─────────────────────────────────────────────────────


def _check_active_batches() -> bool:
    """Return True if there's an in-flight word batch."""
    state = _load_state()
    if not state:
        return False
    if state.get("status") in ("downloaded", "failed", "expired", "cancelled"):
        return False

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return False

    auth = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    for b in state.get("batches", []):
        bid = b.get("batch_id")
        if not bid:
            continue
        try:
            resp = requests.get(f"{OPENAI_API}/batches/{bid}", headers=auth, timeout=30)
            if resp.ok:
                live = resp.json().get("status")
                if live not in ("completed", "failed", "expired", "cancelled"):
                    return True
        except Exception:
            pass
    return False


# ── Command: prepare ───────────────────────────────────────────────────────


def cmd_prepare(args):
    """Enumerate words, classify into tiers, build prompts, write JSONL, upload."""
    os.makedirs(BATCH_DIR, exist_ok=True)

    if _check_active_batches():
        state = _load_state()
        print(f"ERROR: Batch already in-flight (status: {state.get('status', '?')})")
        print("Use 'status' to check progress, or delete .word_batch_state.json to start over.")
        sys.exit(1)

    conn = get_db()
    try:
        _build_lemma_freq(conn)

        verse_set = None
        if args.verses:
            verse_set = set(parse_verse_spec(args.verses))

        pos_map = _build_lemma_pos_map(conn)

        print("Enumerating content words...")
        all_words = _get_content_words(conn, verse_set)
        print(f"Found {len(all_words)} content words")

        # Classify into tiers
        tier1_by_lemma: dict[str, list[tuple[int, int, int]]] = {}
        tier2_words: list[tuple[int, int, int, str]] = []
        tier3_words: list[tuple[int, int, int, str]] = []

        for ch, v, wp, lbw in all_words:
            freq = get_lemma_frequency(lbw)
            pos = pos_map.get(lbw, "")
            tier = classify_word(freq, pos, args.freq_threshold)
            if tier == 1:
                tier1_by_lemma.setdefault(lbw, []).append((ch, v, wp))
            elif tier == 2:
                tier2_words.append((ch, v, wp, lbw))
            else:
                tier3_words.append((ch, v, wp, lbw))

        # Pick one representative per tier-1 lemma (first in Quran order)
        tier1_reps: list[tuple[int, int, int, str]] = []
        for lbw in sorted(tier1_by_lemma):
            ch, v, wp = tier1_by_lemma[lbw][0]
            tier1_reps.append((ch, v, wp, lbw))

        tier1_occ = sum(len(v) for v in tier1_by_lemma.values())
        print(f"\nTier classification (freq threshold = {args.freq_threshold}):")
        print(f"  Tier 1: {len(tier1_by_lemma)} stable lemmas "
              f"({tier1_occ} occurrences) -> {len(tier1_reps)} prompts ({args.smart_model})")
        print(f"  Tier 2: {len(tier2_words)} content words -> {len(tier2_words)} prompts ({args.nano_model})")
        print(f"  Tier 3: {len(tier3_words)} rare words -> {len(tier3_words)} prompts ({args.smart_model})")
        print(f"  Total prompts: {len(tier1_reps) + len(tier2_words) + len(tier3_words)}")

        # Get/create config
        config_id = get_or_create_config(
            conn, args.config, f"{args.nano_model}+{args.smart_model}"
        )

        # Skip already-processed words (unless --include-existing)
        if not args.include_existing:
            rows = conn.execute(
                "SELECT chapter, verse, word_pos FROM ai_word_meanings WHERE config_id = ?",
                (config_id,),
            ).fetchall()
            existing = {(r["chapter"], r["verse"], r["word_pos"]) for r in rows}

            if existing:
                t2_before = len(tier2_words)
                tier2_words = [
                    (c, v, w, l) for c, v, w, l in tier2_words if (c, v, w) not in existing
                ]
                t3_before = len(tier3_words)
                tier3_words = [
                    (c, v, w, l) for c, v, w, l in tier3_words if (c, v, w) not in existing
                ]

                tier1_reps_new = []
                tier1_by_lemma_new: dict[str, list] = {}
                for ch, v, wp, lbw in tier1_reps:
                    if any((c, v2, w) in existing for c, v2, w in tier1_by_lemma[lbw]):
                        continue
                    tier1_reps_new.append((ch, v, wp, lbw))
                    tier1_by_lemma_new[lbw] = tier1_by_lemma[lbw]

                skipped = (
                    (len(tier1_reps) - len(tier1_reps_new))
                    + (t2_before - len(tier2_words))
                    + (t3_before - len(tier3_words))
                )
                if skipped:
                    print(f"\nSkipping {skipped} already-processed entries "
                          "(use --include-existing to override)")
                tier1_reps = tier1_reps_new
                tier1_by_lemma = tier1_by_lemma_new

        nano_words = tier2_words
        gpt51_words = tier1_reps + tier3_words

        if not nano_words and not gpt51_words:
            print("\nNo words to process — all already done!")
            return

        # ── Build JSONL files ──
        ts = int(time.time())
        tier1_lemma_set = set(tier1_by_lemma.keys())
        skipped_prompts = 0
        all_batches: list[dict] = []

        state: dict = {
            "config": args.config,
            "config_id": config_id,
            "nano_model": args.nano_model,
            "smart_model": args.smart_model,
            "freq_threshold": args.freq_threshold,
            "tier1_lemmas": sorted(tier1_lemma_set),
            "prepared_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        if args.verses:
            state["verses"] = args.verses

        # ── Nano JSONL (tier 2) ──
        nano_count = 0
        if nano_words:
            nano_path = os.path.join(BATCH_DIR, f"batch_words_nano_{ts}.jsonl")
            print(f"\nGenerating {len(nano_words)} nano prompts...")
            with open(nano_path, "w") as f:
                for i, (ch, v, wp, lbw) in enumerate(nano_words):
                    prompt = build_word_prompt(conn, ch, v, wp)
                    if prompt is None:
                        skipped_prompts += 1
                        continue

                    body: dict = {
                        "model": args.nano_model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt.replace(" /no_think", "")},
                        ],
                    }
                    if "nano" not in args.nano_model:
                        body["temperature"] = args.temperature

                    req = {
                        "custom_id": f"{ch}:{v}:{wp}",
                        "method": "POST",
                        "url": "/v1/chat/completions",
                        "body": body,
                    }
                    f.write(json.dumps(req) + "\n")
                    nano_count += 1

                    if (i + 1) % 2000 == 0:
                        print(f"  {i + 1}/{len(nano_words)} prompts generated...")

            print(f"Wrote {nano_count} nano requests to {nano_path}")
            print(f"\nUploading nano JSONL...")
            all_batches.extend(_split_and_upload(nano_path, "nano"))

        # ── GPT-5.1 JSONL (tier 1 representatives + tier 3) ──
        gpt51_count = 0
        if gpt51_words:
            gpt51_path = os.path.join(BATCH_DIR, f"batch_words_smart_{ts}.jsonl")
            print(f"\nGenerating {len(gpt51_words)} {args.smart_model} prompts...")
            with open(gpt51_path, "w") as f:
                for i, (ch, v, wp, lbw) in enumerate(gpt51_words):
                    prompt = build_word_prompt(conn, ch, v, wp)
                    if prompt is None:
                        skipped_prompts += 1
                        continue

                    if lbw in tier1_lemma_set:
                        custom_id = f"T1:{lbw}:{ch}:{v}:{wp}"
                    else:
                        custom_id = f"{ch}:{v}:{wp}"

                    req = {
                        "custom_id": custom_id,
                        "method": "POST",
                        "url": "/v1/chat/completions",
                        "body": {
                            "model": args.smart_model,
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": prompt.replace(" /no_think", "")},
                            ],
                            "temperature": args.temperature,
                        },
                    }
                    f.write(json.dumps(req) + "\n")
                    gpt51_count += 1

                    if (i + 1) % 1000 == 0:
                        print(f"  {i + 1}/{len(gpt51_words)} prompts generated...")

            print(f"Wrote {gpt51_count} {args.smart_model} requests to {gpt51_path}")
            print(f"\nUploading {args.smart_model} JSONL...")
            all_batches.extend(_split_and_upload(gpt51_path, "smart"))

        if skipped_prompts:
            print(f"\nSkipped {skipped_prompts} prefix/suffix-only words during prompt generation")

        state["batches"] = all_batches
        state["nano_count"] = nano_count
        state["smart_count"] = gpt51_count
        _save_state(state)

        print(f"\n{len(all_batches)} file(s) uploaded. Run: python word_meanings_ai_batch.py submit")

    finally:
        conn.close()


# ── Command: submit ────────────────────────────────────────────────────────


def cmd_submit(args):
    """Submit batch jobs for all uploaded files.

    Submits one at a time with a delay between each. If OpenAI rejects a
    submission (concurrent limit), retries with exponential backoff.
    """
    DELAY_BETWEEN = 10     # seconds between submissions
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
        label = b["label"]
        count = b["count"]

        for attempt in range(MAX_RETRIES):
            print(f"Submitting {label} batch ({count} requests)...")

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

            # If file expired or invalid, re-upload and retry
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
                print(f"  {label}: {batch_data['id']} ({batch_data['status']})")
                submitted += 1
                _save_state(state)
                break

            # Rate/concurrency limit — backoff and retry
            err = resp.json().get("error", {}).get("message", resp.text)
            wait = DELAY_BETWEEN * (2 ** attempt)
            print(f"  Rejected: {err}")
            if attempt < MAX_RETRIES - 1:
                print(f"  Retrying in {wait}s (attempt {attempt + 2}/{MAX_RETRIES})...")
                time.sleep(wait)
            else:
                print(f"  Failed after {MAX_RETRIES} attempts, skipping.")

        # Delay before next submission
        if i < len(pending) - 1:
            time.sleep(DELAY_BETWEEN)

    state["status"] = "submitted"
    state["submitted_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _save_state(state)

    failed = len(pending) - submitted
    print(f"\n{submitted} submitted, {failed} failed.")
    if failed:
        print("Run 'submit' again later to retry failed ones.")
    print("Check progress: python word_meanings_ai_batch.py status")


# ── Command: status ────────────────────────────────────────────────────────


def _fetch_batch_info(batch_id: str) -> dict:
    """Fetch batch info from OpenAI API."""
    resp = requests.get(
        f"{OPENAI_API}/batches/{batch_id}", headers=_headers(), timeout=30
    )
    resp.raise_for_status()
    return resp.json()


def cmd_status(args):
    """Check progress of all batch jobs."""
    state = _load_state()
    batches = state.get("batches", [])
    if not batches or not any(b.get("batch_id") for b in batches):
        print("No batch jobs found. Run 'prepare' and 'submit' first.")
        return

    print(f"Config:    {state.get('config', '?')}")
    print(f"Submitted: {state.get('submitted_at', '?')}")
    print(f"Batches:   {len(batches)}")
    print()

    all_done = True
    any_failed = False
    total_completed = 0
    total_failed = 0
    total_requests = 0

    for i, b in enumerate(batches):
        bid = b.get("batch_id")
        if not bid:
            print(f"  [{b['label']}] not submitted yet")
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

        # Compact display for many batches
        if len(batches) > 4:
            pct = (completed * 100 // total) if isinstance(total, int) and total > 0 else "?"
            print(f"  {b['label']:6s} {bid}  {status_str:12s}  {completed}/{total} ({pct}%)")
        else:
            print(f"  {b['label'].title()}: {bid}")
            print(f"    Status:   {status_str}")
            print(f"    Progress: {completed}/{total} completed, {failed} failed")
            print()

    if len(batches) > 4:
        print()
    print(f"  Total: {total_completed}/{total_requests} completed, {total_failed} failed")

    if all_done and not any_failed:
        state["status"] = "completed"
        print("\nAll batches complete! Run: python word_meanings_ai_batch.py download")
    elif any_failed:
        state["status"] = "failed"

    _save_state(state)


# ── Command: download ──────────────────────────────────────────────────────


def _download_results_file(batch_id: str, label: str) -> str | None:
    """Download output JSONL for a completed batch. Returns local path or None."""
    batch = _fetch_batch_info(batch_id)

    if batch["status"] != "completed":
        rc = batch.get("request_counts", {})
        print(f"  {label}: not complete ({batch['status']}, "
              f"{rc.get('completed', 0)}/{rc.get('total', '?')})")
        return None

    output_file_id = batch.get("output_file_id")
    if not output_file_id:
        print(f"  {label}: no output file")
        return None

    print(f"  Downloading {label} results...")
    resp = requests.get(
        f"{OPENAI_API}/files/{output_file_id}/content",
        headers={"Authorization": f"Bearer {_get_api_key()}"},
        timeout=600,
    )
    resp.raise_for_status()

    results_path = os.path.join(BATCH_DIR, f"results_{label}_{batch_id}.jsonl")
    with open(results_path, "wb") as f:
        f.write(resp.content)

    error_file_id = batch.get("error_file_id")
    if error_file_id:
        try:
            resp_err = requests.get(
                f"{OPENAI_API}/files/{error_file_id}/content",
                headers={"Authorization": f"Bearer {_get_api_key()}"},
                timeout=300,
            )
            if resp_err.ok and resp_err.content.strip():
                err_path = os.path.join(BATCH_DIR, f"errors_{label}_{batch_id}.jsonl")
                with open(err_path, "wb") as f:
                    f.write(resp_err.content)
                print(f"    Errors saved to {err_path}")
        except Exception:
            pass

    return results_path


def _extract_response(line: str) -> tuple[str, str | None]:
    """Parse one JSONL result line -> (custom_id, raw_content_or_None)."""
    result = json.loads(line.strip())
    custom_id = result["custom_id"]

    response = result.get("response", {})
    if response.get("status_code") != 200:
        return custom_id, None

    choices = response.get("body", {}).get("choices", [])
    if not choices:
        return custom_id, None

    raw = choices[0].get("message", {}).get("content", "")
    return custom_id, raw or None


def _insert_word_meaning(conn, ch, v, wp, config_id, parsed, raw_text, force):
    """Insert a single word meaning row. Returns True if inserted, False if skipped."""
    existing = conn.execute(
        "SELECT id FROM ai_word_meanings "
        "WHERE chapter = ? AND verse = ? AND word_pos = ? AND config_id = ?",
        (ch, v, wp, config_id),
    ).fetchone()

    if existing and not force:
        return False
    if existing:
        conn.execute(
            "DELETE FROM ai_word_meanings "
            "WHERE chapter = ? AND verse = ? AND word_pos = ? AND config_id = ?",
            (ch, v, wp, config_id),
        )

    conn.execute(
        "INSERT INTO ai_word_meanings "
        "(chapter, verse, word_pos, config_id, meaning_short, meaning_detailed, "
        " semantic_field, cross_ref_notes, cognate_notes, morphology_notes, "
        " departure_notes, full_prompt, raw_response, model_response_time_ms) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            ch, v, wp, config_id,
            parsed["meaning_short"],
            parsed["meaning_detailed"],
            parsed.get("semantic_field") or None,
            parsed.get("cross_ref_notes") or None,
            parsed.get("cognate_notes") or None,
            parsed.get("morphology_notes") or None,
            parsed.get("departure_notes") or None,
            "",
            raw_text,
            0,
        ),
    )
    return True


def cmd_download(args):
    """Download results from all batches and store in database."""
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
        label = f"{b['label']}_{bid[-8:]}"
        path = _download_results_file(bid, label)
        if path:
            result_files.append(path)

    if not result_files:
        print("No results ready to download.")
        return

    # Store in DB
    print(f"\nStoring word meanings from {len(result_files)} result file(s)...")
    conn = get_db()
    try:
        config_id = state["config_id"]
        force = getattr(args, "force", False)

        stored = 0
        replicated = 0
        skipped = 0
        errors = 0
        uncommitted = 0

        seen_global: set[str] = set()

        for results_path in result_files:
            with open(results_path) as f:
                for line in f:
                    custom_id, raw = _extract_response(line)

                    if custom_id in seen_global:
                        skipped += 1
                        continue
                    seen_global.add(custom_id)

                    if raw is None:
                        print(f"    {custom_id} — API error")
                        errors += 1
                        continue

                    parsed = parse_response(raw)
                    if not parsed["meaning_short"]:
                        print(f"    {custom_id} — empty meaning_short")
                        errors += 1
                        continue

                    # ── Tier 1: replicate to all occurrences ──
                    if custom_id.startswith("T1:"):
                        parts = custom_id.split(":")
                        lemma_bw = parts[1]
                        rep_ch, rep_v, rep_wp = int(parts[2]), int(parts[3]), int(parts[4])

                        occ_rows = conn.execute(
                            "SELECT DISTINCT chapter, verse, word_pos "
                            "FROM morphology "
                            "WHERE lemma_buckwalter = ? "
                            "AND pos NOT IN ('Prefix', 'Suffix') "
                            "ORDER BY chapter, verse, word_pos",
                            (lemma_bw,),
                        ).fetchall()

                        for occ in occ_rows:
                            ch, v, wp = occ["chapter"], occ["verse"], occ["word_pos"]
                            is_rep = (ch == rep_ch and v == rep_v and wp == rep_wp)
                            raw_text = raw if is_rep else f"[tier1 replicated from {lemma_bw}]"

                            if _insert_word_meaning(conn, ch, v, wp, config_id, parsed, raw_text, force):
                                if is_rep:
                                    stored += 1
                                else:
                                    replicated += 1
                                uncommitted += 1
                            else:
                                skipped += 1

                            if uncommitted >= 500:
                                conn.commit()
                                uncommitted = 0

                    # ── Tier 2 / 3: direct storage ──
                    else:
                        parts = custom_id.split(":")
                        ch, v, wp = int(parts[0]), int(parts[1]), int(parts[2])

                        if _insert_word_meaning(conn, ch, v, wp, config_id, parsed, raw, force):
                            stored += 1
                            uncommitted += 1
                        else:
                            skipped += 1

                        if uncommitted >= 500:
                            conn.commit()
                            uncommitted = 0

                    total_done = stored + replicated
                    if total_done > 0 and total_done % 5000 == 0:
                        print(f"    {total_done} meanings stored so far...")

        conn.commit()
        print(f"\nDone: {stored} stored, {replicated} replicated (tier 1), "
              f"{skipped} skipped, {errors} errors")

        state["status"] = "downloaded"
        state["stored"] = stored
        state["replicated"] = replicated
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
            print("  python word_meanings_ai_batch.py status")
            print("  python word_meanings_ai_batch.py download")
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
                print(f"  [{time.strftime('%H:%M:%S')}] {b['label']}: check failed ({e})")
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
            print(f"  [{time.strftime('%H:%M:%S')}] {b['label']:6s} {batch['status']:12s} "
                  f"{completed}/{total} ({pct}%) done, {failed} failed")

            if batch["status"] != "completed":
                all_done = False
            if batch["status"] in ("failed", "expired", "cancelled"):
                any_failed = True

            if batch.get("output_file_id"):
                b["output_file_id"] = batch["output_file_id"]

        overall_pct = (
            f"{total_completed * 100 // total_requests}%"
            if total_requests > 0 else "?"
        )
        print(f"  [{time.strftime('%H:%M:%S')}] Overall: {total_completed}/{total_requests} ({overall_pct})")

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
        description="Tiered Batch Word Meanings — OpenAI Batch API"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # prepare
    p = sub.add_parser("prepare", help="Classify words, build prompts, upload JSONL")
    p.add_argument("--verses", help="Verse spec, e.g. '2:19-20' (default: all Quran)")
    p.add_argument("--config", default=DEFAULT_CONFIG, help=f"Config name (default: {DEFAULT_CONFIG})")
    p.add_argument("--nano-model", default=DEFAULT_NANO_MODEL, help=f"Nano model (default: {DEFAULT_NANO_MODEL})")
    p.add_argument("--smart-model", default=DEFAULT_SMART_MODEL, help=f"Smart model (default: {DEFAULT_SMART_MODEL})")
    p.add_argument("--freq-threshold", type=int, default=DEFAULT_FREQ_THRESHOLD,
                    help=f"Zipf frequency cutoff (default: {DEFAULT_FREQ_THRESHOLD})")
    p.add_argument("--temperature", type=float, default=0.3)
    p.add_argument("--include-existing", action="store_true",
                    help="Include words already in DB (default: skip them)")

    # submit
    sub.add_parser("submit", help="Submit prepared batch jobs to OpenAI")

    # status
    sub.add_parser("status", help="Check batch job progress")

    # download
    p = sub.add_parser("download", help="Download results and store in DB")
    p.add_argument("--force", action="store_true", help="Overwrite existing meanings")

    # run (all-in-one)
    p = sub.add_parser("run", help="Full pipeline: prepare + submit + poll + download")
    p.add_argument("--verses", help="Verse spec (default: all Quran)")
    p.add_argument("--config", default=DEFAULT_CONFIG)
    p.add_argument("--nano-model", default=DEFAULT_NANO_MODEL)
    p.add_argument("--smart-model", default=DEFAULT_SMART_MODEL)
    p.add_argument("--freq-threshold", type=int, default=DEFAULT_FREQ_THRESHOLD)
    p.add_argument("--temperature", type=float, default=0.3)
    p.add_argument("--include-existing", action="store_true")
    p.add_argument("--force", action="store_true", help="Overwrite existing on download")

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
