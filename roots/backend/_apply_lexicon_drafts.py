#!/usr/bin/env python3
"""Apply lexicon-draft workflow output into root_poetic_lexicon as pending.

Usage: python3 _apply_lexicon_drafts.py <workflow_output.json>

Robust by construction: quoted_lines are rebuilt FROM the [[q:ID|..]] markers in
lexicon_markdown (english/note pulled from the draft's quoted_lines where present),
each enriched via poetry_line_roots -> poetry_lines -> poetry_poems. Any marker id
that does not resolve to a real line for THIS root aborts that entry (no garbage).
"""
import json, re, sqlite3, datetime, sys

DB = "data/quran.db"
MARKER = re.compile(r"\[\[q:(\d+)\|")

if len(sys.argv) < 2:
    sys.exit("usage: _apply_lexicon_drafts.py <output.json>")
raw = json.load(open(sys.argv[1]))
rows = raw.get("result") if isinstance(raw, dict) else raw
if isinstance(rows, str):
    rows = json.loads(rows)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
now = datetime.datetime.now().isoformat(timespec="seconds")
TIER_RANK = {"A": 3, "B": 2, "C": 1, None: 0, "": 0}


def resolve_line(lr_id, bw):
    r = conn.execute(
        """SELECT plr.id AS lr_id, plr.root_buckwalter, plr.surface_word,
                  pl.text_plain, pl.line_no, pl.translation_en, pp.id AS poem_id,
                  pp.poet, pp.auth_tier
             FROM poetry_line_roots plr
             JOIN poetry_lines pl ON pl.id = plr.line_id
             JOIN poetry_poems pp ON pp.id = pl.poem_id
            WHERE plr.id = ?""",
        (lr_id,),
    ).fetchone()
    if r is None or r["root_buckwalter"] != bw:
        return None
    return r


applied, aborted = [], []
for e in rows:
    bw = e["root_buckwalter"] if "root_buckwalter" in e else e.get("fr")
    if not e.get("ok"):
        aborted.append((bw, f"verifier ok=false: {e.get('issues')}")); continue
    p = e["payload"]
    md = p["lexicon_markdown"]
    marker_ids = [int(m) for m in MARKER.findall(md)]
    seen, ordered = set(), []
    for i in marker_ids:
        if i not in seen:
            seen.add(i); ordered.append(i)
    draft_ql = {int(q["line_root_id"]): q for q in p.get("quoted_lines", [])}
    quoted_lines, bad = [], []
    for lr in ordered:
        r = resolve_line(lr, bw)
        if r is None:
            bad.append(lr); continue
        dq = draft_ql.get(lr, {})
        quoted_lines.append({
            "line_root_id": lr,
            "poet": r["poet"],
            "auth_tier": r["auth_tier"],
            "arabic": r["text_plain"],
            "surface_word": r["surface_word"],
            "english": dq.get("english") or r["translation_en"] or "",
            "note": dq.get("note", ""),
            "poem_id": r["poem_id"],
            "line_no": r["line_no"],
        })
    if bad:
        aborted.append((bw, f"unresolved/foreign markers {bad} -> skipped to avoid dangling quotes")); continue

    # stats
    occ = conn.execute(
        "SELECT COUNT(*) FROM poetry_line_roots WHERE root_buckwalter=?", (bw,)).fetchone()[0]
    tiers = conn.execute(
        """SELECT DISTINCT pp.auth_tier FROM poetry_line_roots plr
             JOIN poetry_lines pl ON pl.id=plr.line_id
             JOIN poetry_poems pp ON pp.id=pl.poem_id WHERE plr.root_buckwalter=?""",
        (bw,)).fetchall()
    tier_max = max((t[0] for t in tiers), key=lambda t: TIER_RANK.get(t, 0), default=None)
    qocc = conn.execute(
        "SELECT COUNT(*) FROM morphology WHERE root_buckwalter=?", (bw,)).fetchone()[0]

    conn.execute(
        """INSERT INTO root_poetic_lexicon
            (root_buckwalter, root_arabic, attested_senses_json, poetry_occurrences,
             poetry_tier_max, attestation_strength, quran_internal_summary, quran_occurrences,
             lexicon_markdown, relation_to_quran, quoted_lines_json, lexical_basis,
             counter_search, adversarial_report, confidence, review_status, hidden,
             raw_response, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'pending',0,?,?,?)
           ON CONFLICT(root_buckwalter) DO UPDATE SET
             root_arabic=excluded.root_arabic, attested_senses_json=excluded.attested_senses_json,
             poetry_occurrences=excluded.poetry_occurrences, poetry_tier_max=excluded.poetry_tier_max,
             attestation_strength=excluded.attestation_strength,
             quran_internal_summary=excluded.quran_internal_summary,
             quran_occurrences=excluded.quran_occurrences, lexicon_markdown=excluded.lexicon_markdown,
             relation_to_quran=excluded.relation_to_quran, quoted_lines_json=excluded.quoted_lines_json,
             lexical_basis=excluded.lexical_basis, counter_search=excluded.counter_search,
             adversarial_report=excluded.adversarial_report, confidence=excluded.confidence,
             review_status='pending', updated_at=excluded.updated_at""",
        (bw, e.get("root_ar") or p.get("root_arabic"), json.dumps(p["attested_senses"], ensure_ascii=False),
         occ, tier_max, p["attestation_strength"], p["quran_internal_summary"], qocc,
         md, p["relation_to_quran"], json.dumps(quoted_lines, ensure_ascii=False),
         p.get("lexical_basis", ""), p.get("counter_search", ""), p.get("adversarial_report", ""),
         p.get("confidence", 0.0), json.dumps(p, ensure_ascii=False), now, now),
    )
    applied.append((bw, p["attestation_strength"], p["relation_to_quran"], len(quoted_lines), occ))

conn.commit()
print(f"APPLIED {len(applied)}/{len(rows)} (pending):")
for bw, strg, rel, nq, occ in applied:
    print(f"  {bw:5} {strg:10} {rel:14} {nq:2} quotes  ({occ} poetry lines)")
if aborted:
    print(f"ABORTED {len(aborted)}:")
    for bw, why in aborted:
        print(f"  {bw:5} {why}")
conn.close()
