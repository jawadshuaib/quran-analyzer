#!/usr/bin/env python3
"""Q&A video pipeline — offline builder CLI + the airtight-gate self-test.

Subcommands:
  candidates [--limit N]        list rated-5 Q&A not yet built into videos
  build --fixture PATH          compile a structured script -> payload, run
                                Gate A (punchiness) + Gate B (match), persist
                                a qa_videos row + the payload JSON
  gate  --payload P --intent I  re-run Gate B on an existing payload+intent
  selftest [--no-renderer]      PROVE Gate B catches planted highlight
                                mismatches (the operator's #1 concern)

Phase 0: composes existing slide types (verse-flow + outro), no LLM spend
by default. The LLM punchiness panel is opt-in (build --llm).
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import sys

import qa_video_common as C
import qa_video_compile as CO
import qa_video_match_gate as MG
import qa_video_punch_gate as PG
import qa_video_pipeline as PL
import qa_video_script as SC

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "qa_videos")


def _node_available() -> bool:
    return shutil.which("node") is not None


def _refs_in_script(script: dict) -> list[str]:
    refs = []
    if script.get("anchor_ref"):
        refs.append(script["anchor_ref"])
    for b in script.get("beats") or []:
        if not isinstance(b, dict):
            continue
        ver = b.get("verse")
        if isinstance(ver, dict) and ver.get("ref"):
            refs.append(ver["ref"])
    # de-dup, keep order
    seen, out = set(), []
    for r in refs:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


# ---------------------------------------------------------------------------
#  candidates
# ---------------------------------------------------------------------------

def cmd_candidates(args) -> int:
    conn = C.get_conn()
    try:
        rows = PL.sample_candidates(conn, limit=args.limit)
    finally:
        conn.close()
    print(f"{len(rows)} rated-5 candidate(s) not yet built:\n")
    for r in rows:
        flag = " [needs_voice_revision]" if r["needs_voice_revision"] else ""
        print(f"  qa_id={r['qa_id']:>5}  {r['anchor_ref']:>8}  [{r['category']}]"
              f"  refs={r['cited_refs']}{flag}")
        print(f"      Q: {r['question'][:110]}")
    return 0


# ---------------------------------------------------------------------------
#  build
# ---------------------------------------------------------------------------

def fetch_qa(conn, qa_id: int) -> dict | None:
    r = conn.execute(
        "SELECT id, page_key, question, answer, generation_meta "
        "FROM assistant_conversations WHERE id=?", (qa_id,)).fetchone()
    if not r:
        return None
    try:
        meta = json.loads(r["generation_meta"] or "{}")
    except Exception:
        meta = {}
    return {
        "qa_id": r["id"], "anchor_ref": r["page_key"],
        "question": r["question"], "answer": r["answer"],
        "cited_refs": meta.get("cited_refs") or [],
    }


def cmd_context(args) -> int:
    """Dump everything a script writer (a Claude agent / Routine) needs for
    one Q&A: the question, the answer, and each candidate verse's numbered
    display tokens + translation. The writer copies exact tokens from here."""
    conn = C.get_conn()
    try:
        qa = fetch_qa(conn, args.qa_id)
        if not qa:
            print(f"qa_id {args.qa_id} not found")
            return 2
        ctx = SC.build_context(conn, qa["anchor_ref"], qa.get("cited_refs") or [])
        print(f"qa_id: {qa['qa_id']}\nanchor_ref: {qa['anchor_ref']}\n")
        print(f"QUESTION:\n{qa['question']}\n")
        print(f"ANSWER:\n{qa['answer']}\n")
        print("VERSES YOU MAY SHOW (copy highlight_words_ar EXACTLY from these "
              "tokens; highlight_phrase_en must be a verbatim substring of the ENGLISH):\n")
        print(SC._format_context(ctx))
        # The consolidator: everything else the corpus knows about this verse
        # (exegesis, pre-Islamic poetry, root lexicon, cognates). The writer
        # draws on whatever is most powerful — never beyond it.
        enr = SC.build_enrichment(conn, qa["anchor_ref"])
        if any(enr.get(k) for k in ("exegesis", "poetry_note", "departure_notes", "roots")):
            print("\nENRICHMENT (optional source material — use what is most "
                  "powerful, never fabricate beyond it):")
            print(json.dumps(enr, ensure_ascii=False, indent=1))
        return 0
    finally:
        conn.close()


def cmd_gate(args) -> int:
    """Validate a script JSON file: compile -> Gate A + Gate B -> report,
    optionally persist. The deterministic validator a Claude-written script
    is checked against."""
    with open(args.script, encoding="utf-8") as f:
        script = json.load(f)
    conn = C.get_conn()
    try:
        return _gate_and_report(conn, script, llm=args.llm,
                                no_renderer=args.no_renderer, persist=args.persist)
    finally:
        conn.close()


def gate_script(conn, script, *, use_renderer: bool = True) -> dict:
    """Structured, non-printing gate run for programmatic callers — the
    admin inline-edit endpoint re-validates every human edit through the
    SAME fail-closed gates the original draft passed. Returns a dict:
    {ok, issues[], gate_a, gate_b, payload, match_snapshot}."""
    cited = _refs_in_script(script)
    try:
        payload, intent = CO.compile_payload(conn, script)
    except CO.CompileError as e:
        return {
            "ok": False,
            "issues": [f"compile: {e}"],
            "gate_a": None, "gate_b": None,
            "payload": None, "match_snapshot": None,
        }
    gate_a = PG.run(conn, script, payload, cited_refs=cited, llm=False)
    use_rend = _node_available() and use_renderer
    gate_b = MG.run(conn, payload, intent, cited_refs=cited, use_renderer=use_rend)
    issues = (
        [f"punchiness: {x}" for x in gate_a["precheck"]["issues"]]
        + [f"match: {x}" for x in gate_b["issues"]]
    )
    return {
        "ok": bool(gate_a["ok"] and gate_b["ok"]),
        "issues": issues,
        "gate_a": gate_a,
        "gate_b": gate_b,
        "payload": payload,
        "match_snapshot": gate_b.get("snapshot"),
    }


def _gate_and_report(conn, script, *, llm, no_renderer, persist) -> int:
    """Compile -> Gate A -> Gate B -> print -> optionally persist. Shared by
    `build` (from a fixture) and `from-qa` (LLM-compressed)."""
    cited = _refs_in_script(script)
    try:
        payload, intent = CO.compile_payload(conn, script)
    except CO.CompileError as e:
        print(f"COMPILE FAILED: {e}")
        return 2

    gate_a = PG.run(conn, script, payload, cited_refs=cited, llm=llm)
    use_rend = _node_available() and not no_renderer
    gate_b = MG.run(conn, payload, intent, cited_refs=cited, use_renderer=use_rend)

    print(f"\n=== {script.get('anchor_ref')} — {script.get('title','')} ===")
    pre = gate_a["precheck"]
    print(f"Gate A (punchiness): ok={gate_a['ok']}  "
          f"words={pre['word_count']} (~{pre['est_duration_sec']}s) verses={pre['verse_slides']}")
    for x in pre["issues"]:
        print(f"   A! {x}")
    if gate_a.get("panel"):
        print(f"   panel: {json.dumps(gate_a['panel']['verdicts'])}")
    print(f"Gate B (match):      ok={gate_b['ok']}  renderer={'on' if use_rend else 'OFF'}")
    for x in gate_b["issues"]:
        print(f"   B! {x}")
    if gate_b.get("report"):
        for s in gate_b["report"]["slides"]:
            if s.get("highlighted"):
                print(f"   renderer paints {s['surah']}:{s['ayah']} -> "
                      f"idx {s['paintedIndices']} tokens {s['paintedTokens']} "
                      f"(english_found={s['englishFound']})")

    ok = gate_a["ok"] and gate_b["ok"]
    status = "gate_passed" if ok else (
        "rejected_match" if not gate_b["ok"] else "rejected_uninteresting")

    if persist:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        ppath = os.path.join(OUTPUT_DIR, f"{script.get('qa_id', 0)}.payload.json")
        with open(ppath, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        PL.upsert_video(
            conn, qa_id=int(script.get("qa_id") or 0),
            anchor_ref=script.get("anchor_ref") or "",
            theme=script.get("theme"), title=script.get("title"),
            script_json=json.dumps(script, ensure_ascii=False),
            payload_json=json.dumps(payload, ensure_ascii=False),
            match_snapshot=json.dumps(gate_b["snapshot"], ensure_ascii=False),
            punch_ok=1 if gate_a["ok"] else 0,
            punch_report=json.dumps(gate_a, ensure_ascii=False),
            match_ok=1 if gate_b["ok"] else 0,
            match_report=json.dumps({"issues": gate_b["issues"]}, ensure_ascii=False),
            status=status,
        )
        print(f"\npersisted: status={status}  payload={ppath}")

    print(f"\nRESULT: {'PASS — eligible for review' if ok else 'BLOCKED'}")
    return 0 if ok else 1


def cmd_build(args) -> int:
    with open(args.fixture, encoding="utf-8") as f:
        script = json.load(f)
    conn = C.get_conn()
    try:
        return _gate_and_report(conn, script, llm=args.llm,
                                no_renderer=args.no_renderer, persist=args.persist)
    finally:
        conn.close()


def cmd_from_qa(args) -> int:
    conn = C.get_conn()
    try:
        qa = fetch_qa(conn, args.qa_id)
        if not qa:
            print(f"qa_id {args.qa_id} not found")
            return 2
        print(f"Compressing qa_id={qa['qa_id']} ({qa['anchor_ref']}) with {args.model or SC._DEFAULT_MODEL}…")
        script, hint = None, ""
        for attempt in range(2):  # generate, then one repair pass
            try:
                cand = SC.generate_script(conn, qa, model=args.model, repair_hint=hint)
            except SC.ScriptGenError as e:
                print(f"  attempt {attempt+1}: generation error: {e}")
                hint = str(e)
                continue
            script = cand
            try:
                CO.compile_payload(conn, cand)  # probe; the real run is in _gate_and_report
                break
            except CO.CompileError as e:
                hint = str(e)
                print(f"  attempt {attempt+1} needs repair: {e}")
        if script is None:
            print("script generation failed")
            return 2
        print(json.dumps(script, ensure_ascii=False, indent=2))
        return _gate_and_report(conn, script, llm=args.llm,
                                no_renderer=args.no_renderer, persist=args.persist)
    finally:
        conn.close()


def _diverse_candidate_ids(conn, limit: int) -> list[int]:
    """Evenly spread `limit` rated-5 verse Q&A across the whole pool (by id,
    which tracks surah order), excluding any already built — so a quality
    gauge isn't dominated by one surah's recent sweep."""
    PL.ensure_tables(conn)
    rows = conn.execute(
        "SELECT id FROM assistant_conversations "
        "WHERE source='ai' AND quality_score=5.0 AND page_type='verse' "
        "  AND COALESCE(hidden,0)=0 AND id NOT IN (SELECT qa_id FROM qa_videos) "
        "ORDER BY id"
    ).fetchall()
    ids = [r["id"] for r in rows]
    if len(ids) <= limit:
        return ids
    step = len(ids) / limit
    return [ids[int(i * step)] for i in range(limit)]


def cmd_batch(args) -> int:
    """Compress + gate a diverse sample of rated-5 Q&A (free, local Ollama).
    Journals each result to reviews/qa_video_batch.jsonl and prints a yield
    + block-reason summary so the editorial bar can be judged."""
    conn = C.get_conn()
    journal = os.path.join(os.path.dirname(__file__), "reviews", "qa_video_batch.jsonl")
    os.makedirs(os.path.dirname(journal), exist_ok=True)
    use_rend = _node_available() and not args.no_renderer
    try:
        ids = _diverse_candidate_ids(conn, args.limit)
        print(f"batch: {len(ids)} candidates, model={args.model or SC._DEFAULT_MODEL}, "
              f"renderer={'on' if use_rend else 'OFF'}", flush=True)
        results = []
        for n, qid in enumerate(ids, 1):
            qa = fetch_qa(conn, qid)
            rec = {"qa_id": qid, "anchor_ref": qa["anchor_ref"] if qa else None}
            try:
                script, hint = None, ""
                for attempt in range(2):
                    cand = SC.generate_script(conn, qa, model=args.model, repair_hint=hint)
                    script = cand
                    try:
                        payload, intent = CO.compile_payload(conn, cand)
                        break
                    except CO.CompileError as e:
                        hint = str(e)
                        payload = None
                if payload is None:
                    payload, intent = CO.compile_payload(conn, script)  # raise for the record
                cited = _refs_in_script(script)
                ga = PG.run(conn, script, payload, cited_refs=cited, llm=False)
                gb = MG.run(conn, payload, intent, cited_refs=cited, use_renderer=use_rend)
                ok = ga["ok"] and gb["ok"]
                rec.update({
                    "ok": ok, "title": script.get("title"), "theme": script.get("theme"),
                    "words": ga["precheck"]["word_count"], "est_sec": ga["precheck"]["est_duration_sec"],
                    "gate_a_ok": ga["ok"], "gate_b_ok": gb["ok"],
                    "issues": (ga["precheck"]["issues"] + gb["issues"])[:6],
                    "status": "gate_passed" if ok else ("rejected_match" if not gb["ok"] else "rejected_uninteresting"),
                    "script": script,
                })
            except (SC.ScriptGenError, CO.CompileError) as e:
                rec.update({"ok": False, "status": "build_error", "issues": [str(e)]})
            except Exception as e:  # ollama/network/etc — keep going
                rec.update({"ok": False, "status": "error", "issues": [str(e)[:200]]})
            results.append(rec)
            with open(journal, "a", encoding="utf-8") as jf:
                jf.write(json.dumps(rec, ensure_ascii=False) + "\n")
            mark = "PASS" if rec.get("ok") else rec.get("status")
            print(f"[{n}/{len(ids)}] {rec['anchor_ref']:>8}  {mark:>22}  "
                  f"{rec.get('words','?')}w  {rec.get('title','')[:70]}", flush=True)

        npass = sum(1 for r in results if r.get("ok"))
        from collections import Counter
        reasons = Counter(r["status"] for r in results if not r.get("ok"))
        print("\n" + "=" * 70)
        print(f"YIELD: {npass}/{len(results)} passed BOTH gates "
              f"({100*npass/max(1,len(results)):.0f}%)")
        print(f"blocked: {dict(reasons)}")
        print(f"journal: {journal}")
        return 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
#  selftest — the planted-mismatch proof
# ---------------------------------------------------------------------------

def _payload_for(conn, ref, *, indices, forms, phrase=None, arabic=None, narr="test."):
    """Hand-craft a single-verse-flow payload + intent (for crafting both
    correct and deliberately-broken cases)."""
    c, v = C.parse_ref(ref)
    vd = C.verse_data(conn, c, v)
    arabic_text = arabic if arabic is not None else C.display_arabic(vd["arabic_raw"], c, v)
    slide = {
        "type": "verse-flow", "durationSec": 6, "surah": c, "ayah": v,
        "arabicText": arabic_text, "translation": vd["translation"],
        "highlightWordIndices": indices, "narration": {"text": narr},
    }
    if phrase:
        slide["highlightTranslationText"] = phrase
    intent = [{
        "surah": c, "ayah": v, "indices": indices,
        "skeletons": sorted({C.normalize_ar(f) for f in forms}),
        "forms": forms, "phrase": phrase or "",
    }, None]
    payload = {"slides": [slide, CO._outro_slide()], "videoId": "selftest", "title": "selftest"}
    return payload, intent


def cmd_selftest(args) -> int:
    conn = C.get_conn()
    use_rend = _node_available() and not args.no_renderer
    print(f"Gate B self-test — renderer self-report (Layer 2): "
          f"{'ON' if use_rend else 'OFF (node not found / disabled) — Layer 1 only'}\n")

    results = []  # (name, expected_ok, actual_ok, detail)

    def check(name, expected_ok, payload, intent, cited=None):
        rep = MG.run(conn, payload, intent, cited_refs=cited, use_renderer=use_rend)
        ok = rep["ok"]
        passed = (ok == expected_ok)
        results.append((name, expected_ok, ok, passed, rep["issues"][:3]))
        mark = "PASS" if passed else "XXXX FAIL"
        print(f"[{mark}] {name}")
        print(f"        expected gate_ok={expected_ok}, got={ok}")
        for x in rep["issues"][:3]:
            print(f"          - {x}")

    try:
        # --- POSITIVE: the real 39:42 fixture compiles + passes ---
        with open(os.path.join(os.path.dirname(__file__), "qa_video_fixtures", "39_42.json"),
                  encoding="utf-8") as f:
            script = json.load(f)
        payload, intent = CO.compile_payload(conn, script)
        check("39:42 fixture (correct)", True, payload, intent, _refs_in_script(script))

        # --- NEGATIVE: index off-by-one (lights the wrong word) ---
        bad = copy.deepcopy(payload)
        bad["slides"][0]["highlightWordIndices"] = [3]   # was [2] (yatawaffā)
        check("39:42 index +1 (wrong word lit)", False, bad, copy.deepcopy(intent))

        # --- NEGATIVE: English phrase not a substring (silent pill) ---
        bad = copy.deepcopy(payload)
        bad["slides"][0]["highlightTranslationText"] = "a phrase that is not in the translation"
        check("39:42 phantom English phrase", False, bad, copy.deepcopy(intent))

        # --- NEGATIVE: out-of-range index ---
        bad = copy.deepcopy(payload)
        bad["slides"][0]["highlightWordIndices"] = [99]
        check("39:42 out-of-range index", False, bad, copy.deepcopy(intent))

        # --- BASMALA BUCKET (the 95:1/96:1 class) ---
        c, v = 96, 1
        vd = C.verse_data(conn, c, v)
        # POSITIVE: correctly basmala-stripped, index 1 -> اقرأ
        p_ok, i_ok = _payload_for(conn, "96:1", indices=[1], forms=["اقْرَأْ"])
        check("96:1 basmala-stripped (correct)", True, p_ok, i_ok)
        # NEGATIVE: un-stripped arabicText (the latent bug) -> index 1 lights the basmala
        p_bad, i_bad = _payload_for(conn, "96:1", indices=[1], forms=["اقْرَأْ"],
                                    arabic=C.strip_uthmani_marks(vd["arabic_raw"]))  # no bismillah strip
        check("96:1 basmala NOT stripped (offset bug)", False, p_bad, i_bad)

        # --- ORTHOGRAPHIC BUCKET (37:130 'إِلْ يَاسِينَ') ---
        # POSITIVE: surface-form resolution lands on whitespace token 4 (يَاسِينَ)
        sc = {"qa_id": 0, "anchor_ref": "37:130", "title": "Who is named here?",
              "beats": [{"kind": "set", "narration": "A name appears, split across two written words.",
                         "verse": {"ref": "37:130", "highlight_words_ar": ["يَاسِينَ"]}}]}
        p_o, i_o = CO.compile_payload(conn, sc)
        check("37:130 name via surface form (correct)", True, p_o, i_o)
        # NEGATIVE: naive morphology word_pos=3 lights 'إِلْ', not the name
        p_bad, i_bad = _payload_for(conn, "37:130", indices=[3], forms=["يَاسِينَ"])
        check("37:130 naive word_pos=3 (orthographic bug)", False, p_bad, i_bad)

        print("\n" + "=" * 60)
        n_pass = sum(1 for *_, passed, _ in results if passed)
        for name, exp, got, passed, _ in results:
            print(f"  {'ok ' if passed else 'BAD'}  {name}")
        print(f"\n{n_pass}/{len(results)} self-test expectations met.")
        all_ok = n_pass == len(results)
        print("GATE B SELF-TEST: " + ("PASS — catches every planted mismatch" if all_ok else "FAILED"))
        return 0 if all_ok else 1
    finally:
        conn.close()


def main() -> int:
    ap = argparse.ArgumentParser(description="Q&A video pipeline (Phase 0)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("candidates"); p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_candidates)

    p = sub.add_parser("build")
    p.add_argument("--fixture", required=True)
    p.add_argument("--no-renderer", action="store_true")
    p.add_argument("--llm", action="store_true", help="run the LLM punchiness panel (costs)")
    p.add_argument("--persist", action="store_true", help="write the qa_videos row + payload")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("from-qa", help="LLM-compress a rated-5 Q&A into a script, then gate it")
    p.add_argument("--qa-id", type=int, required=True)
    p.add_argument("--model", default=None, help="Ollama model (default qwen3:14b)")
    p.add_argument("--no-renderer", action="store_true")
    p.add_argument("--llm", action="store_true", help="also run the LLM punchiness panel")
    p.add_argument("--persist", action="store_true")
    p.set_defaults(func=cmd_from_qa)

    p = sub.add_parser("context", help="dump Q&A + verse tokens for a script writer (Claude/Routine)")
    p.add_argument("--qa-id", type=int, required=True)
    p.set_defaults(func=cmd_context)

    p = sub.add_parser("gate", help="validate a script JSON file through both gates")
    p.add_argument("--script", required=True)
    p.add_argument("--no-renderer", action="store_true")
    p.add_argument("--llm", action="store_true")
    p.add_argument("--persist", action="store_true")
    p.set_defaults(func=cmd_gate)

    p = sub.add_parser("batch", help="compress+gate a diverse sample of rated-5 Q&A (free, local)")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--model", default=None)
    p.add_argument("--no-renderer", action="store_true")
    p.set_defaults(func=cmd_batch)

    p = sub.add_parser("selftest"); p.add_argument("--no-renderer", action="store_true")
    p.set_defaults(func=cmd_selftest)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
