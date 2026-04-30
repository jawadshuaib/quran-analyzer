"""Educational video pipeline — Phase 3: rendering.

Composes a vertical 1080x1920 mp4 from a script_ready row in
educational_videos. First implementation handles the
'translation_hides' template; word_origins and grammar_insights
templates extend the same pipeline with different on-screen layouts.

Pipeline:
    1. ElevenLabs TTS over the chosen voiceover (long or short).
    2. ffprobe → audio duration.
    3. Allocate visible time per beat proportionally to word count.
    4. Build an ASS subtitle file with fade-in/out per beat.
    5. ffmpeg composes: solid background + ASS subtitles + audio +
       ~5s al-nuqta outro card.

Output:
    roots/backend/data/educational_videos/<id>-<format>.mp4

The renderer is deliberately minimal for first cut — solid
background, simple text overlays, standard outro. Each visual
template (per type) can replace the _build_<type>_ass step without
touching the audio / composition layers.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import textwrap
import time
from dataclasses import dataclass

import requests


# Vertical 9:16 — works for Shorts/TikTok and is fine for regular
# YouTube uploads of educational content. Switch to 16:9 later if
# the long-form audience demands it.
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30

# How long the al-nuqta outro card holds at the end of the video.
OUTRO_DUR = 5.0
# Beat fade-in / fade-out duration (ms in ASS \fad).
BEAT_FADE_MS = 350

# Where rendered MP4s land.
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data", "educational_videos")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# TTS cache for educational scripts (separate from admin_tts_cache
# which keys on chapter:verse for the recitation pipeline).
TTS_DIR = os.path.join(os.path.dirname(__file__), "data", "tts_cache", "educational")
os.makedirs(TTS_DIR, exist_ok=True)

# Bundled font shipped via Dockerfile fonts-liberation. We use
# Liberation Sans for Latin and Amiri for Arabic (already in
# data/fonts).
FONT_SANS = "Liberation Sans"
FONT_ARABIC = "Amiri"

# Word-per-minute estimate for ElevenLabs eleven_multilingual_v2
# default settings. Used only to prefer cache hits — actual durations
# come from ffprobe on the rendered file.
WORDS_PER_MINUTE = 150


class RenderError(Exception):
    """Raised on any unrecoverable failure during render."""


# --------------------------------------------------------------------------
#  ElevenLabs TTS
# --------------------------------------------------------------------------

def _hash_text(text: str, voice_id: str) -> str:
    import hashlib
    return hashlib.sha256(f"{voice_id}::{text}".encode()).hexdigest()[:16]


def _tts(text: str, *, api_key: str, voice_id: str) -> str:
    """Synthesize `text` to mp3 via ElevenLabs. Cached on disk by
    (voice_id, text) hash so re-renders don't pay for the same audio.
    Returns the absolute mp3 path."""
    if not text:
        raise RenderError("TTS called with empty text")
    if not api_key:
        raise RenderError("ElevenLabs API key not configured (admin → settings)")
    if not voice_id:
        raise RenderError("No ElevenLabs voice configured (admin → settings → voices)")

    h = _hash_text(text, voice_id)
    path = os.path.join(TTS_DIR, f"{h}.mp3")
    if os.path.isfile(path) and os.path.getsize(path) > 0:
        return path

    resp = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        },
        timeout=120,
    )
    if resp.status_code != 200:
        raise RenderError(
            f"ElevenLabs error {resp.status_code}: {resp.text[:200]}"
        )
    with open(path, "wb") as f:
        f.write(resp.content)
    return path


# --------------------------------------------------------------------------
#  ffprobe / ffmpeg helpers
# --------------------------------------------------------------------------

def _probe_duration(path: str) -> float:
    """Seconds, as float."""
    out = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        text=True,
    )
    return float(out.strip())


def _ass_time(seconds: float) -> str:
    """Format seconds as h:mm:ss.cs for ASS dialogue timestamps."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:01d}:{m:02d}:{s:05.2f}"


# --------------------------------------------------------------------------
#  Visual template — Translation Hides (Phase 3a)
# --------------------------------------------------------------------------

@dataclass
class Beat:
    label: str
    text: str
    style: str  # ASS style name


def _word_count(s: str) -> int:
    import re
    return len(re.findall(r"\b\w[\w'-]*\b", s or ""))


