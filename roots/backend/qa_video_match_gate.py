"""Q&A video — Gate B: airtight script <-> video match.

The one the operator flagged as bug-prone. Layered so no single bug
class survives:

  Layer 1  deterministic Python assertions against the SHIPPED payload:
           - arabicText equals the freshly DB-derived display string
             (no hand-authored / stale text);
           - every highlight index is in range;
           - the token the renderer will light, by consonantal skeleton,
             equals the word the script intended (this is what catches
             the basmala-offset and orthographic-split buckets);
           - the English phrase is a real case-insensitive substring of
             the translation (else the pill silently vanishes);
           - translation equals the DB translation;
           - every cited reference exists.
  Layer 2  renderer self-report: run scripts/verify.mjs (which uses the
           SAME highlight.mjs resolver the React slide uses) and assert
           the renderer's painted tokens match intent, with no
           out-of-range indices and the English span found where asked.
  Layer 4  provenance snapshot: content hashes to re-assert later (at
           render and pre-upload) so a downstream DB edit can't silently
           drift the video from what was approved.

All checks FAIL CLOSED. `run` returns a structured report; callers gate
on report["ok"].
"""

from __future__ import annotations

import json
import os
import subprocess

import qa_video_common as C

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_RENDERER_DIR = os.path.normpath(os.path.join(_THIS_DIR, "..", "video-renderer"))
RENDERER_DIR = os.environ.get("REMOTION_RENDERER_DIR", _DEFAULT_RENDERER_DIR)
VERIFY_SCRIPT = os.path.join(RENDERER_DIR, "scripts", "verify.mjs")


# ---------------------------------------------------------------------------
#  Layer 1 — deterministic assertions
# ---------------------------------------------------------------------------


def static_checks(conn, payload: dict, intent: list, cited_refs: list[str] | None = None) -> list[str]:
    issues: list[str] = []
    slides = payload.get("slides") or []
    if len(intent) != len(slides):
        issues.append(f"intent length {len(intent)} != slides length {len(slides)}")

    for i, slide in enumerate(slides):
        if slide.get("type") != "verse-flow":
            continue
        vi = intent[i] if i < len(intent) else None
        c, v = slide.get("surah"), slide.get("ayah")
        tag = f"slide[{i}] {c}:{v}"

        if not C.verse_exists(conn, c, v):
            issues.append(f"{tag}: verse does not exist")
            continue

        vd = C.verse_data(conn, c, v)
        db_arabic = C.display_arabic(vd["arabic_raw"], c, v)
        if slide.get("arabicText") != db_arabic:
            issues.append(f"{tag}: arabicText does not match DB display text (hand-authored / stale)")
        db_tr = vd["translation"] or ""
        if (slide.get("translation") or "") != db_tr:
            issues.append(f"{tag}: translation does not match DB translation")

        tokens = C.verse_tokens(slide.get("arabicText") or "")
        # Renderer paints the UNION of highlightWordIndices + legacy singular.
        idxs = set()
        for k in slide.get("highlightWordIndices") or []:
            if isinstance(k, int):
                idxs.add(k)
        single = slide.get("highlightWordIndex")
        if isinstance(single, int) and single > 0:
            idxs.add(single)

        if not idxs:
            issues.append(f"{tag}: no highlight indices")
        intended_forms = (vi or {}).get("forms") or []
        for k in sorted(idxs):
            if not (1 <= k <= len(tokens)):
                issues.append(f"{tag}: highlight index {k} out of range 1..{len(tokens)}")
                continue
            tok = tokens[k - 1]
            if intended_forms and not any(C.token_matches_form(tok, f) for f in intended_forms):
                issues.append(
                    f"{tag}: index {k} lights {tok!r} (skeleton {C.normalize_ar(tok)!r}) "
                    f"but script intended one of {intended_forms}"
                )

        phrase = (slide.get("highlightTranslationText") or "").strip()
        if phrase and phrase.lower() not in db_tr.lower():
            issues.append(
                f"{tag}: highlightTranslationText {phrase!r} is not a substring of the "
                f"translation — the English pill will silently not render"
            )

    for ref in cited_refs or []:
        try:
            c, v = C.parse_ref(ref)
        except ValueError:
            issues.append(f"cited ref {ref!r} is malformed")
            continue
        if not C.verse_exists(conn, c, v):
            issues.append(f"cited ref {ref} does not exist")

    return issues


# ---------------------------------------------------------------------------
#  Layer 2 — renderer self-report (the renderer's own truth)
# ---------------------------------------------------------------------------


