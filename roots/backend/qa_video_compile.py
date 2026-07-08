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


def _resolve_verse(conn, ref: str, beat_verse: dict) -> dict:
    """Fail-closed resolution of one verse + its highlight intent. Shared by
    verse-flow slides and both halves of a verse-contrast slide, so every
    on-screen highlight goes through the SAME resolver."""
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

    return {
        "surah": c, "ayah": v, "arabic": arabic, "translation": translation,
        "idxs": idxs, "forms": forms, "phrase": phrase,
        "english_omitted": english_omitted,
    }


def _verse_flow_slide(conn, ref: str, beat_verse: dict, narration: str) -> tuple[dict, dict]:
    r = _resolve_verse(conn, ref, beat_verse)
    c, v = r["surah"], r["ayah"]
    arabic, translation = r["arabic"], r["translation"]
    idxs, forms, phrase = r["idxs"], r["forms"], r["phrase"]
    english_omitted = r["english_omitted"]

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


def _root_slide(conn, beat: dict, narration: str) -> dict:
    """A root shown on its own slide. FAIL CLOSED: the root must actually be
    a root of a word in one of the script's verses — we verify by converting
    the anchor verse's morphology roots (Buckwalter) to Arabic and matching
    letter-skeletons, so the writer can never invent a root."""
    import buckwalter as BW
    spec = beat.get("root") or {}
    root_ar = (spec.get("arabic") or "").strip()
    if not root_ar:
        raise CompileError("root beat missing root.arabic")
    want = C.normalize_ar(root_ar.replace(" ", "").replace("-", ""))

    allowed = set()
    refs = beat.get("_script_refs") or []
    for ref in refs:
        try:
            c, v = C.parse_ref(ref)
        except ValueError:
            continue
        try:
            rows = conn.execute(
                "SELECT DISTINCT root_buckwalter FROM morphology "
                "WHERE chapter=? AND verse=? AND root_buckwalter IS NOT NULL "
                "AND root_buckwalter != ''", (c, v)).fetchall()
        except Exception:
            rows = []
        for r in rows:
            try:
                allowed.add(C.normalize_ar(BW.buckwalter_to_arabic(r[0])))
            except Exception:
                pass
    if want not in allowed:
        raise CompileError(
            f"root beat: {root_ar!r} is not a root of any verse in this "
            f"script (allowed roots come from the shown verses' morphology)"
        )

    display = spec.get("display") or " ".join(root_ar.replace("-", " ").split())
    return {
        "type": "root",
        "durationSec": 5,
        "rootArabic": display,
        "rootLabel": (spec.get("label") or "").strip(),
        "meaningTitle": (spec.get("meaning_title") or "Meaning").strip(),
        "meaning": (spec.get("meaning") or "").strip(),
        "narration": {"text": C.sanitize_for_tts(narration)},
    }


def _poetry_slide(conn, beat: dict, narration: str) -> dict:
    """A pre-Islamic bayt on its own slide. FAIL CLOSED: the bayt must exist
    in the poetry corpus (poetry_lines) — matched by letter-skeleton
    containment in either direction — so a writer can never put invented
    'poetry' on screen."""
    spec = beat.get("poetry") or {}
    bayt = (spec.get("arabic") or "").strip()
    if not bayt:
        raise CompileError("poetry beat missing poetry.arabic")
    want = C.normalize_ar(bayt.replace(" ", ""))
    if len(want) < 12:
        raise CompileError("poetry beat: bayt too short to verify against the corpus")

    found = False
    try:
        rows = conn.execute(
            "SELECT hemistich1, hemistich2, text_plain FROM poetry_lines"
        ).fetchall()
    except Exception:
        raise CompileError(
            "poetry beat: poetry_lines table unavailable in this database — "
            "cannot verify the bayt (fail closed)"
        )
    for r in rows:
        line = " ".join(x for x in (r[0], r[1], r[2]) if x)
        have = C.normalize_ar(line.replace(" ", ""))
        if want in have or (len(have) >= 12 and have in want):
            found = True
            break
    if not found:
        raise CompileError(
            "poetry beat: bayt not found in the poetry corpus — quote a line "
            "verbatim from the enrichment (never compose poetry)"
        )

    slide = {
        "type": "poetry",
        "durationSec": 6,
        "bayt": bayt,
        "narration": {"text": C.sanitize_for_tts(narration)},
    }
    if spec.get("english"):
        slide["english"] = str(spec["english"]).strip()
    if spec.get("poet"):
        slide["poet"] = str(spec["poet"]).strip()
    return slide


