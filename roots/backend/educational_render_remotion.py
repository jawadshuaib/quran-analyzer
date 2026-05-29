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

    base_marker = _CATEGORY_TO_MARKER.get(insight.get("category", ""), "default")

    # Collect the script's English emphasis phrases.
    en_emphasis_strings: list[str] = []
    raw_emphases = script.get("english_emphases")
    if isinstance(raw_emphases, list):
        for s in raw_emphases:
            if isinstance(s, str) and s.strip():
                en_emphasis_strings.append(s.strip())

    en_emphases: list[dict] = []
    highlights: list[dict] = []

    if en_emphasis_strings:
        # EMPHASIS-DRIVEN highlighting (operator feedback on 5:1: the
        # Arabic highlights were "all over the place"). The OLD logic
        # derived Arabic highlights from the V7 grammar-evidence
        # positions and the English bolds from script.english_emphases
        # — two INDEPENDENT sources — then color-paired them by array
        # index. Result: the yellow English phrase "has been made
        # permissible" lit up أَوْفُوا (fulfill), and "judges as He
        # intends" lit up يُتْلَىٰ (recited). Nonsense.
        #
        # New approach: each emphasis phrase IS the unit. Map the
        # phrase to its Arabic word span via _align_emphasis_to_positions
        # (combined word_glosses + ai_word_meanings, gap-bridging,
        # Ollama fallback), assign emphasis i a distinct color, and
        # highlight BOTH the English phrase and its mapped Arabic
        # words in that SAME color. Now يَحْكُمُ مَا يُرِيدُ and
        # "judges as He intends" share a color, as they should.
        used_positions: set[int] = set()
        for i, phrase in enumerate(en_emphasis_strings):
            marker = _chunk_marker(i, base_marker)
            en_emphases.append({"phrase": phrase, "marker": marker})
            positions = _align_emphasis_to_positions(conn, chapter, verse, phrase)
            for p in positions:
                if p in used_positions:
                    # A word already claimed by an earlier emphasis
                    # keeps its first color (avoid flicker / overlap).
                    continue
                used_positions.add(p)
                highlights.append({"wordIndex": p, "marker": marker})
        highlights.sort(key=lambda h: h["wordIndex"])
    else:
        # FALLBACK — no script emphases (older rows). Keep the
        # V7-evidence behavior: highlight the grammar-evidence tokens,
        # color-chunked by parallel clause, with per-word glosses as
        # the English side.
        word_positions = _grammar_highlight_positions(conn, chapter, verse, insight)
        chunks = _chunk_word_positions(conn, chapter, verse, word_positions)
        pos_to_chunk: dict[int, tuple[int, str]] = {}
        for ci, chunk in enumerate(chunks):
            chunk_marker = _chunk_marker(ci, base_marker)
            for p in chunk:
                pos_to_chunk[p] = (ci, chunk_marker)
        for pos in word_positions:
            _, marker = pos_to_chunk[pos]
            h: dict = {"wordIndex": pos, "marker": marker}
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
    # Union word_glosses with ai_word_meanings (preferred_translation +
    # meaning_short). The conventional gloss often uses a different word
    # than the script (5:1: gloss says "decrees/wills" but the script +
    # ai_word_meanings say "judges/intends"), so glosses-only matching
    # misses the span entirely. ai_word_meanings.preferred_translation
    # is the same text the script tends to use.
    rows = conn.execute(
        "SELECT g.word_pos, g.translation_en AS gloss, "
        "       a.preferred_translation AS pref, a.meaning_short AS meaning_short "
        "FROM word_glosses g "
        "LEFT JOIN ai_word_meanings a "
        "  ON a.chapter = g.chapter AND a.verse = g.verse "
        "     AND a.word_pos = g.word_pos "
        "WHERE g.chapter = ? AND g.verse = ? "
        "ORDER BY g.word_pos",
        (chapter, verse),
    ).fetchall()
    matches: list[int] = []
    for r in rows:
        g_tokens = _th_tokenize(r["gloss"] or "")
        ai_tokens = _th_tokenize(r["pref"] or "") | _th_tokenize(r["meaning_short"] or "")
        # Match if EITHER source clears the ≥50% bar. We check each
        # source independently (rather than unioning the token sets)
        # so a long ai_meaning_short doesn't dilute the gloss's
        # overlap fraction below the threshold.
        hit = False
        for tokset in (g_tokens, ai_tokens):
            if not tokset:
                continue
            overlap = p_tokens & tokset
            # ≥50% of THIS source's significant tokens must appear in
            # the phrase. Filters incidental "will"/"they" overlaps.
            if overlap and len(overlap) / max(1, len(tokset)) >= 0.5:
                hit = True
                break
        if hit:
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
    # "...isn't about|describing|saying X, but [about|describing] Y" —
    # the speculative-opener register the old script prompt produced
    # ("What if this verse isn't about calling them by a name, but
    # about claiming them as yours?"). Anchor on the contrast pivot
    # `isn't|is not` followed by a contrast verb so the X capture
    # starts right after the verb — without that anchor, the regex
    # would slurp the leading "What if this verse about ..." into
    # the conventional half. Captured here because plenty of
    # existing rows have hooks shaped this way; the new prompt
    # guidance discourages new ones.
    __import__("re").compile(
        r"(?:isn[''‘’]?t|is\s+not)\s+"
        r"(?:about|saying|describing|telling|claiming)\s+"
        r"(.+?)[,;]\s+"
        r"but\s+"
        r"(?:about\s+|that\s+|saying\s+|describing\s+|claiming\s+|it[''‘’]?s\s+about\s+)?"
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


# ---------------------------------------------------------------------------
# Morphology-position resolver for translation_hides signals
#
# Why this exists: the judge's translation_hides_signals row records
# `primary_word_pos` (the judge's own word-index, derived from
# whitespace-splitting the verse text) and `primary_arabic` (the
# actual Arabic word/phrase the judge picked). These two don't
# always line up with the morphology table's `word_pos`, which uses
# a different counting (proclitics like بِ get their own
# segment-grouping, etc.). On 25:58 the signal says position 10
# for dhunūb, but morphology position 10 is bihi — so calling
# `_word_arabic_at_pos(conn, 25, 58, 10)` returned the wrong word
# for the big artifact on the reveal slide and the highlight on
# verse-flow.
#
# The fix is two-pronged:
#
#   1. For the big artifact, don't look it up at all — just trust
#      `signal.primary_arabic`, the word the judge already wrote
#      down. No resolver, no LLM, 100% correct.
#
#   2. For the verse-flow highlight (which DOES need a morphology
#      word_pos because the renderer draws a yellow pill around
#      the N-th word), resolve via algorithmic substring matching
#      first. It handles 99% of cases instantly. Only when the
#      algorithm can't find a unique match do we call an Ollama
#      LLM to disambiguate — and we cache the answer so we never
#      ask twice.
#
# The cache lives in a column on translation_hides_signals
# (`morphology_word_pos`, added below in
# _ensure_morphology_word_pos_column).
# ---------------------------------------------------------------------------


_MWP_COLUMN_CHECKED = False


def _ensure_morphology_word_pos_column(conn) -> None:
    """Add the `morphology_word_pos` cache column to
    translation_hides_signals if it doesn't exist yet. Safe to call
    on every render — short-circuits after the first check per
    process via the module-level flag."""
    global _MWP_COLUMN_CHECKED
    if _MWP_COLUMN_CHECKED:
        return
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(translation_hides_signals)").fetchall()]
        if "morphology_word_pos" not in cols:
            conn.execute("ALTER TABLE translation_hides_signals ADD COLUMN morphology_word_pos INTEGER")
            conn.commit()
            print("[translation-hides] Added morphology_word_pos column to translation_hides_signals")
    except Exception as e:
        # Table might not exist yet on a fresh DB — fail soft and
        # let the resolver no-op when called.
        print(f"[translation-hides] could not ensure morphology_word_pos column: {e}")
    finally:
        _MWP_COLUMN_CHECKED = True


def _normalize_arabic_for_match(s: str) -> str:
    """Lighter normalization than _strip_uthmani_marks — strips ALL
    diacritics and punctuation so that 'ذُنُوبِ' and 'ذنوب' and
    'ذُنوب.' all collapse to the same matchable form."""
    if not s:
        return ""
    import re as _re
    # Strip all Arabic diacritical marks (fatha/kasra/damma/shadda/sukun/etc.)
    s = _re.sub(r"[ً-ٰٟـۖ-ۭ]", "", s)
    # alef wasla → plain alef, alef maksura stays as-is
    s = s.replace("ٱ", "ا")
    # Strip non-Arabic punctuation and whitespace
    s = _re.sub(r"[^؀-ۿ]", "", s)
    return s.strip()


def _signal_for_verse(conn, chapter: int, verse: int) -> dict | None:
    """Pull the most recent translation_hides_signals row for the
    given verse, including cached resolver columns (morphology
    word_pos and the LLM-aligned artifact arabic). Both cache
    columns are created on first call by the _ensure_* helpers so
    a fresh DB or one synced from prod without these columns
    auto-migrates."""
    _ensure_morphology_word_pos_column(conn)
    _ensure_artifact_arabic_column(conn)
    try:
        row = conn.execute(
            """
            SELECT id, primary_word_pos, primary_arabic,
                   COALESCE(morphology_word_pos, NULL) AS morphology_word_pos,
                   COALESCE(artifact_arabic, NULL) AS artifact_arabic
            FROM translation_hides_signals
            WHERE chapter = ? AND verse = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (chapter, verse),
        ).fetchone()
    except Exception:
        return None
    if not row:
        return None
    return {
        "id": row["id"],
        "primary_word_pos": row["primary_word_pos"],
        "primary_arabic": row["primary_arabic"],
        "morphology_word_pos": row["morphology_word_pos"],
        "artifact_arabic": row["artifact_arabic"],
    }


def _morphology_word_forms(conn, chapter: int, verse: int) -> list[tuple[int, str]]:
    """Return [(word_pos, full_concatenated_form), ...] for every
    word position in the verse. The full form is each word's
    segments joined together — so a word stored as multiple
    morphology rows (proclitic + stem + enclitic) shows up as one
    string here."""
    rows = conn.execute(
        """
        SELECT word_pos, GROUP_CONCAT(form_arabic, '') AS full_word
        FROM morphology
        WHERE chapter = ? AND verse = ?
        GROUP BY word_pos
        ORDER BY word_pos
        """,
        (chapter, verse),
    ).fetchall()
    return [(int(r[0]), r[1] or "") for r in rows]


def _resolve_via_substring(
    target_norm: str,
    words: list[tuple[int, str]],
) -> tuple[int | None, list[int]]:
    """Algorithmic resolver. Returns (best_pos, candidate_positions).
    Tries exact-equal first, then substring (target in word), then
    reverse-substring (word in target — handles cases where the
    judge picked a phrase that includes a stem-only word).

    If there's exactly one best match, returns it as best_pos.
    Otherwise best_pos is None and the caller should fall back to
    the LLM disambiguator."""
    if not target_norm:
        return (None, [])
    # Pass 1: exact match after normalization.
    exact = [p for (p, full) in words if _normalize_arabic_for_match(full) == target_norm]
    if len(exact) == 1:
        return (exact[0], exact)
    # Pass 2: target appears inside a word (handles بِذُنُوبِ ⊇ ذُنُوبِ).
    contains = [p for (p, full) in words if target_norm in _normalize_arabic_for_match(full)]
    if len(contains) == 1:
        return (contains[0], contains)
    # Pass 3: word appears inside the target (handles judge-picked phrase).
    contained_by = [p for (p, full) in words
                    if _normalize_arabic_for_match(full)
                    and _normalize_arabic_for_match(full) in target_norm]
    if len(contained_by) == 1:
        return (contained_by[0], contained_by)
    # Collect every candidate from any pass for the LLM.
    candidates = sorted(set(exact + contains + contained_by))
    return (None, candidates)


def _ollama_prefs(conn) -> dict:
    """Read all ollama_* admin_preferences in one query. The table
    is a flat key→value store (`key TEXT PRIMARY KEY, value TEXT`).
    Two earlier callers in this file were SELECTing column names
    that don't exist, which raised silently and made every Ollama
    call fall through to the localhost default — broken on prod."""
    try:
        rows = conn.execute(
            "SELECT key, value FROM admin_preferences WHERE key LIKE 'ollama_%'"
        ).fetchall()
        return {r["key"]: r["value"] for r in rows}
    except Exception as e:
        print(f"[ollama-prefs] could not read admin_preferences: {e}")
        return {}


def _resolve_via_ollama(
    conn,
    chapter: int,
    verse: int,
    target_arabic: str,
    candidates: list[int],
    words: list[tuple[int, str]],
) -> int | None:
    """LLM-based disambiguator. Only invoked when the algorithmic
    resolver finds zero or multiple candidates. Uses the
    admin-configured Ollama endpoint and a small fast local model.

    Returns the resolved word_pos, or None if Ollama is unreachable
    / returns garbage. The caller treats a None as 'don't render
    the highlight rather than render the wrong one.'"""
    import json as _json
    import urllib.request as _urlreq
    import urllib.error as _urlerr
    import re as _re

    # Read Ollama config from admin_preferences. The table is a flat
    # key→value store (key TEXT PRIMARY KEY, value TEXT) — earlier
    # versions of this function ran SELECT ollama_base_url, ollama_api_key
    # FROM admin_preferences which silently raised "no such column"
    # and fell through to the localhost fallback. On prod, where
    # localhost:11434 isn't reachable from inside the container, this
    # made every Ollama call fail and the resolver default to
    # signal.primary_arabic — the source of the 66:12 'فِيهِ' bug.
    prefs = _ollama_prefs(conn)
    base_url = (prefs.get("ollama_base_url") or "http://localhost:11434").rstrip("/")
    api_key = prefs.get("ollama_api_key") or None
    model = "qwen3:14b"  # local, fast, plenty accurate for "pick an integer"

    # Build a clear prompt — give the model the whole verse with
    # numbered positions so it can see the context, not just the
    # candidate set. Otherwise it can't tell which بِذُنُوبِ etc.
    # the judge meant in verses where the same word appears twice.
    numbered = "\n".join(f"  [{p}] {w}" for (p, w) in words)
    candidate_str = ", ".join(str(p) for p in candidates) if candidates else "none — search all"
    prompt = (
        f"You are matching an Arabic word/phrase to its position in a Quranic verse.\n\n"
        f"Verse {chapter}:{verse}, words with positions:\n{numbered}\n\n"
        f"The target word/phrase from the judge: \"{target_arabic}\"\n\n"
        f"Algorithmic-matcher candidates that need disambiguation: {candidate_str}\n\n"
        f"Return ONLY the single integer position of the word that best matches the target. "
        f"If multiple are equally plausible, pick the most semantically central one. "
        f"If nothing matches at all, return 0."
    )
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.0},  # deterministic — we want a single integer
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        req = _urlreq.Request(
            f"{base_url.rstrip('/')}/api/chat",
            data=_json.dumps(payload).encode("utf-8"),
            headers=headers,
        )
        with _urlreq.urlopen(req, timeout=20) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
        content = (data.get("message") or {}).get("content") or ""
        # Strip Ollama <think>...</think> chain-of-thought if present.
        content = _re.sub(r"<think>.*?</think>", "", content, flags=_re.DOTALL).strip()
        m = _re.search(r"\b(\d+)\b", content)
        if not m:
            print(f"[translation-hides] ollama resolver: no integer in response: {content[:120]!r}")
            return None
        pos = int(m.group(1))
        if pos == 0:
            return None
        # Validate: position must exist in the verse's morphology.
        valid_positions = {p for (p, _) in words}
        if pos not in valid_positions:
            print(f"[translation-hides] ollama resolver returned invalid pos {pos} for {chapter}:{verse}")
            return None
        return pos
    except (_urlerr.URLError, _urlerr.HTTPError, TimeoutError, ConnectionError) as e:
        print(f"[translation-hides] ollama resolver unreachable ({e}); falling back")
        return None
    except Exception as e:
        print(f"[translation-hides] ollama resolver crashed: {e}")
        return None


# ---------------------------------------------------------------------------
# Artifact-Arabic resolver for the reveal slide.
#
# The big Arabic word in the center of the reveal slide should match
# what the *script* is narrating about, not necessarily what the
# judge's primary_arabic happens to be. These can disagree:
#
#   - The judge picks the most striking linguistic feature (e.g.
#     for 66:12 it picked فِيهِ, the masculine pronoun where one
#     might expect feminine — a real philological reveal).
#
#   - The script generator writes the narration around a different
#     framing — for 66:12 it built the hook around the chastity
#     narrative ("fortified her private part").
#
# When this happens, the slide ends up showing the judge's word
# while the audio is talking about the script's phrase. On 66:12
# that was a 4-character preposition (فِيهِ) floating alone in
# the center while the voiceover narrated about Mary's chastity —
# operator feedback: "weird; only fi-hi."
#
# The fix: ask Ollama to align the script's english_emphases[0]
# phrase to the corresponding Arabic span in the verse. Falls back
# to signal.primary_arabic when Ollama is unreachable, english_emphases
# is empty, or the LLM returns garbage. Caches per signal row so we
# never call the LLM twice for the same verse.
# ---------------------------------------------------------------------------


def _ensure_artifact_arabic_column(conn) -> None:
    """Add the artifact_arabic cache column to translation_hides_signals
    if it doesn't exist yet. Same shape as _ensure_morphology_word_pos_column."""
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(translation_hides_signals)").fetchall()]
        if "artifact_arabic" not in cols:
            conn.execute("ALTER TABLE translation_hides_signals ADD COLUMN artifact_arabic TEXT")
            conn.commit()
            print("[translation-hides] Added artifact_arabic column to translation_hides_signals")
    except Exception as e:
        print(f"[translation-hides] could not ensure artifact_arabic column: {e}")


def _resolve_artifact_via_ollama(
    conn,
    chapter: int,
    verse: int,
    arabic_verse: str,
    english_translation: str,
    english_phrase: str,
) -> str | None:
    """Ask Ollama: given the verse in Arabic + English, find the
    Arabic phrase that corresponds to this English phrase.

    The phrase will be displayed as the big artifact on the reveal
    slide. Returns the raw Arabic phrase (no normalization) or None
    on any failure — caller falls back to signal.primary_arabic.
    """
    import json as _json
    import urllib.request as _urlreq
    import urllib.error as _urlerr
    import re as _re

    # Same key-value fetch fix as _resolve_via_ollama above — the
    # previous SELECT-by-column-name was raising on every prod call.
    prefs = _ollama_prefs(conn)
    base_url = (prefs.get("ollama_base_url") or "http://localhost:11434").rstrip("/")
    api_key = prefs.get("ollama_api_key") or None
    model = "qwen3:14b"

    prompt = (
        f"You are aligning an English phrase to its corresponding Arabic in a Quranic verse.\n\n"
        f"Arabic verse: {arabic_verse}\n"
        f"English translation: {english_translation}\n\n"
        f'The slide is highlighting this English phrase from the translation: "{english_phrase}"\n\n'
        f"Find the corresponding Arabic phrase IN THE VERSE.\n"
        f"Rules:\n"
        f"  - Output ONLY the Arabic phrase, exactly as it appears in the verse.\n"
        f"  - Keep diacritics from the verse intact. Do not add or remove any.\n"
        f"  - Prefer the tightest matching span (1-4 words). Do not include leading/trailing connectors.\n"
        f"  - If nothing in the verse clearly matches, output the single Arabic word: لا\n"
        f"  - No explanation, no quotes, no transliteration, no English."
    )
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.0},
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        req = _urlreq.Request(
            f"{base_url.rstrip('/')}/api/chat",
            data=_json.dumps(payload).encode("utf-8"),
            headers=headers,
        )
        with _urlreq.urlopen(req, timeout=25) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
        content = (data.get("message") or {}).get("content") or ""
        content = _re.sub(r"<think>.*?</think>", "", content, flags=_re.DOTALL).strip()
        # Strip surrounding quotes or markdown
        content = content.strip().strip('"\'`').strip()
        if not content or content == "لا":
            return None
        # Sanity: must contain at least one Arabic-letter codepoint.
        if not _re.search(r"[؀-ۿݐ-ݿࢠ-ࣿ]", content):
            print(f"[translation-hides] artifact resolver: response contains no Arabic: {content!r}")
            return None
        # Sanity: must appear as a substring of the verse (modulo
        # diacritic differences). This catches LLM hallucinations.
        norm_verse = _normalize_arabic_for_match(arabic_verse)
        norm_content = _normalize_arabic_for_match(content)
        if norm_content and norm_content not in norm_verse:
            print(f"[translation-hides] artifact resolver: response not in verse: {content!r}")
            return None
        return content
    except (_urlerr.URLError, _urlerr.HTTPError, TimeoutError, ConnectionError) as e:
        print(f"[translation-hides] artifact resolver unreachable ({e}); falling back")
        return None
    except Exception as e:
        print(f"[translation-hides] artifact resolver crashed: {e}")
        return None


