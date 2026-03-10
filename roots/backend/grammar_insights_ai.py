"""Offline grammar-insights generation (Qur'an-only) for each verse.

Generates illuminating grammar insights that explain meaning effects often lost
in English translation. Uses only local Quran text, local translation, local
translation notes, and local morphology rows.
"""

import argparse
import json
import re

from app import _strip_bismillah, get_db
from translate_ai import call_model

DEFAULT_MODEL = "qwen3:14b"
DEFAULT_CONFIG = "grammar-insights-quran-only-v7-unified"
DEFAULT_PROMPT_VERSION = "v7-unified"

SYSTEM_PROMPT = """\
You are a Qur'an-only grammar insight engine.

Task:
- Produce concise, high-value grammatical insights for one verse.
- Prioritize insights that materially affect interpretation and can be lost in English.

Hard constraints:
1) Use only the evidence provided in the prompt.
2) Do NOT use tafsir, hadith, or external historical sources.
3) Do NOT invent morphology not present in evidence.
4) Output valid JSON only.
"""


MUNDANE_PHRASES = (
    "this is a noun",
    "this is a verb",
    "past tense verb",
    "present tense verb",
    "has a prefix",
    "has a suffix",
    "contains a pronoun",
    "grammatically correct",
    "means the same as",
)
CONTRAST_MARKERS = (
    "instead of",
    "rather than",
    "if it had",
    "if the verse had",
    "why not",
    "not merely",
    "not just",
    "could have used",
    "chooses",
    "choice of",
)
ALLOWED_EVIDENCE_TYPES = {"form_bw", "lemma_bw", "root_bw", "feature", "case", "voice", "mood", "verb_form", "state"}
ALLOWED_CATEGORIES = {
    "perspective_shift",
    "person_mixture",
    "royal_we_vs_i",
    "gender_nuance",
    "sound_communication",
    "time_perspective",
    "oath_structure",
    "exception_scope",
    "conditional_structure",
    "cognate_accusative",
    "demonstrative_distance",
    "plural_type",
    "educational",
    "other_grammar",
}
SOUND_ROOT_CUES = {"smE", "qwl", "ndy", "nDy", "wHy", "Swt"}
TIME_HASTE_ROOT_CUES = {"Ejl"}
TIME_EVENT_ROOT_CUES = {"qrb", "ywm", "sAE"}
PAYOFF_CUES = {
    "emphasis",
    "continuity",
    "directness",
    "generality",
    "specificity",
    "vividness",
    "agency",
    "stability",
    "sequence",
    "contrast",
    "immediate",
    "ongoing",
    "certainty",
    "direct",
}
GENERIC_PAYOFF_BANNED = {"beautiful", "eloquent", "powerful", "profound", "majestic"}
DEMONSTRATIVE_NEAR_LEMMAS = {"ha`*aA", "ha`*a`n", "hunaA", "ha`ka*aA"}
DEMONSTRATIVE_FAR_LEMMAS = {"*a`lik", ">uwla`^}ik", "tilokum", "*aA", "*a`nik"}
BW_TO_AR = {
    "'": "ء", "|": "آ", ">": "أ", "&": "ؤ", "<": "إ", "}": "ئ", "A": "ا", "b": "ب", "p": "ة",
    "t": "ت", "v": "ث", "j": "ج", "H": "ح", "x": "خ", "d": "د", "*": "ذ", "r": "ر", "z": "ز",
    "s": "س", "$": "ش", "S": "ص", "D": "ض", "T": "ط", "Z": "ظ", "E": "ع", "g": "غ", "f": "ف",
    "q": "ق", "k": "ك", "l": "ل", "m": "م", "n": "ن", "h": "ه", "w": "و", "Y": "ى", "y": "ي",
    "{": "ٱ", "a": "َ", "u": "ُ", "i": "ِ", "o": "ْ", "~": "ّ", "`": "ٰ", "F": "ً", "N": "ٌ", "K": "ٍ", "^": "ٔ",
}


def _verse_num(ref: str) -> tuple[int, int]:
    m = re.match(r"^\s*(\d+):(\d+)\s*$", ref or "")
    if not m:
        return (0, 0)
    return (int(m.group(1)), int(m.group(2)))


def _title_stem(title: str) -> str:
    toks = re.findall(r"[a-z]+", (title or "").lower())
    return " ".join(toks[:4]).strip()


def _text_skeleton(text: str) -> str:
    toks = re.findall(r"[a-z]+", (text or "").lower())
    return " ".join(toks[:12]).strip()


def _extract_counterfactual_text(insight: str) -> str | None:
    low = insight or ""
    m = re.search(r"([^.!?]*\b(rather than|instead of|if it had|if the verse had|could have used)\b[^.!?]*[.!?]?)", low, re.IGNORECASE)
    if not m:
        return None
    txt = m.group(1).strip()
    return txt[:320] if txt else None


def _counterfactual_allowed(kind: str, category: str, insight: str, valid_ev: list[dict], signals: dict) -> tuple[bool, str]:
    if kind != "investigative":
        return (False, "non_investigative")

    low = (insight or "").lower()
    if any(w in low for w in GENERIC_PAYOFF_BANNED):
        return (False, "generic_beauty_language")
    if not any(c in low for c in PAYOFF_CUES):
        return (False, "no_concrete_payoff")

    feature_vals = {str(e.get("value", "")).upper() for e in valid_ev if str(e.get("type", "")) == "feature"}
    voice_vals = {str(e.get("value", "")).upper() for e in valid_ev if str(e.get("type", "")) == "voice"}
    state_vals = {str(e.get("value", "")).upper() for e in valid_ev if str(e.get("type", "")) == "state"}

    has_binary = False
    # Explicit binary contrasts detectable from evidence.
    if ("PERF" in feature_vals and ("IMPF" in feature_vals or "IMPV" in feature_vals)):
        has_binary = True
    if ("1S" in feature_vals and "1P" in feature_vals):
        has_binary = True
    if ("ACTIVE" in voice_vals and ("PASSIVE" in voice_vals or "PASS" in voice_vals)):
        has_binary = True
    if ("DEF" in state_vals and ("INDEF" in state_vals or "INDEFINITE" in state_vals)):
        has_binary = True
    # Category-level binary cues using signal detector.
    if category in {"perspective_shift", "person_mixture"} and (
        signals.get("perspective_shift_window") or signals.get("person_mixture_target")
    ):
        has_binary = True
    if category == "royal_we_vs_i" and (signals.get("royal_we_target") or signals.get("first_i_target")):
        has_binary = True
    if category == "time_perspective" and signals.get("time_perspective_target"):
        has_binary = True

    if not has_binary:
        return (False, "no_detectable_binary_contrast")
    if "could have used" in low and not has_binary:
        return (False, "phantom_counterfactual")
    return (True, "ok")


def _derive_educational_note(category: str, valid_ev: list[dict], insight: str) -> str:
    """Build a short lay-friendly note grounded in available evidence."""
    feature_vals = {str(e.get("value", "")).upper() for e in valid_ev if str(e.get("type", "")) == "feature"}
    case_vals = {str(e.get("value", "")).upper() for e in valid_ev if str(e.get("type", "")) == "case"}
    voice_vals = {str(e.get("value", "")).upper() for e in valid_ev if str(e.get("type", "")) == "voice"}

    if category == "time_perspective":
        if "PERF" in feature_vals and ("IMPF" in feature_vals or "IMPV" in feature_vals):
            return (
                "Why this matters: Arabic can use a completed-looking form (perfective: like 'it has happened') "
                "to signal certainty, while nearby open-ended forms (imperfective: like 'is happening/will keep happening') "
                "preserve ongoing relevance."
            )
        if "PERF" in feature_vals:
            return (
                "Why this matters: A perfective form presents an action as settled/completed "
                "(roughly like 'did/has done'), which can intensify certainty in context."
            )
    if category in {"royal_we_vs_i", "perspective_shift"}:
        return (
            "Why this matters: Person shifts (I/we/you/they) change viewpoint and force. "
            "A quick shift can redirect who is being addressed without changing the core message."
        )
    if category == "sound_communication":
        return (
            "Why this matters: Speech/hearing verbs foreground communication by sound, "
            "not just events; this can make warning, calling, or proclamation central."
        )
    if category == "gender_nuance":
        return (
            "Why this matters: Gender marking in Arabic often helps track who is being referred to, "
            "where English may flatten distinctions."
        )
    if {"ACC", "GEN", "NOM"} & case_vals:
        return (
            "Why this matters: Case endings mark role in the sentence. "
            "Accusative often marks direct focus/object, genitive marks attachment ('of'), and nominative marks the subject/topic."
        )
    if voice_vals:
        return (
            "Why this matters: Voice changes focus: active highlights the doer, "
            "while passive highlights what happened."
        )
    if "IMPF" in feature_vals or "IMPV" in feature_vals:
        return (
            "Why this matters: Imperfective/imperfective-like forms are open-ended "
            "(often like 'is doing/keeps doing'), unlike a one-off completed event."
        )
    if "PERF" in feature_vals:
        return (
            "Why this matters: Perfective forms present action as complete "
            "(often like 'did/has done'), which can add decisiveness."
        )

    low = (insight or "").lower()
    if "case" in low:
        return (
            "Why this matters: Arabic case marking encodes sentence role directly, "
            "which English usually conveys through word order."
        )
    return (
        "Why this matters: This grammatical choice narrows interpretation in Arabic, "
        "beyond what a plain English rendering usually shows."
    )


def _bw_to_ar(text: str) -> str:
    return "".join(BW_TO_AR.get(ch, ch) for ch in (text or ""))


def _ev_lookup(ev: list[dict], etype: str) -> list[str]:
    out = []
    for x in ev:
        if not isinstance(x, dict):
            continue
        if str(x.get("type", "")).strip() != etype:
            continue
        val = str(x.get("value", "")).strip()
        if val:
            out.append(val)
    return out


def _should_add_example(payoff_text: str) -> bool:
    low = (payoff_text or "").lower()
    if "for example" in low or "e.g." in low:
        return False
    generic_markers = (
        "changes how the statement is understood",
        "beyond a flat english rendering",
        "tightens interpretation",
        "can miss",
    )
    if any(m in low for m in generic_markers):
        return True
    return len((payoff_text or "").strip()) < 120


