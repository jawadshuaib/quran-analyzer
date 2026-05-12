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
import educational_planner as _planner


class RemotionRenderError(Exception):
    """Raised when the Remotion subprocess fails or returns a malformed
    result. Caller in the orchestrator catches Exception and writes
    str(e)[:1000] into educational_videos.error_message."""


# Where the renderer subproject lives. Dev and prod have different
# layouts:
#   - Dev: /repo/roots/backend/  + /repo/roots/video-renderer/
#     → resolved via _THIS_DIR/../video-renderer
#   - Prod (Docker): /app/  + /app/video-renderer/
#     → set REMOTION_RENDERER_DIR=/app/video-renderer in the image
# Operators can also override locally for testing alternate trees.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_RENDERER_DIR = os.path.normpath(os.path.join(_THIS_DIR, "..", "video-renderer"))
RENDERER_DIR = os.environ.get("REMOTION_RENDERER_DIR", _DEFAULT_RENDERER_DIR)
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
    caller decides whether to skip the slide or fail.

    Translation source priority:
      1. ai_translations (Quran-only AI revision) — matches what the
         app shows on /verse/<s>:<a> and /read/<surah>. Multiple rows
         can exist per verse from different generation runs; we pick
         the highest id (most recent) and prefer revised_text over
         translation_text.
      2. translations (conventional source like Sahih International)
         — fallback when no AI translation exists.

    Earlier code went straight to `translations`, which produced
    rendered videos with a different translation than the website
    (e.g. "It is You we worship" on the video vs "You alone we serve"
    in the app for 1:5). Operators noticed; this aligns the two.
    """
    arow = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter=? AND verse=?",
        (c, v),
    ).fetchone()
    if not arow:
        return None

    translation = ""
    ai_row = conn.execute(
        "SELECT revised_text, translation_text FROM ai_translations "
        "WHERE chapter=? AND verse=? "
        "ORDER BY id DESC LIMIT 1",
        (c, v),
    ).fetchone()
    if ai_row:
        translation = (ai_row["revised_text"] or ai_row["translation_text"] or "").strip()
    if not translation:
        erow = conn.execute(
            "SELECT text_en FROM translations WHERE chapter=? AND verse=? LIMIT 1",
            (c, v),
        ).fetchone()
        if erow:
            translation = (erow["text_en"] or "").strip()

    return {
        "arabic": arow["text_uthmani"],
        "translation": translation,
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


def _build_outro_slide() -> dict:
    """Slide N — Mushaf-style "Learn Qur'an, every day." splash with
    the SUBSCRIBE pill CTA. Used by every Remotion-rendered
    educational video (word_origins / grammar_insights / word_detail).
    The renderer's OutroPage component holds the actual visual
    (background photograph, headline, CTA, animation choreography);
    this builder just emits the slide marker.

    INTENTIONALLY has no narration: the optional outro audio bite
    is the only sound that should play here, and any close-beat
    narration goes on the final verse slide instead so it finishes
    BEFORE the splash appears (otherwise the splash visual is up
    while the close text is still being spoken — visually wrong).

    The outro audio bite is wired in by the caller (which knows
    the pipeline_id and can look up outro_audio_filename); we
    leave that field empty here so this builder has no DB
    dependency. siteName + tagline used to drive a text splash but
    the renderer now ignores them — they stay on the slide for
    backward compatibility with any older payloads still in the
    queue.
    """
    return {
        "type": "outro",
        # 3 seconds is enough for the full animation choreography
        # (bg fade → Ken Burns → headline → CTA pill → bell jingle)
        # and keeps the outro from feeling like dead air. When the
        # pipeline has an outro audio bite staged, the caller bumps
        # this up to match the audio length below.
        "durationSec": 3,
        # Legacy fields — ignored by the current OutroPage but kept
        # so the slide schema continues to validate older payloads.
        "siteName": "al-nuqta.com",
        "tagline": "A Root Based Translation of the Quran",
    }


def _merge_close_into_last_verse(slides: list[dict], close_text: str) -> None:
    """Append the close-beat narration onto the last verse-flow
    slide before the outro. Mutates `slides` in place. If there's
    no verse slide to merge into (rare — shouldn't happen for
    word_origins), the close is silently dropped to avoid
    creating a phantom narration on the outro splash."""
    close = (close_text or "").strip()
    if not close:
        return
    # Walk backwards to find the last verse slide.
    for s in reversed(slides):
        if s.get("type") == "verse-flow":
            existing = ((s.get("narration") or {}).get("text") or "").strip()
            combined = f"{existing} {close}".strip() if existing else close
            s["narration"] = {"text": sanitize_for_tts(combined).strip()}
            return


def _stage_outro_audio(pipeline_id: int | None, conn) -> tuple[str | None, float]:
    """If the pipeline has an outro_audio_filename configured AND the
    file exists on disk, copy it into the renderer's public/
    directory and return (filename, duration_seconds). Returns
    (None, 0.0) if no outro audio is configured or the file is
    missing.

    Mirrors the flow educational_render uses to find the outro
    audio for the ffmpeg path; reusing OUTRO_AUDIO_DIR from that
    module keeps the source-of-truth single. Also reuses
    educational_render._probe_duration so the duration math is
    consistent across both renderers."""
    if not pipeline_id:
        return None, 0.0
    try:
        prow = conn.execute(
            "SELECT outro_audio_filename FROM educational_pipelines WHERE id = ?",
            (pipeline_id,),
        ).fetchone()
    except Exception:
        return None, 0.0
    if not prow:
        return None, 0.0
    fname = prow["outro_audio_filename"] if "outro_audio_filename" in prow.keys() else None
    if not fname:
        return None, 0.0

    # Pull the source from educational_render's directory rather
    # than re-defining the path. Single source of truth — if that
    # module's OUTRO_AUDIO_DIR ever changes, we follow.
    import educational_render as _r
    src = os.path.join(_r.OUTRO_AUDIO_DIR, fname)
    if not os.path.isfile(src):
        return None, 0.0

    dest_dir = os.path.join(RENDERER_DIR, "public")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, fname)
    # Always copy — file might have been replaced via the admin UI
    # since the last render, and the renderer's public/ is
    # gitignored so there's no merge conflict to worry about.
    shutil.copyfile(src, dest)

    # Probe duration so the outro slide can be sized to fit the
    # whole bite. Failure here just falls back to the default
    # 5s — better than refusing to render.
    duration = 0.0
    try:
        duration = _r._probe_duration(dest)
    except Exception as e:
        print(f"[remotion] outro audio probe failed: {e}; using default duration")
    return fname, duration


def _payload_from_planner_slides(
    conn,
    rd: dict,
    payload_inner: dict,
    planned: list[dict],
) -> list[dict]:
    """Convert the Ollama planner's output into Remotion slide dicts.
    The planner returns abstract slide descriptions (type + narration
    + verse refs); we look up the verse Arabic/translation and the
    per-word gloss here so that's done once and the renderer doesn't
    need to round-trip back to SQLite.

    Special case: any narration the planner placed on the OUTRO
    slide is moved onto the last verse slide instead. The outro
    splash should be silent (or play just the optional outro audio
    bite); narration overlapping with the splash visual is
    confusing — the audience reads the splash as "the end" but
    hears the speaker still talking.
    """
    out: list[dict] = []
    pending_outro_narration = ""

    for s in planned:
        narration_text = (s.get("narration") or "").strip()
        if s["type"] == "root":
            hook = narration_text or (rd.get("hook") or "")
            # tidbit_root is unused here — the planner has already
            # decided what the root slide says, and that text lives
            # in narration_text.
            out.append(_build_root_slide(payload_inner, hook, ""))
            # _build_root_slide synthesizes its own narration from
            # hook+tidbit; we want the planner's polished version
            # exactly, so overwrite.
            out[-1]["narration"] = {"text": sanitize_for_tts(narration_text).strip()}
        elif s["type"] == "verse":
            verse_slide = _build_verse_flow_slide(
                conn,
                int(s["surah"]),
                int(s["ayah"]),
                int(s.get("word_pos") or 1),
                narration_text=narration_text,
            )
            if verse_slide:
                out.append(verse_slide)
        elif s["type"] == "outro":
            # Defer the planner's outro narration — we'll merge it
            # onto the last verse slide AFTER the loop finishes.
            pending_outro_narration = narration_text
            out.append(_build_outro_slide())

    # Merge the planner's outro narration onto the last verse slide.
    # This guarantees the close-beat finishes BEFORE the splash
    # appears.
    if pending_outro_narration:
        _merge_close_into_last_verse(out, pending_outro_narration)

    return out


def _static_fallback_slides(conn, rd: dict, script: dict, payload_inner: dict) -> list[dict]:
    """Original static mapping used when the Ollama planner is
    unavailable or produces invalid output. Same logic that shipped
    in the first cut: Root → Source → Cross-ref[0] → Outro."""
    slides: list[dict] = []

    hook = (script.get("hook") or "").strip()
    tidbit_root = (script.get("tidbit_about_root") or "").strip()
    slides.append(_build_root_slide(payload_inner, hook, tidbit_root))

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
            conn, c, v, wp,
            narration_text=script.get("tidbit_about_semitic", ""),
        )
        if cross_slide:
            slides.append(cross_slide)
        break

    # Outro slide is silent — close beat goes onto the LAST verse
    # slide instead so it finishes before the splash appears. Same
    # rule the planner output processor applies, kept consistent
    # so both paths produce identically-shaped output.
    slides.append(_build_outro_slide())
    _merge_close_into_last_verse(slides, script.get("close", ""))
    return slides


def build_word_origins_payload(conn, rd: dict, script: dict) -> dict:
    """Convert an educational_videos row + its script into a Remotion
    payload. Tries the Ollama-driven planner first (which polishes
    the narration AND matches it to the verses being shown); falls
    back to the static slot-mapping if the planner is unavailable
    or produces invalid output.

    Both paths return the same slide-dict shape, so downstream code
    (subprocess invocation, mp4 staging) doesn't care which produced
    the slides.
    """
    payload_inner = json.loads(rd.get("payload_json") or "{}")
    anchor_word_pos = int(rd.get("anchor_word_pos") or 1)

    slides: list[dict] = []
    # Try the planner. Any failure (Ollama down, invalid output,
    # etc.) silently drops to the static path — we don't want a
    # planner outage to fail the whole render.
    try:
        planned = _planner.plan_word_origins_slides(
            conn, payload_inner, script, anchor_word_pos,
        )
        slides = _payload_from_planner_slides(conn, rd, payload_inner, planned)
        # Need at least 3 slides (root + 1 verse + outro) for the
        # planner output to be useful; otherwise treat as failure
        # and fall back.
        if len(slides) < 3:
            raise _planner.PlannerError(
                f"planner output yielded only {len(slides)} renderable slides"
            )
        print(f"[remotion] Planner produced {len(slides)} slides for video {rd['id']}")
    except Exception as e:
        print(f"[remotion] Planner failed for video {rd['id']}: {e}. Falling back to static mapping.")
        slides = _static_fallback_slides(conn, rd, script, payload_inner)

    # Stage the pipeline's outro sound bite (if any) into the
    # renderer's public/ and attach to whichever slide is the outro.
    # We do this last so both the planner and fallback paths get the
    # same treatment. Also extend the outro slide's durationSec to
    # cover the bite plus a 0.5s tail — same logic the legacy ffmpeg
    # path uses (educational_render._compose_mp4 outro_duration).
    outro_audio_filename, outro_audio_duration = _stage_outro_audio(rd.get("pipeline_id"), conn)
    if outro_audio_filename:
        for s in slides:
            if s.get("type") == "outro":
                s["outroAudioFile"] = outro_audio_filename
                if outro_audio_duration > 0:
                    # Floor at the outro slide's default (3s) so a
                    # very short audio bite doesn't shrink the splash
                    # below the time the animation needs to land.
                    # +0.5s tail prevents the audio from being cut
                    # mid-syllable at the slide boundary.
                    s["durationSec"] = max(s.get("durationSec", 3), outro_audio_duration + 0.5)
                break

    return {
        "videoId": f"educational-{rd['id']}",
        "title": (rd.get("youtube_title") or f"Word Detail {rd['chapter']}:{rd['verse']}"),
        "slides": slides,
    }


# ---------------------------------------------------------------------------
# Grammar Insights — payload builder + render entry point
# ---------------------------------------------------------------------------
def _grammar_highlight_word_index(insight: dict) -> int | None:
    """Pull the first 1-based word index from V7 evidence_trace.

    Kept for callers that need a single anchor (e.g. picking a
    representative gloss). For the verse-card highlights themselves,
    use _grammar_highlight_positions which returns the full set."""
    evidence = insight.get("evidence_trace") or []
    if not evidence:
        return None
    primary = [e for e in evidence if e.get("role") == "primary_support"]
    pool = primary or evidence
    for ev in pool:
        ref = (ev.get("token_ref") or "").strip()
        parts = ref.split(":")
        if len(parts) == 3:
            try:
                return int(parts[2])
            except (TypeError, ValueError):
                continue
    return None


# Agreement codes inside morphology.features_raw: 1S, 1P, 2MS, 2FS,
# 2MP, 2FP, 2MD, 2FD, 3MS, 3FS, 3MP, 3FP, 3MD, 3FD. Person + (M/F/C
# optional) + Number (S/P/D for singular / plural / dual). The
# corpus stores these as a pipe-delimited token in features_raw,
# usually at the end of the row (e.g. "POS:V|IMPF|LEM:Eabada|ROOT:Ebd|1P").
import re as _re_morph
_AGREEMENT_RE = _re_morph.compile(r"(?:^|\|)([123][MFC]?[SPD])(?:\||$)")


def _agreement_code(features_raw: str | None) -> str | None:
    """Extract the agreement code (e.g. '1P', '2MS') from a
    pipe-delimited features_raw string. Returns None if absent."""
    if not features_raw:
        return None
    m = _AGREEMENT_RE.search(features_raw)
    return m.group(1) if m else None


def _resolve_evidence_position(
    conn, chapter: int, verse: int, ev: dict,
) -> int | None:
    """Find the word position an evidence entry actually refers to.

    V7's token_ref is unreliable — the model regularly emits a
    position that doesn't match the lemma/surface it claims to be
    pointing at (e.g. for 79:46 it claimed token_ref=79:46:1 with
    lemma=<il~aA, but position 1 is كَأَنَّ; the actual <il~aA word
    is position 6). Trust the linguistic identifier over the
    position number. Resolution order:

      1. surface_ar exact match against morphology.form_arabic
         (most specific — matches the exact word V7 saw).
      2. feature_type=lemma_bw → find word with that lemma.
      3. feature_type=root_bw → find word with that root.
      4. Fall back to token_ref position, BUT only if it lies in
         range AND morphology has a row at that position. Use the
         position if the linguistic-identifier checks above had
         nothing usable.

    Returns the word_pos (1-based), or None if nothing resolves.
    """
    surface = (ev.get("surface_ar") or "").strip()
    feature_type = (ev.get("feature_type") or "").strip()
    feature_value = (ev.get("feature_value") or "").strip()
    ref = (ev.get("token_ref") or "").strip()

    def _find_first(sql: str, params: tuple) -> int | None:
        row = conn.execute(sql, params).fetchone()
        return row["word_pos"] if row else None

    # 1. surface form match
    if surface:
        # Strip Uthmani diacritics and tatweel for a fuzzier
        # Arabic-script comparison — V7 sometimes reports a
        # normalized surface that differs by diacritics.
        stripped = _strip_uthmani_marks(surface)
        pos = _find_first(
            "SELECT word_pos FROM morphology "
            "WHERE chapter=? AND verse=? AND form_arabic=? "
            "ORDER BY word_pos LIMIT 1",
            (chapter, verse, surface),
        )
        if pos is not None:
            return pos
        if stripped != surface:
            pos = _find_first(
                "SELECT word_pos FROM morphology "
                "WHERE chapter=? AND verse=? AND form_arabic=? "
                "ORDER BY word_pos LIMIT 1",
                (chapter, verse, stripped),
            )
            if pos is not None:
                return pos

    # 2/3. feature lookup by lemma_bw / root_bw / form_bw
    if feature_value:
        if feature_type == "lemma_bw":
            pos = _find_first(
                "SELECT word_pos FROM morphology "
                "WHERE chapter=? AND verse=? AND lemma_buckwalter=? "
                "ORDER BY word_pos LIMIT 1",
                (chapter, verse, feature_value),
            )
            if pos is not None:
                return pos
        elif feature_type == "root_bw":
            pos = _find_first(
                "SELECT word_pos FROM morphology "
                "WHERE chapter=? AND verse=? AND root_buckwalter=? "
                "ORDER BY word_pos LIMIT 1",
                (chapter, verse, feature_value),
            )
            if pos is not None:
                return pos
        elif feature_type == "form_bw":
            pos = _find_first(
                "SELECT word_pos FROM morphology "
                "WHERE chapter=? AND verse=? AND form_buckwalter=? "
                "ORDER BY word_pos LIMIT 1",
                (chapter, verse, feature_value),
            )
            if pos is not None:
                return pos

    # 4. Token_ref position — but ONLY trust it when we can verify
    #    against an additional signal at that position. Without
    #    verification, V7 routinely points to the wrong word
    #    (79:46 case: claimed 79:46:1 had lemma <il~aA but the
    #    actual <il~aA word is at position 6).
    parts = ref.split(":")
    tok_pos: int | None = None
    if len(parts) == 3:
        try:
            tok_pos = int(parts[2])
        except (TypeError, ValueError):
            tok_pos = None

    if tok_pos is not None:
        if feature_type == "feature" and feature_value:
            # The feature_value is an agreement / verb-form / case /
            # POS tag stored in features_raw. The corpus uses two
            # formats interleaved with pipes:
            #   - standalone tokens (e.g. "1P", "PERF", "ACC", "M")
            #   - KEY:VALUE pairs (e.g. "POS:COND", "MOOD:JUS",
            #     "PRON:3MP")
            # A "COND" feature should match either the standalone
            # token OR the value of a POS:COND pair. Without checking
            # the value side, conditional/restriction/accusative
            # particles (whose only marker is POS:X) silently miss.
            def _has_feature(features_raw: str | None, value: str) -> bool:
                if not features_raw:
                    return False
                for part in features_raw.split("|"):
                    if part == value:
                        return True
                    # KEY:VALUE — match on the value side.
                    if ":" in part and part.partition(":")[2] == value:
                        return True
                return False

            row = conn.execute(
                "SELECT word_pos, features_raw FROM morphology "
                "WHERE chapter=? AND verse=? AND word_pos=? "
                "ORDER BY segment LIMIT 1",
                (chapter, verse, tok_pos),
            ).fetchone()
            if row and _has_feature(row["features_raw"], feature_value):
                return tok_pos
            # Mismatch — find any word in the verse with this feature.
            scan = conn.execute(
                "SELECT word_pos, features_raw FROM morphology "
                "WHERE chapter=? AND verse=? "
                "ORDER BY word_pos, segment",
                (chapter, verse),
            ).fetchall()
            for r in scan:
                if _has_feature(r["features_raw"], feature_value):
                    return r["word_pos"]
            return None
        # Last-resort fallback for evidence with no usable identifier
        # at all — just trust the token_ref position if morphology
        # has a row there.
        row = conn.execute(
            "SELECT word_pos FROM morphology "
            "WHERE chapter=? AND verse=? AND word_pos=? LIMIT 1",
            (chapter, verse, tok_pos),
        ).fetchone()
        if row:
            return tok_pos

    return None


def _grammar_highlight_positions(conn, chapter: int, verse: int, insight: dict) -> list[int]:
    """Return ALL word positions that should be highlighted for this
    grammar insight, not just the first one V7 flagged.

    Two layers of inclusion:
      1. Every evidence_trace entry (primary AND secondary support),
         resolved via _resolve_evidence_position so we don't trust
         V7's frequently-wrong token_ref position. Lemma/surface/root
         matching wins over position.
      2. Morphological expansion. For each seed word, also pull in
         other words in the same verse that share the same lemma OR
         the same (POS + agreement code from features_raw). Picks up
         cases V7 didn't explicitly enumerate but that obviously
         belong to the same pattern — e.g. for 1:5's "person mixture"
         insight, V7 flagged ‎نَعْبُدُ‎ (we serve) but not
         ‎نَسْتَعِينُ‎ (we seek help), even though both verbs share
         1st-person-plural (1P) and carry the same grammatical move.

    Expansion is deliberately conservative — only verbs and pronouns
    expand by agreement (sharing 1P/2MS doesn't tell you anything
    interesting about content nouns). Lemma matches expand for any
    POS since identical lemmas in the same verse usually carry the
    same grammatical role.
    """
    seeds: set[int] = set()
    for ev in insight.get("evidence_trace") or []:
        pos = _resolve_evidence_position(conn, chapter, verse, ev)
        if pos is not None:
            seeds.add(pos)
    if not seeds:
        return []

    expanded = set(seeds)
    for seed in seeds:
        # Pick the first content segment of the seed word. Skipping
        # prefixes (Prefix/Particle/Conjunction) keeps "wa-" from
        # masquerading as the lemma we want to expand on.
        seed_row = conn.execute(
            "SELECT lemma_buckwalter, pos, features_raw "
            "FROM morphology "
            "WHERE chapter=? AND verse=? AND word_pos=? "
            "  AND pos IS NOT NULL "
            "  AND pos NOT IN ('Prefix', 'Particle', 'Conjunction') "
            "ORDER BY segment LIMIT 1",
            (chapter, verse, seed),
        ).fetchone()
        if not seed_row:
            continue
        lemma = seed_row["lemma_buckwalter"]
        pos = seed_row["pos"]
        agreement = _agreement_code(seed_row["features_raw"])

        # Same-lemma expansion (e.g. ‎إِيَّاكَ‎ repeated).
        if lemma:
            for r in conn.execute(
                "SELECT DISTINCT word_pos FROM morphology "
                "WHERE chapter=? AND verse=? AND lemma_buckwalter=?",
                (chapter, verse, lemma),
            ):
                expanded.add(r["word_pos"])

        # Same-agreement expansion for verbs/pronouns. Walk the verse
        # and grab any word_pos whose first content segment matches
        # the same POS + agreement code.
        if pos in ("Verb", "Pronoun") and agreement:
            for r in conn.execute(
                "SELECT word_pos, features_raw FROM morphology "
                "WHERE chapter=? AND verse=? AND pos=? "
                "ORDER BY word_pos, segment",
                (chapter, verse, pos),
            ):
                if _agreement_code(r["features_raw"]) == agreement:
                    expanded.add(r["word_pos"])

    return sorted(expanded)


# Per-chunk marker rotation.
#
# The V7 category gives us the *first* chunk's color (so a
# person_mixture insight still leads with blue). Subsequent chunks
# rotate through the other markers so the viewer can visually parse
# parallel structures as distinct pieces — e.g. for 1:5's "we serve /
# we seek help" parallelism, chunk 0 lands blue (pronoun) and chunk 1
# lands amber (tense), instead of clumping everything under one shade
# and hiding the parallel-clause boundary.
_CHUNK_MARKER_ROTATION = ("pronoun", "tense", "fronted", "agent")


def _chunk_marker(chunk_idx: int, base_marker: str) -> str:
    """Pick a marker color for the Nth chunk. Chunk 0 = base_marker
    (the V7-derived color); subsequent chunks rotate through the
    remaining markers, deduped to avoid repeating the base."""
    palette: list[str] = [base_marker]
    for m in _CHUNK_MARKER_ROTATION:
        if m not in palette:
            palette.append(m)
    return palette[chunk_idx % len(palette)]


def _chunk_word_positions(conn, chapter: int, verse: int, positions: list[int]) -> list[list[int]]:
    """Group highlighted word positions into visually-distinct chunks.

    Two break signals, in order:
      1. Conjunction prefix on the next word (waw/fa/etc.) — clear
         clause boundary in Arabic. For 1:5 this splits the
         إِيَّاكَ نَعْبُدُ / وَإِيَّاكَ نَسْتَعِينُ pair on the
         second وَ-prefixed word.
      2. Gap of one or more unhighlighted words between this position
         and the previous — the highlighted span isn't continuous so
         the eye already breaks it.

    Returns a list of chunks, each chunk a list of word_positions in
    ascending order. Empty input → empty output.
    """
    if not positions:
        return []
    sorted_pos = sorted(set(positions))

    # Pull the first segment of every position so we can spot
    # conjunction prefixes (Prefix POS with form_buckwalter starting
    # with 'w' or 'f', the common Arabic conjunction prefixes).
    first_segments: dict[int, dict] = {}
    rows = conn.execute(
        "SELECT word_pos, segment, pos, form_buckwalter "
        "FROM morphology "
        f"WHERE chapter=? AND verse=? AND word_pos IN ({','.join('?' * len(sorted_pos))}) "
        "ORDER BY word_pos, segment",
        (chapter, verse, *sorted_pos),
    ).fetchall()
    for r in rows:
        wp = r["word_pos"]
        if wp not in first_segments:
            first_segments[wp] = dict(r)

    def _starts_with_conjunction(wp: int) -> bool:
        seg = first_segments.get(wp)
        if not seg:
            return False
        if (seg["pos"] or "").lower() not in ("prefix", "conjunction"):
            return False
        form = (seg["form_buckwalter"] or "").lower()
        # Buckwalter 'w' = wa (and), 'f' = fa (so/then). Both are
        # clause-introducers in this position.
        return form.startswith("w") or form.startswith("f")

    chunks: list[list[int]] = [[sorted_pos[0]]]
    for prev, curr in zip(sorted_pos, sorted_pos[1:]):
        if curr - prev > 1 or _starts_with_conjunction(curr):
            chunks.append([curr])
        else:
            chunks[-1].append(curr)
    return chunks


# Maps V7 categories to the GrammarVerseSlide marker enum so multi-
# highlight verses get color-coded by what kind of grammatical move
# is being shown.
_CATEGORY_TO_MARKER = {
    "time_perspective": "tense",
    "perspective_shift": "pronoun",
    "person_mixture": "pronoun",
    "royal_we_vs_i": "pronoun",
    "cognate_accusative": "default",     # root-based emphasis — no canonical color
    "oath_structure": "fronted",
    "exception_scope": "fronted",
    "conditional_structure": "fronted",
    "gender_nuance": "default",
    "sound_communication": "default",
    "demonstrative_distance": "default",
    "plural_type": "default",
    "educational": "default",
    "other_grammar": "default",
}


def _extract_arabic_word_from_evidence(insight: dict) -> str | None:
    """Pull the Arabic surface form of the first primary-support
    evidence token. Used as the saidArabic on the contrast slide."""
    for ev in insight.get("evidence_trace") or []:
        if ev.get("role") == "primary_support":
            sa = (ev.get("surface_ar") or "").strip()
            if sa:
                return sa
    for ev in insight.get("evidence_trace") or []:
        sa = (ev.get("surface_ar") or "").strip()
        if sa:
            return sa
    return None


def _build_grammar_example_slide(
    conn,
    *,
    chapter: int,
    verse: int,
    narration_text: str,
    anchor_insight: dict,
    base_marker: str,
    english_emphasis_strings: list[str],
    dur: float,
) -> dict | None:
    """Build a grammar-verse slide for a cross-reference example.

    Same shape as the main verse slides — Arabic + translation +
    highlights + narration — but the highlights come from looking
    up the anchor insight's lemmas inside THIS verse's morphology.
    The lemma is the strongest signal of "same grammatical move",
    so we light up the same word(s) in the example as we did in
    the anchor (e.g. for an exception_scope insight on 79:46
    anchored on lemma `<il~aA`, an example verse on 2:286 will
    highlight wherever `<il~aA` sits in 2:286).

    Returns None when the verse is missing or no anchor lemma
    appears in it — caller should drop the example silently.
    """
    vd = _verse_data(conn, chapter, verse)
    if not vd or not vd.get("translation"):
        return None
    import app as _app
    arabic = _strip_uthmani_marks(_app._strip_bismillah(vd["arabic"], chapter, verse))
    translation = vd["translation"]

    # Pull anchor lemmas. Two paths, same as the script-side
    # candidate finder: direct lemma_bw evidence, or resolve to the
    # anchor verse position and pull the lemma from morphology.
    # Without the second path, V7 evidence that only carries POS
    # tags (e.g. feature=COND for 80:5) yields no anchor lemma and
    # the example slide renders without highlights.
    anchor_lemmas: set[str] = set()
    for ev in anchor_insight.get("evidence_trace") or []:
        if ev.get("feature_type") == "lemma_bw":
            v = (ev.get("feature_value") or "").strip()
            if v:
                anchor_lemmas.add(v)
    if not anchor_lemmas:
        # Resolve each evidence to a position in the anchor verse —
        # but we need the anchor verse's chapter/verse, which the
        # caller doesn't pass directly. Recover it from the
        # evidence's token_ref (anchor verse is the first token_ref's
        # chapter:verse).
        anchor_ch, anchor_v = None, None
        for ev in anchor_insight.get("evidence_trace") or []:
            ref = (ev.get("token_ref") or "").strip().split(":")
            if len(ref) >= 2:
                try:
                    anchor_ch = int(ref[0])
                    anchor_v = int(ref[1])
                    break
                except (TypeError, ValueError):
                    continue
        if anchor_ch is not None and anchor_v is not None:
            for ev in anchor_insight.get("evidence_trace") or []:
                pos = _resolve_evidence_position(conn, anchor_ch, anchor_v, ev)
                if pos is None:
                    continue
                row = conn.execute(
                    "SELECT lemma_buckwalter FROM morphology "
                    "WHERE chapter=? AND verse=? AND word_pos=? "
                    "  AND lemma_buckwalter IS NOT NULL "
                    "  AND lemma_buckwalter != '' "
                    "ORDER BY segment LIMIT 1",
                    (anchor_ch, anchor_v, pos),
                ).fetchone()
                if row and row["lemma_buckwalter"]:
                    anchor_lemmas.add(row["lemma_buckwalter"])

    # Find every word_pos in this verse whose any segment matches
    # an anchor lemma. Same-feature expansion (1P / 2MS) doesn't
    # apply here — we want a literal lemma echo, not a feature
    # echo, since features can collide across unrelated grammatical
    # moves.
    positions: set[int] = set()
    if anchor_lemmas:
        placeholders = ",".join("?" * len(anchor_lemmas))
        for r in conn.execute(
            f"SELECT DISTINCT word_pos FROM morphology "
            f"WHERE chapter=? AND verse=? AND lemma_buckwalter IN ({placeholders})",
            (chapter, verse, *anchor_lemmas),
        ):
            positions.add(r["word_pos"])
    word_positions = sorted(positions)

    # If we couldn't find the anchor lemma in this verse, the
    # example doesn't visually demonstrate the parallel — render
    # without highlights rather than skip the slide entirely (the
    # script writer's narration may still be valuable).

    # Chunk + assign markers, same as the main verse builder.
    chunks = _chunk_word_positions(conn, chapter, verse, word_positions)
    pos_to_chunk: dict[int, tuple[int, str]] = {}
    for ci, chunk in enumerate(chunks):
        cm = _chunk_marker(ci, base_marker)
        for p in chunk:
            pos_to_chunk[p] = (ci, cm)

    highlights: list[dict] = []
    for pos in word_positions:
        _, marker = pos_to_chunk[pos]
        highlights.append({"wordIndex": pos, "marker": marker})

    # English emphases — same chunk-color pairing as the main verse.
    en_emphases: list[dict] = []
    if english_emphasis_strings and chunks:
        chunk_markers = [_chunk_marker(i, base_marker) for i in range(len(chunks))]
        for i, phrase in enumerate(english_emphasis_strings):
            marker = chunk_markers[min(i, len(chunk_markers) - 1)]
            en_emphases.append({"phrase": phrase, "marker": marker})
    elif english_emphasis_strings:
        for phrase in english_emphasis_strings:
            en_emphases.append({"phrase": phrase, "marker": base_marker})

    slide: dict = {
        "type": "grammar-verse",
        "durationSec": dur,
        "surah": chapter,
        "ayah": verse,
        "arabicText": arabic,
        "translation": translation,
        "highlights": highlights,
        "narration": {"text": narration_text or ""},
    }
    if en_emphases:
        slide["englishEmphases"] = en_emphases
    return slide


def build_grammar_insights_payload(conn, rd: dict, script: dict) -> dict:
    """Convert a grammar_insights educational_videos row + its script
    into a Remotion payload.

    Slide layout:
      1. grammar-verse — verse with highlight, narration = hook
      2. grammar-verse — same verse, annotation = paraphrase of the
         contrast (verse_intro), narration = verse_intro
      3. grammar-verse — same verse, annotation = the meaning payoff,
         narration = insight
      4. outro — narration = close (merged onto slide 3 actually, since
         the outro splash should be silent)

    We deliberately use the SAME verse three times. Repetition + a
    rotating annotation reinforces the point: "look at this verse
    THIS way, now THIS way, now THIS way." Each beat refocuses the
    eye on the same Arabic with a different lens. Phase 4 may
    introduce the contrast slide between slides 1 and 2 once the V7
    counterfactual extraction is reliable.
    """
    # Re-enrich at render time. The candidate metadata stored in
    # payload_json doesn't include the full V7 insight body — that's
    # fetched fresh by educational_scripts.enrich_payload, same as
    # script-generation does. Re-fetching here means the rendered
    # video reflects the latest V7 generator output even if the
    # underlying tables changed since the script was written.
    import educational_scripts as _scripts
    enriched = _scripts.enrich_payload(conn, dict(rd))
    insight = enriched.get("insight") or {}
    chapter = int(rd["chapter"])
    verse = int(rd["verse"])

    vd = _verse_data(conn, chapter, verse)
    if not vd:
        raise RemotionRenderError(f"verse data missing for {chapter}:{verse}")

    # Strip the bismillah from verse 1 of every surah (except 1:1, where
    # it IS the verse). The Uthmani text includes the basmala prefix on
    # all "verse 1"s, but the V7 token_ref word indices count *against*
    # the bismillah-stripped verse — without this strip, evidence_trace
    # token "16:1:1" would highlight "بِسْمِ" instead of the actual
    # first word of the verse content.
    import app as _app  # for _strip_bismillah; lazy import to avoid cycles
    arabic_full = _strip_uthmani_marks(_app._strip_bismillah(vd["arabic"], chapter, verse))
    arabic = arabic_full
    translation = vd["translation"] or ""

    # All word positions to highlight — V7 evidence tokens plus any
    # morphological siblings (same lemma OR same person/number
    # features for verbs/pronouns).
    word_positions = _grammar_highlight_positions(conn, chapter, verse, insight)
    base_marker = _CATEGORY_TO_MARKER.get(insight.get("category", ""), "default")

    # Group positions into chunks (parallel clauses, etc.) so each
    # gets its own color. For 1:5 this splits 1,2,3,4 into [[1,2],
    # [3,4]] on the وَ in word 3.
    chunks = _chunk_word_positions(conn, chapter, verse, word_positions)

    # Map each word_pos to (chunk_idx, marker) so the highlight
    # construction can read it without re-walking chunks.
    pos_to_chunk: dict[int, tuple[int, str]] = {}
    for ci, chunk in enumerate(chunks):
        chunk_marker = _chunk_marker(ci, base_marker)
        for p in chunk:
            pos_to_chunk[p] = (ci, chunk_marker)

    # English-side highlights. Two sources, in priority order:
    #   1. Script's `english_emphases` — phrase-level spans the LLM
    #      picked while writing the script (e.g. ["You alone we
    #      serve", "You alone we seek help from"]). Richer than
    #      per-word gloss because they capture the contextual
    #      framing of the grammatical move.
    #   2. Per-word glosses for each highlighted word_pos. Falls
    #      out from ai_word_meanings / word_glosses lookups.
    # The renderer will find ALL occurrences of each substring, so
    # repeated tokens (إيَّاكَ × 2 → "you" × 2) light up everywhere.
    en_emphasis_strings: list[str] = []
    raw_emphases = script.get("english_emphases")
    if isinstance(raw_emphases, list):
        for s in raw_emphases:
            if isinstance(s, str) and s.strip():
                en_emphasis_strings.append(s.strip())

    # Pair each emphasis with a chunk's marker, by index. Extra
    # emphases (more than chunks) reuse the last chunk's color.
    en_emphases: list[dict] = []
    if en_emphasis_strings and chunks:
        chunk_markers = [_chunk_marker(i, base_marker) for i in range(len(chunks))]
        for i, phrase in enumerate(en_emphasis_strings):
            marker = chunk_markers[min(i, len(chunk_markers) - 1)]
            en_emphases.append({"phrase": phrase, "marker": marker})
    elif en_emphasis_strings:
        # No Arabic chunks but emphases exist — use the base marker.
        for phrase in en_emphasis_strings:
            en_emphases.append({"phrase": phrase, "marker": base_marker})

    highlights: list[dict] = []
    if word_positions:
        for pos in word_positions:
            chunk_idx, marker = pos_to_chunk[pos]
            h: dict = {"wordIndex": pos, "marker": marker}
            # Per-word gloss — used only when the script didn't
            # provide explicit phrase emphases. When emphases ARE
            # present, the slide-level `englishEmphases` field
            # carries the English highlights and these per-highlight
            # `translationSubstring`s are skipped entirely.
            if not en_emphases:
                gloss = _word_gloss(conn, chapter, verse, pos)
                if gloss:
                    h["translationSubstring"] = gloss
            highlights.append(h)

    # Per-slide narration. We use the script's 4 beats:
    #   slide 1 = hook
    #   slide 2 = verse_intro (the contrast)
    #   slide 3 = insight (the payoff) PLUS close, since the outro
    #            should be silent so the splash visual doesn't
    #            interrupt the spoken close.
    hook_text = sanitize_for_tts((script.get("hook") or "").strip())
    intro_text = sanitize_for_tts((script.get("verse_intro") or "").strip())
    insight_text = sanitize_for_tts((script.get("insight") or "").strip())
    close_text = sanitize_for_tts((script.get("close") or "").strip())

    final_slide_narration = insight_text
    if close_text:
        final_slide_narration = (insight_text + " " + close_text).strip()

    def _verse_slide(narration_text: str, dur: float) -> dict:
        # No on-screen annotation — the spoken narration is the
        # whole story. An earlier version drew a small italic
        # paraphrase below the card; it was too easy to clip and
        # competed with the karaoke caption for attention.
        s: dict = {
            "type": "grammar-verse",
            "durationSec": dur,
            "surah": chapter,
            "ayah": verse,
            "arabicText": arabic,
            "translation": translation,
            "highlights": highlights,
            "narration": {"text": narration_text or ""},
        }
        if en_emphases:
            s["englishEmphases"] = en_emphases
        return s

    # Cross-reference example slides ("In another verse, ..." /
    # "Elsewhere, ..."). Each example gets its own grammar-verse
    # slide so the viewer literally sees the other verse on screen
    # while the narrator points to it. Highlights are auto-derived
    # from the anchor insight's lemmas applied against the example
    # verse's morphology — same lemma in the new verse → highlight.
    example_slides: list[dict] = []
    for ex in (script.get("additional_examples") or [])[:2]:
        if not isinstance(ex, dict):
            continue
        try:
            ex_ch = int(ex["chapter"])
            ex_v = int(ex["verse"])
        except (TypeError, ValueError, KeyError):
            continue
        ex_narration = sanitize_for_tts((ex.get("narration") or "").strip())
        if not ex_narration:
            continue
        ex_em = ex.get("english_emphases") if isinstance(ex.get("english_emphases"), list) else []
        ex_em_clean: list[str] = [
            s.strip() for s in ex_em if isinstance(s, str) and s.strip()
        ]
        slide = _build_grammar_example_slide(
            conn,
            chapter=ex_ch, verse=ex_v,
            narration_text=ex_narration,
            anchor_insight=insight,
            base_marker=base_marker,
            english_emphasis_strings=ex_em_clean,
            dur=8.0,
        )
        if slide:
            example_slides.append(slide)

    slides: list[dict] = [
        _verse_slide(hook_text, dur=6.5),
        _verse_slide(intro_text, dur=8.0),
        *example_slides,
        _verse_slide(final_slide_narration, dur=8.5),
        _build_outro_slide(),
    ]

    # Stage outro audio bite — same flow as word_origins.
    outro_audio_filename, outro_audio_duration = _stage_outro_audio(rd.get("pipeline_id"), conn)
    if outro_audio_filename:
        for s in slides:
            if s.get("type") == "outro":
                s["outroAudioFile"] = outro_audio_filename
                if outro_audio_duration > 0:
                    # Floor at the outro slide's default (3s) so a
                    # very short audio bite doesn't shrink the splash
                    # below the time the animation needs to land.
                    # +0.5s tail prevents the audio from being cut
                    # mid-syllable at the slide boundary.
                    s["durationSec"] = max(s.get("durationSec", 3), outro_audio_duration + 0.5)
                break

    return {
        "videoId": f"educational-{rd['id']}",
        "title": (rd.get("youtube_title") or f"Grammar Insight — {chapter}:{verse}"),
        "slides": slides,
    }


def render_grammar_insights_video(
    conn,
    video_id: int,
    *,
    format: str,
    elevenlabs_api_key: str,
    voice_id: str,
) -> tuple[str, int]:
    """Build the grammar payload, invoke the Remotion subprocess,
    return (filename, file_size_bytes). Same return contract as
    render_word_origins_video so the orchestrator's status flow is
    unchanged.

    Implementation re-uses the word_origins subprocess plumbing — the
    only difference is which payload-builder produced the JSON. The
    Remotion bundle handles both via the same WordDetailComposition
    that dispatches by slide.type.
    """
    if format not in ("long", "short"):
        raise RemotionRenderError(f"unknown format: {format}")
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

    payload = build_grammar_insights_payload(conn, rd, script)
    if not payload["slides"]:
        raise RemotionRenderError("payload has no renderable slides")

    out_filename = f"{video_id:06d}-{format}.mp4"
    out_path = os.path.join(OUTPUT_DIR, out_filename)

    with tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(payload, f, ensure_ascii=False)
        payload_path = f.name

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
            cmd, cwd=RENDERER_DIR, env=env,
            capture_output=True, text=True, timeout=600,
        )
    except subprocess.TimeoutExpired as e:
        raise RemotionRenderError(
            f"Remotion render timed out after {e.timeout}s. "
            f"stderr tail: {((e.stderr or b'')[-800:] or b'').decode('utf-8', errors='replace')}"
        )
    finally:
        try:
            os.remove(payload_path)
        except OSError:
            pass

    if proc.returncode != 0:
        tail = (proc.stderr or "")[-800:]
        raise RemotionRenderError(f"Remotion render failed: {tail}")

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
    return out_filename, os.path.getsize(out_path)


# ============================================================================
# What Translation Hides series
# ============================================================================
#
# Series identity: reveal the nuance the conventional English translation
# flattens. Visual signature: rose accent (#BE123C), distinct from yellow
# (Word Origins) and amber (Grammar Insights) so viewers learn the series
# from a thumbnail.
#
# Slide composition (45-65s vertical):
#   1. translation-reveal   ~7s  — "Most translations say X / The Arabic
#                                   actually says Y". Hook narration plays.
#   2. verse-flow           ~10s — Source verse with the target word (and/or
#                                  english_emphases) highlighted in rose.
#                                  verse_intro narration plays.
#   3. word-lens            ~12s — When a single word is the focus: large
#                                  Arabic word, conventional gloss (struck
#                                  through), AI gloss in rose, evidence chip.
#                                  When phrase-level: SKIPPED — verse-flow
#                                  carries the insight directly.
#   4. outro                ~3s  — al-nuqta brand splash. Close narration is
#                                  merged onto the final pre-outro slide so
#                                  the splash is silent.
#
# All slides reuse the same KaraokeOverlay for synchronized captions.
# ============================================================================


# Reuse the existing rose marker for the verse-flow highlight pill so
# the highlight color matches the rest of the series. The verse-flow
# slide already supports marker colors via the (deprecated for word-
# origins, alive for grammar) `grammarMarkerFronted` token which IS
# rose. We don't use a grammar-highlight pill here though — the
# verse-flow slide's standard yellow `highlight` is reused but
# overridden via the slide's payload-level color hooks. Simpler path
# for now: rely on the existing yellow highlight; the rose identity is
# carried by the reveal + word-lens slides, which sandwich the verse.
def _maybe_rose_highlight_word_index(script: dict) -> int | None:
    """Pull selected_word_pos off the script, normalized to a positive
    int or None. Treats 0/None/missing all as None."""
    raw = script.get("selected_word_pos")
    if raw is None:
        return None
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return None
    return n if n >= 1 else None


# English glosses on word_glosses are short per-word fragments
# ("will strike her", "what", "will strike them"). The Translation
# Hides reveal phrases come from the verse's flowing translation
# ("what struck them will be striking her") — so direct substring
# match fails (the per-word glosses use slightly different wording
# than the final translation). Token overlap with a simple stemmer
# is good enough to recover the contiguous run of Arabic words a
# phrase covers — the common case is 2-4 adjacent words, and the
# 50% threshold below keeps unrelated "will" / "they" matches out.
_TH_TOKEN_SPLIT = __import__("re").compile(r"[^\w]+")
_TH_PAREN_STRIP = __import__("re").compile(r"\([^)]*\)")

# Tokens we drop before computing phrase↔gloss overlap. Restricted
# to true function words (articles, conjunctions, copulas, common
# prepositions). Pronouns + interrogatives + modals stay in because
# they're often the semantic anchor of a Translation Hides phrase
# (e.g. "her" in 11:81 "...striking her", "what" in 11:81 "what
# struck them..."). Earlier I had a wider stopword list that
# stripped everything down to verb-stems, which over-filtered
# phrases like 11:81 to {strik, struck} and missed legitimate
# matches on pos 21/23.
_TH_STOPWORDS = frozenset({
    "and", "the", "but", "for", "nor", "yet", "so",
    "with", "from", "into", "onto", "over", "out", "off",
    "are", "was", "were", "has", "have", "had", "been", "being",
    "this", "that", "these", "those",
    "than", "then", "thus", "also",
    "indeed", "surely", "verily", "lo",
})


def _th_crude_stem(t: str) -> str:
    """Strip common English inflections so 'striking' / 'strikes' /
    'strike' all collapse onto a shared stem. Crude but predictable —
    we don't need Porter accuracy here; we just need related forms
    to share a stem when matching. The trailing-'e' rule is what
    lets 'strike' (no suffix) collapse onto 'strik' from 'striking'
    after the -ing strip; without it, 11:81 word 21 ('will strike
    her') failed to match the phrase 'striking her' even though
    the verbs are the same."""
    for suf in ("ing", "ies", "ied", "ed", "es", "er", "s"):
        if t.endswith(suf) and len(t) > len(suf) + 2:
            return t[: -len(suf)]
    if t.endswith("e") and len(t) > 3:
        return t[:-1]
    return t


def _th_tokenize(text: str) -> set[str]:
    """Lowercase, strip parentheticals + punctuation, drop stopwords,
    stem the survivors, return significant tokens (length ≥ 3 after
    stemming)."""
    if not text:
        return set()
    norm = _TH_PAREN_STRIP.sub(" ", text.lower())
    raw = [
        t for t in _TH_TOKEN_SPLIT.split(norm)
        if len(t) >= 3 and t not in _TH_STOPWORDS
    ]
    return {_th_crude_stem(t) for t in raw}


def _arabic_indices_for_english_phrase(
    conn, chapter: int, verse: int, phrase: str
) -> list[int]:
    """Map an English phrase from the verse translation back to the
    1-indexed Arabic word positions whose per-word glosses overlap it.

    Used by the Translation Hides verse-flow slide so the Arabic
    side highlights the same span the English side does — for
    phrase-level reveals (where script.selected_word_pos is null)
    this is the only way the Arabic gets any highlight at all.

    Returns [] when the phrase doesn't substantially overlap any
    word; caller falls back to the single-word highlight (if any).
    """
    p_tokens = _th_tokenize(phrase)
    if not p_tokens:
        return []
    rows = conn.execute(
        "SELECT word_pos, translation_en FROM word_glosses "
        "WHERE chapter = ? AND verse = ? "
        "ORDER BY word_pos",
        (chapter, verse),
    ).fetchall()
    matches: list[int] = []
    for r in rows:
        g_tokens = _th_tokenize(r["translation_en"] or "")
        if not g_tokens:
            continue
        overlap = p_tokens & g_tokens
        # ≥50% of the gloss's significant tokens must appear in the
        # phrase. This filters incidental "will" / "they" overlaps —
        # a gloss "they will reach" has tokens {they, will, reach};
        # phrase "what struck them will be striking her" overlaps
        # only on "will" (1/3 = 33%), so the word isn't picked up.
        if len(overlap) / max(1, len(g_tokens)) >= 0.5:
            matches.append(r["word_pos"])
    return matches


# Patterns the AI hook tends to follow: a "conventional" half and a
# "hidden" half joined by a contrast cue. We try several variants to
# survive minor narration style drift.
_TH_HOOK_PATTERNS = [
    # "Most translations say X. The Arabic [verb] Y"
    __import__("re").compile(
        r"(?:most translations|translators|conventional translations|conventionally|in english|they)"
        r"\s+(?:usually\s+)?(?:say|read|render|translate|put)\s+"
        r"(?:it\s+as|this\s+as|them\s+as|as)?\s*"
        r"(.+?)[\.\?\!]\s+(?:but\s+|yet\s+|however[, ]+)?"
        r"(?:the\s+)?arabic\s+"
        r"(?:actually|literally|really)?\s*"
        r"(?:says|reveals|shows|means|tells|carries|conveys|reads|points to)\s+"
        r"(.+?)[\.\?\!]?$",
        flags=__import__("re").IGNORECASE | __import__("re").DOTALL,
    ),
    # "X. But the Arabic [verb] Y"
    __import__("re").compile(
        r"^(.+?)[\.\?\!]\s+but\s+(?:the\s+)?arabic\s+"
        r"(?:actually|literally|really)?\s*"
        r"(?:says|reveals|shows|means|tells|carries|conveys|reads|points to)\s+"
        r"(.+?)[\.\?\!]?$",
        flags=__import__("re").IGNORECASE | __import__("re").DOTALL,
    ),
]


def _extract_reveal_from_hook(hook: str) -> tuple[str, str]:
    """When `reveal_conventional` / `reveal_hidden` are missing from the
    script (older rows from before the schema was fully enforced, or
    AI generations that slipped past validation), salvage them from
    the hook narration.

    The hook is almost always written in the form "Most translations
    say X. The Arabic reveals Y." — the same pattern the reveal slide
    is designed to display. Pulling X / Y out of that sentence keeps
    the slide from rendering with bare labels and empty bodies (as
    happened on 35:41, video #51 — the operator noticed the blank
    bodies even after the slide was visually rescaled).

    Returns ('', '') when no pattern matches; caller falls back further.
    The 80-char cap matches the schema validator so the rescued text
    behaves identically to native data downstream.
    """
    if not hook or not isinstance(hook, str):
        return ("", "")
    s = hook.strip()
    for pat in _TH_HOOK_PATTERNS:
        m = pat.search(s)
        if not m:
            continue
        conv = m.group(1).strip().rstrip(",;:")
        hidden = m.group(2).strip().rstrip(",;:")
        # Strip wrapping quotes — the AI hook often single-quotes the
        # conventional phrase ("God 'holds' the heavens") which looks
        # awkward on the pill row.
        for ch_open, ch_close in (
            ("'", "'"),
            ('"', '"'),
            ("‘", "’"),  # smart single
            ("“", "”"),  # smart double
        ):
            if conv.startswith(ch_open) and conv.endswith(ch_close) and len(conv) > 2:
                conv = conv[1:-1].strip()
            if hidden.startswith(ch_open) and hidden.endswith(ch_close) and len(hidden) > 2:
                hidden = hidden[1:-1].strip()
        # Cap to the same 80-char limit the schema enforces. If we
        # have to truncate, end on a word boundary so the slide
        # doesn't show "...something more urge..." mid-word.
        def _cap(t: str, n: int = 80) -> str:
            if len(t) <= n:
                return t
            cut = t[: n - 1].rsplit(" ", 1)[0]
            return (cut or t[: n - 1]).rstrip(",;:.") + "…"
        return (_cap(conv), _cap(hidden))
    return ("", "")


def _word_arabic_at_pos(conn, c: int, v: int, p: int) -> str:
    """Reconstruct the visible Arabic surface form for word `p` by
    concatenating its morphology segments. Returns '' if no rows.
    Mirrors AdminEducational / WordAnalysisPage's display approach so
    the Arabic shown on the word-lens slide matches what the operator
    sees in the admin candidate list."""
    rows = conn.execute(
        "SELECT form_arabic FROM morphology "
        "WHERE chapter = ? AND verse = ? AND word_pos = ? "
        "ORDER BY segment",
        (c, v, p),
    ).fetchall()
    return "".join((r["form_arabic"] or "") for r in rows)


def _word_lens_data_for(conn, c: int, v: int, p: int) -> dict | None:
    """Resolve the word-lens display data for word position `p`:
    conventional gloss + AI meaning + transliteration. Returns None
    if the word doesn't have a usable AI meaning (no point rendering
    the lens slide if there's no "hidden" gloss to reveal).

    Conventional gloss falls back through:
      1. ai_word_meanings's recorded conventional_gloss (judge column)
      2. word_glosses.gloss
      3. the morphology row's primary translation, when available
    """
    awm = conn.execute(
        """
        SELECT meaning_short, meaning_detailed, preferred_translation,
               preferred_source
        FROM ai_word_meanings
        WHERE chapter = ? AND verse = ? AND word_pos = ?
        ORDER BY id DESC LIMIT 1
        """,
        (c, v, p),
    ).fetchone()
    if not awm:
        return None
    ai_short = (awm["meaning_short"] or "").strip()
    if not ai_short:
        return None

    # Conventional gloss — prefer word_glosses.gloss because it's the
    # plain conventional English used by the rest of the site.
    conv_row = conn.execute(
        "SELECT translation_en AS gloss FROM word_glosses "
        "WHERE chapter = ? AND verse = ? AND word_pos = ? "
        "LIMIT 1",
        (c, v, p),
    ).fetchone()
    conv = (conv_row["gloss"] if conv_row else "") or ""
    conv = conv.strip()

    # Transliteration — the morphology table holds an English-friendly
    # form per segment. Take the stem's transliteration when present;
    # skip prefixes/suffixes that aren't the focus.
    tlit_row = conn.execute(
        """
        SELECT form_buckwalter
        FROM morphology
        WHERE chapter = ? AND verse = ? AND word_pos = ?
          AND pos NOT IN ('Prefix', 'Suffix')
        ORDER BY segment
        LIMIT 1
        """,
        (c, v, p),
    ).fetchone()
    transliteration = ""
    if tlit_row and tlit_row["form_buckwalter"]:
        # Buckwalter is operator-facing; the renderer will gracefully
        # accept missing transliteration so we just leave this empty
        # rather than ship a Buckwalter string the viewer can't read.
        # If a phonetic transliteration column gets added later, swap
        # it in here.
        transliteration = ""

    return {
        "conventional_gloss": conv,
        "ai_meaning_short": ai_short,
        "transliteration": transliteration,
    }


def build_translation_hides_payload(conn, rd: dict, script: dict) -> dict:
    """Convert a translation_hides educational_videos row + its script
    into a Remotion payload.

    Slide list assembled from the script's structured beats:
      1. translation-reveal — hook narration; reveal_conventional /
         reveal_hidden drive the two contrasting rows.
      2. verse-flow         — verse_intro narration; the target word
         (script.selected_word_pos) is highlighted, and english_emphases
         drives the English-side highlight pills.
      3. word-lens          — insight narration; conventional gloss
         struck through, AI gloss in rose, evidence_chip below. Only
         emitted when a target word is set AND the word has a usable
         AI-preferred meaning. Phrase-level / grammar-driven verses
         skip this slide entirely; insight narration is concatenated
         onto the verse-flow slide instead.
      4. outro              — silent splash. Close narration is merged
         onto the previous slide so the splash visual doesn't overlap
         spoken text.
    """
    chapter = int(rd["chapter"])
    verse = int(rd["verse"])

    vd = _verse_data(conn, chapter, verse)
    if not vd:
        raise RemotionRenderError(f"verse data missing for {chapter}:{verse}")

    # Strip the bismillah from verse 1 of every surah except 1:1, same
    # reason as in build_grammar_insights_payload: word indices on
    # ai_word_meanings count against the bismillah-stripped verse.
    import app as _app
    arabic = _strip_uthmani_marks(_app._strip_bismillah(vd["arabic"], chapter, verse))
    translation = vd["translation"] or ""

    target_pos = _maybe_rose_highlight_word_index(script)

    # Per-slide narration sourced from the script's structured beats.
    hook_text = sanitize_for_tts((script.get("hook") or "").strip())
    intro_text = sanitize_for_tts((script.get("verse_intro") or "").strip())
    insight_text = sanitize_for_tts((script.get("insight") or "").strip())
    close_text = sanitize_for_tts((script.get("close") or "").strip())

    # English emphases — phrase-level spans on the verse translation.
    # Same shape as the grammar series uses. All emphases share the
    # rose marker (no per-chunk color variation for this series; the
    # whole video IS the contrast).
    en_emphases: list[dict] = []
    raw_em = script.get("english_emphases")
    if isinstance(raw_em, list):
        for s in raw_em:
            if isinstance(s, str) and s.strip():
                en_emphases.append({"phrase": s.strip(), "marker": "fronted"})  # rose pill

    # 1. translation-reveal slide. Hook beat narration plays over it.
    # Older script rows (e.g. video #51, 35:41) sometimes have
    # reveal_conventional/reveal_hidden set to null — the slide
    # would render with bare label pills and empty bodies. When
    # either field is missing, salvage the contrast out of the hook
    # narration via _extract_reveal_from_hook so the bodies never
    # show up blank.
    conv_text = (script.get("reveal_conventional") or "").strip()
    hidden_text = (script.get("reveal_hidden") or "").strip()
    if not conv_text or not hidden_text:
        parsed_conv, parsed_hidden = _extract_reveal_from_hook(hook_text)
        if not conv_text and parsed_conv:
            conv_text = parsed_conv
        if not hidden_text and parsed_hidden:
            hidden_text = parsed_hidden
    reveal_slide: dict = {
        "type": "translation-reveal",
        "durationSec": 7,
        "conventionalLabel": "Most translations say",
        "conventionalText": conv_text,
        "hiddenLabel": "The Arabic actually says",
        "hiddenText": hidden_text,
    }
    # Show the target word's Arabic on the reveal slide too — only when
    # a single word is the focus. For phrase-level reveals we omit it
    # so the slide doesn't imply false specificity.
    if target_pos:
        arabic_at_target = _word_arabic_at_pos(conn, chapter, verse, target_pos)
        if arabic_at_target:
            reveal_slide["arabic"] = _strip_uthmani_marks(arabic_at_target)
    if hook_text:
        reveal_slide["narration"] = {"text": hook_text}

    # 2. verse-flow slide. verse_intro narration plays. Highlight the
    # target word in the Arabic and the english_emphases in the
    # translation so the viewer connects "this Arabic word" ↔ "this
    # English span" before the lens reveal explains what's behind it.
    verse_slide: dict = {
        "type": "verse-flow",
        "durationSec": 10,
        "surah": chapter,
        "ayah": verse,
        "arabicText": arabic,
        "translation": translation,
    }
    if target_pos:
        verse_slide["highlightWordIndex"] = target_pos
    # The existing verse-flow slide supports a single highlight word +
    # a single highlight phrase via highlightTranslationText. Use the
    # first emphasis as the translation highlight; the rest are
    # implicit (this series favors one focus per video).
    if en_emphases:
        verse_slide["highlightTranslationText"] = en_emphases[0]["phrase"]
    # Multi-word Arabic highlight. Phrase-level Translation Hides
    # reveals (e.g. 11:81 "what struck them will be striking her")
    # span 2-4 Arabic words; without this the Arabic side would
    # render with no highlight at all, leaving the viewer unsure
    # which Arabic span the reveal is about. Map every English
    # emphasis back to its Arabic word indices via word_glosses,
    # union them, and pass them through. The renderer's
    # VerseFlowPage takes the union of `highlightWordIndices` and
    # `highlightWordIndex` so both fields stay live.
    multi_idx: set[int] = set()
    for em in en_emphases:
        for p in _arabic_indices_for_english_phrase(conn, chapter, verse, em["phrase"]):
            multi_idx.add(p)
    if target_pos:
        multi_idx.add(target_pos)
    if multi_idx:
        verse_slide["highlightWordIndices"] = sorted(multi_idx)
    if intro_text:
        verse_slide["narration"] = {"text": intro_text}

    slides: list[dict] = [reveal_slide, verse_slide]

    # 3. word-lens slide (conditional). Only emitted when a target word
    # is set and we can resolve a usable AI gloss for it. Otherwise the
    # insight narration is concatenated onto the verse-flow slide so the
    # spoken reveal still plays — just over the verse instead of a
    # dedicated lens.
    lens_emitted = False
    if target_pos:
        lens_data = _word_lens_data_for(conn, chapter, verse, target_pos)
        target_arabic = _word_arabic_at_pos(conn, chapter, verse, target_pos)
        if lens_data and target_arabic and lens_data["ai_meaning_short"]:
            # We need BOTH a conventional gloss (for the strikethrough
            # row) and an AI gloss. Without the conventional, the
            # strikethrough has nothing to strike — fall back to a
            # neutral label so the slide still renders meaningfully.
            conv = lens_data["conventional_gloss"]
            if not conv:
                # Use the script's reveal_conventional as the upper row's
                # fallback. Slightly redundant with the reveal slide but
                # the viewer's seen enough variation by now that the
                # repetition reinforces rather than bores.
                conv = (script.get("reveal_conventional") or "").strip() or "the usual reading"
            lens_slide: dict = {
                "type": "word-lens",
                "durationSec": 12,
                "arabic": _strip_uthmani_marks(target_arabic),
                "wordPos": target_pos,
                "conventionalGloss": conv,
                "hiddenGloss": lens_data["ai_meaning_short"],
                "strikeConventional": True,
            }
            if lens_data["transliteration"]:
                lens_slide["transliteration"] = lens_data["transliteration"]
            chip = (script.get("evidence_chip") or "").strip()
            if chip:
                lens_slide["evidenceChip"] = chip
            if insight_text:
                lens_slide["narration"] = {"text": insight_text}
            slides.append(lens_slide)
            lens_emitted = True

    if not lens_emitted and insight_text:
        # No lens slide — concat insight onto verse-flow so the reveal
        # still gets spoken aloud. Bump the verse-flow's dwell time too
        # so the audio fits.
        existing = ((verse_slide.get("narration") or {}).get("text") or "").strip()
        combined = (existing + " " + insight_text).strip() if existing else insight_text
        verse_slide["narration"] = {"text": sanitize_for_tts(combined).strip()}
        # Insight beats are ~25s; verse-flow's default 10s is too short.
        verse_slide["durationSec"] = 18

    # 4. close beat merges onto the final pre-outro slide so the outro
    # splash plays silently. Mirrors grammar-insights' approach.
    if close_text:
        _merge_close_into_last_verse_or_lens(slides, close_text)

    # 5. Outro.
    outro = _build_outro_slide()
    pipeline_id = rd.get("pipeline_id")
    if pipeline_id:
        outro_fname, outro_dur = _stage_outro_audio(int(pipeline_id), conn)
        if outro_fname:
            outro["outroAudioFile"] = outro_fname
            # Match the audio length plus a small tail so the splash
            # doesn't cut off the bite.
            outro["durationSec"] = max(outro["durationSec"], outro_dur + 0.4)
    slides.append(outro)

    payload: dict = {
        "slides": slides,
        "videoId": str(rd.get("id", "")),
        "title": f"Translation Hides — {chapter}:{verse}",
    }
    return payload


def _merge_close_into_last_verse_or_lens(slides: list[dict], close_text: str) -> None:
    """Like _merge_close_into_last_verse, but accepts a word-lens slide
    as a target too. Walks backwards through the slide list and merges
    the close beat onto the first slide that supports narration (i.e.
    not the outro). Mutates `slides` in place."""
    close = (close_text or "").strip()
    if not close:
        return
    for s in reversed(slides):
        if s.get("type") in ("word-lens", "verse-flow", "translation-reveal"):
            existing = ((s.get("narration") or {}).get("text") or "").strip()
            combined = f"{existing} {close}".strip() if existing else close
            s["narration"] = {"text": sanitize_for_tts(combined).strip()}
            return


def render_translation_hides_video(
    conn,
    video_id: int,
    *,
    format: str,
    elevenlabs_api_key: str,
    voice_id: str,
) -> tuple[str, int]:
    """Build the translation-hides payload, invoke the Remotion
    subprocess, return (filename, file_size_bytes). Same contract as
    render_grammar_insights_video and render_word_origins_video so the
    orchestrator's status flow is unchanged.
    """
    if format not in ("long", "short"):
        raise RemotionRenderError(f"unknown format: {format}")
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

    payload = build_translation_hides_payload(conn, rd, script)
    if not payload["slides"]:
        raise RemotionRenderError("payload has no renderable slides")

    out_filename = f"{video_id:06d}-{format}.mp4"
    out_path = os.path.join(OUTPUT_DIR, out_filename)

    with tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(payload, f, ensure_ascii=False)
        payload_path = f.name

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
            cmd, cwd=RENDERER_DIR, env=env,
            capture_output=True, text=True, timeout=600,
        )
    except subprocess.TimeoutExpired as e:
        raise RemotionRenderError(
            f"Remotion render timed out after {e.timeout}s. "
            f"stderr tail: {((e.stderr or b'')[-800:] or b'').decode('utf-8', errors='replace')}"
        )
    finally:
        try:
            os.remove(payload_path)
        except OSError:
            pass

    if proc.returncode != 0:
        tail = (proc.stderr or "")[-800:]
        raise RemotionRenderError(f"Remotion render failed: {tail}")

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
    return out_filename, os.path.getsize(out_path)


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
