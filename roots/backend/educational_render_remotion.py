"""Remotion-based renderer for word_origins educational videos.

Drop-in replacement for the ffmpeg + ASS path inside
educational_render.render_video() — same input contract (conn,
video_id, format, elevenlabs_api_key, voice_id), same output
contract ((filename, file_size_bytes)), same status flow handled
by the orchestrator.

What's different visually: instead of three on-screen verse cards
composed in ffmpeg, the Remotion bundle renders a 4-slide React
composition with synchronized karaoke captions:

    Slide 1: Root page (large RTL letters + meaning)
    Slide 2: Source verse-flow (target word highlighted)
    Slide 3: Cross-reference verse-flow (selected_verse_refs[0])
    Slide 4: al-nuqta brand outro splash

Each slide gets its own per-beat narration so the karaoke and
visuals are tightly coupled. The script's beats map 1:1 onto the
slides:

    Slide 1 narration = hook + tidbit_about_root
    Slide 2 narration = tidbit_about_quran_usage
    Slide 3 narration = tidbit_about_semitic
    Slide 4 narration = close

The video-renderer project sits at roots/video-renderer/ and has
its own node_modules (Remotion v4). We invoke it via subprocess.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile

from educational_scripts import sanitize_for_tts


class RemotionRenderError(Exception):
    """Raised when the Remotion subprocess fails or returns a malformed
    result. Caller in the orchestrator catches Exception and writes
    str(e)[:1000] into educational_videos.error_message."""


# Where the renderer subproject lives. Relative to this file's
# directory so dev + Docker prod both resolve correctly. The
# Dockerfile must COPY the renderer dir + its node_modules.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RENDERER_DIR = os.path.normpath(os.path.join(_THIS_DIR, "..", "video-renderer"))
RENDER_SCRIPT = os.path.join(RENDERER_DIR, "scripts", "render.mjs")

# Output directory mirrors the ffmpeg path so the orchestrator's
# UPDATE statement (filename = filename) lands files in the same
# place regardless of which renderer produced them.
OUTPUT_DIR = os.path.join(_THIS_DIR, "data", "educational_videos")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _strip_uthmani_marks(text: str) -> str:
    """Match educational_render._strip_uthmani_marks so the Arabic
    rendered in Remotion is the same the existing pipeline shows.
    libass and Chromium both struggle with the same set of marks,
    so the stripping rules are identical."""
    if not text:
        return text
    import re
    out = text.replace("ٱ", "ا")  # alef wasla → plain alef
    return re.sub(r"[ٰٓٔۖ-ۭ]", "", out)


def _word_gloss(conn, c: int, v: int, p: int) -> str | None:
    """Best per-word English gloss. Mirrors the lookup in
    educational_render._build_word_origins_ass_for_row → tries
    ai_word_meanings.preferred_translation / meaning_short first
    (curated when present), then word_glosses.translation_en."""
    try:
        wm = conn.execute(
            "SELECT COALESCE(preferred_translation, meaning_short) AS t "
            "FROM ai_word_meanings WHERE chapter=? AND verse=? AND word_pos=? LIMIT 1",
            (c, v, p),
        ).fetchone()
        if wm and wm["t"]:
            return wm["t"].strip()
    except Exception:
        pass
    try:
        wg = conn.execute(
            "SELECT translation_en FROM word_glosses "
            "WHERE chapter=? AND verse=? AND word_pos=? LIMIT 1",
            (c, v, p),
        ).fetchone()
        if wg and wg["translation_en"]:
            return wg["translation_en"].strip()
    except Exception:
        pass
    return None


def _verse_data(conn, c: int, v: int) -> dict | None:
    """Pull Arabic + English for a verse. Returns None if missing —
    caller decides whether to skip the slide or fail."""
    arow = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter=? AND verse=?",
        (c, v),
    ).fetchone()
    erow = conn.execute(
        "SELECT text_en FROM translations WHERE chapter=? AND verse=?",
        (c, v),
    ).fetchone()
    if not arow:
        return None
    return {
        "arabic": arow["text_uthmani"],
        "translation": erow["text_en"] if erow else "",
    }


def _build_root_slide(payload: dict, hook: str, tidbit_root: str) -> dict:
    """Slide 1 — root page. Combines the hook and the root tidbit so
    the slide opens with the surprising fact and follows with the
    root's meaning."""
    root = payload.get("root") or {}
    root_arabic = (root.get("arabic") or "").strip()
    # Render with spaces between letters so each radical reads
    # cleanly at large size — matches the mockup style.
    root_letters = " ".join(list(root_arabic)) if root_arabic else ""
    transliteration = (root.get("transliteration") or root.get("buckwalter") or "").strip()
    rootLabel = f"Root: {transliteration.lower()}" if transliteration else "Root"

    # The "meaning" line on the root slide. The script's
    # tidbit_about_root usually gives a one-line gloss — but it can
    # be 1-2 sentences. We fall back to a derivatives-derived hint
    # if the script didn't write one. The full tidbit also goes
    # into the narration so the audience hears the whole context.
    meaning = ""
    derivs = payload.get("derivatives") or []
    # Prefer a clean Hebrew/Aramaic gloss if available — the
    # cognate concept is usually the cleanest one-line summary of
    # the root's core sense.
    for d in derivs:
        if d.get("language") in ("Hebrew", "Biblical Aramaic", "Aramaic") and d.get("concept"):
            meaning = d["concept"]
            break
    if not meaning and derivs:
        meaning = derivs[0].get("concept") or derivs[0].get("meaning") or ""
    # If still empty, pull a short clause from tidbit_about_root.
    if not meaning and tidbit_root:
        # First clause up to 60 chars, ending at a comma or period
        # if possible — keeps the visible label tight while the
        # audio reads the full text.
        meaning = tidbit_root.split(".")[0][:60].strip()

    # Narration: hook leads, root tidbit follows. Double space so
    # ElevenLabs gets a clear sentence boundary even if the hook
    # didn't end with a period.
    narration = sanitize_for_tts(
        f"{hook.strip().rstrip('.')}. {tidbit_root.strip()}"
    ).strip()

    return {
        "type": "root",
        "durationSec": 6,  # bumped by prepareNarration to fit audio
        "rootArabic": root_letters or "ع",  # fallback if root data missing
        "rootLabel": rootLabel,
        "meaning": meaning or "(no meaning available)",
        "narration": {"text": narration},
    }