def _payoff_example(category: str, insight: str, mev: list[dict]) -> str:
    """Short concrete examples for non-experts to anchor 'why this matters'."""
    cat = (category or "").strip()
    low = (insight or "").lower()
    forms = _ev_lookup(mev, "form_bw")
    roots = _ev_lookup(mev, "root_bw")
    feats = {x.upper() for x in _ev_lookup(mev, "feature")}
    form_ar = _bw_to_ar(forms[0]) if forms else ""
    root_ar = " ".join(list(_bw_to_ar(roots[0]))) if roots else ""

    # Evidence-driven examples first (works even when category is generic "educational")
    if "IMPV" in feats:
        if form_ar:
            return f"For example: command form {form_ar} addresses listeners directly, unlike a descriptive form like 'they do ...'."
        return "For example: an imperative form addresses listeners directly, unlike plain narration."
    if "PERF" in feats and ("IMPF" in feats or "IMPV" in feats):
        return "For example: 'has happened' can signal certainty, while an open-ended form keeps action ongoing."
    if "PERF" in feats:
        return "For example: 'did/has done' presents an action as settled more than 'does/is doing'."
    if "IMPF" in feats:
        return "For example: 'is doing/keeps doing' keeps the action open-ended instead of closed."

    if cat == "time_perspective":
        if form_ar:
            return f"For example: using {form_ar} ('has come') frames certainty more strongly than a merely ongoing form."
        return "For example: 'has come' presents certainty more strongly than 'is coming'."
    if cat in {"person_mixture", "perspective_shift"}:
        if form_ar:
            return f"For example: a direct-address form like {form_ar} can shift tone from description to confrontation."
        return "For example: shifting from 'they' to 'you' turns description into direct address."
    if cat == "royal_we_vs_i":
        return "For example: 'We sent down' and 'I sent down' both point to agency, but with different register."
    if cat == "conditional_structure":
        return "For example: 'if/when X, then Y' frames outcomes as conditional rather than flat statements."
    if cat == "exception_scope":
        return "For example: 'none ... except ...' narrows the statement by explicit exclusion."
    if cat == "demonstrative_distance":
        return "For example: 'this' (near) and 'that' (far) can mark discourse distance."
    if cat == "plural_type":
        return "For example: different plural patterns can signal category/style, not only number."
    if cat == "cognate_accusative":
        if root_ar:
            return f"For example: verb+noun sharing root {root_ar} can intensify the same action."
        return "For example: using a verb with its own verbal noun can intensify the action."
    if cat == "oath_structure":
        return "For example: an oath frame strengthens assertion compared with plain narration."
    if cat == "sound_communication":
        if root_ar:
            return f"For example: root {root_ar} foregrounds hearing/speech as the channel of meaning."
        return "For example: choosing 'call/hear' language foregrounds communication-by-sound."
    if "perfective" in low:
        return "For example: 'did/has done' sounds more settled than 'does/is doing'."
    if "imperfective" in low:
        return "For example: 'is doing/keeps doing' keeps the action open-ended."
    return "For example: a small grammar shift can change focus from state to action."


def parse_verse_spec(spec: str) -> list[tuple[int, int]]:
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(\d+):(\d+)-(\d+)$", part)
        if m:
            s, a0, a1 = int(m.group(1)), int(m.group(2)), int(m.group(3))
            lo, hi = min(a0, a1), max(a0, a1)
            out.extend((s, a) for a in range(lo, hi + 1))
            continue
        m2 = re.match(r"^(\d+):(\d+)$", part)
        if m2:
            out.append((int(m2.group(1)), int(m2.group(2))))
            continue
        raise ValueError(f"Bad verse spec segment: {part}")
    # de-dup preserve order
    seen = set()
    dedup = []
    for x in out:
        if x in seen:
            continue
        seen.add(x)
        dedup.append(x)
    return dedup


def get_or_create_config(conn, config_name: str, model_name: str, prompt_version: str) -> int:
    row = conn.execute(
        "SELECT id FROM grammar_insight_configs WHERE config_name = ?",
        (config_name,),
    ).fetchone()
    if row:
        return row["id"]
    conn.execute(
        "INSERT INTO grammar_insight_configs "
        "(config_name, model_name, prompt_version, methodology_notes) "
        "VALUES (?, ?, ?, ?)",
        (
            config_name,
            model_name,
            prompt_version,
            "Verse-level grammar insights focused on non-mundane meaning effects.",
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id FROM grammar_insight_configs WHERE config_name = ?",
        (config_name,),
    ).fetchone()
    return row["id"]


def _best_translation_and_notes(conn, surah: int, ayah: int) -> tuple[str, str]:
    row = conn.execute(
        "SELECT translation_text, departure_notes "
        "FROM ai_translations WHERE chapter = ? AND verse = ? "
        "ORDER BY created_at DESC LIMIT 1",
        (surah, ayah),
    ).fetchone()
    if row:
        return (row["translation_text"] or "", row["departure_notes"] or "")
    t = conn.execute(
        "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
        (surah, ayah),
    ).fetchone()
    return (t["text_en"] if t else "", "")


def _window_signals(conn, surah: int, ayah: int, radius: int = 2) -> tuple[list[dict], dict]:
    lo = max(1, ayah - radius)
    hi = ayah + radius
    rows = conn.execute(
        "SELECT chapter, verse, text_uthmani FROM verses WHERE chapter = ? AND verse BETWEEN ? AND ? ORDER BY verse",
        (surah, lo, hi),
    ).fetchall()
    refs = [f"{r['chapter']}:{r['verse']}" for r in rows]

    mrows = conn.execute(
        "SELECT chapter, verse, form_buckwalter, lemma_buckwalter, root_buckwalter, pos, tag, features_raw, gender, person, number "
        "FROM morphology WHERE chapter = ? AND verse BETWEEN ? AND ?",
        (surah, lo, hi),
    ).fetchall()
    by_ref: dict[str, dict] = {}
    target_ref = f"{surah}:{ayah}"
    for ref in refs:
        by_ref[ref] = {
            "persons": set(),
            "genders": set(),
            "roots": set(),
            "features": set(),
        }

    target_rows: list[dict] = []
    for r in mrows:
        ref = f"{r['chapter']}:{r['verse']}"
        slot = by_ref.get(ref)
        if not slot:
            continue
        if ref == target_ref:
            target_rows.append(dict(r))
        rbw = (r["root_buckwalter"] or "").strip()
        if rbw:
            slot["roots"].add(rbw)
        if r["person"] is not None:
            slot["persons"].add(str(r["person"]).strip())
        g = (r["gender"] or "").strip()
        if g:
            slot["genders"].add(g.upper())
        feats = (r["features_raw"] or "").split("|")
        for f in feats:
            f = f.strip()
            if f:
                slot["features"].add(f.upper())

    target = by_ref.get(target_ref, {"persons": set(), "genders": set(), "roots": set(), "features": set()})

    window_person_sets = [tuple(sorted(v["persons"])) for v in by_ref.values() if v["persons"]]
    perspective_shift = len(set(window_person_sets)) >= 2

    royal_we = any(("1P" in f or f.endswith(":1P")) for f in target["features"])
    first_i = any(("1S" in f or f.endswith(":1S")) for f in target["features"])
    second_person = any(re.search(r"(^|[:|])2(?:S|P|MS|MP|FS|FP)?($|[:|])", f) for f in target["features"])
    target_gender_nuance = ("F" in target["genders"] and "M" in target["genders"]) or len(target["genders"]) >= 2
    window_roots = set().union(*(v["roots"] for v in by_ref.values()))
    window_features = set().union(*(v["features"] for v in by_ref.values()))
    sound_cues_target = sorted(target["roots"] & SOUND_ROOT_CUES)
    sound_cues_window = sorted(window_roots & SOUND_ROOT_CUES)
    target_feats = target["features"]
    has_perf = any("PERF" in f for f in target_feats)
    has_impf = any("IMPF" in f for f in target_feats) or any("IMPV" in f for f in target_feats)
    has_haste_cue = bool(window_roots & TIME_HASTE_ROOT_CUES)
    has_time_event_cue = bool(window_roots & TIME_EVENT_ROOT_CUES)
    has_open_ended_time_form = any(("IMPF" in f or "IMPV" in f) for f in window_features)
    time_perspective_target = has_perf and (has_haste_cue or (has_time_event_cue and has_open_ended_time_form))

    conditional_particles = []
    exception_particles = []
    oath_markers = []
    demo_near = []
    demo_far = []
    verb_roots = set()
    noun_roots_acc = set()
    plural_types = set()
    for r in target_rows:
        form_bw = str(r.get("form_buckwalter") or "").strip()
        lemma_bw = str(r.get("lemma_buckwalter") or "").strip()
        root_bw = str(r.get("root_buckwalter") or "").strip()
        pos = str(r.get("pos") or "")
        tag = str(r.get("tag") or "").upper()
        feats = str(r.get("features_raw") or "").upper()

        if pos == "Conditional" or "COND" in tag:
            conditional_particles.append(form_bw or lemma_bw)
        if pos in {"Exceptive Particle", "Restriction Particle"} or "EXP" in tag or lemma_bw in {"<il~aA", "gayor", "l~am~aA"}:
            exception_particles.append(form_bw or lemma_bw)
        if root_bw == "qsm" or lemma_bw in {"qasam", "qasamo", ">aqosamu"}:
            oath_markers.append(form_bw or lemma_bw)

        if pos == "Demonstrative":
            if lemma_bw in DEMONSTRATIVE_NEAR_LEMMAS:
                demo_near.append(form_bw or lemma_bw)
            if lemma_bw in DEMONSTRATIVE_FAR_LEMMAS:
                demo_far.append(form_bw or lemma_bw)

        if pos == "Verb" and root_bw:
            verb_roots.add(root_bw)
        if root_bw and ("|ACC" in feats or feats.endswith("ACC")) and pos in {"Noun", "Verbal Noun"}:
            noun_roots_acc.add(root_bw)

        if pos in {"Noun", "Adjective"} and ("|MP" in feats or "|FP" in feats):
            if form_bw.endswith("wna") or form_bw.endswith("yna"):
                plural_types.add("sound_masculine")
            elif form_bw.endswith("At") or form_bw.endswith("aAt"):
                plural_types.add("sound_feminine")
            else:
                plural_types.add("broken_plural")

    window = []
    for r in rows:
        ref = f"{r['chapter']}:{r['verse']}"
        tr, _ = _best_translation_and_notes(conn, surah, r["verse"])
        window.append({
            "ref": ref,
            "arabic": _strip_bismillah(r["text_uthmani"], surah, r["verse"]),
            "translation": tr,
        })

    signals = {
        "perspective_shift_window": perspective_shift,
        "royal_we_target": royal_we,
        "first_i_target": first_i,
        "second_person_target": second_person,
        "person_mixture_target": bool(second_person and (royal_we or first_i)),
        "target_gender_nuance": target_gender_nuance,
        "sound_cues_target": sound_cues_target,
        "sound_cues_window": sound_cues_window,
        "time_perspective_target": time_perspective_target,
        "target_has_perf": has_perf,
        "target_has_impf": has_impf,
        "window_haste_cue": has_haste_cue,
        "window_time_event_cue": has_time_event_cue,
        "conditional_present": bool(conditional_particles),
        "conditional_particles": conditional_particles[:4],
        "exception_present": bool(exception_particles),
        "exception_particles": exception_particles[:4],
        "oath_present": bool(oath_markers),
        "oath_markers": oath_markers[:4],
        "demonstrative_near_present": bool(demo_near),
        "demonstrative_far_present": bool(demo_far),
        "demonstrative_near": demo_near[:4],
        "demonstrative_far": demo_far[:4],
        "cognate_accusative_present": bool(verb_roots & noun_roots_acc),
        "cognate_accusative_roots": sorted(list(verb_roots & noun_roots_acc))[:4],
        "plural_type_present": bool(plural_types),
        "plural_types": sorted(list(plural_types)),
    }
    return window, signals


def _extract_json(raw: str) -> dict:
    def _cleanup_json_like(s: str) -> str:
        # Normalize common model JSON issues.
        s2 = (s or "").replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
        # Remove trailing commas before object/array close.
        s2 = re.sub(r",\s*([}\]])", r"\1", s2)
        return s2

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    try:
        return json.loads(_cleanup_json_like(raw))
    except json.JSONDecodeError:
        pass
    i = raw.find("{")
    j = raw.rfind("}")
    if i == -1 or j == -1 or j <= i:
        raise ValueError("No JSON object found")
    core = raw[i : j + 1]
    try:
        return json.loads(core)
    except json.JSONDecodeError:
        pass
    return json.loads(_cleanup_json_like(core))


def _extract_refs(text: str) -> set[str]:
    out = set()
    for m in re.finditer(r"\b(\d{1,3}):(\d{1,3})\b", text or ""):
        out.add(f"{int(m.group(1))}:{int(m.group(2))}")
    return out


def _norm_ref(ref: str) -> str | None:
    if not isinstance(ref, str):
        return None
    m = re.match(r"^\s*(\d+):(\d+)\s*$", ref)
    if not m:
        return None
    return f"{int(m.group(1))}:{int(m.group(2))}"


def _is_mundane(title: str, insight: str) -> bool:
    t = f"{title} {insight}".strip().lower()
    if len(insight.strip()) < 70:
        return True
    return any(p in t for p in MUNDANE_PHRASES)


def _tokenize(s: str) -> set[str]:
    return {t for t in re.findall(r"[a-zA-Z]{4,}", (s or "").lower())}


def _jaccard(a: str, b: str) -> float:
    ta = _tokenize(a)
    tb = _tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1, len(ta | tb))