def _contrast_slide(conn, beat: dict, narration: str) -> tuple[dict, list[dict]]:
    """Two verses on screen at once. Both halves resolve through the SAME
    fail-closed resolver as verse-flow slides."""
    specs = beat.get("verses") or []
    if not (isinstance(specs, list) and len(specs) == 2):
        raise CompileError("contrast beat needs exactly two entries in verses[]")
    halves, intents = [], []
    for bv in specs:
        ref = (bv or {}).get("ref")
        if not ref:
            raise CompileError("contrast beat verse missing ref")
        r = _resolve_verse(conn, ref, bv)
        halves.append({
            "surah": r["surah"], "ayah": r["ayah"],
            "arabicText": r["arabic"], "translation": r["translation"],
            "highlightWordIndices": r["idxs"],
            **({"highlightTranslationText": r["phrase"]} if r["phrase"] else {}),
        })
        intents.append({
            "surah": r["surah"], "ayah": r["ayah"], "indices": r["idxs"],
            "skeletons": sorted({C.normalize_ar(f) for f in r["forms"]}),
            "forms": r["forms"], "phrase": r["phrase"],
            "english_omitted": r["english_omitted"],
        })
    slide = {
        "type": "verse-contrast",
        "durationSec": 8,
        "top": halves[0],
        "bottom": halves[1],
        "narration": {"text": C.sanitize_for_tts(narration)},
    }
    return slide, intents


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

    # Refs of every verse shown anywhere in the script — used by the root
    # beat's fail-closed "root must belong to a shown verse" check.
    script_refs = []
    for b in beats:
        if isinstance(b, dict):
            if isinstance(b.get("verse"), dict) and b["verse"].get("ref"):
                script_refs.append(b["verse"]["ref"])
            for bv in (b.get("verses") or []):
                if isinstance(bv, dict) and bv.get("ref"):
                    script_refs.append(bv.get("ref"))
    anchor_ref = script.get("anchor_ref")
    if anchor_ref:
        script_refs.append(anchor_ref)

    for beat in beats:
        if not isinstance(beat, dict):
            raise CompileError(f"malformed beat (not an object): {beat!r:.60}")
        narr = (beat.get("narration") or "").strip()
        bverse = beat.get("verse")
        if beat.get("kind") == "contrast" or beat.get("verses"):
            combined = (pending_prefix + " " + narr).strip() if pending_prefix else narr
            pending_prefix = ""
            slide, cintents = _contrast_slide(conn, beat, combined)
            slides.append(slide)
            # Both halves' intents ride on ONE slide; the match gate handles
            # verse-flow slides, so contrast correctness is compile-enforced
            # (same resolver). Store as a list for future gate extension.
            intent.append({"contrast": cintents})
        elif beat.get("kind") == "root" or beat.get("root"):
            combined = (pending_prefix + " " + narr).strip() if pending_prefix else narr
            pending_prefix = ""
            beat = dict(beat)
            beat["_script_refs"] = script_refs
            slides.append(_root_slide(conn, beat, combined))
            intent.append(None)
        elif beat.get("kind") == "poetry" or beat.get("poetry"):
            combined = (pending_prefix + " " + narr).strip() if pending_prefix else narr
            pending_prefix = ""
            slides.append(_poetry_slide(conn, beat, combined))
            intent.append(None)
        elif bverse:
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

    if not any(sl["type"] in ("verse-flow", "verse-contrast") for sl in slides):
        raise CompileError("script shows no Quranic verse — at least one verse or contrast beat is required")
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
