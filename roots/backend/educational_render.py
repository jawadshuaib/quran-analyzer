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
import re
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

# Per-pipeline outro sound bites (e.g. "More details in the
# description"). Each pipeline can have one; we mix it over the
# al-nuqta splash at render time. File extension is preserved from
# the original upload so ffmpeg picks the right decoder.
OUTRO_AUDIO_DIR = os.path.join(os.path.dirname(__file__), "data", "educational_outro_audio")
os.makedirs(OUTRO_AUDIO_DIR, exist_ok=True)

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
# Yellow-gold #FFD700 in ASS BGR. Used for the highlighted Arabic
# word, the matching English phrase in the translation, and the
# Reference badge.
_HIGHLIGHT_COLOR_ASS = "&H0000D7FF"


def _strip_uthmani_marks(text: str) -> str:
    """Remove Quranic-script marks libass struggles to render.

    Mirrors the helper in app.py used by the recitation pipeline:
      U+0671 (ٱ alef wasla) → U+0627 (ا plain alef)
      U+0653 maddah, U+0654 hamza-above, U+0670 superscript alef,
      U+06D6-U+06ED small high/low marks (cancels out the broken-square
      glyphs that show on many Liberation/Amiri builds).
    """
    if not text:
        return text
    out = text.replace("ٱ", "ا")
    return re.sub(r"[ٰٓٔۖ-ۭ]", "", out)


# Verse-excerpt thresholds. Median verse is ~14 words / 92 chars;
# anything beyond ~16 words pushes the bottom-anchored translation
# off-screen at fontsize 108. We window a few words on each side of
# the highlighted target so the viewer still sees the target word in
# its immediate context, with "…" markers indicating truncation.
_ARABIC_EXCERPT_THRESHOLD_WORDS = 16
_ARABIC_EXCERPT_SIDE_WORDS = 5
_TRANSLATION_EXCERPT_THRESHOLD_CHARS = 200
_TRANSLATION_EXCERPT_SIDE_CHARS = 90


def _excerpt_arabic_around_word(
    text: str,
    target_word_pos: int,
    *,
    threshold_words: int = _ARABIC_EXCERPT_THRESHOLD_WORDS,
    side_words: int = _ARABIC_EXCERPT_SIDE_WORDS,
) -> tuple[str, int]:
    """For long verses, take a window of `side_words` on each side of
    the highlighted word and prepend / append "…" so the target word
    stays in view with its immediate context. Returns (excerpted_text,
    new_target_word_pos). For short verses or out-of-range positions,
    returns the input unchanged."""
    if not text:
        return text, target_word_pos
    words = text.split()
    if len(words) <= threshold_words:
        return text, target_word_pos
    idx = target_word_pos - 1
    if idx < 0 or idx >= len(words):
        return text, target_word_pos
    start = max(0, idx - side_words)
    end = min(len(words), idx + side_words + 1)
    window = words[start:end]
    new_idx = idx - start
    prefix_words = ["…"] if start > 0 else []
    suffix_words = ["…"] if end < len(words) else []
    final = prefix_words + window + suffix_words
    new_pos = new_idx + len(prefix_words) + 1
    return " ".join(final), new_pos


def _excerpt_translation_around_gloss(
    text: str,
    gloss: str | None,
    *,
    threshold_chars: int = _TRANSLATION_EXCERPT_THRESHOLD_CHARS,
    side_chars: int = _TRANSLATION_EXCERPT_SIDE_CHARS,
) -> str:
    """For long English translations, return a window of `side_chars`
    around the gloss substring, snapped to word boundaries with "…"
    markers. If the gloss can't be located or the translation is
    already short enough, returns the input unchanged."""
    if not text or len(text) <= threshold_chars:
        return text
    if not gloss:
        return text
    needle = _PARENTHETICAL_RE.sub("", gloss).strip().strip(",.;:")
    if not needle or len(needle) < 2:
        return text
    lower = text.lower()
    pos = lower.find(needle.lower())
    if pos < 0:
        head = needle.split()[-1] if needle.split() else ""
        if len(head) < 3:
            return text
        pos = lower.find(head.lower())
        if pos < 0:
            return text
        needle = head
    start = max(0, pos - side_chars)
    end = min(len(text), pos + len(needle) + side_chars)
    # Snap to word boundaries so we don't slice a word in half.
    while start > 0 and text[start - 1].isalnum():
        start -= 1
    while end < len(text) and text[end].isalnum():
        end += 1
    excerpt = text[start:end].strip()
    prefix = "… " if start > 0 else ""
    suffix = " …" if end < len(text) else ""
    return prefix + excerpt + suffix