def _is_redundant(text: str, translation: str, notes: str) -> bool:
    sim_tr = _jaccard(text, translation)
    sim_notes = _jaccard(text, notes)
    return sim_tr >= 0.42 or sim_notes >= 0.33


def _is_detective_style(title: str, insight: str) -> bool:
    low = f"{title} {insight}".lower()
    return any(m in low for m in CONTRAST_MARKERS)


def _extract_arabic_chunks(text: str) -> list[str]:
    return re.findall(r"[\u0621-\u064A]{2,}", text or "")


def _unknown_arabic_count(text: str, known_arabic: set[str]) -> int:
    count = 0
    for tok in _extract_arabic_chunks(text):
        if tok not in known_arabic:
            count += 1
    return count


def _normalize_case(v: str) -> str:
    return (v or "").strip().upper()


def _build_morph_index(morphology: list[dict]) -> dict:
    idx = {
        "form_bw": set(),
        "lemma_bw": set(),
        "root_bw": set(),
        "feature": set(),
        "feature_token": set(),
        "case": set(),
        "voice": set(),
        "mood": set(),
        "verb_form": set(),
        "state": set(),
        "known_arabic": set(),
    }
    for m in morphology:
        if m.get("form_bw"):
            idx["form_bw"].add(m["form_bw"])
        if m.get("lemma_bw"):
            idx["lemma_bw"].add(m["lemma_bw"])
        if m.get("root_bw"):
            idx["root_bw"].add(m["root_bw"])
        if m.get("features_raw"):
            idx["feature"].add(m["features_raw"])
            for tok in str(m["features_raw"]).split("|"):
                tok = tok.strip()
                if tok:
                    idx["feature_token"].add(tok.upper())
        if m.get("case"):
            idx["case"].add(_normalize_case(m["case"]))
        if m.get("voice"):
            idx["voice"].add(_normalize_case(m["voice"]))
        if m.get("mood"):
            idx["mood"].add(_normalize_case(m["mood"]))
        if m.get("verb_form"):
            idx["verb_form"].add(_normalize_case(m["verb_form"]))
        if m.get("state"):
            idx["state"].add(_normalize_case(m["state"]))
        if m.get("form_arabic"):
            idx["known_arabic"].add(m["form_arabic"])
        if m.get("lemma_arabic"):
            idx["known_arabic"].add(m["lemma_arabic"])
        if m.get("root_arabic"):
            idx["known_arabic"].add(m["root_arabic"].replace(" ", ""))
    return idx


def _has_ev(ev: list[dict], et: str, val: str) -> bool:
    target = _normalize_case(val)
    for item in ev:
        if not isinstance(item, dict):
            continue
        if item.get("type") != et:
            continue
        if _normalize_case(str(item.get("value", ""))) == target:
            return True
    return False


def _claim_evidence_consistent(insight: str, valid_ev: list[dict]) -> bool:
    low = (insight or "").lower()
    if "accusative" in low and not _has_ev(valid_ev, "case", "ACC"):
        return False
    if "genitive" in low and not _has_ev(valid_ev, "case", "GEN"):
        return False
    if "nominative" in low and not _has_ev(valid_ev, "case", "NOM"):
        return False
    if "imperfective" in low and not _has_ev(valid_ev, "feature", "IMPF"):
        return False
    if "perfective" in low and not _has_ev(valid_ev, "feature", "PERF"):
        return False
    if "passive" in low and not (_has_ev(valid_ev, "voice", "PASSIVE") or _has_ev(valid_ev, "voice", "PASS")):
        return False
    if "active" in low and not _has_ev(valid_ev, "voice", "ACTIVE"):
        return False
    if ("royal" in low or "plural" in low) and not _has_ev(valid_ev, "feature", "1P"):
        return False
    return True


def _deterministic_time_perspective_fallback(evidence: dict, target_ref: str) -> dict | None:
    signals = evidence.get("investigative_signals", {}) if isinstance(evidence.get("investigative_signals"), dict) else {}
    if not signals.get("time_perspective_target"):
        return None
    morph = evidence.get("morphology", []) if isinstance(evidence.get("morphology"), list) else []
    if not morph:
        return None

    perf_row = next((m for m in morph if "PERF" in str(m.get("features_raw", "")).upper()), None)
    impf_row = next((m for m in morph if ("IMPF" in str(m.get("features_raw", "")).upper() or "IMPV" in str(m.get("features_raw", "")).upper())), None)
    haste_row = next((m for m in morph if str(m.get("root_bw", "")).strip() in TIME_HASTE_ROOT_CUES), None)
    if not perf_row:
        return None

    ev = []
    if perf_row.get("form_bw"):
        ev.append({"type": "form_bw", "value": str(perf_row["form_bw"])})
    if perf_row.get("root_bw"):
        ev.append({"type": "root_bw", "value": str(perf_row["root_bw"])})
    ev.append({"type": "feature", "value": "PERF"})
    if impf_row:
        ev.append({"type": "feature", "value": "IMPF" if "IMPF" in str(impf_row.get("features_raw", "")).upper() else "IMPV"})
    if haste_row and haste_row.get("root_bw"):
        ev.append({"type": "root_bw", "value": str(haste_row["root_bw"])})

    dedup = []
    seen = set()
    for item in ev:
        k = (item["type"], item["value"])
        if k in seen:
            continue
        seen.add(k)
        dedup.append(item)
    if len(dedup) < 2:
        return None

    perf_form = str(perf_row.get("form_bw") or "the perfective verb")
    perf_root = str(perf_row.get("root_bw") or "")
    cue = "a haste-related cue in the same verse" if haste_row else "a near-term cue in the same passage"
    insight = (
        f"The verse frames the event with a perfective form ({perf_form}"
        + (f", root {perf_root}" if perf_root else "")
        + f"), rather than only an open-ended imperfective framing, while pairing it with {cue}. "
          "This combination marks certainty and imminence together: grammatically past-like wording used for an event treated as decisively forthcoming."
    )
    return {
        "title": "Past-Like Form For Imminent Event",
        "source": "fallback",
        "fallback_tier": 3,
        "template_id": "tp_perf_impf",
        "category": "time_perspective",
        "confidence": 0.9,
        "insight": insight,
        "refs": [target_ref],
        "morph_evidence": dedup[:4],
    }


def _first_with_feature(morph: list[dict], token: str) -> dict | None:
    tok = token.upper()
    for m in morph:
        feats = str(m.get("features_raw", "")).upper()
        if tok in feats:
            return m
    return None


def _first_with_person(morph: list[dict], person_prefix: str) -> dict | None:
    """Find first row whose feature tokens include person-marking for prefix 1/2/3, 1S/1P, etc."""
    pp = (person_prefix or "").upper()
    if not pp:
        return None
    for m in morph:
        feats = str(m.get("features_raw", "")).upper()
        tokens = [t.strip() for t in feats.split("|") if t.strip()]
        for tok in tokens:
            t = tok[5:] if tok.startswith("PRON:") else tok
            # Person tokens are like 1S, 1P, 2MS, 2MP, 3FS, etc.
            if re.fullmatch(r"[123](?:S|P|MS|MP|FS|FP)?", t) and t.startswith(pp):
                return m
    return None


