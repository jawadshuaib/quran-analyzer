"""Q&A video — script compressor.

Turns a rated-5 Q&A row (700-990 char answer) into the punchy, structured
~130-word script the compiler/gate consume. Inherits qa_workflow_brief.md
verbatim (the teaching-voice + Quran-internal doctrine) and adds the
video-specific compression rules + 2 compressed exemplars.

The single most important instruction to the model: highlight_words_ar
must be EXACT tokens copied from the verse's displayed Arabic (we give it
the numbered tokens), and highlight_phrase_en must be a verbatim
substring of the English translation — otherwise Gate B rejects the
script (which is the point: the gate is the backstop, this just makes the
model's job easy enough to usually pass first try).

Import-safe: requests is lazy-imported; no app import. Model-agnostic —
Ollama by default (free, local), works with qwen3:14b.
"""

from __future__ import annotations

import json
import os

import qa_video_common as C

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_BRIEF_PATH = os.path.join(_THIS_DIR, "qa_workflow_brief.md")

_OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
_DEFAULT_MODEL = os.environ.get("QA_VIDEO_SCRIPT_MODEL", "qwen3:14b")


class ScriptGenError(Exception):
    pass


def _read_brief() -> str:
    try:
        with open(_BRIEF_PATH, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


_VIDEO_ADDENDUM = """
---

## VIDEO MODE — additional rules (this task)

You are compressing ONE stored Q&A into a PUNCHY 60-90 second YouTube
short script (~120-170 spoken words total). Same doctrine + voice as
above, now SPOKEN to a viewer who might scroll away.

BEAT STRUCTURE (output exactly these kinds, in order):
  hook  — pose the question on the anchor verse, name the concrete
          artifact (the word/refrain). DO NOT answer yet. No verse field.
          ~12-22 words. Must contain a question mark.
  set   — show the ANCHOR verse; highlight the pivot word. "Notice what
          it does NOT say…". ~22-38 words.
  turn  — ONE cross-reference verse that reframes it. Open with a spoken
          teaching beat like "Okay — here's where it gets interesting:".
          ~24-44 words. (Omit if there is no strong second verse.)
  land  — the quiet resolution, confidence proportioned ("the most we
          can fairly say…"). No verse field. ~20-36 words.

SPOKEN VOICE: speak WITH the viewer, never preach AT them. Use at most
ONE connective beat ("Notice…", "Okay, here's where it gets
interesting…"). Proportion confidence: flat assertion only for what the
text plainly states; "suggests"/"seems" for inference.

HARD RULES:
- AT MOST TWO verse beats total (one set + at most one turn).
- highlight_words_ar: copy the EXACT token string(s) from the numbered
  token list given for that verse — 1 to 3 contiguous tokens, INCLUDING
  any leading connective letter the token carries (وَ / فَ / بِ / الـ).
  Copy the token verbatim; do not strip its prefix. These are the Arabic
  words that will light up on screen; they MUST be the words your
  narration is talking about. Choose a CONTENT word — the verb or noun
  that carries the insight — NEVER a bare particle/preposition (فِى, مِن,
  عَلَى, إِنَّ…), and NEVER a word that appears more than once in the
  verse (an ambiguous highlight is rejected).
  Each array element is EXACTLY ONE token (no spaces inside it); to
  highlight a 2-3 word phrase, list each token as its own element.
- highlight_phrase_en: copy a phrase VERBATIM (exact characters) from
  that verse's English translation given below — do NOT paraphrase,
  reword, or shorten it, or the on-screen highlight silently fails.
- Use ONLY the anchor verse and the listed cross-reference verses. Never
  invent a reference.
- title: the intriguing question itself, ending in "?". theme: a short
  lowercase slug (e.g. "death-and-sleep").

OUTPUT STRICT JSON ONLY, this shape:
{"qa_id": <int>, "anchor_ref": "C:V", "title": "...?", "theme": "slug",
 "beats": [
   {"kind":"hook","narration":"..."},
   {"kind":"set","narration":"...","verse":{"ref":"C:V","highlight_phrase_en":"...","highlight_words_ar":["..."]}},
   {"kind":"turn","narration":"...","verse":{"ref":"C:V","highlight_phrase_en":"...","highlight_words_ar":["..."]}},
   {"kind":"land","narration":"..."}
 ]}

TEMPLATE — fill the <bracketed> slots with content about YOUR verse.
The bracketed text is an INSTRUCTION, never literal output. Do NOT carry
any wording from this template into your narration.
{"qa_id": <int>, "anchor_ref":"<C:V>","title":"<the intriguing question, ending in ?>","theme":"<lowercase-slug>",
 "beats":[
  {"kind":"hook","narration":"<12-22 words: name THIS verse's concrete artifact (a word/refrain) and pose the question. Do not answer. End with ?>"},
  {"kind":"set","narration":"<22-38 words about THIS verse: what it commits to or leaves open; you may open with 'Notice what it doesn't say…'>","verse":{"ref":"<anchor C:V>","highlight_phrase_en":"<verbatim substring of this verse's ENGLISH>","highlight_words_ar":["<exact Arabic token copied from this verse>"]}},
  {"kind":"turn","narration":"<24-44 words: the cross-reference that reframes it; you may open with 'Okay — here's where it gets interesting:'>","verse":{"ref":"<a listed cross-ref C:V>","highlight_phrase_en":"<verbatim substring of that verse's ENGLISH>","highlight_words_ar":["<exact Arabic token copied from that verse>"]}},
  {"kind":"land","narration":"<20-36 words: the quiet resolution, confidence proportioned (e.g. 'the most we can fairly say…')>"}
 ]}
"""


def build_context(conn, anchor_ref: str, cited_refs: list[str]) -> dict:
    """Numbered display tokens + translation for the anchor and each
    distinct cited cross-reference verse, so the model can copy exact
    surface forms."""
    refs, seen = [], set()
    for r in [anchor_ref] + list(cited_refs or []):
        try:
            c, v = C.parse_ref(r)
        except ValueError:
            continue
        key = f"{c}:{v}"
        if key != anchor_ref and key not in seen:
            seen.add(key)
        if key not in [x["ref"] for x in refs]:
            vd = C.verse_data(conn, c, v)
            if not vd:
                continue
            disp = C.display_arabic(vd["arabic_raw"], c, v)
            toks = C.verse_tokens(disp)
            refs.append({
                "ref": key,
                "is_anchor": key == anchor_ref,
                "tokens": [{"i": i + 1, "ar": t} for i, t in enumerate(toks)],
                "translation": vd["translation"],
            })
    return {"verses": refs}


def _format_context(ctx: dict) -> str:
    lines = []
    for v in ctx["verses"]:
        tag = "ANCHOR" if v["is_anchor"] else "cross-ref"
        toks = "  ".join(f"[{t['i']}]{t['ar']}" for t in v["tokens"])
        lines.append(f"{tag} {v['ref']}\n  TOKENS: {toks}\n  ENGLISH: {v['translation']}")
    return "\n\n".join(lines)


def _ollama_chat(system: str, user: str, model: str) -> str:
    import requests  # lazy
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "think": False,
        "format": "json",
        "options": {"temperature": 0.4},
    }
    resp = requests.post(_OLLAMA_URL, json=payload, timeout=240)
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def generate_script(conn, qa_row: dict, *, model: str | None = None,
                    repair_hint: str = "") -> dict:
    """Compress one Q&A row into a structured script dict. `qa_row` needs
    qa_id, anchor_ref, question, answer, cited_refs."""
    model = model or _DEFAULT_MODEL
    ctx = build_context(conn, qa_row["anchor_ref"], qa_row.get("cited_refs") or [])
    if not ctx["verses"]:
        raise ScriptGenError(f"no usable verses for {qa_row['anchor_ref']}")

    system = _read_brief() + _VIDEO_ADDENDUM
    user = (
        f"STORED Q&A (compress this faithfully — do not invent beyond it):\n"
        f"qa_id: {qa_row['qa_id']}\nanchor_ref: {qa_row['anchor_ref']}\n"
        f"QUESTION: {qa_row['question']}\n\nANSWER: {qa_row['answer']}\n\n"
        f"VERSES YOU MAY SHOW (copy highlight_words_ar EXACTLY from these tokens; "
        f"highlight_phrase_en must be a substring of the ENGLISH):\n\n{_format_context(ctx)}\n"
    )
    if repair_hint:
        user += f"\nPREVIOUS ATTEMPT FAILED VALIDATION. Fix exactly this and try again:\n{repair_hint}\n"

    raw = _ollama_chat(system, user, model)
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end < 0:
        raise ScriptGenError(f"no JSON in model reply: {raw[:200]}")
    try:
        script = json.loads(raw[start:end + 1])
    except json.JSONDecodeError as e:
        raise ScriptGenError(f"model JSON parse error: {e}; raw={raw[:200]}")

    script.setdefault("qa_id", qa_row["qa_id"])
    script.setdefault("anchor_ref", qa_row["anchor_ref"])
    _light_validate(script)
    return script


def _light_validate(script: dict) -> None:
    beats = script.get("beats") or []
    if not beats:
        raise ScriptGenError("script has no beats")
    if not all(isinstance(b, dict) for b in beats):
        raise ScriptGenError("malformed beat (not an object)")
    if not any(isinstance(b.get("verse"), dict) for b in beats):
        raise ScriptGenError("script has no verse beat")
    n_verse = sum(1 for b in beats if isinstance(b.get("verse"), dict))
    if n_verse > 2:
        raise ScriptGenError(f"{n_verse} verse beats (max 2)")
