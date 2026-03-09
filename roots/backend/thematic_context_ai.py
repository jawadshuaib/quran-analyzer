"""Offline Qur'an-only thematic context generation pipeline.

Generates and stores versioned thematic context per verse using a local LLM
(default: Ollama qwen3:14b). No tafsir/hadith/secondary sources are used.

Usage:
  python thematic_context_ai.py --verses "105:1,106:1-4" --config thematic-quran-only-v1
  python thematic_context_ai.py --config thematic-quran-only-v1 --model qwen3:14b
"""

import argparse
import json
import re
from typing import Any

from app import DB_PATH, _find_related_verses, _strip_bismillah, get_db
from translate_ai import call_model

DEFAULT_MODEL = "qwen3:14b"
DEFAULT_CONFIG = "thematic-quran-only-v1"
DEFAULT_PROMPT_VERSION = "v1"

SYSTEM_PROMPT = """\
You are a Qur'an-only thematic analysis engine.

Hard constraints:
1) Use ONLY the Qur'an evidence provided in the prompt.
2) Do NOT use tafsir, hadith, historical narrations, or external religious literature.
3) Do NOT invent verse references. Only use verse refs present in provided evidence.
4) Output valid JSON only, with no markdown and no extra text.
"""

BLOCKED_NON_QURANIC_ENTITIES = {
    "abraha",
    "abrahah",
    "byzantine",
    "sasanian",
    "sassanian",
    "umayyad",
    "abbasid",
}

MIN_LINK_CONFIDENCE = 0.62
GENERIC_PHRASES = (
    "divine punishment",
    "divine judgment",
    "human schemes",
    "futility of opposing",
    "those who oppose",
    "human arrogance",
)