def _variant_phrase(target_ref: str, template_id: str, options: list[str]) -> str:
    if not options:
        return ""
    s, a = _verse_num(target_ref)
    idx = (s * 37 + a * 17 + sum(ord(c) for c in template_id)) % len(options)
    return options[idx]


def _deterministic_educational_fallbacks(evidence: dict, target_ref: str) -> list[dict]:
    out: list[dict] = []
    morph = evidence.get("morphology", []) if isinstance(evidence.get("morphology"), list) else []
    signals = evidence.get("investigative_signals", {}) if isinstance(evidence.get("investigative_signals"), dict) else {}
    if not morph:
        return out

    # Tier 1: compact educational cues.
    for m in morph:
        feats = str(m.get("features_raw", "")).upper()
        form = str(m.get("form_bw", "")).strip()
        root = str(m.get("root_bw", "")).strip()
        if "IMPV" in feats and form:
            phr = _variant_phrase(target_ref, "ed_imperative", [
                "The wording uses a command form rather than plain narration, which turns this clause into direct address.",
                "This is an imperative form, so the verse speaks as instruction rather than description.",
                "A command-form verb appears here, moving the line from statement to direct directive.",
            ])
            out.append({
                "title": "Command Form Sets Direct Address",
                "source": "fallback",
                "fallback_tier": 1,
                "template_id": "ed_imperative",
                "kind": "educational",
                "category": "educational",
                "confidence": 0.82,
                "insight": phr,
                "refs": [target_ref],
                "morph_evidence": [{"type": "form_bw", "value": form}, {"type": "feature", "value": "IMPV"}] + ([{"type": "root_bw", "value": root}] if root else []),
            })
            break

    for m in morph:
        feats = str(m.get("features_raw", "")).upper()
        form = str(m.get("form_bw", "")).strip()
        if "PERF" in feats and form:
            phr = _variant_phrase(target_ref, "ed_perf", [
                "A completed-form verb appears here, presenting the action as established rather than merely unfolding.",
                "The verb is in a completed form, which frames the event as settled in expression.",
                "This line uses a completed verbal form, giving the statement a settled, established force.",
            ])
            out.append({
                "title": "Completed Form Framing",
                "source": "fallback",
                "fallback_tier": 1,
                "template_id": "ed_perf",
                "kind": "educational",
                "category": "educational",
                "confidence": 0.81,
                "insight": phr,
                "refs": [target_ref],
                "morph_evidence": [{"type": "form_bw", "value": form}, {"type": "feature", "value": "PERF"}],
            })
            break

    if signals.get("conditional_present"):
        parts = ", ".join(signals.get("conditional_particles", [])[:2])
        out.append({
            "title": "Conditional Particle Sets Scenario Logic",
            "source": "fallback",
            "fallback_tier": 1,
            "template_id": "ed_conditional_structure",
            "kind": "educational",
            "category": "conditional_structure",
            "confidence": 0.82,
            "insight": (
                f"A conditional particle ({parts}) appears here, which frames the clause in if/when logic rather than flat assertion."
            ),
            "refs": [target_ref],
            "morph_evidence": [{"type": "feature", "value": "COND"}],
        })

    if signals.get("exception_present"):
        parts = ", ".join(signals.get("exception_particles", [])[:2])
        out.append({
            "title": "Exception Particle Narrows Scope",
            "source": "fallback",
            "fallback_tier": 1,
            "template_id": "ed_exception_scope",
            "kind": "educational",
            "category": "exception_scope",
            "confidence": 0.82,
            "insight": (
                f"An exception marker ({parts}) appears, so the statement is scoped with an explicit exclusion rather than left unrestricted."
            ),
            "refs": [target_ref],
            "morph_evidence": [{"type": "lemma_bw", "value": "<il~aA"}],
        })

    if signals.get("demonstrative_near_present") or signals.get("demonstrative_far_present"):
        near = ", ".join(signals.get("demonstrative_near", [])[:1])
        far = ", ".join(signals.get("demonstrative_far", [])[:1])
        if near and far:
            phr = f"The verse uses near ({near}) and far ({far}) demonstratives, rather than one distance only, which can mark discourse distance and focus."
        elif near:
            phr = f"A near demonstrative ({near}) appears, signaling immediacy/proximity in reference."
        else:
            phr = f"A far demonstrative ({far}) appears, signaling distance in reference."
        out.append({
            "title": "Demonstrative Distance Shapes Reference",
            "source": "fallback",
            "fallback_tier": 2,
            "template_id": "ed_demonstrative_distance",
            "kind": "educational",
            "category": "demonstrative_distance",
            "confidence": 0.8,
            "insight": phr,
            "refs": [target_ref],
            "morph_evidence": [{"type": "feature", "value": "DEM"}],
        })

    if signals.get("plural_type_present"):
        ptypes = ", ".join(signals.get("plural_types", [])[:2])
        out.append({
            "title": "Plural Form Type Carries Nuance",
            "source": "fallback",
            "fallback_tier": 2,
            "template_id": "ed_plural_type",
            "kind": "educational",
            "category": "plural_type",
            "confidence": 0.8,
            "insight": (
                f"The verse contains plural morphology ({ptypes}), and plural pattern choice can add nuance beyond simple number marking."
            ),
            "refs": [target_ref],
            "morph_evidence": [{"type": "feature", "value": "MP"}],
        })

    if signals.get("cognate_accusative_present"):
        roots = ", ".join(signals.get("cognate_accusative_roots", [])[:2])
        out.append({
            "title": "Possible Cognate-Accusative Intensification",
            "source": "fallback",
            "fallback_tier": 3,
            "template_id": "ed_cognate_accusative",
            "kind": "investigative",
            "category": "cognate_accusative",
            "confidence": 0.8,
            "insight": (
                f"A verb and accusative noun share root ({roots}) in this verse, rather than using unrelated wording, which can intensify or specify the verbal action."
            ),
            "refs": [target_ref],
            "morph_evidence": [{"type": "feature", "value": "ACC"}],
        })

    if signals.get("oath_present"):
        markers = ", ".join(signals.get("oath_markers", [])[:2])
        out.append({
            "title": "Oath Marker Introduces Strong Assertion Frame",
            "source": "fallback",
            "fallback_tier": 3,
            "template_id": "ed_oath_structure",
            "kind": "investigative",
            "category": "oath_structure",
            "confidence": 0.79,
            "insight": (
                f"An oath-related marker ({markers}) appears, rather than a plain statement frame, which strengthens the asserted proposition."
            ),
            "refs": [target_ref],
            "morph_evidence": [{"type": "root_bw", "value": "qsm"}],
        })
    return out