def _format_arabic_with_highlight(text: str, target_word_pos: int) -> str:
    """Wrap the target word (1-indexed) in inline gold-yellow ASS tags.
    Splits by whitespace; word_pos matches the same 1-indexed position
    used in morphology and the reader UI. Strips Uthmani marks first
    so libass renders the verse cleanly, then trims long verses to a
    window around the target word so the bottom-anchored translation
    stays on screen. Falls back to unhighlighted text if word_pos is
    out of range."""
    text = _strip_uthmani_marks(text or "")
    text, target_word_pos = _excerpt_arabic_around_word(text, target_word_pos)
    words = text.split()
    idx = target_word_pos - 1
    if idx < 0 or idx >= len(words):
        return _ass_escape(text)
    before = " ".join(words[:idx])
    target = words[idx]
    after = " ".join(words[idx + 1:])
    parts = []
    if before:
        parts.append(_ass_escape(before) + " ")
    # \c switches primary colour; \r resets to the line's style.
    # Gold-yellow matches the Reference badge so the eye links
    # the badge → the highlighted word → the English equivalent.
    parts.append(f"{{\\c{_HIGHLIGHT_COLOR_ASS}&}}" + _ass_escape(target) + "{\\r}")
    if after:
        parts.append(" " + _ass_escape(after))
    return "".join(parts)


# Strip leading/trailing parentheticals — "(as) few" → "few",
# "[remember] when" → "when". Used so a per-word gloss like
# "(as) few" matches "few" in the verse translation.
_PARENTHETICAL_RE = re.compile(r"\s*[(\[][^\])]*[)\]]\s*")


def _format_translation_with_highlight(text: str, gloss: str | None) -> str:
    """If `gloss` appears (case-insensitively, ignoring parentheticals)
    in `text`, wrap that range in inline gold-yellow ASS tags. Otherwise
    return the translation as-is. Operator gets a visual link between
    the highlighted Arabic word and the corresponding English phrase.

    Long translations are first windowed around the gloss so the
    on-screen text fits in the bottom-anchored Translation slot
    without overlapping the Arabic verse."""
    if not text:
        return ""
    text = _excerpt_translation_around_gloss(text, gloss)
    safe = _ass_escape(text)
    if not gloss:
        return safe
    needle = _PARENTHETICAL_RE.sub("", gloss).strip().strip(",.;:")
    if not needle or len(needle) < 2:
        return safe
    # Case-insensitive substring search on the unescaped text.
    lower = text.lower()
    idx = lower.find(needle.lower())
    if idx < 0:
        # Try just the head word as a last resort — "your eyes" → "eyes".
        head = needle.split()[-1] if needle.split() else ""
        if len(head) < 3:
            return safe
        idx = lower.find(head.lower())
        if idx < 0:
            return safe
        needle = head
    end = idx + len(needle)
    # Recompute the highlighted span on the original (case-preserved)
    # text and rebuild the escaped output around it.
    pre = _ass_escape(text[:idx])
    mid = _ass_escape(text[idx:end])
    post = _ass_escape(text[end:])
    return pre + f"{{\\c{_HIGHLIGHT_COLOR_ASS}&}}" + mid + "{\\r}" + post


def _wrap_arabic(text: str, width_chars: int = 28) -> str:
    """Wrap by word so long verses fit on screen. Preserves any inline
    ASS color tags by splitting on visible spaces only — the
    `_format_arabic_with_highlight` output uses spaces between words
    even after the highlight tags, so simple split-and-rejoin works."""
    # Split into [pre-tag, color-tag, target, color-end, post-tag] safely
    # by extracting the plain text first, wrapping that, then re-applying
    # the highlight at the corresponding word index.
    # Simpler approach: textwrap on the rendered string. ASS tags are
    # treated as part of words; libass tolerates them mid-line.
    return "\\N".join(textwrap.wrap(text, width=width_chars) or [text])


