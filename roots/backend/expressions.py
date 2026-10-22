"""Qur'anic expressions: the table behind /expressions and its queries.

Entries are produced offline by expressions_ai.py (mined, written from the
Qur'an alone, checked claim by claim against their verses, revised) and
loaded here with `python expressions_ai.py publish --final final_all.jsonl`.
Stdlib only, so app.py can import it cheaply.
"""
import difflib
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


# Widest stretch of a verse marked on hover, in words.
MAX_SPAN = 12

# Order on a verse page: the entries most particular to the verse first.
_KIND_ORDER = {"mirror": 0, "closing": 1, "contrast": 2, "twin": 3, "family": 4, "frame": 5}

_ALIFS = str.maketrans({"ٱ": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه"})


def _skeleton(text):
    """Bare letters of an Arabic word, so a quotation matches the verse's own
    spelling whatever its marks: alif variants folded, then alifs dropped
    (Uthmani writes many long ā's as a dagger alif)."""
    s = "".join(ch for ch in (text or "").translate(_ALIFS) if "\u0621" <= ch <= "\u064a")
    return s.replace("ا", "")


def _keys(source_id, kind):
    """What marks the expression in a verse: roots for a mirror or a contrast,
    lemmas for a family, frame or closing pair (Buckwalter, as in morphology).
    A twin is matched by its text instead."""
    body = (source_id or "").split(":", 1)[-1]
    if kind == "mirror":
        return "root", {body.rsplit(":", 1)[-1]}
    if kind == "contrast":
        return "root", set(body.split("|"))
    if kind in ("family", "frame", "closing"):
        return "lemma", set(body.split("|"))
    return None, set()


def _span(words, kind_key, keys, expression_ar):
    """1-indexed inclusive (start, end) of the expression's words in a verse,
    or None. `words` is [(pos, lemmas, roots, skeleton)] in verse order.

    First the quoted Arabic itself (exact where the verse is the one quoted),
    then the tightest window holding the most of the entry's roots/lemmas."""
    quoted = [_skeleton(t) for t in (expression_ar or "").split()]
    quoted = [q for q in quoted if q]
    if quoted:
        sm = difflib.SequenceMatcher(None, quoted, [w[3] for w in words], autojunk=False)
        hit = [b.b + k for b in sm.get_matching_blocks() for k in range(b.size)]
        # All of a one- or two-word quotation; at least half of a longer one.
        if hit and len(hit) >= (len(quoted) if len(quoted) <= 2 else (len(quoted) + 1) // 2):
            return words[hit[0]][0], words[hit[-1]][0]
    if not kind_key:
        return None
    marked = [(k, w[0]) for k, w in enumerate(words)
              if (w[1] if kind_key == "lemma" else w[2]) & keys]
    if not marked:
        return None
    best = None  # (distinct keys covered, -width, start, end)
    for a in range(len(marked)):
        seen = set()
        for b in range(a, len(marked)):
            w = words[marked[b][0]]
            seen |= (w[1] if kind_key == "lemma" else w[2]) & keys
            cand = (len(seen), -(marked[b][1] - marked[a][1]), marked[a][1], marked[b][1])
            if best is None or cand[:2] > best[:2]:
                best = cand
    start, end = best[2], best[3]
    # A family's words recur inside the phrase (faḍḍalnā baʿḍahum ʿalā baʿḍ):
    # take in marked words that sit right next to the window.
    for _, pos in marked:
        if end < pos <= end + 2:
            end = pos
    for _, pos in reversed(marked):
        if start - 2 <= pos < start:
            start = pos
    return start, end


def for_verses(conn, surah, ayah=None, brief=False):
    """verse -> the visible expressions that draw on it, for the verse page
    and the reader. Each item carries the span of its words in that verse
    (start/end, word positions) when one can be found, for hover marking.
    `brief` drops the per-verse role line (the reader shows titles only)."""
    ensure_table(conn)
    prefix = f"{surah}:"
    wanted = {}  # verse -> [(row, ref)]
    for r in conn.execute(
            "SELECT slug, kind, title, expression_ar, gloss, refs_json, occurrences_json, source_id "
            "FROM expressions WHERE hidden = 0 AND refs_json LIKE ?", (f'%"{prefix}%',)):
        for ref in json.loads(r[5] or "[]"):
            if not ref.startswith(prefix):
                continue
            v = int(ref.split(":")[1])
            if ayah is None or v == ayah:
                wanted.setdefault(v, []).append(r)
    if not wanted:
        return {}

    verses = sorted(wanted)
    words = {}  # verse -> {pos: [lemmas, roots, skeleton]}
    for v, pos, form, lemma, root in conn.execute(
            f"SELECT verse, word_pos, form_arabic, lemma_buckwalter, root_buckwalter FROM morphology "
            f"WHERE chapter = ? AND verse IN ({','.join('?' * len(verses))}) ORDER BY verse, word_pos, segment",
            [surah, *verses]):
        w = words.setdefault(v, {}).setdefault(pos, [set(), set(), ""])
        if lemma:
            w[0].add(lemma)
        if root:
            w[1].add(root)
        w[2] += form or ""

    out = {}
    for v, rows in wanted.items():
        vw = [(p, w[0], w[1], _skeleton(w[2])) for p, w in sorted(words.get(v, {}).items())]
        items = []
        for slug, kind, title, ar, gloss, refs_json, occ_json, source_id in rows:
            kind_key, keys = _keys(source_id, kind)
            span = _span(vw, kind_key, keys, ar) if vw else None
            if span and span[1] - span[0] >= MAX_SPAN:
                span = None  # words far apart: marking the whole stretch would mislead
            item = {"slug": slug, "kind": kind, "kind_label": KIND_LABEL.get(kind, kind),
                    "title": title, "expression_ar": ar,
                    "verse_count": len(json.loads(refs_json or "[]")),
                    "start": span[0] if span else None, "end": span[1] if span else None}
            if not brief:
                ref = f"{surah}:{v}"
                item["gloss"] = gloss
                item["role"] = next((o.get("role") for o in json.loads(occ_json or "[]")
                                     if o.get("ref") == ref), None)
            items.append(item)
        items.sort(key=lambda i: (_KIND_ORDER.get(i["kind"], 9), i["verse_count"], i["slug"]))
        out[v] = items
    return out


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
