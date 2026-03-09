"""Offline Surah-so-far context generation using Qur'an text and translation notes.

Generates context answering: "What has happened so far in this surah up to this verse?"
Uses only verses and available AI translation notes from the local database.
"""

import argparse
import json
import re
from collections import defaultdict

from app import _strip_bismillah, get_db
from translate_ai import call_model

DEFAULT_MODEL = "qwen3:14b"
DEFAULT_CONFIG = "surah-context-quran-only-v2-summary"
DEFAULT_PROMPT_VERSION = "v2-summary"

SYSTEM_PROMPT = """\
You are a Qur'an-only context engine.

Task: summarize what has happened so far within the current surah up to the target verse.

Hard constraints:
1) Use only verse/translation/note evidence provided in the prompt.
2) Do NOT use tafsir, hadith, or external historical sources.
3) Do NOT cite verses outside the provided surah window.
4) Output valid JSON only.
"""

MIN_SIGNAL_TO_SHOW = 0.68


def parse_verse_spec(spec: str) -> list[tuple[int, int]]:
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(\d+):(\d+)-(\d+)$", part)
        if m:
            s, a1, a2 = int(m.group(1)), int(m.group(2)), int(m.group(3))
            for a in range(min(a1, a2), max(a1, a2) + 1):
                out.append((s, a))
            continue
        m = re.match(r"^(\d+):(\d+)$", part)
        if m:
            out.append((int(m.group(1)), int(m.group(2))))
    seen = set()
    dedup = []
    for x in out:
        if x not in seen:
            seen.add(x)
            dedup.append(x)
    return dedup


