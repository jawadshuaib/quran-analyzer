"""Lightweight wrapper around Anthropic's Message Batches API.

Anthropic's batch API (https://docs.anthropic.com/en/api/creating-message-batches)
is roughly 50% cheaper than the synchronous /messages endpoint and
returns within 24 h (often minutes for small batches). This module
exposes a tiny three-function interface used by our bias-revision
scripts:

  submit_batch(api_key, requests, label) -> batch_id
  wait_for_batch(api_key, batch_id, poll_every=30) -> when 'ended', returns batch info
  fetch_results(api_key, results_url) -> iterator over result records

State is persisted to a JSON file under /tmp so a script can be
interrupted (Ctrl-C, laptop sleep, network glitch) and resumed —
the next invocation reads the batch_id and skips the submit step.
"""
from __future__ import annotations

import json
import os
import sys
import time
from typing import Iterator

import requests

ANTHROPIC_API = "https://api.anthropic.com/v1/messages/batches"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_BETA = "message-batches-2024-09-24"

STATE_DIR = "/tmp"


def _state_path(label: str) -> str:
    safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in label)
    return os.path.join(STATE_DIR, f"anthropic_batch_{safe}.json")


def load_batch_state(label: str) -> dict | None:
    path = _state_path(label)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def save_batch_state(label: str, state: dict) -> None:
    with open(_state_path(label), "w") as f:
        json.dump(state, f, indent=2)


def clear_batch_state(label: str) -> None:
    path = _state_path(label)
    if os.path.exists(path):
        os.remove(path)


def submit_batch(
    api_key: str,
    requests_list: list[dict],
    label: str,
) -> str:
    """Submit a batch. Each item in requests_list must be:
        {"custom_id": "...", "params": {model, max_tokens, system?, messages, ...}}

    Returns the batch_id. Persists state to disk so the caller can resume.
    """
    if not requests_list:
        raise ValueError("empty batch")
    if len(requests_list) > 10_000:
        raise ValueError(f"batch too big: {len(requests_list)} (max 10000)")

    resp = requests.post(
        ANTHROPIC_API,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "anthropic-beta": DEFAULT_BETA,
        },
        json={"requests": requests_list},
        timeout=120,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"submit failed ({resp.status_code}): {resp.text[:600]}")
    body = resp.json()
    batch_id = body["id"]
    save_batch_state(label, {
        "batch_id": batch_id,
        "submitted_at": body.get("created_at"),
        "total_requests": len(requests_list),
        "label": label,
    })
    return batch_id


def get_batch_status(api_key: str, batch_id: str) -> dict:
    resp = requests.get(
        f"{ANTHROPIC_API}/{batch_id}",
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "anthropic-beta": DEFAULT_BETA,
        },
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"status fetch failed ({resp.status_code}): {resp.text[:400]}")
    return resp.json()


def wait_for_batch(
    api_key: str,
    batch_id: str,
    poll_every: int = 30,
    timeout_seconds: int = 24 * 3600,
) -> dict:
    """Poll until processing_status == 'ended'. Prints progress lines.
    Returns the final batch object."""
    deadline = time.time() + timeout_seconds
    last_status_line = None
    while time.time() < deadline:
        info = get_batch_status(api_key, batch_id)
        status = info.get("processing_status")
        counts = info.get("request_counts") or {}
        line = (
            f"[batch {batch_id[:18]}…] status={status}  "
            f"processing={counts.get('processing', 0)}  "
            f"succeeded={counts.get('succeeded', 0)}  "
            f"errored={counts.get('errored', 0)}  "
            f"canceled={counts.get('canceled', 0)}  "
            f"expired={counts.get('expired', 0)}"
        )
        if line != last_status_line:
            print(line)
            last_status_line = line
        if status == "ended":
            return info
        time.sleep(poll_every)
    raise TimeoutError(f"batch {batch_id} did not end within {timeout_seconds}s")


def fetch_results(api_key: str, results_url: str) -> Iterator[dict]:
    """Stream the JSONL results. Each yielded record has shape:
        {"custom_id": "...", "result": {...}}
    Where result.type is 'succeeded' | 'errored' | 'canceled' | 'expired'.
    On succeeded, result.message is a standard /messages response.
    """
    resp = requests.get(
        results_url,
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "anthropic-beta": DEFAULT_BETA,
        },
        stream=True,
        timeout=300,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"results fetch failed ({resp.status_code}): {resp.text[:400]}")
    for raw_line in resp.iter_lines():
        if not raw_line:
            continue
        try:
            yield json.loads(raw_line)
        except json.JSONDecodeError as e:
            print(f"  skipping malformed line: {e}", file=sys.stderr)