def _build_beat_timings(
    beats: list[Beat],
    audio_duration: float,
    *,
    min_per_beat: float = 1.5,
) -> list[tuple[float, float]]:
    """Return [(start_s, end_s)] per beat.

    Allocates audio_duration proportionally to word count, with a
    floor (min_per_beat) so a one-word beat doesn't flash on screen.
    Times are end-aligned to audio_duration so the last beat ends
    exactly when the audio does — the outro then takes over.
    """
    weights = [max(_word_count(b.text), 1) for b in beats]
    total_weight = sum(weights)
    raw = [audio_duration * w / total_weight for w in weights]
    # Apply min floor; redistribute deficit from longer beats.
    durs = [max(d, min_per_beat) for d in raw]
    overflow = sum(durs) - audio_duration
    if overflow > 0:
        # Subtract proportionally from beats that are above min.
        slack = sum(d - min_per_beat for d in durs if d > min_per_beat)
        if slack > 0:
            for i in range(len(durs)):
                if durs[i] > min_per_beat:
                    share = (durs[i] - min_per_beat) / slack
                    durs[i] -= overflow * share
    starts: list[float] = [0.0]
    for d in durs[:-1]:
        starts.append(starts[-1] + d)
    timings = [(starts[i], starts[i] + durs[i]) for i in range(len(durs))]
    # Snap last end to audio_duration in case of float drift.
    if timings:
        timings[-1] = (timings[-1][0], audio_duration)
    return timings


def _ass_escape(text: str) -> str:
    """Escape characters that have meaning in ASS Dialogue text."""
    return (
        text
        .replace("\\", "\\\\")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("\n", "\\N")
    )


def _wrap_for_overlay(text: str, width_chars: int) -> str:
    """Wrap a single beat to fit on screen without overflowing.
    Returns ASS-friendly text with \\N line breaks."""
    paragraphs = text.split("\n")
    out_lines: list[str] = []
    for p in paragraphs:
        out_lines.extend(textwrap.wrap(p, width=width_chars) or [""])
    return "\\N".join(_ass_escape(line) for line in out_lines)


# Header template — define styles once, then dump dialogue lines.
_ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
ScaledBorderAndShadow: yes
Collisions: Normal

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,{font_sans},78,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,0,5,80,80,0,1
Style: Body,{font_sans},58,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,5,80,80,0,1
Style: Small,{font_sans},42,&H00CFCFCF,&H000000FF,&H00000000,&H80000000,0,1,0,0,100,100,0,0,1,2,0,5,80,80,0,1
Style: Reference,{font_sans},36,&H006E9BB8,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,0,8,80,80,140,1
Style: OutroSite,{font_sans},90,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,2,0,1,0,0,5,40,40,0,0
Style: OutroTag,{font_sans},48,&H80FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,40,40,0,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _build_ass_translation_hides(
    *,
    chapter: int,
    verse: int,
    beats: list[Beat],
    timings: list[tuple[float, float]],
    audio_duration: float,
) -> str:
    """ASS subtitle file for the Translation Hides template.

    Layout per beat:
      - Top reference badge "Quran X:Y" persistent through the
        narration (top-aligned, gold accent).
      - Centered text box switches between beats with fade-in/out.
      - Outro card overlays "al-nuqta.com" + tagline at end.
    """
    lines: list[str] = []

    narration_end = audio_duration
    outro_end = audio_duration + OUTRO_DUR

    # Persistent reference badge (visible during narration only)
    ref = f"Quran {chapter}:{verse}"
    lines.append(
        f"Dialogue: 0,{_ass_time(0)},{_ass_time(narration_end)},Reference,,0,0,0,,"
        f"{{\\fad(400,400)}}{_ass_escape(ref)}"
    )

    # Per-beat centered text. Hook gets the bold style; the rest use Body.
    for beat, (start, end) in zip(beats, timings):
        wrapped = _wrap_for_overlay(beat.text, width_chars=24 if beat.style == "Hook" else 28)
        lines.append(
            f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},{beat.style},,0,0,0,,"
            f"{{\\fad({BEAT_FADE_MS},{BEAT_FADE_MS})}}{wrapped}"
        )

    # Outro card — al-nuqta branding (matches the recitation pipeline outro)
    cx = VIDEO_WIDTH // 2
    site_y = VIDEO_HEIGHT // 2 - 60
    tag_y = VIDEO_HEIGHT // 2 + 60
    lines.append(
        f"Dialogue: 0,{_ass_time(narration_end)},{_ass_time(outro_end)},OutroSite,,0,0,0,,"
        f"{{\\fad(800,0)\\pos({cx},{site_y})}}al-nuqta.com"
    )
    lines.append(
        f"Dialogue: 0,{_ass_time(narration_end)},{_ass_time(outro_end)},OutroTag,,0,0,0,,"
        f"{{\\fad(1200,0)\\pos({cx},{tag_y})}}A Root Based Translation of the Quran"
    )

    header = _ASS_HEADER.format(
        w=VIDEO_WIDTH, h=VIDEO_HEIGHT, font_sans=FONT_SANS,
    )
    return header + "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
#  Compose
# --------------------------------------------------------------------------

