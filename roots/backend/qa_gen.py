#!/usr/bin/env python3
"""qa_gen.py — scaffolding for the /loop agent to pre-populate "Ask the Quran".

The intelligence lives in the /loop agent (Opus 4.8). This CLI is only the
plumbing around it — it makes NO API calls and contains NO model logic:

    python qa_gen.py next [--count 3]      # next unprocessed verses (priority order)
    python qa_gen.py context 2:255         # dump all pre-computed material for a verse
    python qa_gen.py add 2:255 --file q.json   # validate + store AI-drafted Q&A
    python qa_gen.py skip 2:255 --reason "…"   # record "no insightful question here"
    python qa_gen.py stats                  # progress + review-queue summary

Each /loop iteration: read `context`, reason as Opus, then `add` (or `skip`).
Drafts land in assistant_conversations as source='ai', review_status='pending'
and never show publicly until an admin approves them in /admin/qa.

`add` payload (JSON list, 1–3 items):
    [{"question": "...", "answer": "...", "category": "grammar",
      "score": 4, "source_notes": "which observation this came from"}]
"""
import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "quran.db")
DEFAULT_MODEL = "opus-4.8-loop"

# Question archetypes (the `category` field). Keeps the corpus varied and
# lets the admin filter the review queue by type.
ALLOWED_CATEGORIES = {
    "implication",    # what the verse implies / commits us to / leaves open (substantive,
                      #   reader-driven inquiry answered from the Quran's own evidence)
    "lexical",        # word/root choice vs a near-synonym
    "morphology",     # significance of the form (voice, verb form, number…)
    "grammar",        # case, tense, particle, word order, definiteness
    "cross_reference",# how usage here relates to elsewhere in the Quran
    "semantic",       # a departure / unexpected nuance of meaning
    "cognate",        # Semitic cognate depth
    "rhetorical",     # repetition, ring composition, emphasis, sound
    "other",
}

# Post-Quranic vocabulary the Quran-only doctrine forbids in outputs. A hit is
# flagged in generation_meta (not auto-blocked) so the admin can judge context.
BANNED_TERMS = [
    "islamic", "islam", "muslim", "halal", "haram", "sunnah", "hadith",
    "sharia", "shariah", "fiqh", "madhhab", "caliph", "caliphate",
    "sahaba", "tafsir", "scholars say", "jurist",
]

# Pilot set — processed first so quality can be reviewed early. Mixes famous +
# grammatically rich verses with a few short/formulaic ones to confirm the gate
# can correctly return "no question" rather than forcing one.
PILOT_VERSES = [
    "1:1", "1:2", "1:5", "2:2", "2:30", "2:152", "2:255",
    "3:139", "4:3", "4:56", "12:2", "13:28", "17:1", "18:10",
    "19:1", "20:1", "21:107", "24:35", "31:18", "36:1",
    "39:53", "49:13", "55:13", "56:77", "59:22", "67:1",
    "94:5", "94:6", "96:1", "99:1", "101:1", "103:1", "103:2",
    "103:3", "108:1", "108:2", "108:3", "112:1", "112:2", "114:1",
]

# ----------------------------------------------------------------------------
# DB helpers
# ----------------------------------------------------------------------------