def _deterministic_investigative_fallbacks(evidence: dict, target_ref: str) -> list[dict]:
    out: list[dict] = []
    signals = evidence.get("investigative_signals", {}) if isinstance(evidence.get("investigative_signals"), dict) else {}
    morph = evidence.get("morphology", []) if isinstance(evidence.get("morphology"), list) else []
    if not morph:
        return out

    tp = _deterministic_time_perspective_fallback(evidence, target_ref)
    if tp:
        out.append(tp)

    if signals.get("royal_we_target") or signals.get("first_i_target"):
        row_1p = _first_with_person(morph, "1P")
        row_1s = _first_with_person(morph, "1S")
        row_2x = _first_with_person(morph, "2")
        ev = []
        if row_1p and row_1p.get("form_bw"):
            ev.append({"type": "form_bw", "value": str(row_1p["form_bw"])})
            ev.append({"type": "feature", "value": "1P"})
        if row_1s and row_1s.get("form_bw"):
            ev.append({"type": "form_bw", "value": str(row_1s["form_bw"])})
            ev.append({"type": "feature", "value": "1S"})
        if row_2x and row_2x.get("form_bw"):
            ev.append({"type": "form_bw", "value": str(row_2x["form_bw"])})

        if row_1p and row_1s and ev:
            out.append({
                "title": "Pronoun Perspective Choice (Royal We / I)",
                "source": "fallback",
                "fallback_tier": 3,
                "template_id": "inv_royal_we_i",
                "category": "royal_we_vs_i",
                "confidence": 0.88,
                "insight": (
                    "The verse uses first-person divine marking rather than a detached third-person frame, "
                    "which foregrounds agency and rhetorical immediacy instead of distance."
                ),
                "refs": [target_ref],
                "morph_evidence": ev[:4],
            })
        elif row_1s and row_2x and ev:
            out.append({
                "title": "Self-Reference Inside Direct Address",
                "source": "fallback",
                "fallback_tier": 2,
                "template_id": "inv_person_mixture",
                "category": "person_mixture",
                "confidence": 0.88,
                "insight": (
                    "The verse combines direct second-person address with a first-person self-reference, "
                    "rather than staying in one person throughout. That shift binds command and speaker identity in one frame."
                ),
                "refs": [target_ref],
                "morph_evidence": ev[:4],
            })
        elif row_1s and ev:
            out.append({
                "title": "First-Person Divine Self-Reference",
                "source": "fallback",
                "fallback_tier": 2,
                "template_id": "inv_first_person_selfref",
                "category": "royal_we_vs_i",
                "confidence": 0.84,
                "insight": (
                    "A first-person self-reference appears here rather than only third-person mention, "
                    "which creates directness and removes narrative distance."
                ),
                "refs": [target_ref],
                "morph_evidence": ev[:4],
            })

    if signals.get("perspective_shift_window"):
        row_2 = _first_with_person(morph, "2")
        row_3 = _first_with_person(morph, "3")
        ev = []
        if row_2 and row_2.get("form_bw"):
            ev.append({"type": "form_bw", "value": str(row_2["form_bw"])})
            ev.append({"type": "feature", "value": "2"})
        if row_3 and row_3.get("form_bw"):
            ev.append({"type": "form_bw", "value": str(row_3["form_bw"])})
            ev.append({"type": "feature", "value": "3"})
        if ev:
            out.append({
                "title": "Local Perspective Shift",
                "source": "fallback",
                "fallback_tier": 2,
                "template_id": "inv_perspective_shift",
                "category": "perspective_shift",
                "confidence": 0.84,
                "insight": (
                    "Nearby clauses shift grammatical person rather than staying in one address frame, "
                    "which redirects who is being confronted and how responsibility is distributed."
                ),
                "refs": [target_ref],
                "morph_evidence": ev[:4],
            })

    target_roots = {str(m.get("root_bw", "")).strip() for m in morph if m.get("root_bw")}
    sound_roots = sorted(target_roots & SOUND_ROOT_CUES)
    if sound_roots:
        out.append({
            "title": "Sound/Utterance Channel Is Foregrounded",
            "source": "fallback",
            "fallback_tier": 3,
            "template_id": "inv_sound_channel",
            "category": "sound_communication",
            "confidence": 0.86,
            "insight": (
                "The verse selects a speech/hearing/call root rather than a purely visual-action frame, "
                "so communication-by-sound becomes the primary channel of meaning."
            ),
            "refs": [target_ref],
            "morph_evidence": [{"type": "root_bw", "value": sound_roots[0]}],
        })

    genders = {str(m.get("gender", "")).strip().upper() for m in morph if str(m.get("gender", "")).strip()}
    if len(genders) >= 2:
        row = next((m for m in morph if str(m.get("gender", "")).strip()), None)
        if row and row.get("form_bw"):
            out.append({
                "title": "Gender Marking Carries Referential Nuance",
                "source": "fallback",
                "fallback_tier": 3,
                "template_id": "inv_gender_nuance",
                "category": "gender_nuance",
                "confidence": 0.84,
                "insight": (
                    "The verse preserves explicit gender marking rather than flattening to a neutral form, "
                    "which helps track referents and role-structure that English often smooths out."
                ),
                "refs": [target_ref],
                "morph_evidence": [{"type": "form_bw", "value": str(row["form_bw"])}],
            })

    dedup = []
    seen = set()
    for item in out:
        cat = item.get("category")
        if cat in seen:
            continue
        seen.add(cat)
        dedup.append(item)
    if dedup:
        return dedup

    # Final grounded fallback: extract one meaningful, evidence-backed grammar signal
    # from target morphology so the UI is not empty when there is useful structure.
    for m in morph:
        feats = str(m.get("features_raw", "")).upper()
        form = str(m.get("form_bw", "")).strip()
        root = str(m.get("root_bw", "")).strip()
        if "PERF" in feats and form:
            return [{
                "title": "Completed Form Signals Decisive Action",
                "source": "fallback",
                "fallback_tier": 1,
                "template_id": "ed_completed_decisive",
                "kind": "educational",
                "category": "other_grammar",
                "confidence": 0.82,
                "insight": (
                    "A perfective verb is used rather than only an open-ended form, "
                    "which frames the action as decisively established, not merely pending."
                ),
                "refs": [target_ref],
                "morph_evidence": [
                    {"type": "form_bw", "value": form},
                    {"type": "feature", "value": "PERF"},
                ] + ([{"type": "root_bw", "value": root}] if root else []),
            }]
        if "IMPF" in feats and form:
            return [{
                "title": "Open-Ended Form Signals Continuing Force",
                "source": "fallback",
                "fallback_tier": 1,
                "template_id": "ed_open_ended",
                "kind": "educational",
                "category": "other_grammar",
                "confidence": 0.82,
                "insight": (
                    "An imperfective form appears instead of a fully completed one, "
                    "which keeps the meaning open as ongoing or repeatedly relevant."
                ),
                "refs": [target_ref],
                "morph_evidence": [
                    {"type": "form_bw", "value": form},
                    {"type": "feature", "value": "IMPF"},
                ] + ([{"type": "root_bw", "value": root}] if root else []),
            }]
        case_val = str(m.get("case", "")).strip().upper()
        if case_val in {"ACC", "GEN", "NOM"} and form:
            case_gloss = {"ACC": "direct focus/object", "GEN": "attachment/association", "NOM": "subject/topic role"}[case_val]
            return [{
                "title": "Case Marking Directs Sentence Role",
                "source": "fallback",
                "fallback_tier": 1,
                "template_id": "ed_case_role",
                "kind": "educational",
                "category": "other_grammar",
                "confidence": 0.81,
                "insight": (
                    f"The marked case here is {case_val} ({case_gloss}) rather than an unmarked alternative, "
                    "which helps fix how this word functions in the clause."
                ),
                "refs": [target_ref],
                "morph_evidence": [
                    {"type": "form_bw", "value": form},
                    {"type": "case", "value": case_val},
                ],
            }]
    return dedup


def _select_fallbacks(candidates: list[dict], recent_memory: list[dict] | None, max_items: int = 2) -> list[dict]:
    if not candidates:
        return []
    recent_memory = recent_memory or []
    recent_templates = {str(x.get("template_id", "")) for x in recent_memory[-3:]}
    recent_categories = [str(x.get("category", "")) for x in recent_memory[-3:]]
    recent_skeletons = {str(x.get("skeleton", "")) for x in recent_memory[-2:]}

    # Prefer lower tiers first (educational-safe), then confidence.
    ordered = sorted(
        candidates,
        key=lambda x: (int(x.get("fallback_tier", 9)), -float(x.get("confidence", 0.0) or 0.0)),
    )
    selected: list[dict] = []
    used_tiers: set[int] = set()
    for c in ordered:
        tier = int(c.get("fallback_tier", 9))
        tmpl = str(c.get("template_id", ""))
        cat = str(c.get("category", ""))
        skel = _text_skeleton(str(c.get("insight", "")))
        if tier in used_tiers:
            continue
        if tmpl and tmpl in recent_templates:
            continue
        if cat and recent_categories.count(cat) >= 2:
            continue
        if skel and skel in recent_skeletons:
            continue
        selected.append(c)
        used_tiers.add(tier)
        if len(selected) >= max_items:
            break
    return selected


def build_prompt(conn, surah: int, ayah: int) -> tuple[str, set[str], dict]:
    row = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
        (surah, ayah),
    ).fetchone()
    if not row:
        raise ValueError(f"Verse {surah}:{ayah} not found")

    tr, notes = _best_translation_and_notes(conn, surah, ayah)
    morph_rows = conn.execute(
        "SELECT word_pos, segment, form_arabic, form_buckwalter, tag, pos, lemma_arabic, "
        "lemma_buckwalter, root_arabic, root_buckwalter, features_raw, gender, number, person, "
        "case_val, voice, mood, verb_form, state "
        "FROM morphology WHERE chapter = ? AND verse = ? ORDER BY word_pos, segment",
        (surah, ayah),
    ).fetchall()

    morphology = []
    for r in morph_rows:
        morphology.append(
            {
                "word_pos": r["word_pos"],
                "segment": r["segment"],
                "form_arabic": r["form_arabic"],
                "form_bw": r["form_buckwalter"],
                "tag": r["tag"],
                "pos": r["pos"],
                "lemma_arabic": r["lemma_arabic"],
                "lemma_bw": r["lemma_buckwalter"],
                "root_arabic": r["root_arabic"],
                "root_bw": r["root_buckwalter"],
                "features_raw": r["features_raw"],
                "gender": r["gender"],
                "number": r["number"],
                "person": r["person"],
                "case": r["case_val"],
                "voice": r["voice"],
                "mood": r["mood"],
                "verb_form": r["verb_form"],
                "state": r["state"],
            }
        )

    ref = f"{surah}:{ayah}"
    allowed_refs = {ref}
    allowed_refs.update(_extract_refs(notes))
    window, signals = _window_signals(conn, surah, ayah, radius=2)

    evidence = {
        "target_ref": ref,
        "arabic": _strip_bismillah(row["text_uthmani"], surah, ayah),
        "translation": tr,
        "translation_notes": notes,
        "morphology": morphology,
        "window_verses": window,
        "investigative_signals": signals,
    }

    prompt = f"""Target verse: {ref}

Evidence:
{json.dumps(evidence, ensure_ascii=False)}

Return JSON exactly in this shape:
{{
  "overview": "string",
  "insights": [
    {{
      "title": "string",
      "kind": "investigative|educational",
      "category": "perspective_shift|person_mixture|royal_we_vs_i|gender_nuance|sound_communication|time_perspective|oath_structure|exception_scope|conditional_structure|cognate_accusative|demonstrative_distance|plural_type|educational|other_grammar",
      "insight": "string",
      "educational_note": "string",
      "confidence": 0.0,
      "refs": ["surah:ayah"],
      "morph_evidence": [
        {{"type": "form_bw|lemma_bw|root_bw|feature|case|voice|mood|verb_form|state", "value": "string"}}
      ]
    }}
  ]
}}

Rules:
- Give 0 to 4 insights only. Include fewer rather than weak points.
- Blend investigative and educational insights when useful.
- Each insight must be contrastive/detective style:
  - explain why this grammatical phrasing is used and not a plausible alternative.
  - include wording like "instead of", "rather than", "if it had used ...".
- Each insight must explain the meaning payoff of that specific grammatical choice.
- For educational insights, focus on one simple grammar concept and why it matters in this verse.
- If you use a technical grammar term (e.g., imperfective, accusative, jussive), add a brief lay explanation and tiny example in the same sentence.
- For any high-confidence insight (>=0.85), include a concise educational_note in plain language for a non-expert.
- Use precise evidence from provided morphology and notes.
- refs must cite verse support (usually {ref}).
- Avoid repeating the translation in different words.
- If you cannot produce a genuinely detective insight, return fewer insights.
- Every insight must include at least one valid morph_evidence item from the provided morphology.
- Do NOT invent hypothetical Arabic forms/spellings; describe alternatives in English only.
- If you claim case/aspect/voice (e.g., accusative, genitive, imperfective, perfective, passive), include matching morph_evidence entries.
- Prefer these categories when supported by evidence: sound_communication, perspective_shift, person_mixture, royal_we_vs_i, gender_nuance, time_perspective, oath_structure, exception_scope, conditional_structure, cognate_accusative, demonstrative_distance, plural_type.
- Only output those categories if supported by investigative_signals.
- confidence must be between 0 and 1 and should be conservative.
"""
    return prompt, allowed_refs, evidence