def get_or_create_config(conn, config_name: str, model_name: str, prompt_version: str) -> int:
    row = conn.execute(
        "SELECT id FROM surah_context_configs WHERE config_name = ?",
        (config_name,),
    ).fetchone()
    if row:
        return row["id"]
    conn.execute(
        "INSERT INTO surah_context_configs "
        "(config_name, model_name, prompt_version, methodology_notes) "
        "VALUES (?, ?, ?, ?)",
        (
            config_name,
            model_name,
            prompt_version,
            "Surah-so-far context from Qur'an text + translation notes only.",
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id FROM surah_context_configs WHERE config_name = ?",
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


def _build_blocks(ayah: int, block_size: int = 6) -> list[dict]:
    blocks = []
    start = 1
    while start <= ayah:
        end = min(ayah, start + block_size - 1)
        blocks.append({"start_ayah": start, "end_ayah": end})
        start = end + 1
    return blocks


def _compute_lexical_continuity(conn, surah: int, ayah: int, limit: int = 6) -> list[dict]:
    target_rows = conn.execute(
        "SELECT DISTINCT root_buckwalter, root_arabic "
        "FROM morphology WHERE chapter = ? AND verse = ? "
        "AND root_buckwalter IS NOT NULL AND root_buckwalter != ''",
        (surah, ayah),
    ).fetchall()
    if not target_rows:
        return []

    target_roots = {r["root_buckwalter"]: r["root_arabic"] for r in target_rows}
    prior_rows = conn.execute(
        "SELECT verse, root_buckwalter "
        "FROM morphology WHERE chapter = ? AND verse < ? "
        "AND root_buckwalter IS NOT NULL AND root_buckwalter != ''",
        (surah, ayah),
    ).fetchall()

    occ = defaultdict(int)
    refs = defaultdict(list)
    for r in prior_rows:
        rbw = r["root_buckwalter"]
        if rbw not in target_roots:
            continue
        occ[rbw] += 1
        if len(refs[rbw]) < 3:
            refs[rbw].append(f"{surah}:{r['verse']}")

    items = []
    for rbw, count in occ.items():
        items.append(
            {
                "root_buckwalter": rbw,
                "root_arabic": target_roots.get(rbw, ""),
                "occurrences_before": count,
                "example_refs": refs[rbw],
            }
        )
    items.sort(key=lambda x: -x["occurrences_before"])
    return items[:limit]


def build_prompt(conn, surah: int, ayah: int) -> tuple[str, set[str], dict]:
    rows = conn.execute(
        "SELECT chapter, verse, text_uthmani FROM verses "
        "WHERE chapter = ? AND verse BETWEEN 1 AND ? ORDER BY verse",
        (surah, ayah),
    ).fetchall()
    if not rows:
        raise ValueError(f"Verse {surah}:{ayah} not found")

    evidence_rows = []
    allowed_refs = set()
    note_refs = []
    for r in rows:
        ref = f"{r['chapter']}:{r['verse']}"
        tr, notes = _best_translation_and_notes(conn, r["chapter"], r["verse"])
        if notes.strip():
            note_refs.append(ref)
        evidence_rows.append(
            {
                "ref": ref,
                "arabic": _strip_bismillah(r["text_uthmani"], r["chapter"], r["verse"]),
                "translation": tr,
                "translation_notes": notes,
            }
        )
        allowed_refs.add(ref)

    target_tr = evidence_rows[-1]["translation"] if evidence_rows else ""
    target_notes = evidence_rows[-1]["translation_notes"] if evidence_rows else ""
    prompt = f"""Current surah: {surah}
Target verse: {surah}:{ayah}

Evidence verses from start of surah to target:
{json.dumps(evidence_rows, ensure_ascii=False)}

Return JSON with exactly this shape:
{{
  "summary_so_far": "string",
  "summary_points": [
    {{
      "text": "string",
      "refs": ["surah:ayah", "surah:ayah"]
    }}
  ]
}}

Rules:
- Use only provided evidence.
- `summary_so_far` is the primary output and must be the highest-quality part.
- `summary_so_far` must synthesize the progression up to {surah}:{ayah}, not restate one verse.
- Prefer new synthesis over repeating literal wording already present in translation notes.
- Highlight the major turning points, argumentative shifts, and outcomes established so far.
- Every summary_points item must include refs.
- Prioritize verses with translation_notes where useful.
- Keep claims concrete and evidence-grounded.
"""
    evidence_meta = {
        "surah": surah,
        "target_ayah": ayah,
        "target_ref": f"{surah}:{ayah}",
        "target_translation": target_tr,
        "target_notes": target_notes,
        "evidence_count": len(evidence_rows),
        "note_refs": note_refs,
    }
    if note_refs:
        prompt += f"\nNote-priority refs:\n{json.dumps(note_refs, ensure_ascii=False)}\n"
    return prompt, allowed_refs, evidence_meta


def _extract_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    i = raw.find("{")
    j = raw.rfind("}")
    if i == -1 or j == -1 or j <= i:
        raise ValueError("No JSON object found")
    return json.loads(raw[i : j + 1])


def _norm_ref(ref: str, surah: int, ayah: int) -> str | None:
    if not isinstance(ref, str):
        return None
    m = re.match(r"^\s*(\d+):(\d+)\s*$", ref)
    if not m:
        return None
    s, a = int(m.group(1)), int(m.group(2))
    if s != surah or a < 1 or a > ayah:
        return None
    return f"{s}:{a}"


def _focus_mentions_wrong_verse(focus: str, ayah: int) -> bool:
    m = re.search(r"\bverse\s+(\d+)\b", focus.lower())
    if not m:
        return False
    try:
        mentioned = int(m.group(1))
    except ValueError:
        return False
    return mentioned != ayah


def _tokenize(s: str) -> set[str]:
    return {t for t in re.findall(r"[a-zA-Z]{4,}", (s or "").lower())}


def _jaccard(a: str, b: str) -> float:
    ta = _tokenize(a)
    tb = _tokenize(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


def _is_redundant_focus(focus: str, target_notes: str, target_tr: str) -> bool:
    if not focus.strip():
        return True
    sim_notes = _jaccard(focus, target_notes)
    sim_tr = _jaccard(focus, target_tr)
    return sim_notes >= 0.35 or sim_tr >= 0.40


def _focus_links_prior(focus: str, points: list[dict], target_ref: str) -> bool:
    prior_text = " ".join(
        p.get("text", "") for p in points if isinstance(p, dict) and target_ref not in p.get("refs", [])
    )
    if not prior_text.strip():
        return True
    return len(_tokenize(focus) & _tokenize(prior_text)) >= 2


def _synthesized_additive_focus(points: list[dict], surah: int, ayah: int, target_ref: str) -> str:
    prior_points = [p for p in points if isinstance(p, dict) and target_ref not in p.get("refs", [])]
    if prior_points:
        prior = prior_points[-1].get("text", "").strip().rstrip(".")
        if prior:
            return (
                f"After {prior.lower()}, {surah}:{ayah} turns that pattern into an explicit outcome: "
                "God's promise to His messengers is realized through rescue, while excess leads to collapse."
            )
    return (
        f"In {surah}:{ayah}, the verse advances the surah's argument by converting earlier warnings "
        "into an explicit rule of outcome: rescue for those upheld by God, and ruin for persistent excess."
    )


def _claim_supported(text: str, refs: list[str], evidence_lookup: dict[str, dict]) -> bool:
    claim_tokens = _tokenize(text)
    if not claim_tokens:
        return False
    evidence_text = []
    for ref in refs:
        row = evidence_lookup.get(ref)
        if not row:
            continue
        evidence_text.append(row.get("translation", ""))
        evidence_text.append(row.get("translation_notes", ""))
    ev_tokens = _tokenize(" ".join(evidence_text))
    if not ev_tokens:
        return False
    overlap = len(claim_tokens & ev_tokens)
    return overlap >= 2


def sanitize(payload: dict, surah: int, ayah: int, allowed_refs: set[str], evidence_meta: dict) -> dict:
    summary = str(payload.get("summary_so_far", "")).strip()[:2400]
    points_raw = payload.get("summary_points", [])
    if not isinstance(points_raw, list):
        points_raw = []
    points = []
    for p in points_raw[:8]:
        if not isinstance(p, dict):
            continue
        text = str(p.get("text", "")).strip()[:500]
        refs = []
        for ref in p.get("refs", []):
            nr = _norm_ref(ref, surah, ayah)
            if nr and nr in allowed_refs:
                refs.append(nr)
        if text and refs:
            points.append({"text": text, "refs": refs[:4]})

    if not summary and points:
        summary = " ".join(p["text"] for p in points[:5])[:2400]
    summary = summary[:2400]

    return {
        "summary_so_far": summary,
        "current_verse_focus": "",
        "current_verse_focus_refs_json": "[]",
        "key_verses_json": "[]",
        "summary_points_json": json.dumps(points, ensure_ascii=False),
        "blocks_json": "[]",
        "lexical_continuity_json": "[]",
    }


def verify_and_score(sanitized: dict, evidence_meta: dict) -> tuple[float, dict]:
    try:
        points = json.loads(sanitized.get("summary_points_json", "[]"))
    except Exception:
        points = []

    score = 0.0
    report = {"checks": {}}
    summary = sanitized.get("summary_so_far", "")
    report["checks"]["has_summary"] = bool(summary and len(summary) >= 180)
    report["checks"]["has_summary_points"] = len(points) >= 3
    if report["checks"]["has_summary"]:
        score += 0.35
    if report["checks"]["has_summary_points"]:
        score += 0.2

    # Citation quality on summary points
    cited_points = 0
    point_refs: set[str] = set()
    for p in points[:8]:
        refs = p.get("refs", []) if isinstance(p, dict) else []
        txt = p.get("text", "") if isinstance(p, dict) else ""
        if refs and txt:
            cited_points += 1
            point_refs.update(r for r in refs if isinstance(r, str))
    report["checks"]["cited_points"] = cited_points
    if cited_points:
        score += min(0.2, cited_points * 0.04)

    # Note-priority coverage from cited summary points
    note_refs = set(evidence_meta.get("note_refs", []))
    if note_refs and point_refs:
        overlap = len(point_refs & note_refs) / max(1, len(point_refs))
        score += min(0.15, overlap * 0.15)
    report["checks"]["note_ref_overlap"] = round(len(point_refs & note_refs), 3) if note_refs else 0

    # Ensure the target verse is represented in cited points.
    target_ref = evidence_meta.get("target_ref")
    report["checks"]["points_hit_target"] = target_ref in point_refs
    if report["checks"]["points_hit_target"]:
        score += 0.1

    # Penalize summary that just mirrors target-verse wording.
    target_notes = str(evidence_meta.get("target_notes", ""))
    target_tr = str(evidence_meta.get("target_translation", ""))
    summary_too_close = _is_redundant_focus(summary, target_notes, target_tr)
    report["checks"]["summary_not_restatement"] = not summary_too_close
    if not summary_too_close:
        score += 0.1

    score = max(0.0, min(1.0, score))
    report["signal_score"] = round(score, 3)
    return score, report


def upsert(
    conn,
    surah: int,
    ayah: int,
    config_id: int,
    sanitized: dict,
    signal_score: float,
    verifier_report: dict,
    evidence: dict,
    raw: str,
    elapsed_ms: int,
    force: bool,
) -> bool:
    existing = conn.execute(
        "SELECT id FROM verse_surah_contexts WHERE chapter = ? AND verse = ? AND config_id = ?",
        (surah, ayah, config_id),
    ).fetchone()
    if existing and not force:
        return False
    if existing and force:
        conn.execute(
            "DELETE FROM verse_surah_contexts WHERE chapter = ? AND verse = ? AND config_id = ?",
            (surah, ayah, config_id),
        )
    conn.execute(
        "INSERT INTO verse_surah_contexts ("
        "chapter, verse, config_id, summary_so_far, current_verse_focus, key_verses_json, "
        "summary_points_json, lexical_continuity_json, signal_score, verifier_report_json, "
        "evidence_json, raw_response, model_response_time_ms"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            surah,
            ayah,
            config_id,
            sanitized["summary_so_far"],
            sanitized["current_verse_focus"],
            sanitized["key_verses_json"],
            sanitized["summary_points_json"],
            sanitized["lexical_continuity_json"],
            signal_score,
            json.dumps(verifier_report, ensure_ascii=False),
            json.dumps(evidence, ensure_ascii=False),
            raw,
            elapsed_ms,
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
        print(f"Generating surah context for {len(verses)} verse(s) with model '{args.model}'")
        for i, (s, a) in enumerate(verses, start=1):
            if not args.force:
                already = conn.execute(
                    "SELECT 1 FROM verse_surah_contexts WHERE chapter = ? AND verse = ? AND config_id = ?",
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
                payload = _extract_json(raw)
                sanitized = sanitize(payload, s, a, allowed_refs, evidence)
                signal_score, verifier = verify_and_score(sanitized, evidence)
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
                    evidence,
                    raw,
                    elapsed,
                    args.force,
                )
                conn.commit()
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
    p = argparse.ArgumentParser(description="Generate Surah-so-far context")
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