def _positions_for_arabic_span(conn, chapter: int, verse: int, arabic_text: str) -> list[int]:
    """Given an Arabic phrase (e.g. from Ollama), return the morphology
    word positions whose surface form sits inside it (diacritics
    stripped). Used to map an LLM-aligned Arabic span back to word
    indices for highlighting."""
    span_norm = _normalize_arabic_for_match(arabic_text or "")
    if not span_norm:
        return []
    out: list[int] = []
    for pos, full in _morphology_word_forms(conn, chapter, verse):
        wn = _normalize_arabic_for_match(full)
        if wn and wn in span_norm:
            out.append(pos)
    return sorted(out)


def _align_emphasis_to_positions(
    conn, chapter: int, verse: int, phrase: str, *, use_ollama: bool = True
) -> list[int]:
    """Map an English emphasis phrase to the Arabic word positions it
    corresponds to, for COLOR-COORDINATED highlighting on the
    grammar / translation verse slides.

    Same scoring engine as _resolve_artifact_via_glosses (union of
    word_glosses + ai_word_meanings, n+n² weighting, content-word
    anchor, fa-/sa- clause guard) but with two differences tuned for
    highlighting:
      - returns the POSITION list, not joined Arabic text
      - BRIDGES single-word gaps so a connector with no token overlap
        (e.g. مَا = "as"/"what" between "judges" and "intends") doesn't
        split the highlight. Operator feedback on 5:1: "judges as He
        intends" must light up يَحْكُمُ مَا يُرِيدُ as one span.

    Falls back to the Ollama artifact resolver (then maps its Arabic
    span back to positions) when token scoring finds nothing — covers
    pure synonym-gap phrases the glosses can't bridge.
    """
    phrase_toks = _th_tokenize(phrase)
    if not phrase_toks:
        return []

    rows = conn.execute(
        "SELECT g.word_pos, g.translation_en AS gloss, "
        "       a.preferred_translation AS pref, "
        "       a.meaning_short AS meaning_short "
        "FROM word_glosses g "
        "LEFT JOIN ai_word_meanings a "
        "  ON a.chapter = g.chapter AND a.verse = g.verse "
        "     AND a.word_pos = g.word_pos "
        "WHERE g.chapter = ? AND g.verse = ? "
        "ORDER BY g.word_pos",
        (chapter, verse),
    ).fetchall()

    scores: dict[int, float] = {}
    for r in rows:
        toks = (
            _th_tokenize(r["gloss"] or "")
            | _th_tokenize(r["pref"] or "")
            | _th_tokenize(r["meaning_short"] or "")
        )
        if not toks:
            continue
        overlap = toks & phrase_toks
        if not overlap:
            continue
        n = len(overlap)
        scores[int(r["word_pos"])] = n * (1 + n)

    if not scores:
        # Glosses found nothing — synonym gap. Try Ollama (returns an
        # Arabic span), then map that span back to positions.
        if use_ollama:
            vd = _verse_data(conn, chapter, verse)
            if vd and vd.get("arabic"):
                span = _resolve_artifact_via_ollama(
                    conn, chapter, verse, vd["arabic"],
                    vd.get("translation") or "", phrase,
                )
                if span:
                    return _positions_for_arabic_span(conn, chapter, verse, span)
        return []

    # Content-word anchor (don't seed on a bare particle).
    content_positions: set[int] = set()
    try:
        for m in conn.execute(
            "SELECT word_pos, tag FROM morphology WHERE chapter = ? AND verse = ?",
            (chapter, verse),
        ).fetchall():
            if (m["tag"] or "").upper() in ("V", "N", "PN", "ADJ"):
                content_positions.add(int(m["word_pos"]))
    except Exception:
        content_positions = set(scores.keys())
    anchor_scores = {p: s for p, s in scores.items() if p in content_positions} or scores
    anchor = max(anchor_scores, key=anchor_scores.get)

    # fa-/sa- clause-starter guard (don't cross a new clause).
    clause_starters: set[int] = set()
    try:
        for r in conn.execute(
            "SELECT word_pos, MIN(segment), tag, form_arabic FROM morphology "
            "WHERE chapter = ? AND verse = ? GROUP BY word_pos",
            (chapter, verse),
        ).fetchall():
            if (r["tag"] or "").upper() != "PREFIX":
                continue
            if _normalize_arabic_for_match(r["form_arabic"] or "") in ("ف", "س"):
                clause_starters.add(int(r["word_pos"]))
    except Exception:
        pass

    def _can_step(p: int) -> bool:
        return p not in clause_starters

    # Extend with single-gap bridging. A neighbor with overlap extends
    # the span; a single gap is bridged only when the word TWO away
    # has overlap (so connectors like مَا join "judges ... intends"),
    # never across a clause-starter.
    lo = anchor
    while True:
        if (lo - 1) in scores and _can_step(lo - 1):
            lo -= 1
        elif (lo - 2) in scores and _can_step(lo - 1) and _can_step(lo - 2):
            lo -= 2
        else:
            break
    hi = anchor
    while True:
        if (hi + 1) in scores and _can_step(hi + 1):
            hi += 1
        elif (hi + 2) in scores and _can_step(hi + 1) and _can_step(hi + 2):
            hi += 2
        else:
            break

    # Return every position in [lo..hi] that's a real word (the bridged
    # gap IS included so the highlight is visually contiguous).
    valid = {p for p, _ in _morphology_word_forms(conn, chapter, verse)}
    return [p for p in range(lo, hi + 1) if p in valid]