def _build_verse_flow_slide(
    conn,
    chapter: int,
    verse: int,
    word_pos: int,
    narration_text: str,
    duration_floor: float = 6.0,
) -> dict | None:
    """A verse-flow slide for chapter:verse with the target word at
    word_pos highlighted. Returns None if the verse can't be
    loaded — caller should skip rather than fail the whole render."""
    vd = _verse_data(conn, chapter, verse)
    if not vd:
        return None
    arabic = _strip_uthmani_marks(vd["arabic"])
    translation = vd["translation"] or ""
    gloss = _word_gloss(conn, chapter, verse, word_pos)
    return {
        "type": "verse-flow",
        "durationSec": duration_floor,
        "surah": chapter,
        "ayah": verse,
        "arabicText": arabic,
        "translation": translation,
        "highlightWordIndex": word_pos,
        # The renderer's VerseFlowPage will look for this exact
        # substring (case-insensitive) in the translation and
        # apply the matching English-side highlight. When the
        # gloss isn't a substring, the English just reads plain.
        **({"highlightTranslationText": gloss} if gloss else {}),
        "narration": {"text": sanitize_for_tts(narration_text or "").strip()},
    }


def _build_outro_slide(close_text: str) -> dict:
    """Slide 4 — al-nuqta brand splash. The close beat narrates the
    splash so the video doesn't end on dead air."""
    return {
        "type": "outro",
        "durationSec": 5,
        "siteName": "al-nuqta.com",
        "tagline": "A Root Based Translation of the Quran",
        "narration": {"text": sanitize_for_tts(close_text or "").strip()},
    }


def build_word_origins_payload(conn, rd: dict, script: dict) -> dict:
    """Convert an educational_videos row + its script into a Remotion
    payload. Skips slides that can't be built (e.g. missing cross-
    reference verse data) rather than failing the whole render —
    the audience gets a slightly shorter video instead of nothing.

    Slide order is fixed: Root → Source verse → Cross-ref → Outro.
    Each slide has per-beat narration so karaoke aligns naturally.
    """
    payload_inner = json.loads(rd.get("payload_json") or "{}")
    slides: list[dict] = []

    # Slide 1 — Root page
    hook = (script.get("hook") or "").strip()
    tidbit_root = (script.get("tidbit_about_root") or "").strip()
    slides.append(_build_root_slide(payload_inner, hook, tidbit_root))

    # Slide 2 — Source verse-flow
    src_word_pos = int(rd.get("anchor_word_pos") or 1)
    src_slide = _build_verse_flow_slide(
        conn,
        rd["chapter"],
        rd["verse"],
        src_word_pos,
        narration_text=script.get("tidbit_about_quran_usage", ""),
    )
    if src_slide:
        slides.append(src_slide)

    # Slide 3 — Cross-reference verse-flow (first selected ref)
    refs = script.get("selected_verse_refs") or []
    other_pool = {
        (int(o["chapter"]), int(o["verse"])): int(o.get("word_pos") or 1)
        for o in (payload_inner.get("other_verses") or [])
        if o.get("chapter") is not None and o.get("verse") is not None
    }
    for ref in refs[:1]:
        try:
            c = int(ref["chapter"])
            v = int(ref["verse"])
        except (KeyError, TypeError, ValueError):
            continue
        wp = other_pool.get((c, v), 1)
        cross_slide = _build_verse_flow_slide(
            conn,
            c, v, wp,
            narration_text=script.get("tidbit_about_semitic", ""),
        )
        if cross_slide:
            slides.append(cross_slide)
        break

    # Slide 4 — Outro
    slides.append(_build_outro_slide(script.get("close", "")))

    return {
        "videoId": f"educational-{rd['id']}",
        "title": (rd.get("youtube_title") or f"Word Detail {rd['chapter']}:{rd['verse']}"),
        "slides": slides,
    }