@dataclass
class WordOriginsSegment:
    chapter: int
    verse: int
    arabic_text: str
    translation: str
    target_word_pos: int
    # Per-word English gloss for the target Arabic word. When non-empty
    # and the gloss text appears as a substring in `translation`, the
    # renderer highlights that span in gold so the viewer can see the
    # English equivalent of the highlighted Arabic word. Optional —
    # falls back to a plain translation when missing.
    target_gloss: str | None = None


def _build_ass_word_origins(
    *,
    segments: list[WordOriginsSegment],
    audio_duration: float,
    voiceover_text: str,
    beat_word_counts: list[int],
    outro_duration: float = OUTRO_DUR,
) -> str:
    """Word Origins template: three segments, each shows a Quran verse
    on screen with the target word highlighted in gold. Narration
    plays underneath; we DO NOT show the script text on screen.

    Layout per segment (1080x1920):
      - Top: gold "Quran X:Y" reference badge
      - Center: Arabic verse (RTL, large Amiri), target word in gold
      - Below: English translation in smaller white
    """
    lines: list[str] = []
    if not segments:
        raise RenderError("word_origins template needs at least 1 segment")
    if not audio_duration or audio_duration <= 0:
        raise RenderError("invalid audio_duration for word_origins template")

    # Allocate audio time to segments proportional to the narration
    # word counts (hook+tidbit_root → seg 1, tidbit_quran → seg 2,
    # tidbit_semitic → seg 3). Falls back to equal thirds if the
    # weights aren't available.
    if beat_word_counts and len(beat_word_counts) == len(segments):
        total = sum(max(w, 1) for w in beat_word_counts)
        weights = [max(w, 1) / total for w in beat_word_counts]
    else:
        weights = [1.0 / len(segments)] * len(segments)

    durations = [audio_duration * w for w in weights]
    # Floor 4s per segment so the verse has time to land visually.
    MIN_PER_SEG = 4.0
    total_floor = MIN_PER_SEG * len(segments)
    if sum(durations) < total_floor:
        durations = [audio_duration / len(segments)] * len(segments)
    starts: list[float] = [0.0]
    for d in durations[:-1]:
        starts.append(starts[-1] + d)
    timings = [(starts[i], starts[i] + durations[i]) for i in range(len(segments))]
    timings[-1] = (timings[-1][0], audio_duration)

    # Vertical layout (1080x1920) — anchor-based, NOT \pos, so long
    # verses don't push past their slot and overlap the translation:
    #   Reference   Alignment=8 (top-center)    MarginV=80    from top
    #   Arabic      Alignment=8 (top-center)    MarginV=340   from top
    #                 → verse grows downward only; reference safely above
    #   Translation Alignment=2 (bottom-center) MarginV=140   from bottom
    #                 → translation pinned to base; never overlaps verse
    for seg, (s, e) in zip(segments, timings):
        # Reference badge (top-center) — fades in slightly later than
        # the verse so the eye lands on the Arabic first.
        ref = f"Quran {seg.chapter}:{seg.verse}"
        lines.append(
            f"Dialogue: 0,{_ass_time(s)},{_ass_time(e)},Reference,,0,0,0,,"
            f"{{\\fad(450,300)}}{_ass_escape(ref)}"
        )
        # Arabic verse — top-aligned with margin so the verse grows
        # downward as it wraps; the bottom of long verses still has
        # plenty of clearance from the bottom-anchored translation.
        ar = _format_arabic_with_highlight(seg.arabic_text, seg.target_word_pos)
        lines.append(
            f"Dialogue: 0,{_ass_time(s)},{_ass_time(e)},ArabicVerse,,0,0,0,,"
            f"{{\\fad(400,300)}}{ar}"
        )
        # English translation pinned to the bottom of the frame so the
        # verse and translation never overlap regardless of verse
        # length, with the gloss-matched phrase highlighted in
        # gold-yellow when found.
        if seg.translation:
            tr = _format_translation_with_highlight(seg.translation, seg.target_gloss)
            lines.append(
                f"Dialogue: 0,{_ass_time(s)},{_ass_time(e)},Translation,,0,0,0,,"
                f"{{\\fad(500,300)}}{tr}"
            )

    # Outro card — al-nuqta branding. Identical to the translation_hides
    # template so all series share the same close. outro_duration is
    # caller-supplied so the splash holds long enough to cover any
    # configured outro audio bite.
    narration_end = audio_duration
    outro_end = audio_duration + outro_duration
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
    # voiceover_text isn't used in the visual layer — narration is the
    # audio track only. Suppress the unused-arg warning.
    del voiceover_text

    header = _ASS_HEADER.format(
        w=VIDEO_WIDTH, h=VIDEO_HEIGHT,
        font_sans=FONT_SANS, font_arabic=FONT_ARABIC,
    )
    return header + "\n".join(lines) + "\n"


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
Style: Reference,{font_sans},86,&H0000D7FF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,2,8,40,40,80,1
Style: ArabicVerse,{font_arabic},108,&H00FFFFFF,&H000000FF,&H00000000,&HC0000000,0,0,0,0,100,100,0,0,1,4,3,8,60,60,340,1
Style: Translation,{font_sans},58,&H00FFFFFF,&H000000FF,&H00000000,&HC0000000,0,0,0,0,100,100,0,0,1,3,2,2,60,60,140,1
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
    outro_duration: float = OUTRO_DUR,
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
    outro_end = audio_duration + outro_duration

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
        w=VIDEO_WIDTH, h=VIDEO_HEIGHT,
        font_sans=FONT_SANS, font_arabic=FONT_ARABIC,
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
    background_video_path: str | None = None,
    dim_during_narration: bool = True,
    outro_duration: float = OUTRO_DUR,
    outro_audio_path: str | None = None,
) -> None:
    """ffmpeg compose. If `background_video_path` is set, the supplied
    mp4 is looped, scaled, cropped to 1080x1920, and dimmed by ~40%
    so white narration text on top stays legible. Otherwise we fall
    back to a warm-charcoal solid background. ASS subtitles overlay.

    Audio: the narration is padded with silence to (audio_duration +
    outro_duration). If `outro_audio_path` is provided (a sound bite
    for the outro), it's delayed by `audio_duration` and mixed into
    that silence so the splash card has audio over it. Caller is
    responsible for choosing `outro_duration` long enough that the
    sound bite has time to finish."""
    total_duration = audio_duration + outro_duration
    # Warm-charcoal fallback — matches al-nuqta's dark accent.
    bg_color = "0x2D2620"

    # Outro dim — drops a 75% black box over the entire frame from the
    # moment the narration ends so the al-nuqta splash text reads
    # cleanly against a near-black background instead of the still
    # animating bg video. Mirrors the Arabic pipeline's outro dim.
    outro_dim = (
        f"drawbox=x=0:y=0:w=iw:h=ih:color=black@0.75:t=fill"
        f":enable='gte(t\\,{audio_duration:.3f})'"
    )

    # Audio filter — common to both bg-video and solid-bg paths. When
    # outro_audio_path is set, mix the outro bite into the padded
    # silence at offset = audio_duration. amix normalize=0 keeps the
    # bite at full volume during what would otherwise be silent
    # outro time (narration is already silent there post-pad, so the
    # mix output equals the bite's volume).
    if outro_audio_path and os.path.isfile(outro_audio_path):
        delay_ms = int(audio_duration * 1000)
        audio_filter = (
            f"[1:a]apad=whole_dur={total_duration}[narr];"
            f"[2:a]adelay={delay_ms}|{delay_ms}[outro_aud];"
            f"[narr][outro_aud]amix=inputs=2:duration=longest:normalize=0[a]"
        )
        extra_inputs = ["-i", outro_audio_path]
    else:
        audio_filter = f"[1:a]apad=whole_dur={total_duration}[a]"
        extra_inputs = []

    if background_video_path and os.path.isfile(background_video_path):
        # Loop the bg video for the entire run, scale to fill 1080x1920
        # (cover, not contain), crop the overflow, dim during narration
        # (gated by dim_during_narration) so foreground text reads,
        # then dim deeper during the outro.
        narration_dim = "eq=brightness=-0.20:saturation=0.85," if dim_during_narration else ""
        vf = (
            f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
            "setsar=1,"
            "format=yuv420p,"
            f"{narration_dim}"
            f"{outro_dim},"
            f"trim=duration={total_duration},setpts=PTS-STARTPTS"
        )
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", background_video_path,
            "-i", audio_path,
            *extra_inputs,
            "-filter_complex",
            (
                f"[0:v]{vf}[bg];"
                f"[bg]ass='{ass_path}'[v];"
                f"{audio_filter}"
            ),
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k",
            "-shortest",
            "-t", f"{total_duration}",
            output_path,
        ]
    else:
        # Solid-bg path also gets the outro dim so the splash card
        # has the same visual treatment whether or not a tagged
        # background video was found.
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c={bg_color}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:r={VIDEO_FPS}:d={total_duration}",
            "-i", audio_path,
            *extra_inputs,
            "-filter_complex",
            (
                f"[0:v]{outro_dim}[bg];"
                f"[bg]ass='{ass_path}'[v];"
                f"{audio_filter}"
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
        tail = (proc.stderr or "")[-800:]
        raise RenderError(f"ffmpeg failed: {tail}")


# --------------------------------------------------------------------------
#  Public entrypoint
# --------------------------------------------------------------------------

def _build_word_origins_ass_for_row(
    conn, rd: dict, script: dict, audio_duration: float, voiceover: str,
    *, outro_duration: float = OUTRO_DUR,
) -> str:
    """Glue between the row/script and the word_origins ASS builder.
    Looks up the source verse + the two selected_verse_refs in the
    payload, picks the word position for each (where the same root
    appears), and assembles the segment list."""
    payload_json = rd.get("payload_json") or "{}"
    try:
        payload = json.loads(payload_json)
    except Exception:
        payload = {}

    # Source verse — from the candidate row itself.
    src_verse_row = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
        (rd["chapter"], rd["verse"]),
    ).fetchone()
    src_translation_row = conn.execute(
        "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
        (rd["chapter"], rd["verse"]),
    ).fetchone()
    if not src_verse_row:
        raise RenderError(f"source verse {rd['chapter']}:{rd['verse']} not found")

    def _gloss_for(c: int, v: int, p: int) -> str | None:
        """Best per-word English for the target Arabic word. Tries
        ai_word_meanings.preferred_translation / meaning_short first
        (curated when present), then word_glosses.translation_en
        (broader coverage)."""
        try:
            wm = conn.execute(
                "SELECT COALESCE(preferred_translation, meaning_short) AS t "
                "FROM ai_word_meanings WHERE chapter=? AND verse=? AND word_pos=? LIMIT 1",
                (c, v, p),
            ).fetchone()
            if wm and wm["t"]:
                return (wm["t"] or "").strip()
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

    src_word_pos = int(rd.get("anchor_word_pos") or 1)
    segments: list[WordOriginsSegment] = [
        WordOriginsSegment(
            chapter=rd["chapter"],
            verse=rd["verse"],
            arabic_text=src_verse_row["text_uthmani"],
            translation=(src_translation_row["text_en"] if src_translation_row else ""),
            target_word_pos=src_word_pos,
            target_gloss=_gloss_for(rd["chapter"], rd["verse"], src_word_pos),
        ),
    ]

    # selected_verse_refs[0..1] from script — match against payload's
    # other_verses to pull the word_pos. Validation guarantees these
    # refs come from the candidate pool, so the lookup should succeed.
    pool: dict[tuple[int, int], dict] = {
        (o["chapter"], o["verse"]): o
        for o in (payload.get("other_verses") or [])
    }
    refs = script.get("selected_verse_refs") or []
    for r in refs[:2]:
        try:
            c = int(r["chapter"]); v = int(r["verse"])
        except (KeyError, TypeError, ValueError):
            continue
        ov = pool.get((c, v))
        if not ov:
            # Validation should have prevented this, but be defensive.
            raise RenderError(
                f"selected_verse_ref {c}:{v} missing from payload other_verses"
            )
        ow_pos = int(ov.get("word_pos") or 1)
        segments.append(WordOriginsSegment(
            chapter=c, verse=v,
            arabic_text=ov.get("text_uthmani") or "",
            translation=ov.get("translation") or "",
            target_word_pos=ow_pos,
            target_gloss=_gloss_for(c, v, ow_pos),
        ))

    # If for any reason we have fewer than 3 segments (e.g., LLM gave
    # only 1 ref, or pool had < 2 — extremely rare), pad by duplicating
    # the source verse so the layout doesn't collapse.
    while len(segments) < 3:
        segments.append(segments[0])
    segments = segments[:3]

    # Beat-weight allocation: hook+tidbit_root → seg 1,
    # tidbit_quran_usage → seg 2, tidbit_semitic → seg 3.
    def _wc(s: str) -> int:
        import re as _re
        return len(_re.findall(r"\b\w[\w'-]*\b", s or ""))
    beat_word_counts = [
        _wc(script.get("hook", "")) + _wc(script.get("tidbit_about_root", "")),
        _wc(script.get("tidbit_about_quran_usage", "")),
        _wc(script.get("tidbit_about_semitic", "")) + _wc(script.get("close", "")),
    ]

    return _build_ass_word_origins(
        segments=segments,
        audio_duration=audio_duration,
        voiceover_text=voiceover,
        beat_word_counts=beat_word_counts,
        outro_duration=outro_duration,
    )