def _resolve_artifact_via_glosses(
    conn, chapter: int, verse: int, english_phrase: str
) -> str | None:
    """Algorithmic artifact resolver — no LLM needed, runs everywhere.

    Why this exists alongside the Ollama resolver: prod doesn't have
    Ollama reachable (the container's network can't hit
    localhost:11434), so the Ollama path falls through and we end up
    showing signal.primary_arabic — which on 66:12 is the pronoun
    فِيهِ while the script narrates about Mary's chastity. This is
    the deterministic path that catches the common case without an
    LLM round-trip.

    Method:
      1. Score every word_pos by overlap between english_phrase
         tokens and a UNION of (word_glosses.translation_en,
         ai_word_meanings.preferred_translation, .meaning_short).
         Pulling in ai_word_meanings is what unlocks 66:12 — its
         preferred_translation for pos 6 is "her private part",
         which `her chastity` (the word_glosses version) doesn't
         cover.
      2. Weight by overlap size so multi-token matches dominate
         the 1-token "her" / "his" matches that would otherwise
         pull anchors across the whole verse.
      3. Take the highest-scoring position as the anchor; extend
         left/right into adjacent words whose score is also above
         a noise floor.
      4. Concatenate morphology forms across the contiguous span.

    Returns the Arabic phrase string, or None when no position
    cleared the noise floor.
    """
    phrase_toks = _th_tokenize(english_phrase)
    if not phrase_toks:
        return None

    # Per-position English signal — union of glosses + AI meaning.
    rows = conn.execute(
        "SELECT g.word_pos, g.translation_en AS gloss, "
        "       a.preferred_translation AS pref, "
        "       a.meaning_short AS meaning_short "
        "FROM word_glosses g "
        "LEFT JOIN ai_word_meanings a "
        "  ON a.chapter = g.chapter AND a.verse = g.verse "
        "     AND a.word_pos = g.word_pos "
        "WHERE g.chapter = ? AND g.verse = ? "
        "ORDER BY g.word_pos",
        (chapter, verse),
    ).fetchall()
    if not rows:
        return None

    scores: dict[int, float] = {}
    for r in rows:
        toks = (
            _th_tokenize(r["gloss"] or "")
            | _th_tokenize(r["pref"] or "")
            | _th_tokenize(r["meaning_short"] or "")
        )
        if not toks:
            continue
        overlap = toks & phrase_toks
        if not overlap:
            continue
        # Score = overlap_count * (1 + overlap_count). This is
        # n + n²: it rewards multi-token matches much more strongly
        # than 1-token matches without dividing by signal size
        # (which would let a tight 1-token gloss tie a broader
        # multi-token gloss). Concretely on 34:39 / "will replace
        # it (succession)" this is what lets pos 17 (gloss "will
        # replace it" — overlap {will, replac}, score 6) beat
        # pos 7 (gloss "He wills" — overlap {will}, score 2).
        n = len(overlap)
        scores[int(r["word_pos"])] = n * (1 + n)

    if not scores:
        return None

    # Identify which positions are CONTENT words (have a Verb,
    # Noun, Proper Noun, or Adjective segment in their morphology).
    # We restrict the ANCHOR pick to these — pure-particle words
    # like لِلَّذِينَ ("for those who") would otherwise win the
    # anchor on phrases like "those who covered the truth" simply
    # because their gloss is itself "for those who" (100% overlap
    # against a function-word slot). The focal verb كَفَرُوا is
    # what the script actually wants the slide to show. Non-content
    # positions can still be PICKED UP via the lo/hi extension step
    # below — they just can't seed the anchor.
    content_positions: set[int] = set()
    try:
        morph_tags = conn.execute(
            "SELECT word_pos, tag FROM morphology "
            "WHERE chapter = ? AND verse = ?",
            (chapter, verse),
        ).fetchall()
        for m in morph_tags:
            tag = (m["tag"] or "").upper()
            if tag in ("V", "N", "PN", "ADJ"):
                content_positions.add(int(m["word_pos"]))
    except Exception:
        # If we can't read morphology for any reason, fall through
        # and let any position anchor — better than no result.
        content_positions = set(scores.keys())

    anchor_scores = {p: s for p, s in scores.items() if p in content_positions}
    if not anchor_scores:
        # No content-word anchor — fall back to any-position anchor
        # so we don't return None just because the matched gloss is
        # on a particle (rare; usually the script picks content
        # phrases).
        anchor_scores = scores
    anchor = max(anchor_scores, key=anchor_scores.get)
    # Pre-compute which positions START a new clause (their first
    # morphology segment is a fa- or sa- prefix). We refuse to
    # extend ACROSS those — even when the position has a weak
    # token overlap — because in Arabic those prefixes mark a
    # clause boundary, and the script's english_emphases is
    # almost always a sub-clause, not a spanning one. Concretely
    # on 66:12, pos 7 (فَنَفَخْنَا "so We breathed") shares the
    # promiscuous token "her" with the phrase "fortified her
    # private part" via its ai_meaning "breathe into her", which
    # without this guard would over-extend the span by pulling
    # in pos 7. wa- (و) is intentionally NOT treated as a hard
    # boundary because it's also used to coordinate noun lists
    # (e.g. الرَّحْمَٰنِ الرَّحِيمِ has no wa-, but many noun
    # phrases do — being too aggressive splits legitimate lists).
    clause_starters: set[int] = set()
    try:
        first_segs = conn.execute(
            "SELECT word_pos, MIN(segment), tag, form_arabic FROM morphology "
            "WHERE chapter = ? AND verse = ? "
            "GROUP BY word_pos",
            (chapter, verse),
        ).fetchall()
        for r in first_segs:
            tag = (r["tag"] or "").upper()
            if tag != "PREFIX":
                continue
            form_norm = _normalize_arabic_for_match(r["form_arabic"] or "")
            if form_norm in ("ف", "س"):
                clause_starters.add(int(r["word_pos"]))
    except Exception:
        pass

    # Extension: walk outward as long as the IMMEDIATE neighbor
    # has overlap AND isn't a clause-starter. "In scores" already
    # filters to positions with non-zero overlap; the clause
    # filter blocks the fa-/sa- bleed described above.
    lo = anchor
    while lo - 1 in scores and (lo - 1) not in clause_starters:
        lo -= 1
    hi = anchor
    while hi + 1 in scores and (hi + 1) not in clause_starters:
        hi += 1

    # Walk morphology to build the Arabic surface form.
    morph_rows = conn.execute(
        "SELECT word_pos, segment, form_arabic FROM morphology "
        "WHERE chapter = ? AND verse = ? "
        "ORDER BY word_pos, segment",
        (chapter, verse),
    ).fetchall()
    by_pos: dict[int, list[str]] = {}
    for m in morph_rows:
        by_pos.setdefault(int(m["word_pos"]), []).append(m["form_arabic"] or "")
    parts: list[str] = []
    for p in range(lo, hi + 1):
        segs = by_pos.get(p)
        if not segs:
            continue
        parts.append("".join(segs))
    if not parts:
        return None
    return " ".join(parts)


