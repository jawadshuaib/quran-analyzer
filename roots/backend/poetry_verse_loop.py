#!/usr/bin/env python3
"""Scale the verse-level "In Pre-Islamic Poetry" notes, drafted by a LOCAL model.

WHY LOCAL. The 60 root-level comparisons and the first 23 verse notes were written
by Claude Code on subscription tokens. Scaling to a four-figure queue on those
tokens is not affordable, and the work is well-bounded: every poetic line the
note may cite is already indexed, authenticated and tier-graded in the database,
so the model is composing an argument over supplied evidence rather than
recalling anything. That is the shape of task a good local model can carry.

MODEL CHOICE IS MEASURED, NOT ASSUMED. Each local model drafted the held-out
2:197 brief, whose Claude-written note is already human-approved, and then judged
four verses of known character (two load-bearing, two incidental):

    model                 prose        cited real lines   knew when NOT to write
    muse-glimmer:30b      cleanest     yes (2/2)          4/4            <- drafter
    gpt-oss:20b           leaked the   yes (2/2)          not tested     <- judge
                          rubric's section headers
    qwen3:14b             sermonising  NO - cited none    not tested     rejected

qwen3 is disqualified outright: it wrote "as seen in the line below" and then
cited nothing, which is fatal for a feature whose entire point is the quotation.
gpt-oss judges rather than drafts - a different family from the drafter, so the
review is not the drafter marking its own homework.

THE SKIP GATE IS THE HEART OF THIS. The candidate pool is dominated by ubiquitous
roots: rbb alone occurs in 871 verses, almost always as the ordinary divine title,
where a note could only restate the root-level verdict any other verse would carry
equally well. Two defences: verses whose root is ubiquitous (> ROOT_VERSE_CAP
verses) are never queued at all, and every survivor must still pass the model's
own "is a note warranted here?" judgement before anything is drafted. Declining is
the expected answer, not a failure.

Nothing here publishes. Every note lands review_status='pending' for the admin
queue, exactly as the Claude-drafted ones did.

Usage:
  python3 poetry_verse_loop.py stats                 # queue depth + yield so far
  python3 poetry_verse_loop.py tick --count 5        # one paced tick
  python3 poetry_verse_loop.py run --count 5 --sleep 60   # continuous, resumable
  python3 poetry_verse_loop.py show <ref>            # what got stored
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "data", "quran.db")
sys.path.insert(0, HERE)
from poetry_gen import _enrich_quotes, POST_QURANIC  # noqa: E402

DRAFTER = "muse-glimmer:30b-mlx"
JUDGE = "gpt-oss:20b"
OLLAMA = "http://localhost:11434/api/generate"

# A root in more verses than this is ubiquitous (rbb 871, Amn 723, kfr 465...).
# Its occurrences are overwhelmingly incidental and a note under each would be
# the same note 800 times. Excluded from the queue entirely.
ROOT_VERSE_CAP = 120

MIN_WORDS, MAX_WORDS = 90, 320

SKIP_DDL = """
CREATE TABLE IF NOT EXISTS poetry_verse_skipped (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
    page_key TEXT NOT NULL,
    focus_root_buckwalter TEXT,
    reason TEXT,
    model_used TEXT,
    at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chapter, verse)
);
"""


def get_conn():
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.executescript(SKIP_DDL)
    return conn


# ---------------------------------------------------------------- the queue

def candidates(conn, limit=None):
    """Verses still owed a note, best-first.

    Ordering is the whole curation strategy: a verse earns its place by using a
    RARE form of the root (a lemma confined to a handful of verses is where the
    root is doing something particular) and by the root itself being uncommon
    enough that this verse is not one of hundreds telling the same story.
    """
    rows = conn.execute(
        """
        WITH cand AS (
          SELECT DISTINCT m.chapter c, m.verse v, m.root_buckwalter rb, m.lemma_buckwalter lb
          FROM morphology m
          JOIN root_poetry_comparisons rpc ON rpc.root_buckwalter = m.root_buckwalter
          WHERE rpc.review_status='approved' AND rpc.hidden=0
        ),
        rootfreq AS (SELECT rb, COUNT(DISTINCT c||':'||v) vn FROM cand GROUP BY rb),
        lemfreq  AS (SELECT rb, lb, COUNT(DISTINCT c||':'||v) ln FROM cand
                     WHERE lb IS NOT NULL GROUP BY rb, lb),
        -- only roots with authenticated evidence can support a note at all
        ab AS (SELECT DISTINCT plr.root_buckwalter rb FROM poetry_line_roots plr
               JOIN poetry_lines pl ON pl.id=plr.line_id
               JOIN poetry_poems pp ON pp.id=pl.poem_id
               WHERE pp.auth_tier IN ('A','B'))
        SELECT cand.c, cand.v, cand.rb, rootfreq.vn, COALESCE(lemfreq.ln, 9999) ln
        FROM cand
        JOIN rootfreq ON rootfreq.rb = cand.rb
        JOIN ab ON ab.rb = cand.rb
        LEFT JOIN lemfreq ON lemfreq.rb = cand.rb AND lemfreq.lb = cand.lb
        WHERE rootfreq.vn <= ?
          AND NOT EXISTS (SELECT 1 FROM verse_poetry_notes n
                          WHERE n.chapter=cand.c AND n.verse=cand.v)
          AND NOT EXISTS (SELECT 1 FROM poetry_verse_skipped s
                          WHERE s.chapter=cand.c AND s.verse=cand.v)
        GROUP BY cand.c, cand.v
        ORDER BY MIN(COALESCE(lemfreq.ln, 9999)) ASC, rootfreq.vn ASC, cand.c, cand.v
        """,
        (ROOT_VERSE_CAP,),
    ).fetchall()
    out = [{"ref": f"{r['c']}:{r['v']}", "chapter": r["c"], "verse": r["v"],
            "focus_root": r["rb"], "root_verses": r["vn"], "lemma_verses": r["ln"]}
           for r in rows]
    return out[:limit] if limit else out


def brief(conn, ref, root_bw, max_lines=16):
    """The drafting brief: this verse, where the root sits in it, the approved
    root-level verdict, and the authenticated lines available to quote."""
    c, v = (int(x) for x in ref.split(":"))
    vt = conn.execute("SELECT text_uthmani FROM verses WHERE chapter=? AND verse=?", (c, v)).fetchone()
    tr = conn.execute("SELECT text_en FROM translations WHERE chapter=? AND verse=?", (c, v)).fetchone()
    ra = conn.execute("SELECT root_arabic FROM morphology WHERE root_buckwalter=? "
                      "AND root_arabic IS NOT NULL LIMIT 1", (root_bw,)).fetchone()
    rc = conn.execute("""SELECT shift_type, continuity, quran_usage_summary, poetry_usage_summary
                         FROM root_poetry_comparisons WHERE root_buckwalter=?""", (root_bw,)).fetchone()
    words = conn.execute("""SELECT word_pos, form_arabic, tag FROM morphology
                            WHERE chapter=? AND verse=? AND root_buckwalter=?
                            ORDER BY word_pos""", (c, v, root_bw)).fetchall()
    occ = conn.execute(
        """SELECT plr.id lrid, plr.surface_word, plr.sense_hint, pp.poet, pp.auth_tier, pl.text_plain
           FROM poetry_line_roots plr
           JOIN poetry_lines pl ON pl.id=plr.line_id
           JOIN poetry_poems pp ON pp.id=pl.poem_id
           WHERE plr.root_buckwalter=? AND pp.auth_tier IN ('A','B')
           ORDER BY pp.auth_tier ASC, plr.confidence DESC LIMIT ?""", (root_bw, max_lines)).fetchall()

    L = [f"# Verse-note brief — {ref}  (focus root {ra['root_arabic'] if ra else ''} / {root_bw})\n",
         "## This verse"]
    if vt:
        L.append(f"Arabic: {vt['text_uthmani']}")
    if tr:
        L.append(f"Translation: {tr['text_en']}")
    L.append("\n## Where the root actually sits in this verse")
    for w in words:
        L.append(f"  word {w['word_pos']}: {w['form_arabic']} ({w['tag']})")
    L.append(f"\n## Approved root-level verdict for {root_bw} — be consistent with it; "
             "the verse note is MORE SPECIFIC than this")
    if rc:
        L.append(f"Verdict: {'continuity' if rc['continuity'] else rc['shift_type']}")
        L.append(f"Qur'an usage: {rc['quran_usage_summary']}")
        L.append(f"Poetry usage: {rc['poetry_usage_summary']}")
    L.append(f"\n## Authenticated (Tier A/B) lines for {root_bw} — the ONLY lines you may quote")
    cur = None
    for o in occ:
        if o["auth_tier"] != cur:
            cur = o["auth_tier"]
            L.append(f"\n-- Tier {cur} --")
        L.append(f"  [lr:{o['lrid']}] «{o['surface_word']}» ({o['sense_hint']}) — "
                 f"{o['poet']}: {o['text_plain']}")
    return "\n".join(L)


# ------------------------------------------------------------ the model calls

DRAFT_SYSTEM = """You write short scholarly notes for a Qur'an study site, in a section titled
"In Pre-Islamic Poetry" that sits under a single verse. A note shows how a root in that verse
was used in 6th-century Arabian poetry, as external evidence for what the word meant then.