def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def ensure_progress_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_question_progress (
            chapter      INTEGER NOT NULL,
            verse        INTEGER NOT NULL,
            status       TEXT NOT NULL,          -- 'done' | 'none'
            num_questions INTEGER DEFAULT 0,
            reason       TEXT,
            model        TEXT,
            assessed_at  TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (chapter, verse)
        )
        """
    )
    conn.commit()


_VERSE_COUNTS = None


def verse_counts(conn):
    """{chapter: max_verse} for reference validation."""
    global _VERSE_COUNTS
    if _VERSE_COUNTS is None:
        _VERSE_COUNTS = {
            r["chapter"]: r["mx"]
            for r in conn.execute(
                "SELECT chapter, MAX(verse) AS mx FROM verses GROUP BY chapter"
            )
        }
    return _VERSE_COUNTS


def parse_ref(s):
    m = re.match(r"^\s*(\d{1,3}):(\d{1,3})\s*$", s)
    if not m:
        raise ValueError(f"Bad verse ref '{s}' (expected 'surah:ayah')")
    return int(m.group(1)), int(m.group(2))


def valid_ref(conn, ch, v):
    counts = verse_counts(conn)
    return ch in counts and 1 <= v <= counts[ch]


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# ----------------------------------------------------------------------------
# context — dump all pre-computed material for a verse
# ----------------------------------------------------------------------------

def _verse_words(conn, ch, v):
    """Reconstruct per-word data from morphology segments, keyed by word_pos.
    Arabic = concatenated segment forms; root/lemma/pos taken from the stem."""
    rows = conn.execute(
        "SELECT word_pos, segment, form_arabic, tag, pos, root_arabic, "
        "       root_buckwalter, lemma_arabic, voice, verb_form, case_val, number "
        "FROM morphology WHERE chapter=? AND verse=? ORDER BY word_pos, segment",
        (ch, v),
    ).fetchall()
    words = {}
    for r in rows:
        wp = r["word_pos"]
        w = words.setdefault(wp, {
            "pos": wp, "arabic": "", "root_ar": "", "root_bw": "",
            "lemma_ar": "", "tag": "", "gram": "",
        })
        w["arabic"] += r["form_arabic"] or ""
        if r["root_buckwalter"]:
            w["root_ar"] = r["root_arabic"] or ""
            w["root_bw"] = r["root_buckwalter"] or ""
            w["lemma_ar"] = r["lemma_arabic"] or ""
            w["tag"] = r["pos"] or r["tag"] or ""
            gram = []
            for k in ("voice", "verb_form", "case_val", "number"):
                if r[k]:
                    gram.append(str(r[k]))
            w["gram"] = ", ".join(gram)
    return [words[k] for k in sorted(words)]


def _word_meanings(conn, ch, v):
    out = {}
    try:
        for r in conn.execute(
            "SELECT word_pos, meaning_short, semantic_field, morphology_notes, "
            "       departure_notes, cross_ref_notes, cognate_notes "
            "FROM ai_word_meanings WHERE chapter=? AND verse=?",
            (ch, v),
        ):
            out[r["word_pos"]] = r
    except sqlite3.OperationalError:
        pass
    return out


def _cross_refs(conn, ch, v, words, max_roots=6, examples=3):
    """For the verse's content roots, count Quran-wide usage + a few example
    verses — fuel for intra-Quranic ('how is this root used elsewhere') questions."""
    seen = set()
    lines = []
    for w in words:
        bw = w["root_bw"]
        if not bw or bw in seen:
            continue
        seen.add(bw)
        if len(seen) > max_roots:
            break
        cnt = conn.execute(
            "SELECT COUNT(DISTINCT chapter || ':' || verse) AS c "
            "FROM morphology WHERE root_buckwalter=?", (bw,),
        ).fetchone()["c"]
        ex = conn.execute(
            "SELECT DISTINCT chapter, verse FROM morphology "
            "WHERE root_buckwalter=? AND NOT (chapter=? AND verse=?) "
            "ORDER BY chapter, verse LIMIT ?", (bw, ch, v, examples),
        ).fetchall()
        ex_s = ", ".join(f"{r['chapter']}:{r['verse']}" for r in ex)
        lines.append(f"- {w['root_ar']} ({bw}) — {cnt} verse(s) Quran-wide"
                     + (f"; e.g. {ex_s}" if ex_s else ""))
    return lines


def _strip_bismillah_prefix(conn, text, ch, v):
    """Drop the embedded basmala from verse-1 display text (except 1:1), matching
    by letter skeleton so diacritic variants (e.g. 95:1, 97:1) still strip."""
    import unicodedata
    if v != 1 or ch == 1:
        return text
    bis = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter=1 AND verse=1"
    ).fetchone()["text_uthmani"]
    skel = [c for c in bis if not unicodedata.combining(c) and not c.isspace()]
    ti = 0
    for i, chr_ in enumerate(text):
        if unicodedata.combining(chr_) or chr_.isspace():
            continue
        if ti < len(skel) and chr_ == skel[ti]:
            ti += 1
            if ti == len(skel):
                j = i + 1
                while j < len(text) and unicodedata.combining(text[j]):
                    j += 1
                return text[j:].strip()
        else:
            return text
    return text


def build_context(conn, ch, v):
    ref = f"{ch}:{v}"
    row = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter=? AND verse=?", (ch, v)
    ).fetchone()
    if not row:
        return None
    uthmani = _strip_bismillah_prefix(conn, row["text_uthmani"], ch, v)
    tr = conn.execute(
        "SELECT text_en FROM translations WHERE chapter=? AND verse=?", (ch, v)
    ).fetchone()
    ai_tr = conn.execute(
        "SELECT translation_text, departure_notes FROM ai_translations "
        "WHERE chapter=? AND verse=? LIMIT 1", (ch, v)
    ).fetchone()
    gram = conn.execute(
        "SELECT notes_markdown FROM ai_grammar_notes WHERE chapter=? AND verse=? LIMIT 1",
        (ch, v),
    ).fetchone()
    themes = [r["theme"] for r in conn.execute(
        "SELECT theme FROM verse_themes WHERE chapter=? AND verse=? "
        "ORDER BY confidence DESC LIMIT 6", (ch, v))]

    words = _verse_words(conn, ch, v)
    meanings = _word_meanings(conn, ch, v)

    P = []
    P.append(f"# Verse {ref}\n")
    P.append(f"**Arabic (Uthmani):** {uthmani}")
    if tr:
        P.append(f"**Translation:** {tr['text_en']}")
    if ai_tr and ai_tr["translation_text"]:
        P.append(f"**Root-based translation:** {ai_tr['translation_text']}")
        if ai_tr["departure_notes"]:
            P.append(f"**Translation departure notes:** {ai_tr['departure_notes']}")
    if themes:
        P.append(f"**Themes:** {', '.join(themes)}")

    P.append("\n## Word-by-word")
    for w in words:
        head = f"{w['pos']}. {w['arabic']}".rstrip()
        bits = []
        if w["root_ar"]:
            bits.append(f"root {w['root_ar']} ({w['root_bw']})")
        if w["lemma_ar"]:
            bits.append(f"lemma {w['lemma_ar']}")
        if w["tag"]:
            bits.append(w["tag"])
        if w["gram"]:
            bits.append(w["gram"])
        m = meanings.get(w["pos"])
        if m and m["meaning_short"]:
            bits.append(f"“{m['meaning_short']}”")
        if m and m["semantic_field"]:
            bits.append(f"[field: {m['semantic_field']}]")
        P.append(f"- {head} — " + "; ".join(b for b in bits if b))
        # The pre-computed notes are the richest seeds for questions.
        if m:
            for label, key in (("morphology", "morphology_notes"),
                               ("departure", "departure_notes"),
                               ("cross-ref", "cross_ref_notes"),
                               ("cognate", "cognate_notes")):
                val = m[key]
                if val and val.strip():
                    P.append(f"    - _{label}_: {val.strip()}")

    if gram and gram["notes_markdown"]:
        P.append("\n## Grammar notes")
        P.append(gram["notes_markdown"].strip())

    xr = _cross_refs(conn, ch, v, words)
    if xr:
        P.append("\n## Same-root cross-references (intra-Quranic)")
        P.extend(xr)

    # Surface anything already asked so the agent doesn't duplicate it.
    existing = conn.execute(
        "SELECT question, COALESCE(source,'user') AS src, "
        "       COALESCE(review_status,'') AS rs "
        "FROM assistant_conversations WHERE page_type='verse' AND page_key=? "
        "ORDER BY id", (ref,),
    ).fetchall()
    if existing:
        P.append("\n## Already asked on this verse (do NOT duplicate)")
        for e in existing:
            tag = e["src"] + (f"/{e['rs']}" if e["rs"] else "")
            P.append(f"- [{tag}] {e['question']}")

    return "\n".join(P)


# ----------------------------------------------------------------------------
# next — priority-ordered unprocessed verses
# ----------------------------------------------------------------------------

def cmd_next(conn, args):
    processed = {
        (r["chapter"], r["verse"])
        for r in conn.execute("SELECT chapter, verse FROM ai_question_progress")
    }
    order = []
    seen = set()
    for ref in PILOT_VERSES:
        ch, v = parse_ref(ref)
        if (ch, v) not in processed and (ch, v) not in seen:
            order.append((ch, v)); seen.add((ch, v))
    if not args.pilot_only:
        for r in conn.execute("SELECT chapter, verse FROM verses ORDER BY chapter, verse"):
            key = (r["chapter"], r["verse"])
            if key not in processed and key not in seen:
                order.append(key); seen.add(key)

    picked = order[: args.count]
    total_verses = conn.execute("SELECT COUNT(*) AS c FROM verses").fetchone()["c"]
    pilot_remaining = sum(
        1 for ref in PILOT_VERSES if parse_ref(ref) not in processed
    )
    out = {
        "verses": [f"{c}:{v}" for c, v in picked],
        "remaining_pilot": pilot_remaining,
        "remaining_total": total_verses - len(processed),
    }
    print(json.dumps(out, ensure_ascii=False))


# ----------------------------------------------------------------------------
# add / skip — store drafts or record an empty assessment
# ----------------------------------------------------------------------------

def _load_payload(args):
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            raw = f.read()
    elif args.json:
        raw = args.json
    else:
        raw = sys.stdin.read()
    data = json.loads(raw)
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("payload must be a JSON object or list of objects")
    return data


def _find_refs(conn, text):
    """Return (valid_refs, invalid_refs) cited in text."""
    valid, invalid = [], []
    for m in re.findall(r"\b(\d{1,3}):(\d{1,3})\b", text or ""):
        ch, v = int(m[0]), int(m[1])
        (valid if valid_ref(conn, ch, v) else invalid).append(f"{ch}:{v}")
    return valid, invalid


def _banned_hits(text):
    low = (text or "").lower()
    return sorted({t for t in BANNED_TERMS if re.search(r"\b" + re.escape(t) + r"\b", low)})


def _norm_q(q):
    return re.sub(r"[^a-z0-9؀-ۿ ]", "", (q or "").lower()).strip()


def cmd_add(conn, args):
    ch, v = parse_ref(args.ref)
    ref = f"{ch}:{v}"
    if not valid_ref(conn, ch, v):
        print(json.dumps({"error": f"{ref} is not a valid verse"})); return 1
    items = _load_payload(args)

    existing_qs = {
        _norm_q(r["question"])
        for r in conn.execute(
            "SELECT question FROM assistant_conversations "
            "WHERE page_type='verse' AND page_key=?", (ref,))
    }

    ensure_progress_table(conn)
    stored, skipped = [], []
    for it in items:
        q = (it.get("question") or "").strip()
        a = (it.get("answer") or "").strip()
        cat = (it.get("category") or "other").strip().lower()
        score = it.get("score")
        if not q or not a:
            skipped.append({"question": q[:60], "reason": "empty question/answer"}); continue
        if cat not in ALLOWED_CATEGORIES:
            cat = "other"
        if _norm_q(q) in existing_qs:
            skipped.append({"question": q[:60], "reason": "duplicate"}); continue

        flags = []
        bad = _banned_hits(q + " " + a)
        if bad:
            flags.append("post_quranic_terms:" + ",".join(bad))
        valid_refs, invalid_refs = _find_refs(conn, q + " " + a)
        if invalid_refs:
            flags.append("invalid_refs:" + ",".join(invalid_refs))

        meta = {
            "source_notes": it.get("source_notes", ""),
            "cited_refs": valid_refs,
            "flags": flags,
            "voice": "v2",  # written under the teacher/triangulate answer voice
        }
        cur = conn.execute(
            "INSERT INTO assistant_conversations "
            "(session_id, page_type, page_key, question, answer, model_used, "
            " source, review_status, category, quality_score, generation_meta, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            ("ai", "verse", ref, q[:500], a[:50000], args.model,
             "ai", "pending", cat,
             float(score) if score is not None else None,
             json.dumps(meta, ensure_ascii=False), now_iso()),
        )
        existing_qs.add(_norm_q(q))
        stored.append({"id": cur.lastrowid, "category": cat, "score": score, "flags": flags})

    conn.execute(
        "INSERT INTO ai_question_progress (chapter, verse, status, num_questions, model, assessed_at) "
        "VALUES (?,?,?,?,?,?) "
        "ON CONFLICT(chapter, verse) DO UPDATE SET "
        "status='done', num_questions=excluded.num_questions, "
        "model=excluded.model, assessed_at=excluded.assessed_at",
        (ch, v, "done", len(stored), args.model, now_iso()),
    )
    conn.commit()
    print(json.dumps({"verse": ref, "stored": stored, "skipped": skipped}, ensure_ascii=False))
    return 0


def cmd_revise(conn, args):
    """Rewrite an existing AI draft in place (e.g. to apply a new answer
    voice). Re-runs the same validation as `add` so flags stay accurate,
    preserves category/score when the payload omits them, and stamps
    edited_at. Payload is a single object (or one-element list) with at
    least `answer`; `question`, `category`, `score`, `source_notes` are
    optional overrides."""
    row = conn.execute(
        "SELECT id, page_key, question, category, quality_score, generation_meta "
        "FROM assistant_conversations WHERE id=? AND source='ai'",
        (args.id,),
    ).fetchone()
    if not row:
        print(json.dumps({"error": f"no AI draft with id {args.id}"})); return 1

    items = _load_payload(args)
    if not items:
        print(json.dumps({"error": "empty payload"})); return 1
    it = items[0]

    q = (it.get("question") or row["question"] or "").strip()
    a = (it.get("answer") or "").strip()
    if not a:
        print(json.dumps({"error": "revise payload must include a non-empty answer"})); return 1
    cat = (it.get("category") or row["category"] or "other").strip().lower()
    if cat not in ALLOWED_CATEGORIES:
        cat = "other"
    score = it.get("score", row["quality_score"])

    flags = []
    bad = _banned_hits(q + " " + a)
    if bad:
        flags.append("post_quranic_terms:" + ",".join(bad))
    valid_refs, invalid_refs = _find_refs(conn, q + " " + a)
    if invalid_refs:
        flags.append("invalid_refs:" + ",".join(invalid_refs))

    try:
        meta = json.loads(row["generation_meta"]) if row["generation_meta"] else {}
    except Exception:
        meta = {}
    if "source_notes" in it:
        meta["source_notes"] = it.get("source_notes", "")
    meta["cited_refs"] = valid_refs
    meta["flags"] = flags
    meta["voice"] = "v2"               # revising IS the voice fix → now new-voice
    meta.pop("needs_voice_revision", None)  # clear the backlog flag

    conn.execute(
        "UPDATE assistant_conversations SET question=?, answer=?, category=?, "
        "quality_score=?, generation_meta=?, edited_at=? WHERE id=?",
        (q[:500], a[:50000], cat,
         float(score) if score is not None else None,
         json.dumps(meta, ensure_ascii=False), now_iso(), args.id),
    )
    conn.commit()
    print(json.dumps(
        {"id": args.id, "verse": row["page_key"], "category": cat, "score": score, "flags": flags},
        ensure_ascii=False,
    ))
    return 0


def cmd_revise_queue(conn, args):
    """The voice-revision backlog: drafts written in the old verdict-first
    voice, flagged for a later rephrasing pass. The discovered evidence
    already lives in each row's source_notes, so the later pass is
    *rephrasing*, not re-research. New/revised drafts carry meta.voice ==
    'v2' and are excluded automatically.

      --mark-all  one-time: flag every old-voice (non-v2) AI draft.
      --stats     how many remain flagged, by category.
      (default)   list the next N flagged drafts WITH their current
                  question/answer/source_notes — everything the pass needs
                  to rephrase in one call. Pending first, then by score.
    """
    if args.mark_all:
        marked = 0
        for r in conn.execute(
            "SELECT id, generation_meta FROM assistant_conversations WHERE source='ai'"
        ).fetchall():
            try:
                meta = json.loads(r["generation_meta"]) if r["generation_meta"] else {}
            except Exception:
                meta = {}
            if meta.get("voice") == "v2" or meta.get("needs_voice_revision"):
                continue  # already new-voice, or already flagged
            meta["needs_voice_revision"] = True
            conn.execute(
                "UPDATE assistant_conversations SET generation_meta=? WHERE id=?",
                (json.dumps(meta, ensure_ascii=False), r["id"]),
            )
            marked += 1
        conn.commit()
        print(json.dumps({"marked_needs_voice_revision": marked}, ensure_ascii=False))
        return 0

    rows = conn.execute(
        "SELECT id, page_key, category, quality_score, review_status, question, answer, generation_meta "
        "FROM assistant_conversations WHERE source='ai' "
        "ORDER BY (review_status='pending') DESC, quality_score DESC, id ASC"
    ).fetchall()
    flagged, by_cat = [], {}
    for r in rows:
        try:
            meta = json.loads(r["generation_meta"]) if r["generation_meta"] else {}
        except Exception:
            meta = {}
        if not meta.get("needs_voice_revision"):
            continue
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + 1
        if args.category and r["category"] != args.category:
            continue
        flagged.append((r, meta))

    if args.stats:
        print(json.dumps(
            {"remaining_by_category": by_cat, "remaining_total": sum(by_cat.values())},
            ensure_ascii=False))
        return 0

    out = [{
        "id": r["id"], "ref": r["page_key"], "category": r["category"],
        "score": r["quality_score"], "review_status": r["review_status"],
        "question": r["question"], "answer": r["answer"],
        "source_notes": meta.get("source_notes", ""),
    } for r, meta in flagged[:args.count]]
    print(json.dumps(
        {"items": out, "shown": len(out), "remaining_total": sum(by_cat.values())},
        ensure_ascii=False, indent=2))
    return 0


def cmd_skip(conn, args):
    ch, v = parse_ref(args.ref)
    if not valid_ref(conn, ch, v):
        print(json.dumps({"error": f"{ch}:{v} is not a valid verse"})); return 1
    ensure_progress_table(conn)
    conn.execute(
        "INSERT INTO ai_question_progress (chapter, verse, status, num_questions, reason, model, assessed_at) "
        "VALUES (?,?,?,?,?,?,?) "
        "ON CONFLICT(chapter, verse) DO UPDATE SET "
        "status='none', reason=excluded.reason, model=excluded.model, assessed_at=excluded.assessed_at",
        (ch, v, "none", 0, (args.reason or "")[:500], args.model, now_iso()),
    )
    conn.commit()
    print(json.dumps({"verse": f"{ch}:{v}", "status": "skipped (no question)"}, ensure_ascii=False))
    return 0


def cmd_stats(conn, args):
    ensure_progress_table(conn)

    def scalar(sql, params=()):
        return conn.execute(sql, params).fetchone()[0]

    total = scalar("SELECT COUNT(*) FROM verses")
    processed = scalar("SELECT COUNT(*) FROM ai_question_progress")
    done = scalar("SELECT COUNT(*) FROM ai_question_progress WHERE status='done'")
    none = scalar("SELECT COUNT(*) FROM ai_question_progress WHERE status='none'")
    pilot_done = sum(1 for ref in PILOT_VERSES
                     if conn.execute(
                         "SELECT 1 FROM ai_question_progress WHERE chapter=? AND verse=?",
                         parse_ref(ref)).fetchone())
    drafts = scalar("SELECT COUNT(*) FROM assistant_conversations WHERE source='ai'")
    pending = scalar("SELECT COUNT(*) FROM assistant_conversations WHERE source='ai' AND review_status='pending'")
    approved = scalar("SELECT COUNT(*) FROM assistant_conversations WHERE source='ai' AND review_status='approved'")
    rejected = scalar("SELECT COUNT(*) FROM assistant_conversations WHERE source='ai' AND review_status='rejected'")
    out = {
        "verses_total": total,
        "verses_processed": processed,
        "verses_with_questions": done,
        "verses_no_question": none,
        "verses_remaining": total - processed,
        "pilot_done": f"{pilot_done}/{len(PILOT_VERSES)}",
        "ai_drafts_total": drafts,
        "ai_pending_review": pending,
        "ai_approved": approved,
        "ai_rejected": rejected,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Scaffolding for /loop-driven Ask-the-Quran Q&A generation")
    sub = p.add_subparsers(dest="cmd", required=True)

    pn = sub.add_parser("next", help="Next unprocessed verses (priority order)")
    pn.add_argument("--count", type=int, default=3)
    pn.add_argument("--pilot-only", action="store_true", help="Only serve pilot verses")

    pc = sub.add_parser("context", help="Dump pre-computed material for a verse")
    pc.add_argument("ref")

    pa = sub.add_parser("add", help="Store AI-drafted Q&A (JSON list)")
    pa.add_argument("ref")
    pa.add_argument("--file")
    pa.add_argument("--json")
    pa.add_argument("--model", default=DEFAULT_MODEL)

    ps = sub.add_parser("skip", help="Record a verse with no insightful question")
    ps.add_argument("ref")
    ps.add_argument("--reason", default="")
    ps.add_argument("--model", default=DEFAULT_MODEL)

    prv = sub.add_parser("revise", help="Rewrite an existing AI draft by id (re-validates, stamps edited_at)")
    prv.add_argument("--id", type=int, required=True)
    prv.add_argument("--file")
    prv.add_argument("--json")

    prq = sub.add_parser("revise-queue", help="Voice-revision backlog: --mark-all flags old-voice drafts; default lists next N with full payload; --stats counts")
    prq.add_argument("--count", type=int, default=5)
    prq.add_argument("--category")
    prq.add_argument("--mark-all", action="store_true", help="One-time: flag every old-voice (non-v2) AI draft for later revision")
    prq.add_argument("--stats", action="store_true", help="Show how many remain flagged, by category")

    sub.add_parser("stats", help="Progress + review-queue summary")

    args = p.parse_args()
    conn = get_conn()
    try:
        if args.cmd == "next":
            ensure_progress_table(conn); cmd_next(conn, args)
        elif args.cmd == "context":
            ch, v = parse_ref(args.ref)
            ctx = build_context(conn, ch, v)
            if ctx is None:
                print(f"Verse {args.ref} not found", file=sys.stderr); return 1
            print(ctx)
        elif args.cmd == "add":
            return cmd_add(conn, args)
        elif args.cmd == "skip":
            return cmd_skip(conn, args)
        elif args.cmd == "revise":
            return cmd_revise(conn, args)
        elif args.cmd == "revise-queue":
            return cmd_revise_queue(conn, args)
        elif args.cmd == "stats":
            cmd_stats(conn, args)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
