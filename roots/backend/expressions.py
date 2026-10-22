"""Qur'anic expressions: the table behind /expressions and its queries.

Entries are produced offline by expressions_ai.py (mined, written from the
Qur'an alone, checked claim by claim against their verses, revised) and
loaded here with `python expressions_ai.py publish --final final_all.jsonl`.
Stdlib only, so app.py can import it cheaply.
"""
import json
import re
import unicodedata

KINDS = [
    ("mirror", "Mirror", "One root used twice in a verse, the action passing between the parties."),
    ("family", "Family", "Words that keep appearing together; read side by side, the verses show what none shows alone."),
    ("twin", "Near-twin verses", "Verses that are almost identical, and what the word that differs does."),
    ("closing", "Closing pair", "The pair of names that ends a verse, and how it answers what the verse has said."),
    ("contrast", "Contrast pair", "Two roots the Qur'an sets against each other in one verse."),
    ("frame", "Frame", "A fixed formula with a changing slot, and what it does to the words that fill it."),
]
KIND_LABEL = {k: label for k, label, _ in KINDS}

DDL = """
CREATE TABLE IF NOT EXISTS expressions (
    slug TEXT PRIMARY KEY,
    source_id TEXT UNIQUE,             -- pipeline id, e.g. family:faD~ala|baEoD
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    expression_ar TEXT NOT NULL,
    transliteration TEXT,
    gloss TEXT,
    summary TEXT,
    explanation TEXT,
    occurrences_json TEXT,             -- [{"ref": "2:152", "role": "..."}]
    variation TEXT,
    for_researchers_json TEXT,         -- ["...", ...]
    refs_json TEXT,                    -- every verse the entry draws on
    first_ref_key INTEGER,             -- chapter*1000+verse of its first verse, for Qur'an order
    hidden INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
)"""

_FOLD = {"ā": "a", "ī": "i", "ū": "u", "ḥ": "h", "ṣ": "s", "ḍ": "d", "ṭ": "t", "ẓ": "z",
         "ḏ": "dh", "ṯ": "th", "ḫ": "kh", "š": "sh", "ġ": "gh", "ʿ": "", "ʾ": "", "'": "", "’": ""}


def ensure_table(conn):
    conn.execute(DDL)


def slugify(text, max_words=6):
    s = (text or "").lower()
    s = "".join(_FOLD.get(ch, ch) for ch in s)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    words = re.findall(r"[a-z0-9]+", s)
    return "-".join(words[:max_words]) or "expression"


def _ref_key(ref):
    ch, v = map(int, ref.split(":"))
    return ch * 1000 + v


def list_expressions(conn):
    ensure_table(conn)
    rows = conn.execute(
        "SELECT slug, kind, title, expression_ar, transliteration, gloss, summary, refs_json "
        "FROM expressions WHERE hidden = 0 ORDER BY first_ref_key, slug").fetchall()
    return [{"slug": r[0], "kind": r[1], "title": r[2], "expression_ar": r[3],
             "transliteration": r[4], "gloss": r[5], "summary": r[6],
             "verse_count": len(json.loads(r[7] or "[]"))} for r in rows]


def get_expression(conn, slug):
    ensure_table(conn)
    r = conn.execute(
        "SELECT slug, kind, title, expression_ar, transliteration, gloss, summary, explanation, "
        "occurrences_json, variation, for_researchers_json, refs_json "
        "FROM expressions WHERE slug = ? AND hidden = 0", (slug,)).fetchone()
    if not r:
        return None
    return {"slug": r[0], "kind": r[1], "kind_label": KIND_LABEL.get(r[1], r[1]), "title": r[2],
            "expression_ar": r[3], "transliteration": r[4], "gloss": r[5], "summary": r[6],
            "explanation": r[7], "occurrences": json.loads(r[8] or "[]"), "variation": r[9],
            "for_researchers": json.loads(r[10] or "[]"), "refs": json.loads(r[11] or "[]")}


def slugs(conn):
    ensure_table(conn)
    return [r[0] for r in conn.execute("SELECT slug FROM expressions WHERE hidden = 0 ORDER BY first_ref_key")]


def neighbours(conn, slug, limit=4):
    """Other expressions that share a verse with this one, for 'see also'."""
    me = conn.execute("SELECT refs_json FROM expressions WHERE slug = ?", (slug,)).fetchone()
    if not me:
        return []
    mine = set(json.loads(me[0] or "[]"))
    out = []
    for s, title, ar, kind, refs in conn.execute(
            "SELECT slug, title, expression_ar, kind, refs_json FROM expressions "
            "WHERE hidden = 0 AND slug != ?", (slug,)):
        shared = mine & set(json.loads(refs or "[]"))
        if shared:
            out.append((len(shared), {"slug": s, "title": title, "expression_ar": ar, "kind": kind}))
    out.sort(key=lambda x: -x[0])
    return [o for _, o in out[:limit]]


def publish(conn, records):
    """Replace the table's contents with these finished pipeline records."""
    ensure_table(conn)
    # Entries hidden by hand (overlaps, owner's call) stay hidden on a reload.
    hidden = {r[0] for r in conn.execute("SELECT source_id FROM expressions WHERE hidden = 1")}
    conn.execute("DELETE FROM expressions")
    used = set()
    for r in records:
        e = r["entry"]
        base = slugify(e.get("transliteration") or e.get("title"))
        slug, n = base, 2
        while slug in used:
            slug, n = f"{base}-{n}", n + 1
        used.add(slug)
        occ_refs = [o.get("ref") for o in e.get("occurrences") or [] if o.get("ref")]
        # Context verses (a twin's neighbours) are not "occurrences"; keep the
        # verses the entry is actually about, in Qur'an order.
        refs = sorted(set(occ_refs) | set(r["candidate"].get("refs", [])), key=_ref_key)
        refs = [x for x in refs if x in set(r.get("given_refs") or refs)]
        conn.execute(
            "INSERT INTO expressions (slug, source_id, kind, title, expression_ar, transliteration, gloss, "
            "summary, explanation, occurrences_json, variation, for_researchers_json, refs_json, first_ref_key, hidden) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (slug, r["id"], r["kind"], e["title"], e["expression_ar"], e.get("transliteration"),
             e.get("gloss"), e.get("summary"), e.get("explanation"),
             json.dumps(e.get("occurrences") or [], ensure_ascii=False), e.get("variation"),
             json.dumps(e.get("for_researchers") or [], ensure_ascii=False),
             json.dumps(refs), _ref_key(refs[0]) if refs else 999999, int(r["id"] in hidden)))
    conn.commit()
    return len(used)