def resolve_artifact_arabic(
    conn,
    chapter: int,
    verse: int,
    signal: dict | None,
    english_emphases: list[str],
    *,
    use_ollama: bool = True,
) -> tuple[str, str]:
    """Choose the Arabic to display as the reveal slide's big artifact.

    Priority order:
      1. Algorithmic glosses+ai_word_meanings match — runs first
         because it's fast (a couple of SQL queries), deterministic,
         and ALWAYS reflects the current script.english_emphases. We
         deliberately do NOT cache its result: re-running at render
         time costs almost nothing and avoids stale cache mismatches
         when the script gets regenerated with a different emphasis.
      2. Cached signals.artifact_arabic — only populated by the
         Ollama path below (kept as a hint when the algorithmic path
         failed but Ollama once succeeded for this verse).
      3. Ollama-aligned phrase from script.english_emphases[0] —
         the fallback for verses the algorithm can't handle (e.g.,
         when the script's emphasis uses tokens that don't appear
         anywhere in the per-word gloss data).
      4. signal.primary_arabic (the judge's pick — may be a tiny
         pronoun, but better than nothing).
      5. empty string (caller skips the artifact).

    Returns (arabic, source_label).
    """
    _ensure_artifact_arabic_column(conn)

    # 1. Algorithmic — fast, deterministic, no LLM. This is what
    # makes prod work (Ollama not reachable there). It also takes
    # precedence over the cache because the cache may have been
    # populated against an OLDER script.english_emphases — running
    # algorithm fresh against the current phrase keeps the artifact
    # in sync with whatever the audio is narrating right now.
    if english_emphases:
        phrase = (english_emphases[0] or "").strip()
        if phrase:
            resolved = _resolve_artifact_via_glosses(conn, chapter, verse, phrase)
            if resolved:
                return (resolved, "glosses")

    # 2. Cached (from a prior Ollama run)?
    if signal and signal.get("artifact_arabic"):
        return (signal["artifact_arabic"], "cached")

    # 3. Ollama alignment from english_emphases[0]?
    if use_ollama and english_emphases:
        phrase = (english_emphases[0] or "").strip()
        if phrase:
            vd = _verse_data(conn, chapter, verse)
            if vd and vd.get("arabic"):
                resolved = _resolve_artifact_via_ollama(
                    conn,
                    chapter,
                    verse,
                    vd["arabic"],
                    vd.get("translation") or "",
                    phrase,
                )
                if resolved:
                    # Cache to the signal row if we have one.
                    if signal and signal.get("id"):
                        try:
                            conn.execute(
                                "UPDATE translation_hides_signals SET artifact_arabic = ? WHERE id = ?",
                                (resolved, signal["id"]),
                            )
                            conn.commit()
                            print(
                                f"[translation-hides] resolved artifact_arabic for "
                                f"{chapter}:{verse} → {resolved!r} (via ollama); cached"
                            )
                        except Exception as e:
                            print(f"[translation-hides] could not cache artifact_arabic: {e}")
                    return (resolved, "ollama")
    # 4. Signal's primary_arabic (the judge's pick — may be short).
    if signal and signal.get("primary_arabic"):
        return (signal["primary_arabic"], "primary")
    # 5. Nothing usable.
    return ("", "none")