FIRST, JUDGE WHETHER A NOTE IS WARRANTED AT ALL.
Warranted only when the root does real work in THIS verse AND the poetic evidence tells the
reader something they could not get from the verse alone. NOT warranted when the root is an
ordinary incidental word here and a note would merely restate the general root-level verdict
that any other verse could carry equally well. Most occurrences of a common root are
incidental. Declining is the correct, expected answer - it is not a failure.

If not warranted: {"skip": true, "reason": "<one sentence>"}

If warranted, write the note in THREE MOVEMENTS, 110-260 words total, as flowing prose with
NO headings and NO labels (never write "ON-RAMP" or "THIS VERSE" in the output):
1. A warm 1-2 sentence on-ramp establishing the pre-Islamic cultural motif for a reader with
   NO background - the world the word lived in. Tailor it to this root's own theme. Never
   open by assuming the reader already knows the comparison.
2. What the Qur'an does with that motif in THIS verse - echo, elevate, overturn, narrow.
3. The evidence: quote one or two of the supplied lines and land the point.

HARD RULES:
- Quote poetry ONLY as [[q:<line_root_id>|<that line's Arabic, copied EXACTLY as supplied>]].
  Use only line_root_ids from the brief. Never invent a line, a poet, or an id. Never alter
  the Arabic.
- Meaning comes from the Qur'an's own usage and contemporaneous attestation only.
- BANNED (later doctrine): muslim, hadith, sunnah, sharia, fiqh, caliph, halal, haram,
  madhhab, ulama, tafsir, "scholars say". ("pre-Islamic" is fine - it is the subject.)
- No sermon, no moralising tail, no second-person exhortation.

Return: {"skip": false, "note_markdown": "...", "quoted_lines": [{"line_root_id": N,
"english": "<plain English of that line>"}], "confidence": 0.0-1.0}
JSON only, no prose around it."""

JUDGE_SYSTEM = """You are an adversarial reviewer for a Qur'an study site. You did not write
this note. Judge it strictly against the brief it was written from.

REJECT (fatal) if any of:
  F1 the note's claim about the poetry contradicts the supplied lines or the approved verdict
  F2 it asserts something the brief does not support (invented poet, invented sense, invented line)
  F3 it imports later doctrine, or sermonises / exhorts the reader
  F4 it is generic - it would read identically under any other verse using this root

FLAG (non-fatal) if: the opening assumes background instead of easing the reader in; the prose
is padded or repetitive; the quotation is decorative rather than load-bearing.

Return JSON only: {"verdict": "approve"|"flag"|"reject", "codes": ["F4"], "why": "<one sentence>"}"""


def ollama(model, system, prompt, num_predict=5000, temperature=0.4, retries=2,
           think=None, num_ctx=16384):
    """One Ollama call. `num_predict` is deliberately generous: the drafter is a
    thinking model whose reasoning length varies a lot, and a budget that fits
    the median run truncates the long ones mid-JSON.

    Keep `num_ctx` no larger than the prompt needs. Drafter and judge are both
    resident at once (~41GB of a 64GB machine); an oversized KV cache on top of
    that has been observed to come back as an empty response rather than an
    error."""
    body = {"model": model, "system": system, "prompt": prompt, "stream": False,
            "options": {"temperature": temperature, "num_predict": num_predict, "num_ctx": num_ctx}}
    if think is not None:
        body["think"] = think
    data = json.dumps(body).encode()
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(OLLAMA, data=data,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=1800) as r:
                return json.loads(r.read()).get("response", "")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if attempt == retries:
                raise RuntimeError(f"{model} unreachable after {retries + 1} tries: {e}") from e
            time.sleep(3 * (attempt + 1))
    return ""


def parse_json(text):
    """Models wrap JSON in prose or fences often enough to be worth tolerating."""
    if not text:
        return None
    t = text.strip()
    t = re.sub(r"^```(?:json)?|```$", "", t, flags=re.MULTILINE).strip()
    try:
        return json.loads(t[t.index("{"):t.rindex("}") + 1])
    except (ValueError, json.JSONDecodeError):
        return None


# ------------------------------------------------------------ the hard gates

MARKER = re.compile(r"\[\[q:(\d+)\|([^\]]*)\]\]")
LABEL_LEAK = re.compile(r"^\s*(on[-\s]?ramp|this verse|the evidence|movement \d)\s*:",
                        re.IGNORECASE | re.MULTILINE)


def gate(conn, ref, root_bw, payload):
    """Deterministic checks a local draft must clear before it is stored at all.

    These are the checks that do not need judgement, so they must never be left
    to a model: the ids must exist, the Arabic must be the corpus' Arabic, the
    evidence must be authenticated, the banned vocabulary must be absent.
    Returns (ok, [failures], [warnings], enriched_quotes, auth_tier_max, continuity).
    Failures stop the note; warnings ride along to the reviewer.
    """
    fails, warns = [], []
    md = (payload.get("note_markdown") or "").strip()
    words = len(md.split())
    if words < MIN_WORDS or words > MAX_WORDS:
        fails.append(f"length {words}w outside {MIN_WORDS}-{MAX_WORDS}")
    if LABEL_LEAK.search(md):
        fails.append("rubric section labels leaked into the prose")

    low = md.lower()
    banned = [w for w in POST_QURANIC if w in low]
    if banned:
        fails.append(f"post-Qur'anic terms: {banned}")

    markers = MARKER.findall(md)
    if not markers:
        fails.append("no poetry quoted - the note has no evidence")

    # Every marker must name a real line for THIS root, and carry that line's
    # own Arabic: the marker text is what the page displays, so a mangled or
    # invented Arabic string would be shown to readers as if it were the corpus.
    declared = {int(q.get("line_root_id")) for q in (payload.get("quoted_lines") or [])
                if str(q.get("line_root_id", "")).isdigit()}
    for lrid, arabic in markers:
        row = conn.execute(
            """SELECT pl.text_plain FROM poetry_line_roots plr
               JOIN poetry_lines pl ON pl.id=plr.line_id
               WHERE plr.id=? AND plr.root_buckwalter=?""", (int(lrid), root_bw)).fetchone()
        if not row:
            fails.append(f"marker [[q:{lrid}]] is not a line of root {root_bw}")
            continue
        if _bare(arabic) != _bare(row["text_plain"]):
            fails.append(f"marker [[q:{lrid}]] Arabic does not match the corpus line")
        if int(lrid) not in declared:
            fails.append(f"marker [[q:{lrid}]] missing from quoted_lines")

    enriched, tier_max = [], None
    try:
        enriched, tier_max = _enrich_quotes(conn, root_bw, payload.get("quoted_lines") or [])
    except ValueError as e:
        fails.append(str(e))

    # continuity is INHERITED from the approved root-level verdict, never taken
    # from the draft. It drives a visible verdict label, and the local drafter
    # stamped "continuity" on every note of a calibration batch - including ones
    # whose own prose argued a reassignment. The root verdict is human-approved
    # and the verse note is required to stay consistent with it, so the honest
    # value is the one already reviewed.
    rc = conn.execute("SELECT continuity, shift_type FROM root_poetry_comparisons "
                      "WHERE root_buckwalter=?", (root_bw,)).fetchone()
    continuity = bool(rc["continuity"]) if rc is not None else False
    if not continuity and tier_max not in ("A", "B"):
        fails.append("a contrast needs Tier-A/B evidence")

    return (not fails), fails, warns, enriched, tier_max, continuity


def _bare(s):
    """Compare Arabic on letters alone - diacritics and spacing vary harmlessly."""
    return re.sub(r"[^ء-ي]", "", s or "")


# ------------------------------------------------------------------ one item

def draft_one(conn, item, dry=False):
    """Phase 1 for one verse: the drafter judges whether a note is warranted and,
    if so, writes it. Returns (result, payload|None)."""
    ref, root_bw = item["ref"], item["focus_root"]
    c, v = item["chapter"], item["verse"]
    b = brief(conn, ref, root_bw)

    ask = f"{b}\n\nJudge, then write if warranted, for {ref}. JSON only."
    raw = ollama(DRAFTER, DRAFT_SYSTEM, ask)
    payload = parse_json(raw)
    if payload is None:
        # Long reasoning occasionally runs past the budget and cuts the JSON in
        # half. Retry once with reasoning off: measurably the same draft quality,
        # a much shorter and more predictable response.
        raw = ollama(DRAFTER, DRAFT_SYSTEM, ask, think=False)
        payload = parse_json(raw)
    if payload is None:
        return {"ref": ref, "outcome": "unparsable", "detail": raw[:160]}, None

    if payload.get("skip"):
        reason = (payload.get("reason") or "no reason given").strip()
        if not dry:
            conn.execute(
                """INSERT OR IGNORE INTO poetry_verse_skipped
                   (chapter, verse, page_key, focus_root_buckwalter, reason, model_used)
                   VALUES (?,?,?,?,?,?)""", (c, v, ref, root_bw, reason, DRAFTER))
            conn.commit()
        return {"ref": ref, "outcome": "skip", "detail": reason}, None

    ok, fails, warns, enriched, tier_max, continuity = gate(conn, ref, root_bw, payload)
    if not ok:
        # A gate failure is the draft's fault, not the verse's: leave the verse
        # in the queue so a later tick can try it again, and say why here.
        return {"ref": ref, "outcome": "gate_failed", "detail": "; ".join(fails)}, None
    return ({"ref": ref, "outcome": "pending_review"},
            {"payload": payload, "warns": warns, "enriched": enriched,
             "tier_max": tier_max, "continuity": continuity, "brief": b})


def review_and_store(conn, item, draft, dry=False):
    """Phase 2 for one verse: an independent model reviews the drafted note, then
    it is stored pending. Nothing here calls the drafter."""
    ref, root_bw = item["ref"], item["focus_root"]
    c, v = item["chapter"], item["verse"]
    payload, warns = draft["payload"], draft["warns"]
    md = payload["note_markdown"].strip()

    # think=False for the judge: it returns a three-field verdict, and with
    # reasoning on, its own chain of thought ran past the budget and cut the
    # JSON in half - which used to land silently as a "flag".
    ask_judge = f"{draft['brief']}\n\n## The note under review\n{md}\n\nJudge it. JSON only."
    review = parse_json(ollama(JUDGE, JUDGE_SYSTEM, ask_judge, num_predict=1200,
                               temperature=0.2, think=False, num_ctx=8192)) or {}
    if not review.get("verdict"):
        review = parse_json(ollama(JUDGE, JUDGE_SYSTEM, ask_judge, num_predict=1200,
                                   temperature=0.0, think=False, num_ctx=8192)) or {}
    verdict = (review.get("verdict") or "").lower()
    if verdict not in ("approve", "flag", "reject"):
        # No usable verdict came back. Say so: recording this as a flag would
        # claim an independent review that never happened.
        verdict = "unreviewed"
    if warns and verdict == "approve":
        verdict = "flag"          # a gate warning outranks the judge's approval
    report = json.dumps({"judge": JUDGE, "verdict": verdict,
                         "codes": review.get("codes") or [], "why": review.get("why"),
                         "gate_warnings": warns}, ensure_ascii=False)

    if verdict == "reject":
        # Rejected by an independent reader: don't store a note nobody vouches
        # for, and don't bury the verse either - record why and move on.
        if not dry:
            conn.execute(
                """INSERT OR IGNORE INTO poetry_verse_skipped
                   (chapter, verse, page_key, focus_root_buckwalter, reason, model_used)
                   VALUES (?,?,?,?,?,?)""",
                (c, v, ref, root_bw, f"judge rejected: {review.get('why')}", JUDGE))
            conn.commit()
        return {"ref": ref, "outcome": "rejected", "detail": str(review.get("why"))[:120]}

    if not dry:
        conn.execute("DELETE FROM verse_poetry_notes WHERE chapter=? AND verse=?", (c, v))
        conn.execute(
            """INSERT INTO verse_poetry_notes
               (chapter, verse, page_key, focus_root_buckwalter, note_markdown,
                quoted_lines_json, continuity, confidence, auth_tier_max,
                adversarial_report, review_status, raw_response)
               VALUES (?,?,?,?,?,?,?,?,?,?,'pending',?)""",
            (c, v, ref, root_bw, md, json.dumps(draft["enriched"], ensure_ascii=False),
             1 if draft["continuity"] else 0,
             float(payload.get("confidence") or 0.0), draft["tier_max"], report,
             json.dumps(payload, ensure_ascii=False)))
        conn.commit()
    return {"ref": ref, "outcome": "drafted", "verdict": verdict,
            "detail": f"judge={verdict} {len(md.split())}w tier-{draft['tier_max']} "
                      f"{len(draft['enriched'])} quoted"
                      + (f" {review.get('codes')}" if review.get("codes") else "")}


# ----------------------------------------------------------------- commands

def cmd_stats(args):
    conn = get_conn()
    try:
        q = candidates(conn)
        notes = conn.execute("SELECT COUNT(*) n, "
                             "SUM(review_status='pending') p, SUM(review_status='approved') a "
                             "FROM verse_poetry_notes").fetchone()
        sk = conn.execute("SELECT COUNT(*) n FROM poetry_verse_skipped").fetchone()["n"]
        print(json.dumps({
            "queue_remaining": len(q),
            "notes_total": notes["n"], "notes_pending": notes["p"] or 0,
            "notes_approved": notes["a"] or 0,
            "skipped_recorded": sk,
            "root_verse_cap": ROOT_VERSE_CAP,
            "next": [f"{i['ref']} ({i['focus_root']})" for i in q[:8]],
        }, indent=1))
    finally:
        conn.close()
    return 0


def _tick(conn, count, dry):
    """One tick, run in two phases.

    Drafter (~29GB) and judge (~12GB) do not sit comfortably in memory together,
    and swapping between them per verse produced empty responses that looked
    like review failures. Drafting the whole batch first, then reviewing the
    whole batch, keeps one model hot at a time and lets the other fall out of
    residency on its own.
    """
    items = candidates(conn, limit=count)
    tally, drafts = {}, []

    for item in items:                              # phase 1 - drafter only
        t0 = time.time()
        try:
            r, draft = draft_one(conn, item, dry=dry)
        except RuntimeError as e:                   # ollama down: stop, don't burn the queue
            print(json.dumps({"fatal": str(e)}), flush=True)
            return None
        if draft is None:
            tally[r["outcome"]] = tally.get(r["outcome"], 0) + 1
            print(f"  {r['ref']:9} {r['outcome']:12} {round(time.time()-t0)}s  "
                  f"{r.get('detail','')[:110]}", flush=True)
        else:
            drafts.append((item, draft))

    for item, draft in drafts:                      # phase 2 - judge only
        t0 = time.time()
        try:
            r = review_and_store(conn, item, draft, dry=dry)
        except RuntimeError as e:
            print(json.dumps({"fatal": str(e)}), flush=True)
            return None
        tally[r["outcome"]] = tally.get(r["outcome"], 0) + 1
        print(f"  {r['ref']:9} {r['outcome']:12} {round(time.time()-t0)}s  "
              f"{r.get('detail','')[:110]}", flush=True)
    return tally


def cmd_tick(args):
    conn = get_conn()
    try:
        tally = _tick(conn, args.count, args.dry)
        if tally is None:
            return 1
        print(json.dumps({"tick": tally, "remaining": len(candidates(conn))}), flush=True)
    finally:
        conn.close()
    return 0


def cmd_run(args):
    """Continuous and resumable: state lives in the two tables, never in memory."""
    while True:
        conn = get_conn()
        try:
            remaining = len(candidates(conn))
            if remaining == 0:
                print(json.dumps({"done": True}), flush=True)
                return 0
            print(f"[{time.strftime('%H:%M:%S')}] remaining={remaining}", flush=True)
            if _tick(conn, args.count, False) is None:
                return 1
        finally:
            conn.close()
        time.sleep(args.sleep)


def cmd_show(args):
    conn = get_conn()
    try:
        r = conn.execute("SELECT * FROM verse_poetry_notes WHERE page_key=?", (args.ref,)).fetchone()
        if not r:
            s = conn.execute("SELECT * FROM poetry_verse_skipped WHERE page_key=?", (args.ref,)).fetchone()
            print(f"skipped: {s['reason']}" if s else "nothing stored for that verse")
            return 0
        print(f"{r['page_key']}  root={r['focus_root_buckwalter']}  "
              f"{'continuity' if r['continuity'] else 'contrast'}  tier={r['auth_tier_max']}  "
              f"conf={r['confidence']}  status={r['review_status']}")
        print(f"judge: {r['adversarial_report']}\n")
        print(r["note_markdown"])
    finally:
        conn.close()
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stats").set_defaults(fn=cmd_stats)
    t = sub.add_parser("tick"); t.add_argument("--count", type=int, default=5)
    t.add_argument("--dry", action="store_true"); t.set_defaults(fn=cmd_tick)
    r = sub.add_parser("run"); r.add_argument("--count", type=int, default=5)
    r.add_argument("--sleep", type=int, default=60); r.set_defaults(fn=cmd_run)
    s = sub.add_parser("show"); s.add_argument("ref"); s.set_defaults(fn=cmd_show)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