def parse_verse_spec(spec: str) -> list[tuple[int, int]]:
    verses: list[tuple[int, int]] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(\d+):(\d+)-(\d+)$", part)
        if m:
            s, a1, a2 = int(m.group(1)), int(m.group(2)), int(m.group(3))
            lo, hi = min(a1, a2), max(a1, a2)
            for a in range(lo, hi + 1):
                verses.append((s, a))
            continue
        m = re.match(r"^(\d+):(\d+)$", part)
        if m:
            verses.append((int(m.group(1)), int(m.group(2))))
    # de-dupe preserving order
    seen = set()
    out = []
    for v in verses:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def get_or_create_thematic_config(
    conn,
    config_name: str,
    model_name: str,
    prompt_version: str,
) -> int:
    row = conn.execute(
        "SELECT id FROM thematic_context_configs WHERE config_name = ?",
        (config_name,),
    ).fetchone()
    if row:
        return row["id"]
    conn.execute(
        "INSERT INTO thematic_context_configs "
        "(config_name, model_name, prompt_version, methodology_notes) "
        "VALUES (?, ?, ?, ?)",
        (
            config_name,
            model_name,
            prompt_version,
            "Qur'an-only thematic context generated offline; no tafsir/hadith inputs.",
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id FROM thematic_context_configs WHERE config_name = ?",
        (config_name,),
    ).fetchone()
    return row["id"]


def verse_exists(conn, surah: int, ayah: int) -> bool:
    row = conn.execute(
        "SELECT 1 FROM verses WHERE chapter = ? AND verse = ?",
        (surah, ayah),
    ).fetchone()
    return bool(row)


def _clamp_conf(v: Any) -> float:
    try:
        f = float(v)
    except Exception:
        return 0.0
    return max(0.0, min(1.0, f))


def _contains_blocked_entity(text: str) -> bool:
    low = text.lower()
    return any(term in low for term in BLOCKED_NON_QURANIC_ENTITIES)


def _scrub_text(text: str) -> str:
    if not text:
        return ""
    if _contains_blocked_entity(text):
        return ""
    return text.strip()


def _is_generic_text(text: str) -> bool:
    low = text.lower().strip()
    if len(low) < 28:
        return True
    return any(p in low for p in GENERIC_PHRASES)


def _norm_ref(ref: str) -> str | None:
    if not isinstance(ref, str):
        return None
    m = re.match(r"^\s*(\d+):(\d+)\s*$", ref)
    if not m:
        return None
    return f"{int(m.group(1))}:{int(m.group(2))}"


def _extract_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model response")
    return json.loads(raw[start : end + 1])


def _load_context_rows(conn, surah: int, ayah: int, radius: int = 3) -> list[dict]:
    total_row = conn.execute(
        "SELECT COUNT(*) AS cnt FROM verses WHERE chapter = ?",
        (surah,),
    ).fetchone()
    total = total_row["cnt"] if total_row else 0
    start = max(1, ayah - radius)
    end = min(total, ayah + radius)
    rows = conn.execute(
        "SELECT chapter, verse, text_uthmani FROM verses "
        "WHERE chapter = ? AND verse BETWEEN ? AND ? ORDER BY verse",
        (surah, start, end),
    ).fetchall()
    out = []
    for r in rows:
        out.append(
            {
                "ref": f"{r['chapter']}:{r['verse']}",
                "arabic": _strip_bismillah(r["text_uthmani"], r["chapter"], r["verse"]),
                "translation": _best_translation(conn, r["chapter"], r["verse"]),
            }
        )
    return out


def _best_translation(conn, surah: int, ayah: int) -> str:
    row = conn.execute(
        "SELECT translation_text FROM ai_translations "
        "WHERE chapter = ? AND verse = ? ORDER BY created_at DESC LIMIT 1",
        (surah, ayah),
    ).fetchone()
    if row and row["translation_text"]:
        return row["translation_text"]
    row = conn.execute(
        "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
        (surah, ayah),
    ).fetchone()
    return row["text_en"] if row else ""


def _surah_samples(conn, surah: int) -> list[dict]:
    count_row = conn.execute(
        "SELECT COUNT(*) AS cnt FROM verses WHERE chapter = ?",
        (surah,),
    ).fetchone()
    total = count_row["cnt"] if count_row else 0
    if total == 0:
        return []
    picks = sorted(set([1, 2, 3, max(1, total - 2), max(1, total - 1), total]))
    rows = conn.execute(
        "SELECT chapter, verse, text_uthmani FROM verses WHERE chapter = ? AND verse IN (%s) ORDER BY verse"
        % ",".join("?" * len(picks)),
        (surah, *picks),
    ).fetchall()
    out = []
    for r in rows:
        out.append(
            {
                "ref": f"{r['chapter']}:{r['verse']}",
                "arabic": _strip_bismillah(r["text_uthmani"], r["chapter"], r["verse"]),
                "translation": _best_translation(conn, r["chapter"], r["verse"]),
            }
        )
    return out


def _related_candidates(conn, surah: int, ayah: int, limit: int = 20) -> list[dict]:
    refs = []
    for containment, _shared_weight, (ch, v), _shared_roots in _find_related_verses(surah, ayah, limit=limit):
        vr = conn.execute(
            "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
            (ch, v),
        ).fetchone()
        if not vr:
            continue
        refs.append(
            {
                "ref": f"{ch}:{v}",
                "similarity": round(float(containment), 3),
                "arabic": _strip_bismillah(vr["text_uthmani"], ch, v),
                "translation": _best_translation(conn, ch, v),
            }
        )
    return refs


def build_prompt(conn, surah: int, ayah: int) -> tuple[str, set[str], dict]:
    target_row = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
        (surah, ayah),
    ).fetchone()
    if not target_row:
        raise ValueError(f"Verse {surah}:{ayah} not found")

    target_ref = f"{surah}:{ayah}"
    immediate = _load_context_rows(conn, surah, ayah, radius=3)
    related = _related_candidates(conn, surah, ayah, limit=25)
    this_surah_samples = _surah_samples(conn, surah)
    prev_surah_samples = _surah_samples(conn, surah - 1) if surah > 1 else []
    next_surah_samples = _surah_samples(conn, surah + 1) if surah < 114 else []

    allowed_refs = {target_ref}
    for block in (immediate, related, this_surah_samples, prev_surah_samples, next_surah_samples):
        for item in block:
            allowed_refs.add(item["ref"])

    evidence = {
        "target_ref": target_ref,
        "immediate_refs": [x["ref"] for x in immediate],
        "related_candidate_refs": [x["ref"] for x in related],
        "this_surah_sample_refs": [x["ref"] for x in this_surah_samples],
        "prev_surah_sample_refs": [x["ref"] for x in prev_surah_samples],
        "next_surah_sample_refs": [x["ref"] for x in next_surah_samples],
    }

    prompt = f"""Target verse
{target_ref}
Arabic: {_strip_bismillah(target_row["text_uthmani"], surah, ayah)}
Translation: {_best_translation(conn, surah, ayah)}

Immediate vicinity evidence (same surah)
{json.dumps(immediate, ensure_ascii=False)}

Same-surah anchor samples
{json.dumps(this_surah_samples, ensure_ascii=False)}

Previous-surah anchor samples
{json.dumps(prev_surah_samples, ensure_ascii=False)}

Next-surah anchor samples
{json.dumps(next_surah_samples, ensure_ascii=False)}

Qur'an-wide related candidate verses
{json.dumps(related, ensure_ascii=False)}

Return JSON with exactly this shape:
{{
  "passage": {{
    "start_ayah": int,
    "end_ayah": int,
    "theme": "string",
    "confidence": 0.0
  }},
  "surah_role": {{
    "summary": "string",
    "confidence": 0.0
  }},
  "neighbor_surahs": {{
    "summary": "string",
    "confidence": 0.0
  }},
  "quran_wide_links": [
    {{
      "theme": "string",
      "summary": "string",
      "confidence": 0.0,
      "related_verses": ["surah:ayah", "surah:ayah"]
    }}
  ]
}}

Rules:
- Use only evidence in this prompt.
- Do not mention non-Qur'anic named entities (for example: Abraha).
- Avoid generic statements. Prefer specific, evidence-rich wording tied to cited ayat.
- All related_verses must come from provided evidence refs.
- Keep quran_wide_links length between 2 and 5.
- confidence values must be between 0 and 1.
- start_ayah/end_ayah must be valid ayah numbers in this surah.
"""
    return prompt, allowed_refs, evidence