def sanitize(
    payload: dict,
    allowed_refs: set[str],
    target_ref: str,
    translation: str,
    notes: str,
    evidence: dict,
    recent_fallback_memory: list[dict] | None = None,
) -> dict:
    overview = str(payload.get("overview", "")).strip()[:2000]
    raw = payload.get("insights", [])
    if not isinstance(raw, list):
        raw = []
    morph_index = _build_morph_index(evidence.get("morphology", []) if isinstance(evidence.get("morphology"), list) else [])
    known_arabic = morph_index.get("known_arabic", set())
    signals = evidence.get("investigative_signals", {}) if isinstance(evidence.get("investigative_signals"), dict) else {}

    insights = []
    seen = set()
    for item in raw[:10]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()[:120]
        category = str(item.get("category", "")).strip()
        kind = str(item.get("kind", "")).strip().lower()
        insight = str(item.get("insight", "")).strip()[:800]
        educational_note = str(item.get("educational_note", "")).strip()[:320]
        try:
            conf = float(item.get("confidence", 0.0))
        except Exception:
            conf = 0.0
        if not title or not insight:
            continue
        if category not in ALLOWED_CATEGORIES:
            category = "other_grammar"
        if kind not in {"investigative", "educational"}:
            kind = "investigative" if category != "educational" else "educational"
        if conf < 0.72:
            continue
        if kind == "investigative" and _is_mundane(title, insight):
            continue
        has_counterfactual = _is_detective_style(title, insight)
        if kind == "educational" and has_counterfactual:
            continue
        if _is_redundant(insight, translation, notes):
            continue
        if "*" in insight or _unknown_arabic_count(insight, known_arabic) > 2:
            # Reject invented Arabic alternatives; require grounded terminology.
            continue
        txt_refs = _extract_refs(f"{title} {insight} {educational_note}")
        if any(r not in allowed_refs for r in txt_refs):
            continue

        ev_raw = item.get("morph_evidence", [])
        if not isinstance(ev_raw, list):
            ev_raw = []
        valid_ev = []
        for ev in ev_raw[:6]:
            if not isinstance(ev, dict):
                continue
            et_raw = str(ev.get("type", "")).strip()
            val_raw = str(ev.get("value", "")).strip()
            if not et_raw or not val_raw:
                continue
            # Support compact model output like:
            # type: "form_bw|root_bw|feature", value: "Sadaqo|Sdq|PERF"
            et_parts = [p.strip() for p in et_raw.split("|") if p.strip()]
            val_parts = [p.strip() for p in val_raw.split("|") if p.strip()]
            if len(et_parts) == len(val_parts) and len(et_parts) > 1:
                pairs = list(zip(et_parts, val_parts))
            else:
                pairs = [(et_raw, val_raw)]
            for et, val in pairs:
                if et not in ALLOWED_EVIDENCE_TYPES:
                    continue
                if et == "feature":
                    if _normalize_case(val) in morph_index.get("feature_token", set()):
                        valid_ev.append({"type": et, "value": _normalize_case(val)})
                    continue
                check_val = _normalize_case(val) if et in {"case", "voice", "mood", "verb_form", "state"} else val
                if check_val in morph_index.get(et, set()):
                    valid_ev.append({"type": et, "value": val})
        if not valid_ev:
            continue
        if not _claim_evidence_consistent(insight, valid_ev):
            continue
        if category == "sound_communication" and not (signals.get("sound_cues_target") or signals.get("sound_cues_window")):
            continue
        if category == "perspective_shift" and not signals.get("perspective_shift_window"):
            continue
        if category == "person_mixture" and not signals.get("person_mixture_target"):
            continue
        if category == "royal_we_vs_i" and not (signals.get("royal_we_target") or signals.get("first_i_target")):
            continue
        if category == "gender_nuance" and not signals.get("target_gender_nuance"):
            continue
        if category == "time_perspective" and not signals.get("time_perspective_target"):
            continue
        if category == "oath_structure" and not signals.get("oath_present"):
            continue
        if category == "exception_scope" and not signals.get("exception_present"):
            continue
        if category == "conditional_structure" and not signals.get("conditional_present"):
            continue
        if category == "cognate_accusative" and not signals.get("cognate_accusative_present"):
            continue
        if category == "demonstrative_distance" and not (signals.get("demonstrative_near_present") or signals.get("demonstrative_far_present")):
            continue
        if category == "plural_type" and not signals.get("plural_type_present"):
            continue
        if has_counterfactual:
            ok_cf, reason = _counterfactual_allowed(kind, category, insight, valid_ev, signals)
            if not ok_cf:
                continue
            cf_text = _extract_counterfactual_text(insight)
        else:
            ok_cf, reason = (False, "none")
            cf_text = None

        key = re.sub(r"\s+", " ", f"{title}::{insight}".lower()).strip()
        if key in seen:
            continue
        seen.add(key)
        refs = []
        for ref in item.get("refs", []):
            nr = _norm_ref(ref)
            if nr and nr in allowed_refs:
                refs.append(nr)
        if not refs:
            refs = [target_ref]
        if conf >= 0.85 and not educational_note:
            educational_note = _derive_educational_note(category, valid_ev, insight)
        elif educational_note and len(educational_note) < 40:
            educational_note = _derive_educational_note(category, valid_ev, insight)
        insights.append({
            "title": title,
            "kind": kind,
            "category": category,
            "confidence": round(conf, 3),
            "insight": insight,
            "educational_note": educational_note,
            "counterfactual_present": bool(has_counterfactual and cf_text),
            "counterfactual_text": cf_text,
            "counterfactual_rule_reason": reason,
            "refs": refs[:4],
            "morph_evidence": valid_ev[:4],
        })
        if len(insights) >= 4:
            break

    fallbacks = _deterministic_educational_fallbacks(evidence, target_ref) + _deterministic_investigative_fallbacks(evidence, target_ref)
    selected_fallbacks = _select_fallbacks(fallbacks, recent_fallback_memory, max_items=2)
    if not insights:
        insights.extend(selected_fallbacks[:2])
    else:
        # Ensure at least one investigative candidate survives when model output is generic.
        has_investigative = any(
            (it.get("category") in {"perspective_shift", "person_mixture", "royal_we_vs_i", "gender_nuance", "sound_communication", "time_perspective"})
            for it in insights
            if isinstance(it, dict)
        )
        if not has_investigative and selected_fallbacks:
            insights.append(selected_fallbacks[0])

    for it in insights:
        if not isinstance(it, dict):
            continue
        note = str(it.get("educational_note", "") or "").strip()
        if note:
            continue
        ev = it.get("morph_evidence", [])
        if not isinstance(ev, list):
            ev = []
        it["educational_note"] = _derive_educational_note(
            str(it.get("category", "other_grammar")),
            ev,
            str(it.get("insight", "")),
        )

    if not overview and insights:
        overview = " ".join(i["insight"] for i in insights[:2])[:2000]
    if _is_redundant(overview, translation, notes):
        overview = ""

    return {
        "overview_text": overview,
        "insights_json": json.dumps(insights, ensure_ascii=False),
    }


def _category_threshold(category: str) -> float:
    low = {
        "person_mixture",
        "perspective_shift",
        "royal_we_vs_i",
        "time_perspective",
        "conditional_structure",
        "exception_scope",
        "demonstrative_distance",
        "plural_type",
    }
    medium = {
        "gender_nuance",
        "cognate_accusative",
        "oath_structure",
    }
    if category in low:
        return 0.66
    if category in medium:
        return 0.72
    return 0.80


def _ev_has_person_prefix(ev: list[dict], prefix: str) -> bool:
    p = prefix.upper()
    for e in ev:
        if not isinstance(e, dict) or str(e.get("type", "")) != "feature":
            continue
        v = str(e.get("value", "")).upper()
        if v.startswith(p):
            return True
    return False


def _observation_atoms(text: str) -> list[tuple[str, bool]]:
    low = (text or "").lower()
    atoms: list[tuple[str, bool]] = []
    checks = [
        ("perfective", "perf", True),
        ("imperfective", "impf", True),
        ("imperative", "impv", True),
        ("first-person", "person1", True),
        ("second-person", "person2", True),
        ("third-person", "person3", True),
        ("passive", "passive", True),
        ("active", "active", True),
        ("accusative", "acc", True),
        ("genitive", "gen", True),
        ("nominative", "nom", True),
        ("conditional", "conditional", True),
        ("exception", "exception", True),
        ("oath", "oath", True),
        ("demonstrative", "demonstrative", True),
        ("plural", "plural", False),
        ("cognate", "cognate", True),
    ]
    for needle, key, core in checks:
        if needle in low:
            atoms.append((key, core))
    return atoms


def _atom_alignment(text: str, ev: list[dict], signals: dict) -> tuple[float, bool, int]:
    atoms = _observation_atoms(text)
    if not atoms:
        return (1.0, False, 0)

    def supported(key: str) -> bool:
        if key == "perf":
            return _has_ev(ev, "feature", "PERF")
        if key == "impf":
            return _has_ev(ev, "feature", "IMPF") or _has_ev(ev, "feature", "IMPV")
        if key == "impv":
            return _has_ev(ev, "feature", "IMPV")
        if key == "person1":
            return _ev_has_person_prefix(ev, "1") or bool(signals.get("first_i_target") or signals.get("royal_we_target"))
        if key == "person2":
            return _ev_has_person_prefix(ev, "2") or bool(signals.get("second_person_target"))
        if key == "person3":
            return _ev_has_person_prefix(ev, "3") or bool(signals.get("perspective_shift_window"))
        if key == "passive":
            return _has_ev(ev, "voice", "PASSIVE") or _has_ev(ev, "voice", "PASS")
        if key == "active":
            return _has_ev(ev, "voice", "ACTIVE")
        if key == "acc":
            return _has_ev(ev, "case", "ACC") or _has_ev(ev, "feature", "ACC")
        if key == "gen":
            return _has_ev(ev, "case", "GEN") or _has_ev(ev, "feature", "GEN")
        if key == "nom":
            return _has_ev(ev, "case", "NOM") or _has_ev(ev, "feature", "NOM")
        if key == "conditional":
            return bool(signals.get("conditional_present"))
        if key == "exception":
            return bool(signals.get("exception_present"))
        if key == "oath":
            return bool(signals.get("oath_present"))
        if key == "demonstrative":
            return bool(signals.get("demonstrative_near_present") or signals.get("demonstrative_far_present"))
        if key == "plural":
            return bool(signals.get("plural_type_present")) or _has_ev(ev, "feature", "MP") or _has_ev(ev, "feature", "FP")
        if key == "cognate":
            return bool(signals.get("cognate_accusative_present"))
        return True

    matched = 0
    core_fail = False
    unsupported = 0
    for key, core in atoms:
        ok = supported(key)
        if ok:
            matched += 1
        else:
            unsupported += 1
            if core:
                core_fail = True
    return (matched / max(1, len(atoms)), core_fail, unsupported)