def resolve_morphology_word_pos(
    conn,
    chapter: int,
    verse: int,
    target_arabic: str,
    *,
    use_ollama: bool = True,
) -> tuple[int | None, str]:
    """Public entry point. Given a verse and the Arabic word/phrase
    the judge identified, return the morphology word_pos that
    contains it (or None if we can't determine one safely).

    The second tuple element is a source label for logging:
      'exact'      — algorithmic exact match after normalization
      'substring'  — algorithmic unique substring match
      'cached'     — pulled from translation_hides_signals.morphology_word_pos
      'ollama'     — LLM disambiguated
      'no-match'   — couldn't resolve; caller should skip highlight
    """
    _ensure_morphology_word_pos_column(conn)
    target_norm = _normalize_arabic_for_match(target_arabic)
    if not target_norm:
        return (None, "no-match")
    words = _morphology_word_forms(conn, chapter, verse)
    if not words:
        return (None, "no-match")
    # Algorithmic first — fast and free.
    best, candidates = _resolve_via_substring(target_norm, words)
    if best is not None:
        return (best, "substring")
    if not use_ollama:
        return (None, "no-match")
    # LLM fallback for genuinely ambiguous cases.
    pos = _resolve_via_ollama(conn, chapter, verse, target_arabic, candidates, words)
    if pos is not None:
        return (pos, "ollama")
    return (None, "no-match")