def sanitize_payload(payload: dict, surah: int, ayah: int, allowed_refs: set[str], surah_total: int) -> dict:
    passage = payload.get("passage", {}) if isinstance(payload, dict) else {}
    p_start = int(passage.get("start_ayah", ayah)) if isinstance(passage, dict) else ayah
    p_end = int(passage.get("end_ayah", ayah)) if isinstance(passage, dict) else ayah
    p_start = max(1, min(surah_total, p_start))
    p_end = max(1, min(surah_total, p_end))
    if p_start > p_end:
        p_start, p_end = p_end, p_start

    surah_role = payload.get("surah_role", {}) if isinstance(payload, dict) else {}
    neighbor = payload.get("neighbor_surahs", {}) if isinstance(payload, dict) else {}
    links_raw = payload.get("quran_wide_links", []) if isinstance(payload, dict) else []
    if not isinstance(links_raw, list):
        links_raw = []

    links = []
    for item in links_raw[:5]:
        if not isinstance(item, dict):
            continue
        theme_txt = _scrub_text(str(item.get("theme", "")))
        summary_txt = _scrub_text(str(item.get("summary", "")))
        if not theme_txt and not summary_txt:
            continue
        if _is_generic_text(theme_txt) and _is_generic_text(summary_txt):
            continue
        refs = []
        for ref in item.get("related_verses", []):
            nr = _norm_ref(ref)
            if nr and nr in allowed_refs:
                refs.append(nr)
        if len(refs) < 2:
            continue
        conf = _clamp_conf(item.get("confidence", 0))
        if conf < MIN_LINK_CONFIDENCE:
            continue
        links.append(
            {
                "theme": theme_txt,
                "summary": summary_txt,
                "confidence": conf,
                "related_verses": refs[:4],
            }
        )

    return {
        "passage_start_ayah": p_start,
        "passage_end_ayah": p_end,
        "passage_theme": _scrub_text(str(passage.get("theme", ""))) if isinstance(passage, dict) else "",
        "passage_confidence": _clamp_conf(passage.get("confidence", 0) if isinstance(passage, dict) else 0),
        "surah_role_summary": _scrub_text(str(surah_role.get("summary", ""))) if isinstance(surah_role, dict) else "",
        "surah_role_confidence": _clamp_conf(surah_role.get("confidence", 0) if isinstance(surah_role, dict) else 0),
        "neighbor_surah_summary": _scrub_text(str(neighbor.get("summary", ""))) if isinstance(neighbor, dict) else "",
        "neighbor_surah_confidence": _clamp_conf(neighbor.get("confidence", 0) if isinstance(neighbor, dict) else 0),
        "quran_wide_links_json": json.dumps(links, ensure_ascii=False),
    }