def _compose_mp4(
    *,
    audio_path: str,
    ass_path: str,
    audio_duration: float,
    output_path: str,
) -> None:
    """ffmpeg compose: solid stone background → ASS subtitles → audio
    + outro silence padding. Replaces the output file if it exists."""
    total_duration = audio_duration + OUTRO_DUR
    # Warm-charcoal background — matches al-nuqta's dark accent so the
    # white narration overlays + gold reference badge + white outro
    # all read cleanly. Solid color first cut; backgrounds with motion
    # land in a later iteration.
    bg_color = "0x2D2620"

    cmd = [
        "ffmpeg", "-y",
        # Background video — generated solid color of the right duration.
        "-f", "lavfi",
        "-i", f"color=c={bg_color}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:r={VIDEO_FPS}:d={total_duration}",
        # Audio — original narration; outro silence is appended in filter.
        "-i", audio_path,
        # Pad the audio with OUTRO_DUR seconds of silence so the file
        # length matches the video. apad with whole_dur ensures the
        # padding extends to total_duration.
        "-filter_complex",
        (
            f"[0:v]ass='{ass_path}'[v];"
            f"[1:a]apad=whole_dur={total_duration}[a]"
        ),
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest",
        "-t", f"{total_duration}",
        output_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        # Don't dump the entire stderr — last 800 chars is usually the
        # actual error message. The full transcript goes to logs above.
        tail = (proc.stderr or "")[-800:]
        raise RenderError(f"ffmpeg failed: {tail}")


# --------------------------------------------------------------------------
#  Public entrypoint
# --------------------------------------------------------------------------

def render_video(
    conn,
    video_id: int,
    *,
    format: str,
    elevenlabs_api_key: str,
    voice_id: str,
) -> tuple[str, int]:
    """Render an educational video. Returns (filename, file_size_bytes).

    format: 'long' or 'short' — picks voiceover_long (from
            voiceover_text column) or voiceover_short (from
            script_json).
    """
    if format not in ("long", "short"):
        raise RenderError(f"unknown format: {format}")

    row = conn.execute(
        "SELECT * FROM educational_videos WHERE id = ?", (video_id,)
    ).fetchone()
    if not row:
        raise RenderError(f"video {video_id} not found")
    rd = dict(row)
    if rd.get("status") not in ("script_ready", "rendered", "failed"):
        raise RenderError(
            f"cannot render while status={rd.get('status')}; "
            "row must be script_ready first"
        )

    # Pull the script.
    if not rd.get("script_json"):
        raise RenderError("no script on this row — generate first")
    script = json.loads(rd["script_json"])

    # Pick the voiceover for this format.
    if format == "long":
        voiceover = rd.get("voiceover_text") or script.get("voiceover_long") or ""
    else:
        voiceover = script.get("voiceover_short") or ""
    voiceover = voiceover.strip()
    if not voiceover:
        raise RenderError(f"no voiceover_{format} on this row")

    # Beats for visual overlay.
    beats: list[Beat] = []
    if script.get("hook"):
        beats.append(Beat("hook", script["hook"], style="Hook"))
    if script.get("verse_intro"):
        beats.append(Beat("verse_intro", script["verse_intro"], style="Body"))
    if script.get("insight"):
        beats.append(Beat("insight", script["insight"], style="Body"))
    if script.get("close"):
        beats.append(Beat("close", script["close"], style="Small"))
    if not beats:
        raise RenderError("script has no beats to display")

    # 1. TTS
    audio_path = _tts(voiceover, api_key=elevenlabs_api_key, voice_id=voice_id)

    # 2. duration
    audio_duration = _probe_duration(audio_path)
    # Hard sanity check — Shorts have a strict ≤60s budget. We
    # planned for ≤45s of narration + ≤10s outro; abort if we're
    # already over.
    if format == "short" and audio_duration + OUTRO_DUR > 60.0:
        raise RenderError(
            f"short voiceover would render at {audio_duration + OUTRO_DUR:.1f}s "
            f"(>60s Shorts cap). Trim voiceover_short."
        )

    # 3. beat timings
    timings = _build_beat_timings(beats, audio_duration)

    # 4. ASS subtitle file (per-type — Phase 3a does Translation Hides)
    if rd["type"] == "translation_hides":
        ass_text = _build_ass_translation_hides(
            chapter=rd["chapter"],
            verse=rd["verse"],
            beats=beats,
            timings=timings,
            audio_duration=audio_duration,
        )
    else:
        # Other types still fall back to the Translation Hides layout
        # for now — visual differentiation lands in Phase 3b/c.
        ass_text = _build_ass_translation_hides(
            chapter=rd["chapter"],
            verse=rd["verse"],
            beats=beats,
            timings=timings,
            audio_duration=audio_duration,
        )

    # 5. Compose
    out_filename = f"{video_id:06d}-{format}.mp4"
    out_path = os.path.join(OUTPUT_DIR, out_filename)
    with tempfile.NamedTemporaryFile("w", suffix=".ass", delete=False, encoding="utf-8") as f:
        f.write(ass_text)
        ass_path = f.name
    try:
        _compose_mp4(
            audio_path=audio_path,
            ass_path=ass_path,
            audio_duration=audio_duration,
            output_path=out_path,
        )
    finally:
        if os.path.isfile(ass_path):
            os.remove(ass_path)

    size = os.path.getsize(out_path)
    return out_filename, size