def _resolve_lens_focal_pos(
    conn,
    chapter: int,
    verse: int,
    artifact_arabic: str,
    signal: dict | None,
) -> int | None:
    """Pick the single morphology word_pos that should drive the
    word-lens slide.

    The lens magnifies ONE word and shows its conventional vs AI
    glosses. When the artifact (from the script's english_emphases)
    is a multi-word phrase, the signal's primary_arabic may point
    at a completely different word — leaving the lens magnifying
    something the audio isn't even talking about. Operator
    feedback on 66:12: the audio narrates "fortified her farj.
    Farj is..." while the lens slide displays فِيهِ ("into it") —
    misaligned.

    Resolution order:
      1. If signal.primary_arabic is contained in the artifact
         phrase, the lens is already aligned — use the signal's
         cached morphology_word_pos (the previous fix).
      2. Otherwise, scan morphology for words whose stripped form
         appears inside the stripped artifact AND that have a
         usable ai_word_meanings row. Prefer the LAST such word,
         which in Arabic noun-phrases is typically the focal noun
         the audio will name. (For 66:12 artifact
         "أَحْصَنَتْ فَرْجَهَا" this returns pos 6 / فَرْجَهَا — what
         the audio is actually narrating about.)
      3. None — caller skips the lens slide and lets the insight
         narration play over the verse-flow instead.
    """
    if not artifact_arabic:
        return None
    art_norm = _normalize_arabic_for_match(artifact_arabic)
    if not art_norm:
        return None
    # Case 1: signal's primary_arabic is part of the artifact — use
    # the morphology position of that primary word. If the cached
    # value isn't on the signal dict (e.g. first render of a new
    # signal where the caller forgot to patch the in-memory dict
    # after the DB UPDATE), resolve it on the fly via the
    # algorithm-only path so we never fall through to the LAST-wins
    # Case 2 just because of stale dict state. This is the
    # defense-in-depth half of the 17:62 / 25:58 lens bug fix.
    if signal and signal.get("primary_arabic"):
        sig_norm = _normalize_arabic_for_match(signal["primary_arabic"])
        if sig_norm and sig_norm in art_norm:
            mp = signal.get("morphology_word_pos")
            if mp is None:
                resolved, _src = resolve_morphology_word_pos(
                    conn, chapter, verse, signal["primary_arabic"],
                    use_ollama=False,  # algorithm-only — fast + deterministic
                )
                mp = resolved
            if mp is not None:
                return int(mp)
    # Case 2: scan morphology words; pick the last one that's both
    # inside the artifact and has an ai_word_meanings entry.
    words = _morphology_word_forms(conn, chapter, verse)
    if not words:
        return None
    # Pre-fetch which positions have ai_word_meanings to avoid
    # per-iteration queries.
    try:
        meaning_positions = {
            int(r[0])
            for r in conn.execute(
                "SELECT word_pos FROM ai_word_meanings WHERE chapter = ? AND verse = ?",
                (chapter, verse),
            ).fetchall()
        }
    except Exception:
        meaning_positions = set()
    best_pos: int | None = None
    for pos, full in words:
        full_norm = _normalize_arabic_for_match(full)
        if not full_norm:
            continue
        if full_norm in art_norm and pos in meaning_positions:
            best_pos = pos  # keep advancing; last wins
    return best_pos


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
      1. word_glosses.translation_en (the plain conventional English)
      2. None (caller substitutes a neutral label like "the usual reading")

    For the "actually means" (ai_short) side, we pick between two
    candidates on the ai_word_meanings row:
      - meaning_short: the polished AI gloss (e.g. "the sins")
      - preferred_translation: the judge's preferred surface form
        (e.g. "the tails")
    and prefer the one that CONTRASTS MORE with the conventional
    gloss. Operator feedback on 25:58: conv was "regarding the sins",
    meaning_short was "the sins" (just a synonym → no reveal),
    preferred_translation was "the tails" — which is what the audio
    is unpacking. Picking by contrast lands the right answer in both
    that case and 17:62 (where meaning_short "I will firmly seize
    /control" is more contrasty than preferred "take full control").
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
    meaning_short = (awm["meaning_short"] or "").strip()
    preferred = (awm["preferred_translation"] or "").strip()
    if not meaning_short and not preferred:
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

    # Pick the hidden gloss. Prefer meaning_short (the judge's
    # polished default) UNLESS its content tokens are a subset of
    # the conventional gloss — that's the synonym-swap case where
    # the lens slide would show "regarding the sins" → "the sins"
    # (no reveal). When that happens, fall back to
    # preferred_translation, which on those rows tends to carry the
    # actual literal/etymological surface form (e.g. "the tails").
    #
    # Tested on:
    #   25:58 pos 11: conv "regarding the sins" / meaning_short
    #       "the sins" (subset → reject) / preferred "the tails"
    #       → use "the tails" ✓
    #   17:62 pos 12: conv "I will surely destroy" / meaning_short
    #       "I will firmly seize/control" (adds seize+firmly+control)
    #       → use meaning_short ✓
    #   66:12 pos 6:  conv "her chastity" / meaning_short
    #       "her private parts" (adds privat+part) → use meaning_short ✓
    conv_tokens = _th_tokenize(conv)

    def _is_subset_of_conv(candidate: str) -> bool:
        """True when candidate's significant tokens are all already
        in the conventional gloss — i.e. nothing new is revealed."""
        toks = _th_tokenize(candidate)
        if not toks:
            return True  # empty has nothing to reveal
        return toks.issubset(conv_tokens)

    if meaning_short and not _is_subset_of_conv(meaning_short):
        ai_short = meaning_short
    elif preferred and not _is_subset_of_conv(preferred):
        ai_short = preferred
    elif meaning_short:
        # Both look like synonym-swaps but we have to render
        # something — pick the more verbose one.
        ai_short = meaning_short
    else:
        ai_short = preferred

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

    # Pull the signals row — the judge already wrote down the
    # exact Arabic word/phrase it picked, and we trust that as the
    # source of truth for what to display. The script's
    # selected_word_pos is the judge's own count (whitespace-based);
    # it doesn't always agree with the morphology table's word_pos
    # because proclitics (بِ, لِ, وَ, ...) get split differently.
    # The signal row lets us SIDESTEP the count entirely for the
    # big reveal-slide artifact and resolve the morphology position
    # only for the highlight (which truly needs an integer position).
    signal = _signal_for_verse(conn, chapter, verse)

    # Resolve the *morphology-aligned* word position so the
    # verse-flow highlight lands on the right word. Order of
    # preference:
    #   1. cached signals.morphology_word_pos (resolved once, used forever)
    #   2. algorithmic substring match on signal.primary_arabic
    #   3. Ollama LLM disambiguator for ambiguous candidates
    #   4. fall back to script.selected_word_pos (the original bug)
    morph_pos: int | None = None
    if signal and signal.get("morphology_word_pos"):
        morph_pos = int(signal["morphology_word_pos"])
    elif signal and signal.get("primary_arabic"):
        resolved, source = resolve_morphology_word_pos(
            conn, chapter, verse, signal["primary_arabic"]
        )
        if resolved is not None:
            morph_pos = resolved
            # CRITICAL: also patch the in-memory signal dict, NOT
            # just the DB. _resolve_lens_focal_pos below reads
            # signal["morphology_word_pos"] directly and used to
            # see the pre-resolution None value, dropping into Case
            # 2 (LAST-matching-word) which picks the wrong focal
            # word in verb+noun artifacts (17:62 noun ذُرِّيَّتَهُ
            # instead of verb لَأَحْتَنِكَنَّ; 25:58 noun عِبَادِهِ
            # instead of verb بِذُنُوبِ). Cached DB rows used Case 1
            # correctly on SECOND render, which is why these bugs
            # were invisible during diagnostics — only the FIRST
            # render of any new signal hit them.
            signal["morphology_word_pos"] = morph_pos
            # Cache the answer back to the signals row so we never
            # have to call the LLM again for this verse.
            try:
                conn.execute(
                    "UPDATE translation_hides_signals SET morphology_word_pos = ? WHERE id = ?",
                    (morph_pos, signal["id"]),
                )
                conn.commit()
                print(
                    f"[translation-hides] resolved morphology_word_pos for "
                    f"{chapter}:{verse} → {morph_pos} (via {source}); cached"
                )
            except Exception as e:
                print(f"[translation-hides] could not cache morphology_word_pos: {e}")
    # If we have a morph_pos from signal-resolution AND a script
    # target_pos that disagrees, prefer the resolved one — the
    # signal's primary_arabic is the most trustworthy anchor.
    highlight_pos = morph_pos if morph_pos is not None else target_pos

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
    # The hookLine field is now OPTIONAL. Previous defaults
    # ("Most translations miss this." / "There's a word in this
    # verse...") were dismissive of the conventional reading and
    # operator feedback on the 33:5 render called them out —
    # "Most translations miss this... can come off as a bit
    # offensive." The contrast pills the viewer is about to see
    # already make the same point without sounding accusatory, so
    # we just omit the hook chrome and let the artifact + verse
    # reference open the slide on their own.
    reveal_slide: dict = {
        "type": "translation-reveal",
        "durationSec": 10,  # bumped from 7s; the new 4-beat
                            # choreography needs the runway. The
                            # narration audio still drives final
                            # playback length via prepareNarration.
        "chapter": chapter,
        "verse": verse,
        "verseRef": f"Quran {chapter}:{verse}",
        "conventionalLabel": "Most translations say",
        "conventionalText": conv_text,
        "hiddenLabel": "The Arabic actually says",
        "hiddenText": hidden_text,
    }
    # Choose the artifact Arabic. The script's english_emphases is
    # the strongest signal of what the AUDIO is actually talking
    # about — much stronger than signal.primary_arabic, which can
    # be a tiny pronoun (66:12 فِيهِ) while the script is narrating
    # about a completely different facet of the same verse (66:12
    # script talks about Mary's chastity, not the pronoun shift).
    # The resolver tries Ollama to align english_emphases[0] to the
    # Arabic span in the verse, then caches; falls back to
    # signal.primary_arabic if Ollama is unreachable.
    emphases_for_resolver = [em["phrase"] for em in en_emphases]
    artifact_arabic_raw, artifact_source = resolve_artifact_arabic(
        conn, chapter, verse, signal, emphases_for_resolver
    )
    # If everything failed and we have a highlight_pos, last-ditch
    # morphology lookup (may be wrong word due to position-mismatch,
    # but better than showing nothing).
    if not artifact_arabic_raw and highlight_pos:
        fallback = _word_arabic_at_pos(conn, chapter, verse, highlight_pos)
        if fallback:
            artifact_arabic_raw = fallback
            artifact_source = "morphology-fallback"
    if artifact_arabic_raw:
        reveal_slide["arabic"] = _strip_uthmani_marks(artifact_arabic_raw)
    # Also pass the English emphasis as a gloss line so the viewer
    # has a context anchor below the Arabic. Even when the Arabic
    # is short or unfamiliar, the English under it makes it land.
    if en_emphases:
        reveal_slide["glossLine"] = en_emphases[0]["phrase"]
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
    if highlight_pos:
        verse_slide["highlightWordIndex"] = highlight_pos
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
    if highlight_pos:
        multi_idx.add(highlight_pos)
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
    # Lens slide focus — pick the word the AUDIO is talking about,
    # not the word the judge originally flagged. The new resolver
    # walks the morphology, intersects with the artifact phrase,
    # and prefers the LAST matching word that has an
    # ai_word_meanings row (typically the focal noun in Arabic
    # noun-phrases). For verses where artifact and signal agree
    # this is a no-op; for verses like 66:12 where they diverge,
    # this picks فَرْجَهَا (pos 6) instead of فِيهِ (pos 8).
    lens_focal_pos = _resolve_lens_focal_pos(
        conn, chapter, verse, artifact_arabic_raw, signal
    )
    if lens_focal_pos is None:
        # No lens-aligned word found — fall back to highlight_pos
        # so we don't lose the lens slide entirely on edge cases
        # (e.g. videos without a signal row).
        lens_focal_pos = highlight_pos

    lens_emitted = False
    if lens_focal_pos:
        lens_data = _word_lens_data_for(conn, chapter, verse, lens_focal_pos)
        # The lens's big Arabic word should be the focal word at
        # lens_focal_pos — NOT signal.primary_arabic, which can be
        # a different word entirely. Fetch the word's surface form
        # from morphology.
        target_arabic = _word_arabic_at_pos(conn, chapter, verse, lens_focal_pos)
        # Last resort if morphology lookup somehow fails: signal's
        # primary_arabic (may be wrong word, but at least non-empty).
        if not target_arabic and signal and signal.get("primary_arabic"):
            target_arabic = signal["primary_arabic"]
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
                "wordPos": lens_focal_pos,
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