def render_word_origins_video(
    conn,
    video_id: int,
    *,
    format: str,
    elevenlabs_api_key: str,
    voice_id: str,
) -> tuple[str, int]:
    """Build the payload, invoke the Remotion renderer subprocess,
    move the resulting mp4 into the canonical OUTPUT_DIR location,
    and return (filename, file_size_bytes). Same return shape as
    educational_render.render_video so the orchestrator's UPDATE
    code path is unchanged.

    The renderer handles its own ElevenLabs TTS (via narration.mjs)
    using the API key + voice_id we pass through as env vars. Audio
    is cached at audio-cache/<sha256-hash>.mp3 inside the renderer
    directory, so re-renders of the same script reuse audio for
    free.
    """
    if format not in ("long", "short"):
        raise RemotionRenderError(f"unknown format: {format}")

    # Sanity-check the renderer is actually present. Not having it
    # is a deploy / Docker-image issue, not a per-video failure —
    # surface it loudly.
    if not os.path.isfile(RENDER_SCRIPT):
        raise RemotionRenderError(
            f"Remotion renderer not found at {RENDER_SCRIPT}. "
            f"Make sure roots/video-renderer/ is present and `npm install` "
            f"has been run in that directory."
        )

    row = conn.execute(
        "SELECT * FROM educational_videos WHERE id = ?", (video_id,)
    ).fetchone()
    if not row:
        raise RemotionRenderError(f"video {video_id} not found")
    rd = dict(row)
    if not rd.get("script_json"):
        raise RemotionRenderError("no script on this row — generate first")
    script = json.loads(rd["script_json"])

    # Build the payload from script + DB lookups.
    payload = build_word_origins_payload(conn, rd, script)
    if not payload["slides"]:
        raise RemotionRenderError("payload has no renderable slides")

    # Stage payload to a temp file the renderer can read. We don't
    # mutate any committed files — the renderer's narration prep
    # mutates the input file in place to add audioFile + alignment,
    # which lives only in the temp file and dies after the run.
    out_filename = f"{video_id:06d}-{format}.mp4"
    out_path = os.path.join(OUTPUT_DIR, out_filename)

    with tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(payload, f, ensure_ascii=False)
        payload_path = f.name

    # Pass ElevenLabs creds via env. The renderer reads ELEVENLABS_*
    # and uses Node's --env-file-if-exists to ALSO honor a local .env
    # if one exists (which is a noop when env is already set in the
    # parent process). This way, dev with a .env file and prod with
    # injected env vars both work.
    env = dict(os.environ)
    env["ELEVENLABS_API_KEY"] = elevenlabs_api_key or ""
    env["ELEVENLABS_VOICE_ID"] = voice_id or ""

    cmd = [
        "node",
        "--env-file-if-exists=.env",
        "scripts/render.mjs",
        "--payload", payload_path,
        "--out", out_path,
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=RENDERER_DIR,
            env=env,
            capture_output=True,
            text=True,
            # 10-minute ceiling — plenty for a 30-50s video. Each
            # slide's TTS adds ~3-5s, the actual render adds ~30s.
            # If we ever blow this, the bundle/Chromium is broken.
            timeout=600,
        )
    except subprocess.TimeoutExpired as e:
        raise RemotionRenderError(
            f"Remotion render timed out after {e.timeout}s. "
            f"stderr tail: {((e.stderr or b'')[-800:] or b'').decode('utf-8', errors='replace')}"
        )
    finally:
        # Clean up the temp payload file — narration prep mutated
        # it in place but we don't need it after the render.
        try:
            os.remove(payload_path)
        except OSError:
            pass

    if proc.returncode != 0:
        # Surface the renderer's stderr for debugging — it's the
        # most useful signal (the JSON-line stdout is just the
        # error message, while stderr has Remotion's progress logs
        # and any Node tracebacks).
        tail = (proc.stderr or "")[-800:]
        raise RemotionRenderError(f"Remotion render failed: {tail}")

    # Renderer writes one JSON line on stdout when successful. Parse
    # the LAST line in case there are trailing newlines or a stray
    # warning printed before it.
    last = (proc.stdout or "").strip().splitlines()
    if not last:
        raise RemotionRenderError("Remotion renderer produced no stdout")
    try:
        result = json.loads(last[-1])
    except json.JSONDecodeError:
        raise RemotionRenderError(f"Remotion stdout not JSON: {last[-1][:200]}")
    if not result.get("ok"):
        raise RemotionRenderError(
            f"Remotion render failed: {result.get('error') or 'unknown'}"
        )

    if not os.path.isfile(out_path):
        raise RemotionRenderError(
            f"Remotion reported success but {out_path} doesn't exist"
        )
    size = os.path.getsize(out_path)
    return out_filename, size
