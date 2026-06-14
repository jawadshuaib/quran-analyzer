"""Q&A video — Gate B, Layer 0: compile the renderer payload FROM the
structured script's semantic intent.

The script never hand-authors word indices. It says, per verse beat,
"highlight this Arabic word (by surface form) and this English phrase".
This compiler resolves those into the 1-based whitespace indices the
renderer uses, by locating the intended surface form inside the EXACT
arabicText the renderer will receive (basmala- and mark-stripped). That
is what immunizes the highlights against the two known divergence
buckets:

  - verse-1 basmala offset (indices shift by ~4 if the basmala isn't
    stripped) — we strip it, and the surface-form check would catch a
    mistake anyway.
  - orthographic multi-token words (e.g. 37:130 'إِلْ يَاسِينَ' is one
    morphology word_pos but two whitespace tokens) — surface-form
    resolution lands on the right whitespace token, not a stale
    morphology position.

Output: (payload, intent) where `intent` is a per-slide list (aligned
to payload.slides) carrying what each verse-flow slide is SUPPOSED to
light, so the match-gate can re-validate independently.

Phase-0 slide mapping (compose existing slides — no renderer redesign):
  verse beats  -> verse-flow slides (anchor first, then cross-ref)
  hook         -> prepended to the first verse-flow's narration
  land         -> appended to the last verse-flow's narration
  + a silent outro slide
A dedicated question/answer card is Phase 1.
"""

from __future__ import annotations

import qa_video_common as C


class CompileError(Exception):
    pass


def _resolve_indices(tokens: list[str], intended_forms: list[str],
                     hint_indices: list[int] | None) -> list[int]:
    """1-based whitespace indices for the intended surface forms.

    With `hint_indices` (explicit 1-based positions for ambiguous /
    orthographic-split cases) we trust them but the gate still validates
    the surface form lands. Otherwise we locate each intended form by
    consonantal-skeleton equality and REQUIRE an unambiguous single
    match (fail closed)."""
    if hint_indices:
        idxs = sorted({int(i) for i in hint_indices})
        for i in idxs:
            if not (1 <= i <= len(tokens)):
                raise CompileError(f"hint index {i} out of range 1..{len(tokens)}")
        return idxs
    # A single array element may itself be a multi-word phrase (the model
    # sometimes puts "يَتَٰمَى ٱلنِّسَآء" in one slot); split into tokens so
    # each resolves independently.
    flat_forms: list[str] = []
    for f in intended_forms:
        flat_forms += [p for p in str(f).split() if p]

    idxs: list[int] = []
    for form in flat_forms:
        matches = [i + 1 for i, t in enumerate(tokens) if C.token_matches_form(t, form)]
        if not matches:
            raise CompileError(
                f"intended word {form!r} (skeleton {C.normalize_ar(form)!r}) "
                f"not found among verse tokens"
            )
        if len(matches) > 1:
            raise CompileError(
                f"intended word {form!r} is ambiguous (positions {matches}); "
                f"add \"word_indices\" to the beat to disambiguate"
            )
        idxs.append(matches[0])
    return sorted(set(idxs))


def _verse_flow_slide(conn, ref: str, beat_verse: dict, narration: str) -> tuple[dict, dict]:
    if not isinstance(beat_verse, dict):
        raise CompileError(f"verse beat for {ref} is malformed (not an object)")
    c, v = C.parse_ref(ref)
    vd = C.verse_data(conn, c, v)
    if not vd:
        raise CompileError(f"verse {ref} not found")
    arabic = C.display_arabic(vd["arabic_raw"], c, v)
    tokens = C.verse_tokens(arabic)
    raw_forms = beat_verse.get("highlight_words_ar") or []
    # Each element may itself be a multi-word phrase — flatten to tokens so
    # both the resolver and the gate's intent agree on the unit.
    forms = [p for f in raw_forms for p in str(f).split() if p]
    if not forms:
        raise CompileError(f"verse beat for {ref} has no highlight_words_ar")
    idxs = _resolve_indices(tokens, forms, beat_verse.get("word_indices"))

    # The English pill is a SECONDARY aid; the airtight requirement is the
    # Arabic highlight. If the model's phrase isn't a verbatim substring of
    # the translation (it would silently not render), degrade gracefully —
    # omit the English pill rather than fail the whole video. The gate then
    # only ever sees a phrase that genuinely renders.
    phrase = (beat_verse.get("highlight_phrase_en") or "").strip()
    translation = vd["translation"] or ""
    english_omitted = bool(phrase) and phrase.lower() not in translation.lower()
    if english_omitted:
        phrase = ""

    slide = {
        "type": "verse-flow",
        "durationSec": 6,
        "surah": c,
        "ayah": v,
        "arabicText": arabic,
        "translation": translation,
        "highlightWordIndices": idxs,
        "narration": {"text": C.sanitize_for_tts(narration)},
    }
    if phrase:
        slide["highlightTranslationText"] = phrase

    intent = {
        "surah": c,
        "ayah": v,
        "indices": idxs,
        "skeletons": sorted({C.normalize_ar(f) for f in forms}),
        "forms": forms,
        "phrase": phrase,
        "english_omitted": english_omitted,
    }
    return slide, intent


def _outro_slide() -> dict:
    return {
        "type": "outro",
        "durationSec": 3,
        "siteName": "al-nuqta.com",
        "tagline": "A Root Based Translation of the Quran",
    }


def compile_payload(conn, script: dict) -> tuple[dict, list[dict | None]]:
    """Compile a structured script into a renderer payload + per-slide
    intent. Raises CompileError on any unresolvable highlight."""
    beats = script.get("beats") or []
    if not beats:
        raise CompileError("script has no beats")

    slides: list[dict] = []
    intent: list[dict | None] = []
    pending_prefix = ""  # leading no-verse narration (e.g. the hook)

    for beat in beats:
        if not isinstance(beat, dict):
            raise CompileError(f"malformed beat (not an object): {beat!r:.60}")
        narr = (beat.get("narration") or "").strip()
        bverse = beat.get("verse")
        if bverse:
            ref = bverse.get("ref")
            if not ref:
                raise CompileError(f"verse beat {beat.get('kind')!r} missing ref")
            combined = (pending_prefix + " " + narr).strip() if pending_prefix else narr
            pending_prefix = ""
            slide, vintent = _verse_flow_slide(conn, ref, bverse, combined)
            slides.append(slide)
            intent.append(vintent)
        else:
            # No-verse beat (hook / land / connective): attach narration
            # to the current slide, or buffer it for the first verse slide.
            if slides:
                prev = slides[-1]
                existing = ((prev.get("narration") or {}).get("text") or "").strip()
                merged = f"{existing} {C.sanitize_for_tts(narr)}".strip()
                prev["narration"] = {"text": merged}
            else:
                pending_prefix = (pending_prefix + " " + narr).strip()

    if not slides:
        raise CompileError("script produced no verse slides — nothing to show")
    if pending_prefix:
        # Hook with no verse anywhere after it: prepend to first slide.
        first = slides[0]
        existing = ((first.get("narration") or {}).get("text") or "").strip()
        first["narration"] = {"text": f"{C.sanitize_for_tts(pending_prefix)} {existing}".strip()}

    if sum(1 for s in slides if s["type"] == "verse-flow") > 2:
        # Not fatal at compile; the punchiness gate enforces the ≤2 rule.
        pass

    slides.append(_outro_slide())
    intent.append(None)

    payload = {
        "slides": slides,
        "videoId": str(script.get("qa_id") or 0),
        "title": script.get("title") or "",
    }
    return payload, intent