def upsert_thematic_context(
    conn,
    surah: int,
    ayah: int,
    config_id: int,
    sanitized: dict,
    evidence: dict,
    raw_response: str,
    elapsed_ms: int,
    force: bool,
) -> bool:
    existing = conn.execute(
        "SELECT id FROM verse_thematic_contexts WHERE chapter = ? AND verse = ? AND config_id = ?",
        (surah, ayah, config_id),
    ).fetchone()
    if existing and not force:
        return False
    if existing and force:
        conn.execute(
            "DELETE FROM verse_thematic_contexts WHERE chapter = ? AND verse = ? AND config_id = ?",
            (surah, ayah, config_id),
        )

    conn.execute(
        "INSERT INTO verse_thematic_contexts ("
        "chapter, verse, config_id, "
        "passage_start_ayah, passage_end_ayah, passage_theme, passage_confidence, "
        "surah_role_summary, surah_role_confidence, "
        "neighbor_surah_summary, neighbor_surah_confidence, "
        "quran_wide_links_json, evidence_json, raw_response, model_response_time_ms"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            surah,
            ayah,
            config_id,
            sanitized["passage_start_ayah"],
            sanitized["passage_end_ayah"],
            sanitized["passage_theme"],
            sanitized["passage_confidence"],
            sanitized["surah_role_summary"],
            sanitized["surah_role_confidence"],
            sanitized["neighbor_surah_summary"],
            sanitized["neighbor_surah_confidence"],
            sanitized["quran_wide_links_json"],
            json.dumps(evidence, ensure_ascii=False),
            raw_response,
            elapsed_ms,
        ),
    )
    return True


def run(args: argparse.Namespace) -> None:
    conn = get_db()
    try:
        config_id = get_or_create_thematic_config(
            conn,
            config_name=args.config,
            model_name=args.model,
            prompt_version=args.prompt_version,
        )
        if args.verses:
            verses = parse_verse_spec(args.verses)
        else:
            rows = conn.execute(
                "SELECT chapter, verse FROM verses ORDER BY chapter, verse"
            ).fetchall()
            verses = [(r["chapter"], r["verse"]) for r in rows]

        if not verses:
            print("No verses to process.")
            return

        print(
            f"Generating thematic context for {len(verses)} verse(s) "
            f"using model '{args.model}' and config '{args.config}'"
        )
        inserted = 0
        skipped = 0
        errors = 0

        for idx, (surah, ayah) in enumerate(verses, start=1):
            if not verse_exists(conn, surah, ayah):
                print(f"[{idx}/{len(verses)}] {surah}:{ayah} skipped (not found)")
                skipped += 1
                continue

            if not args.force:
                already = conn.execute(
                    "SELECT 1 FROM verse_thematic_contexts "
                    "WHERE chapter = ? AND verse = ? AND config_id = ?",
                    (surah, ayah, config_id),
                ).fetchone()
                if already:
                    print(f"[{idx}/{len(verses)}] {surah}:{ayah} skipped (already generated)")
                    skipped += 1
                    continue

            print(f"[{idx}/{len(verses)}] {surah}:{ayah} ...", end="", flush=True)
            try:
                prompt, allowed_refs, evidence = build_prompt(conn, surah, ayah)
                raw, elapsed_ms = call_model(
                    args.model,
                    SYSTEM_PROMPT,
                    prompt,
                    temperature=args.temperature,
                )
                payload = _extract_json(raw)
                total_row = conn.execute(
                    "SELECT COUNT(*) AS cnt FROM verses WHERE chapter = ?",
                    (surah,),
                ).fetchone()
                total = total_row["cnt"] if total_row else ayah
                sanitized = sanitize_payload(payload, surah, ayah, allowed_refs, total)

                if args.dry_run:
                    print(" dry-run")
                    continue

                did_insert = upsert_thematic_context(
                    conn,
                    surah,
                    ayah,
                    config_id,
                    sanitized,
                    evidence,
                    raw,
                    elapsed_ms,
                    args.force,
                )
                conn.commit()
                if did_insert:
                    inserted += 1
                    print(" stored")
                else:
                    skipped += 1
                    print(" skipped (exists)")
            except Exception as e:
                conn.rollback()
                errors += 1
                print(f" error: {e}")

        print(
            f"\nDone. inserted={inserted}, skipped={skipped}, errors={errors}, db={DB_PATH}"
        )
    finally:
        conn.close()


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Offline Qur'an-only thematic context generator")
    p.add_argument("--verses", help='Verse spec like "1:1-7,105:1"', default=None)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--config", default=DEFAULT_CONFIG)
    p.add_argument("--prompt-version", default=DEFAULT_PROMPT_VERSION)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--force", action="store_true", help="Overwrite existing rows for this config")
    p.add_argument("--dry-run", action="store_true")
    return p


if __name__ == "__main__":
    run(build_arg_parser().parse_args())
