#!/usr/bin/env python3
"""Render a gate-passed Q&A video (script bank) into an MP4.

Thin bridge between the qa_videos table and the Remotion renderer: the
payload was already compiled AND validated by the gates (qa_video_compile +
qa_video_match_gate), so this module deliberately does no payload surgery —
it ships payload_json byte-for-byte to `node scripts/render.mjs`, the same
subprocess plumbing educational_render_remotion uses. That "render exactly
what the gate verified" property is what makes the script↔highlight
guarantee hold end to end.

Usage (CLI, local or in the container):
    python3 qa_video_render.py --id 5              # render qa_videos row 5
    python3 qa_video_render.py --id 5 --voice-id X # override voice

Lifecycle (script-first review): status is never changed by rendering —
the file is an orthogonal artifact. The transient `rendering` flag guards
double-renders; success sets filename/file_size, failure sets
error_message. Renderable from status gate_passed (preview) or approved
(the publish tick's auto-render).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

import qa_video_common as C

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
# Same layout contract as educational_render_remotion: dev = sibling
# ../video-renderer; prod image sets REMOTION_RENDERER_DIR=/app/video-renderer.
_DEFAULT_RENDERER_DIR = os.path.normpath(os.path.join(_THIS_DIR, "..", "video-renderer"))
RENDERER_DIR = os.environ.get("REMOTION_RENDERER_DIR", _DEFAULT_RENDERER_DIR)
RENDER_SCRIPT = os.path.join(RENDERER_DIR, "scripts", "render.mjs")
OUTPUT_DIR = os.path.join(_THIS_DIR, "data", "qa_videos")


class QaRenderError(Exception):
    pass


def render_qa_video(
    conn,
    row_id: int,
    *,
    elevenlabs_api_key: str,
    voice_id: str,
    timeout: int = 600,
) -> tuple[str, int]:
    """Render qa_videos row `row_id`. Returns (filename, file_size)."""
    if not os.path.isfile(RENDER_SCRIPT):
        raise QaRenderError(f"Remotion renderer not found at {RENDER_SCRIPT}")

    row = conn.execute("SELECT * FROM qa_videos WHERE id = ?", (row_id,)).fetchone()
    if not row:
        raise QaRenderError(f"qa_videos row {row_id} not found")
    rd = dict(row)
    # Script-first model: renders are allowed for scripts awaiting review
    # (preview) and approved scripts (the publish tick's auto-render).
    # Status is NEVER changed by rendering — the file is orthogonal to the
    # review state; the transient `rendering` flag guards double-renders.
    if rd.get("status") not in ("gate_passed", "approved"):
        raise QaRenderError(
            f"row {row_id} is status={rd.get('status')} — only gate_passed "
            f"or approved scripts are renderable"
        )
    if rd.get("rendering"):
        raise QaRenderError(f"row {row_id} is already rendering")
    if not rd.get("payload_json"):
        raise QaRenderError(f"row {row_id} has no payload_json — re-run the gate")

    payload = json.loads(rd["payload_json"])

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_filename = f"qa-{row_id:06d}-short.mp4"
    out_path = os.path.join(OUTPUT_DIR, out_filename)

    conn.execute(
        "UPDATE qa_videos SET rendering=1, error_message=NULL WHERE id=?",
        (row_id,),
    )
    conn.commit()

    with tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(payload, f, ensure_ascii=False)
        payload_path = f.name

    env = dict(os.environ)
    env["ELEVENLABS_API_KEY"] = elevenlabs_api_key or ""
    env["ELEVENLABS_VOICE_ID"] = voice_id or ""
    # The renderer's .env may carry the dev kill-switch
    # (ELEVENLABS_DISABLE_GENERATION=1, used when iterating on visuals).
    # A bank render is a FINAL render — narration must be real, and a
    # silent slide would ship a broken video. Process env wins over
    # --env-file in Node, so force generation on here.
    env["ELEVENLABS_DISABLE_GENERATION"] = "0"

    cmd = [
        "node",
        "--env-file-if-exists=.env",
        "scripts/render.mjs",
        "--payload", payload_path,
        "--out", out_path,
    ]
    try:
        proc = subprocess.run(
            cmd, cwd=RENDERER_DIR, env=env,
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        _mark_failed(conn, row_id, f"render timed out after {timeout}s")
        raise QaRenderError(f"render timed out after {timeout}s")
    finally:
        try:
            os.remove(payload_path)
        except OSError:
            pass

    if proc.returncode != 0:
        tail = (proc.stderr or "")[-800:]
        _mark_failed(conn, row_id, f"renderer exited {proc.returncode}: {tail}")
        raise QaRenderError(f"Remotion render failed: {tail}")

    lines = (proc.stdout or "").strip().splitlines()
    result = None
    if lines:
        try:
            result = json.loads(lines[-1])
        except json.JSONDecodeError:
            pass
    if not (result and result.get("ok")):
        err = (result or {}).get("error") or (lines[-1][:200] if lines else "no stdout")
        _mark_failed(conn, row_id, f"renderer reported failure: {err}")
        raise QaRenderError(f"Remotion render failed: {err}")
    if not os.path.isfile(out_path):
        _mark_failed(conn, row_id, "renderer said ok but output file missing")
        raise QaRenderError(f"renderer reported success but {out_path} doesn't exist")

    size = os.path.getsize(out_path)
    conn.execute(
        "UPDATE qa_videos SET rendering=0, filename=?, file_size=?, "
        "error_message=NULL, completed_at=datetime('now') WHERE id=?",
        (out_filename, size, row_id),
    )
    conn.commit()
    return out_filename, size


def _mark_failed(conn, row_id: int, msg: str) -> None:
    try:
        conn.execute(
            "UPDATE qa_videos SET rendering=0, error_message=? WHERE id=?",
            (msg[:1000], row_id),
        )
        conn.commit()
    except Exception:
        pass


def _creds_from_db(conn) -> tuple[str, str]:
    """(elevenlabs_api_key, default voice_id) from admin settings."""
    row = conn.execute(
        "SELECT value FROM admin_preferences WHERE key='elevenlabs_api_key'"
    ).fetchone()
    key = row["value"] if row and row["value"] else ""
    voice = ""
    try:
        # Prefer the bank's configured voice (qa_publish_schedule pref).
        import json as _json
        prow = conn.execute(
            "SELECT value FROM admin_preferences WHERE key='qa_publish_schedule'"
        ).fetchone()
        if prow and prow["value"]:
            want = (_json.loads(prow["value"]).get("voice_id") or "").strip()
            if want and conn.execute(
                "SELECT 1 FROM admin_voices WHERE voice_id=?", (want,)
            ).fetchone():
                voice = want
        if not voice:
            vrow = conn.execute(
                "SELECT voice_id FROM admin_voices ORDER BY id LIMIT 1"
            ).fetchone()
            voice = vrow["voice_id"] if vrow else ""
    except Exception:
        pass
    return key, voice


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", type=int, required=True, help="qa_videos row id")
    ap.add_argument("--voice-id", default=None)
    args = ap.parse_args()

    conn = C.get_conn()
    try:
        key, default_voice = _creds_from_db(conn)
        if not key:
            print("ERROR: elevenlabs_api_key not set in admin_preferences", file=sys.stderr)
            return 2
        voice = args.voice_id or default_voice
        if not voice:
            print("ERROR: no voice available (admin_voices empty, no --voice-id)", file=sys.stderr)
            return 2
        fn, size = render_qa_video(conn, args.id, elevenlabs_api_key=key, voice_id=voice)
        print(json.dumps({"ok": True, "filename": fn, "file_size": size}))
        return 0
    except QaRenderError as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