# --------------------------------------------------------------------------
#  Background video selection
# --------------------------------------------------------------------------

# Per-type tag the renderer looks for in admin_resources.tags. If no
# resources match, the renderer falls back to the solid-color bg.
_BG_TAG_PER_TYPE = {
    "word_origins": "word-origins",
    "translation_hides": "translation-hides",
    "grammar_insights": "grammar-insights",
}


def _pick_background(conn, vtype: str) -> str | None:
    """Random admin_resources entry whose `tags` contains the
    series-specific tag. Returns the absolute path to the mp4, or
    None if the tags column doesn't exist or no matches found.
    The educational pipeline will fall back to a solid bg when None."""
    tag = _BG_TAG_PER_TYPE.get(vtype)
    if not tag:
        return None
    try:
        cols = [c[1] for c in conn.execute("PRAGMA table_info(admin_resources)").fetchall()]
        if "tags" not in cols:
            return None
        # SQLite has no "split into list" — match the comma-bounded
        # token by wrapping both with commas. Stored format is
        # "alpha,beta,word-origins" (no spaces, lowercase).
        rows = conn.execute(
            "SELECT filename FROM admin_resources "
            "WHERE ',' || COALESCE(tags,'') || ',' LIKE ?",
            (f"%,{tag},%",),
        ).fetchall()
    except Exception:
        return None
    if not rows:
        return None
    import random as _r
    pick = _r.choice(rows)
    path = os.path.join(
        os.path.dirname(__file__), "data", "resources", pick["filename"],
    )
    return path if os.path.isfile(path) else None


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

    Routing: `word_origins` videos render through the Remotion
    pipeline (richer per-slide visuals + karaoke captions). The
    other types stay on the ffmpeg + ASS path below until they get
    Remotion templates of their own. The orchestrator's status
    transitions and DB writes are unaffected — both renderers
    return the same (filename, size) shape.
    """
    if format not in ("long", "short"):
        raise RenderError(f"unknown format: {format}")

    row = conn.execute(
        "SELECT * FROM educational_videos WHERE id = ?", (video_id,)
    ).fetchone()
    if not row:
        raise RenderError(f"video {video_id} not found")
    rd = dict(row)

    # Route word_origins to the Remotion renderer. The shape of the
    # call is the same — same inputs, same return, same output
    # path — so the orchestrator's UPDATE statement after this
    # function returns is unchanged.
    if rd["type"] == "word_origins":
        try:
            import educational_render_remotion as _rr
        except Exception as e:
            raise RenderError(f"Remotion renderer module failed to load: {e}")
        try:
            return _rr.render_word_origins_video(
                conn, video_id,
                format=format,
                elevenlabs_api_key=elevenlabs_api_key,
                voice_id=voice_id,
            )
        except _rr.RemotionRenderError as e:
            # Convert to RenderError so the orchestrator's existing
            # exception-to-status-failed path catches it identically
            # to ffmpeg failures.
            raise RenderError(str(e))
    # NOTE: We deliberately don't check status here. The HTTP endpoint
    # already gates on status before flipping the row to 'rendering'
    # and spawning this work in a background thread; by the time we
    # arrive, the row IS in 'rendering' state and that's expected.
    # Pull the script.
    if not rd.get("script_json"):
        raise RenderError("no script on this row — generate first")
    script = json.loads(rd["script_json"])

    # Pick the voiceover for this format. Long form lives in the
    # voiceover_text column (legacy storage) with a fallback to
    # script_json's voiceover_long; short form lives in script_json.
    # Both go through the same fail-loud check so an empty short
    # render can't silently produce a 0-second narration mp4.
    if format == "long":
        voiceover = (rd.get("voiceover_text") or script.get("voiceover_long") or "").strip()
    else:
        voiceover = (script.get("voiceover_short") or "").strip()
    if not voiceover:
        raise RenderError(
            f"no voiceover_{format} text on this row — regenerate the script"
        )

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
    # No hard length cap. The historical reason for clamping shorts at
    # 60s was YouTube's someone-else-audio policy on Shorts longer
    # than a minute — but educational videos contain only ElevenLabs
    # narration (our own AI voice), no reciter audio, so the policy
    # doesn't apply. A short that runs 65-90s is fine.

    # 3. beat timings
    timings = _build_beat_timings(beats, audio_duration)

    # Per-pipeline overrides (background-dim flag, optional outro
    # sound bite). Manual rows (no pipeline_id) default sensibly.
    dim_during_narration = True
    outro_audio_path: str | None = None
    outro_audio_duration = 0.0
    if rd.get("pipeline_id"):
        prow = conn.execute(
            "SELECT show_dim_background, outro_audio_filename "
            "FROM educational_pipelines WHERE id = ?",
            (rd["pipeline_id"],),
        ).fetchone()
        if prow is not None:
            dim_during_narration = bool(prow["show_dim_background"])
            fname = prow["outro_audio_filename"] if "outro_audio_filename" in prow.keys() else None
            if fname:
                candidate = os.path.join(OUTRO_AUDIO_DIR, fname)
                if os.path.isfile(candidate):
                    outro_audio_path = candidate
                    try:
                        outro_audio_duration = _probe_duration(candidate)
                    except Exception as e:
                        # Don't block render — fall back to silent outro.
                        print(f"[educational render] outro audio probe failed: {e}")
                        outro_audio_path = None

    # Outro window must hold long enough for the audio to finish, plus
    # a small tail so the splash card doesn't cut at the same instant
    # the audio does. Default OUTRO_DUR (5s) is the floor.
    outro_duration = max(OUTRO_DUR, outro_audio_duration + 0.5) if outro_audio_path else OUTRO_DUR

    # 4. ASS subtitle file — per-type template selection
    if rd["type"] == "word_origins":
        ass_text = _build_word_origins_ass_for_row(
            conn, rd, script, audio_duration, voiceover,
            outro_duration=outro_duration,
        )
    else:
        # Translation Hides + Grammar Insights both use the beat-overlay
        # template for now (script text on screen). Visual differentiation
        # for Grammar Insights lands later.
        ass_text = _build_ass_translation_hides(
            chapter=rd["chapter"],
            verse=rd["verse"],
            beats=beats,
            timings=timings,
            audio_duration=audio_duration,
            outro_duration=outro_duration,
        )

    # 5. Compose
    out_filename = f"{video_id:06d}-{format}.mp4"
    out_path = os.path.join(OUTPUT_DIR, out_filename)
    with tempfile.NamedTemporaryFile("w", suffix=".ass", delete=False, encoding="utf-8") as f:
        f.write(ass_text)
        ass_path = f.name
    bg_path = _pick_background(conn, rd["type"])
    try:
        _compose_mp4(
            audio_path=audio_path,
            ass_path=ass_path,
            audio_duration=audio_duration,
            output_path=out_path,
            background_video_path=bg_path,
            dim_during_narration=dim_during_narration,
            outro_duration=outro_duration,
            outro_audio_path=outro_audio_path,
        )
    finally:
        if os.path.isfile(ass_path):
            os.remove(ass_path)

    size = os.path.getsize(out_path)
    return out_filename, size