def _quality_dimensions_for_insight(item: dict, translation: str, notes: str, target_ref: str, signals: dict | None = None) -> dict:
    signals = signals or {}
    txt = str(item.get("insight", "") or "")
    ed = str(item.get("educational_note", "") or "")
    refs = item.get("refs", []) if isinstance(item.get("refs", []), list) else []
    mev = item.get("morph_evidence", []) if isinstance(item.get("morph_evidence", []), list) else []
    category = str(item.get("category", "other_grammar"))
    conf_raw = float(item.get("confidence", 0.0) or 0.0)
    kind = str(item.get("kind", "investigative"))

    direct_feature_match = 1.0 if len(mev) >= 1 else 0.0
    primary_support_count_score = 1.0 if len(mev) >= 2 else (0.5 if len(mev) == 1 else 0.0)
    atom_alignment, core_atom_fail, unsupported_atoms = _atom_alignment(txt, mev, signals)
    role_coherence = atom_alignment
    unsupported_leap_penalty = min(0.8, (unsupported_atoms / 4.0) + (0.2 if ("might" in txt.lower() or "possibly" in txt.lower()) else 0.0))
    E = max(0.0, min(1.0, 0.35 * direct_feature_match + 0.20 * primary_support_count_score + 0.20 * role_coherence + 0.25 * (1.0 - unsupported_leap_penalty)))

    category_fit = 1.0 if category in ALLOWED_CATEGORIES else 0.5
    feature_accuracy = 1.0 if len(mev) >= 1 else 0.0
    clause_accuracy = 1.0 if target_ref in refs else 0.8 if refs else 0.6
    invention_penalty = 0.0  # invention checks already enforced during sanitize()
    L = max(0.0, min(1.0, 0.30 * category_fit + 0.25 * feature_accuracy + 0.20 * clause_accuracy + 0.25 * (1.0 - invention_penalty)))

    payoff_specificity = 1.0 if any(x in txt.lower() for x in ("rather than", "instead of", "which")) else 0.65
    non_triviality = 1.0 if not _is_mundane(str(item.get("title", "")), txt) else 0.25
    reader_helpfulness = 1.0 if len(ed) >= 40 else 0.6
    observable_distinctiveness = 1.0 if len(mev) >= 2 else 0.7
    V = max(0.0, min(1.0, 0.25 * observable_distinctiveness + 0.30 * payoff_specificity + 0.20 * non_triviality + 0.25 * reader_helpfulness))

    overlap_score = max(_jaccard(txt, translation), _jaccard(txt, notes))
    N = max(0.0, min(1.0, 1.0 - overlap_score))

    plain_language = 1.0 if len(ed) >= 30 else 0.65
    brevity = 1.0 if len(txt) <= 420 else 0.7
    terminology_control = 1.0 if len(detect := re.findall(r"\b(imperfective|perfective|accusative|genitive|jussive|subjunctive)\b", txt.lower())) <= 2 else 0.7
    C = max(0.0, min(1.0, 0.40 * plain_language + 0.30 * brevity + 0.30 * terminology_control))

    unsupported_claim_risk = 0.35 if len(mev) == 0 else 0.0
    cf_present = bool(item.get("counterfactual_present"))
    cf_text = str(item.get("counterfactual_text") or "").strip()
    counterfactual_risk = 0.20 if (cf_present and not cf_text) else 0.0
    perspective_error_risk = 0.25 if ("first-person" in txt.lower() and "second-person" not in txt.lower() and category == "person_mixture") else 0.0
    novelty_failure_risk = 0.25 if N < 0.35 else 0.0
    overstatement_risk = 0.20 if any(w in txt.lower() for w in ("always", "never")) else 0.0
    atom_risk = 0.40 if core_atom_fail else (0.20 if unsupported_atoms >= 2 else 0.0)
    R = max(unsupported_claim_risk, counterfactual_risk, perspective_error_risk, novelty_failure_risk, overstatement_risk, atom_risk)

    base = 0.30 * E + 0.30 * L + 0.20 * V + 0.10 * N + 0.10 * C
    overall_conf = max(0.0, min(1.0, base - 0.55 * R))
    return {
        "model_confidence_raw": round(conf_raw, 3),
        "evidence_sufficiency": round(E, 3),
        "linguistic_correctness": round(L, 3),
        "interpretive_value": round(V, 3),
        "novelty": round(N, 3),
        "clarity": round(C, 3),
        "risk": round(R, 3),
        "atom_alignment": round(atom_alignment, 3),
        "core_atom_fail": bool(core_atom_fail),
        "unsupported_atoms": int(unsupported_atoms),
        "overall_confidence": round(overall_conf, 3),
    }


def _to_v7_insight(item: dict, target_ref: str, translation: str, notes: str, idx: int, signals: dict | None = None) -> dict:
    txt = str(item.get("insight", "") or "").strip()
    title = str(item.get("title", "") or "").strip()[:120]
    category = str(item.get("category", "other_grammar"))
    kind = str(item.get("kind", "investigative"))
    refs = item.get("refs", []) if isinstance(item.get("refs", []), list) else [target_ref]
    mev = item.get("morph_evidence", []) if isinstance(item.get("morph_evidence", []), list) else []
    ed = str(item.get("educational_note", "") or "").strip()

    has_cf = bool(item.get("counterfactual_present"))
    cf_text = str(item.get("counterfactual_text") or "").strip() or None
    payoff_type = "none"
    low = txt.lower()
    if "direct" in low:
        payoff_type = "directness"
    elif "ongoing" in low or "continu" in low:
        payoff_type = "continuity"
    elif "agency" in low:
        payoff_type = "agency"
    elif "emphasis" in low:
        payoff_type = "emphasis"
    elif "specific" in low:
        payoff_type = "specificity"

    # Split raw text into observation vs payoff so the UI doesn't repeat identical content.
    # Remove machine-like morphology dumps from model prose (too technical for UI).
    clean_txt = re.sub(r"\(\s*morph:[^)]+\)", "", txt, flags=re.IGNORECASE)
    clean_txt = re.sub(r"\s{2,}", " ", clean_txt).strip()
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", clean_txt) if p.strip()]
    observation_text = parts[0] if parts else txt
    # Ground observation with concrete in-verse anchor if missing.
    if not re.search(r"[\u0621-\u064A]", observation_text):
        forms = _ev_lookup(mev, "form_bw")
        roots = _ev_lookup(mev, "root_bw")
        if forms:
            form_ar = _bw_to_ar(forms[0])
            if roots:
                root_ar = " ".join(list(_bw_to_ar(roots[0])))
                observation_text = f"{observation_text} This is visible in form {form_ar} (root {root_ar})."
            else:
                observation_text = f"{observation_text} This is visible in form {form_ar}."
    payoff_text = " ".join(parts[1:]).strip()
    if not payoff_text:
        # Heuristic extraction for "which/so/therefore" tail clauses.
        m_pay = re.search(r"\b(which|so|therefore|thus|this means|this marks|this makes)\b(.+)$", txt, re.IGNORECASE)
        if m_pay:
            payoff_text = (m_pay.group(1) + m_pay.group(2)).strip()
    if not payoff_text:
        payoff_text = (
            "This grammatical choice changes how the statement is understood in Arabic, beyond a flat English rendering."
        )
    if _text_skeleton(observation_text) == _text_skeleton(payoff_text):
        payoff_text = (
            "The choice tightens interpretation by signaling a specific framing that translation alone can miss."
        )
    if _should_add_example(payoff_text):
        payoff_text = f"{payoff_text} {_payoff_example(category, txt, mev)}".strip()

    novelty_overlap = max(_jaccard(txt, translation), _jaccard(txt, notes))
    novelty_tag = "overlap" if novelty_overlap >= 0.42 else ("low" if novelty_overlap >= 0.30 else ("medium" if novelty_overlap >= 0.18 else "high"))
    quality = _quality_dimensions_for_insight(item, translation, notes, target_ref, signals)
    th = _category_threshold(category)
    eligible = (
        quality["evidence_sufficiency"] >= 0.75
        and quality["linguistic_correctness"] >= 0.80
        and quality["interpretive_value"] >= 0.55
        and quality["clarity"] >= 0.60
        and quality["risk"] <= 0.25
        and quality["overall_confidence"] >= th
    )
    tier = "primary" if eligible and quality["overall_confidence"] >= max(0.78, th + 0.08) else ("secondary" if eligible else "suppressed")
    reason_codes = []
    if not eligible:
        if quality["overall_confidence"] < th:
            reason_codes.append("below_category_threshold")
        if quality["risk"] > 0.25:
            reason_codes.append("risk_too_high")
        if quality["novelty"] < 0.4:
            reason_codes.append("low_novelty")
        if bool(quality.get("core_atom_fail")):
            reason_codes.append("core_atom_unsupported")

    evidence_trace = []
    for j, ev in enumerate(mev[:4], start=1):
        evidence_trace.append({
            "token_ref": f"{target_ref}:{j}",
            "surface_ar": "",
            "buckwalter": "",
            "root": "",
            "feature_type": str(ev.get("type", "")),
            "feature_value": str(ev.get("value", "")),
            "role": "primary_support" if j == 1 else "secondary_support",
        })

    return {
        "id": f"{target_ref.replace(':', '_')}_{idx:02d}",
        "kind": kind,
        "category": category,
        "title": title,
        "claim": {
            "observation": observation_text,
            "scope": "verse",
            "strength": "direct" if quality["evidence_sufficiency"] >= 0.85 else "probable",
        },
        "counterfactual": {
            "present": bool(has_cf and cf_text),
            "type": "explicit_alternative" if (has_cf and cf_text) else "none",
            "text": cf_text if (has_cf and cf_text) else None,
            "safety": "high" if category in {"person_mixture", "perspective_shift", "royal_we_vs_i", "time_perspective"} else "medium",
        },
        "meaning_payoff": {
            "text": payoff_text,
            "type": payoff_type,
            "strength": "strong" if quality["interpretive_value"] >= 0.8 else ("moderate" if quality["interpretive_value"] >= 0.62 else "light"),
        },
        "evidence_trace": evidence_trace,
        "educational_note": {
            "text": ed,
            "reading_level": "basic",
        },
        "novelty_check": {
            "against_translation_notes": novelty_tag,
            "reason": "Computed from lexical overlap against translation notes.",
        },
        "quality": quality,
        "display": {
            "tier": tier,
            "eligible": eligible,
            "reason_codes": reason_codes,
        },
        "fallback": {
            "source": str(item.get("source", "model")),
            "tier": int(item.get("fallback_tier", 0) or 0),
            "template_id": str(item.get("template_id", "")),
        },
        "refs": [
            {
                "verse_key": refs[0] if refs else target_ref,
                "token_refs": [x["token_ref"] for x in evidence_trace],
            }
        ],
    }