def renderer_report(payload: dict, tmp_dir: str | None = None) -> dict:
    """Invoke scripts/verify.mjs and return its parsed JSON. Raises on a
    missing node / verifier or malformed output (fail closed)."""
    import tempfile

    fd_dir = tmp_dir or tempfile.gettempdir()
    path = os.path.join(fd_dir, f"qa_verify_{C.sha(json.dumps(payload, sort_keys=True))}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    try:
        proc = subprocess.run(
            ["node", VERIFY_SCRIPT, "--payload", path],
            capture_output=True, text=True, timeout=60,
        )
    except FileNotFoundError as e:
        raise RuntimeError(f"node not available for renderer self-report: {e}")
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    out = (proc.stdout or "").strip().splitlines()
    if not out:
        raise RuntimeError(f"verify.mjs produced no output (stderr: {proc.stderr[:300]})")
    try:
        result = json.loads(out[-1])
    except json.JSONDecodeError as e:
        raise RuntimeError(f"verify.mjs output not JSON: {out[-1][:200]} ({e})")
    if not result.get("ok"):
        raise RuntimeError(f"verify.mjs error: {result.get('error')}")
    return result


def crosscheck(payload: dict, intent: list, report: dict) -> list[str]:
    """Diff the renderer's painted-token truth against the script intent."""
    issues: list[str] = []
    rep_by_index = {s.get("index"): s for s in report.get("slides") or []}
    for i, slide in enumerate(payload.get("slides") or []):
        if slide.get("type") != "verse-flow":
            continue
        vi = intent[i] if i < len(intent) else None
        rep = rep_by_index.get(i)
        tag = f"slide[{i}] {slide.get('surah')}:{slide.get('ayah')}"
        if not rep:
            issues.append(f"{tag}: missing from renderer self-report")
            continue
        if rep.get("outOfRangeIndices"):
            issues.append(f"{tag}: renderer reports out-of-range indices {rep['outOfRangeIndices']}")
        painted = rep.get("paintedTokens") or []
        intended_forms = (vi or {}).get("forms") or []
        if intended_forms:
            # Every lit token must be an intended word, and every intended
            # word must be lit (proclitic-tolerant, same matcher as compile).
            extra = [t for t in painted if not any(C.token_matches_form(t, f) for f in intended_forms)]
            missing = [f for f in intended_forms if not any(C.token_matches_form(t, f) for t in painted)]
            if extra:
                issues.append(f"{tag}: renderer would light unintended word(s) {extra}")
            if missing:
                issues.append(f"{tag}: renderer would NOT light intended word(s) {missing}")
        if rep.get("englishRequested") and not rep.get("englishFound"):
            issues.append(f"{tag}: renderer could not find the English phrase to highlight")
    return issues


# ---------------------------------------------------------------------------
#  Layer 4 — provenance snapshot
# ---------------------------------------------------------------------------


def snapshot(payload: dict) -> dict:
    snap = {"slides": []}
    for i, slide in enumerate(payload.get("slides") or []):
        if slide.get("type") != "verse-flow":
            continue
        snap["slides"].append({
            "index": i,
            "ref": f"{slide.get('surah')}:{slide.get('ayah')}",
            "arabic_sha": C.sha(slide.get("arabicText") or ""),
            "translation_sha": C.sha(slide.get("translation") or ""),
            "highlight": sorted(slide.get("highlightWordIndices") or []),
            "phrase": (slide.get("highlightTranslationText") or ""),
        })
    return snap


def assert_snapshot(conn, payload: dict, snap: dict) -> list[str]:
    """Re-assert a stored snapshot against the live DB + payload (Layer 4
    drift lock — run at render time and pre-upload)."""
    issues: list[str] = []
    cur = snapshot(payload)
    cur_by_idx = {s["index"]: s for s in cur["slides"]}
    for s in snap.get("slides") or []:
        c = cur_by_idx.get(s["index"])
        if not c:
            issues.append(f"snapshot slide[{s['index']}] {s.get('ref')} no longer present")
            continue
        for key in ("arabic_sha", "translation_sha", "highlight", "phrase"):
            if c.get(key) != s.get(key):
                issues.append(f"snapshot drift on slide[{s['index']}] {s.get('ref')}: {key} changed")
    return issues


# ---------------------------------------------------------------------------
#  Orchestration
# ---------------------------------------------------------------------------


def run(conn, payload: dict, intent: list, *, cited_refs: list[str] | None = None,
        use_renderer: bool = True) -> dict:
    """Full Gate B. Returns {ok, issues, layers, report, snapshot}."""
    layers: dict = {}
    issues: list[str] = []

    l1 = static_checks(conn, payload, intent, cited_refs)
    layers["static"] = {"ok": not l1, "issues": l1}
    issues += [f"[static] {x}" for x in l1]

    report = None
    if use_renderer:
        try:
            report = renderer_report(payload)
            l2 = crosscheck(payload, intent, report)
            layers["renderer"] = {"ok": not l2, "issues": l2}
            issues += [f"[renderer] {x}" for x in l2]
        except Exception as e:  # fail closed — a verifier that won't run is a fail
            layers["renderer"] = {"ok": False, "issues": [str(e)]}
            issues.append(f"[renderer] {e}")
    else:
        layers["renderer"] = {"ok": None, "issues": ["skipped (use_renderer=False)"]}

    snap = snapshot(payload)
    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "layers": layers,
        "report": report,
        "snapshot": snap,
    }