def verify_and_score(sanitized: dict, target_ref: str, translation: str, notes: str, evidence: dict | None = None) -> tuple[float, dict, dict]:
    try:
        insights = json.loads(sanitized.get("insights_json", "[]"))
    except Exception:
        insights = []

    score = 0.0
    report = {"checks": {}}
    overview = sanitized.get("overview_text", "")

    report["checks"]["has_overview"] = bool(overview and len(overview) >= 100)
    report["checks"]["has_strong_insights"] = len(insights) >= 2
    if report["checks"]["has_overview"]:
        score += 0.3
    if report["checks"]["has_strong_insights"]:
        score += 0.3

    cited = 0
    target_hits = 0
    detective_hits = 0
    for it in insights:
        if not isinstance(it, dict):
            continue
        refs = it.get("refs", [])
        title = it.get("title", "")
        txt = it.get("insight", "")
        mev = it.get("morph_evidence", [])
        if refs and txt:
            cited += 1
        if target_ref in refs:
            target_hits += 1
        if _is_detective_style(title, txt):
            detective_hits += 1
        if isinstance(mev, list) and len(mev) > 0:
            report["checks"]["morph_evidence_items"] = report["checks"].get("morph_evidence_items", 0) + 1
    report["checks"]["cited_insights"] = cited
    report["checks"]["target_hits"] = target_hits
    report["checks"]["detective_insights"] = detective_hits
    if cited:
        score += min(0.2, cited * 0.05)
    if target_hits:
        score += min(0.2, target_hits * 0.05)
    if detective_hits:
        score += min(0.15, detective_hits * 0.05)
    morph_ev_count = int(report["checks"].get("morph_evidence_items", 0))
    if morph_ev_count:
        score += min(0.1, morph_ev_count * 0.03)

    report["checks"]["non_redundant_overview"] = bool(overview and not _is_redundant(overview, translation, notes))
    if report["checks"]["non_redundant_overview"]:
        score += 0.05

    signals = {}
    if isinstance(evidence, dict) and isinstance(evidence.get("investigative_signals"), dict):
        signals = evidence.get("investigative_signals", {})

    v7_insights = []
    for i, it in enumerate(insights, start=1):
        if not isinstance(it, dict):
            continue
        v7_insights.append(_to_v7_insight(it, target_ref, translation, notes, i, signals))

    if v7_insights:
        overall_candidates = [float(x.get("quality", {}).get("overall_confidence", 0.0) or 0.0) for x in v7_insights]
        v7_score = max(overall_candidates) if overall_candidates else 0.0
        score = max(score, v7_score)
    score = max(0.0, min(1.0, score))
    report["signal_score"] = round(score, 3)
    report["generation_version"] = "v7"
    report["quality_dimensions"] = {
        "avg_evidence_sufficiency": round(sum(float(x.get("quality", {}).get("evidence_sufficiency", 0.0) or 0.0) for x in v7_insights) / max(1, len(v7_insights)), 3),
        "avg_linguistic_correctness": round(sum(float(x.get("quality", {}).get("linguistic_correctness", 0.0) or 0.0) for x in v7_insights) / max(1, len(v7_insights)), 3),
        "avg_interpretive_value": round(sum(float(x.get("quality", {}).get("interpretive_value", 0.0) or 0.0) for x in v7_insights) / max(1, len(v7_insights)), 3),
        "avg_novelty": round(sum(float(x.get("quality", {}).get("novelty", 0.0) or 0.0) for x in v7_insights) / max(1, len(v7_insights)), 3),
        "avg_clarity": round(sum(float(x.get("quality", {}).get("clarity", 0.0) or 0.0) for x in v7_insights) / max(1, len(v7_insights)), 3),
        "max_risk": round(max((float(x.get("quality", {}).get("risk", 0.0) or 0.0) for x in v7_insights), default=0.0), 3),
    }
    enriched = {
        "generation_version": "v7",
        "insights_v7_json": json.dumps(v7_insights, ensure_ascii=False),
        "quality_json": json.dumps(report.get("quality_dimensions", {}), ensure_ascii=False),
        "overall_confidence": round(score, 3),
        "model_confidence_raw": round(max((float((x.get("quality", {}) or {}).get("model_confidence_raw", 0.0) or 0.0) for x in v7_insights), default=0.0), 3),
        "display_json": json.dumps({"max_displayed": 2, "eligible_count": sum(1 for x in v7_insights if (x.get("display", {}) or {}).get("eligible"))}, ensure_ascii=False),
    }
    return score, report, enriched


def upsert(
    conn,
    surah: int,
    ayah: int,
    config_id: int,
    sanitized: dict,
    signal_score: float,
    verifier_report: dict,
    enriched: dict,
    evidence: dict,
    raw: str,
    elapsed_ms: int,
    force: bool,
) -> bool:
    existing = conn.execute(
        "SELECT id FROM verse_grammar_insights WHERE chapter = ? AND verse = ? AND config_id = ?",
        (surah, ayah, config_id),
    ).fetchone()
    if existing and not force:
        return False
    if existing and force:
        conn.execute(
            "DELETE FROM verse_grammar_insights WHERE chapter = ? AND verse = ? AND config_id = ?",
            (surah, ayah, config_id),
        )

    conn.execute(
        "INSERT INTO verse_grammar_insights ("
        "chapter, verse, config_id, overview_text, insights_json, signal_score, verifier_report_json, "
        "evidence_json, raw_response, model_response_time_ms, generation_version, insights_v7_json, "
        "quality_json, overall_confidence, model_confidence_raw, display_json"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            surah,
            ayah,
            config_id,
            sanitized["overview_text"],
            sanitized["insights_json"],
            signal_score,
            json.dumps(verifier_report, ensure_ascii=False),
            json.dumps(evidence, ensure_ascii=False),
            raw,
            elapsed_ms,
            str(enriched.get("generation_version", "v6")),
            str(enriched.get("insights_v7_json", "[]")),
            str(enriched.get("quality_json", "{}")),
            float(enriched.get("overall_confidence", signal_score)),
            float(enriched.get("model_confidence_raw", 0.0)),
            str(enriched.get("display_json", "{}")),
        ),
    )
    return True


def run(args: argparse.Namespace) -> None:
    conn = get_db()
    try:
        cfg_id = get_or_create_config(conn, args.config, args.model, args.prompt_version)
        if args.verses:
            verses = parse_verse_spec(args.verses)
        else:
            rows = conn.execute("SELECT chapter, verse FROM verses ORDER BY chapter, verse").fetchall()
            verses = [(r["chapter"], r["verse"]) for r in rows]

        ins = skip = err = 0
        recent_fallback_memory: list[dict] = []
        print(f"Generating grammar insights for {len(verses)} verse(s) with model '{args.model}'")
        for i, (s, a) in enumerate(verses, start=1):
            if not args.force:
                already = conn.execute(
                    "SELECT 1 FROM verse_grammar_insights WHERE chapter = ? AND verse = ? AND config_id = ?",
                    (s, a, cfg_id),
                ).fetchone()
                if already:
                    print(f"[{i}/{len(verses)}] {s}:{a} skipped (already generated)")
                    skip += 1
                    continue

            print(f"[{i}/{len(verses)}] {s}:{a} ...", end="", flush=True)
            try:
                prompt, allowed_refs, evidence = build_prompt(conn, s, a)
                raw, elapsed = call_model(args.model, SYSTEM_PROMPT, prompt, temperature=args.temperature)
                try:
                    payload = _extract_json(raw)
                except Exception:
                    # One strict retry for malformed JSON responses.
                    repair_prompt = (
                        prompt
                        + "\n\nIMPORTANT: Return valid JSON only. Do not include any prose before or after JSON."
                    )
                    raw2, elapsed2 = call_model(args.model, SYSTEM_PROMPT, repair_prompt, temperature=0.0)
                    payload = _extract_json(raw2)
                    raw = raw2
                    elapsed += elapsed2
                target_ref = f"{s}:{a}"
                sanitized = sanitize(
                    payload,
                    allowed_refs,
                    target_ref,
                    str(evidence.get("translation", "")),
                    str(evidence.get("translation_notes", "")),
                    evidence,
                    recent_fallback_memory,
                )
                signal_score, verifier, enriched = verify_and_score(
                    sanitized,
                    target_ref,
                    str(evidence.get("translation", "")),
                    str(evidence.get("translation_notes", "")),
                    evidence,
                )
                if args.dry_run:
                    print(" dry-run")
                    continue
                did = upsert(
                    conn,
                    s,
                    a,
                    cfg_id,
                    sanitized,
                    signal_score,
                    verifier,
                    enriched,
                    evidence,
                    raw,
                    elapsed,
                    args.force,
                )
                conn.commit()
                try:
                    parsed = json.loads(sanitized.get("insights_json", "[]"))
                except Exception:
                    parsed = []
                for it in parsed:
                    if not isinstance(it, dict):
                        continue
                    if str(it.get("source", "")) != "fallback":
                        continue
                    recent_fallback_memory.append({
                        "category": str(it.get("category", "")),
                        "template_id": str(it.get("template_id", "")),
                        "skeleton": _text_skeleton(str(it.get("insight", ""))),
                        "title_stem": _title_stem(str(it.get("title", ""))),
                    })
                if len(recent_fallback_memory) > 12:
                    recent_fallback_memory = recent_fallback_memory[-12:]
                if did:
                    ins += 1
                    print(f" stored (score={signal_score:.2f})")
                else:
                    skip += 1
                    print(" skipped")
            except Exception as e:
                conn.rollback()
                err += 1
                print(f" error: {e}")
        print(f"\nDone. inserted={ins}, skipped={skip}, errors={err}")
    finally:
        conn.close()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate verse grammar insights")
    p.add_argument("--verses", default=None, help='Verse spec like "21:1-28,1:1"')
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--config", default=DEFAULT_CONFIG)
    p.add_argument("--prompt-version", default=DEFAULT_PROMPT_VERSION)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    return p


if __name__ == "__main__":
    run(build_parser().parse_args())
