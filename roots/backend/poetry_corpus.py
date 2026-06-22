"""Phase 0 — the pre-Islamic poetry corpus.

This is the prerequisite for the whole Qurʾān↔poetry comparison feature
(see ../../docs/pre-islamic-poetry-implementation.md). Before any agent can
draft "how does root K-F-R differ in the poetry?", the system needs the
poetry: acquired, tiered for trustworthiness, and indexed by root.

It is a SELF-CONTAINED CLI (raw sqlite3 — it does NOT import app.py, so it
stays fast and never triggers the IDF engine build). It owns three tables:

    poetry_poems        one row per poem  (poet, era, meter, rhyme, auth_tier)
    poetry_lines        one row per bayt  (two hemistichs)
    poetry_line_roots   the root index    (LLM-extracted; humans verify quotes)

Authentication ladder (the objectivity backbone — see the research doc §2.2):
    A  Muʿallaqāt (hand-curated / promoted)        -> strong contrast claims
    B  critical anthologies, major Jahilī poets    -> normal contrast claims
    C  raw scraped corpus (Kaggle, era=jahili)      -> statistics + discovery only
    D  disputed                                     -> teaching the problem only

Usage:
    python poetry_corpus.py init
    python poetry_corpus.py load-muallaqat                      # data/poetry/muallaqat.json
    python poetry_corpus.py load-kaggle data/poetry/arabic-poetry.csv
    python poetry_corpus.py tiers                               # promote Muʿallaqāt / major poets
    python poetry_corpus.py index-root kfr --dry-run
    python poetry_corpus.py index-root kfr                      # LLM root extraction
    python poetry_corpus.py verify-root kfr                     # list candidates for human check
    python poetry_corpus.py verify-root kfr --set 12 --set 15   # mark line_root ids verified
    python poetry_corpus.py stats

index-root needs a Claude API key (admin_preferences.claude_api_key or
CLAUDE_API_KEY env). The loaders/tiers/stats do not.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sqlite3
import sys
import time
import unicodedata

import requests

try:
    from buckwalter import buckwalter_to_arabic, space_root
except Exception:  # pragma: no cover - fallback if run from elsewhere
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from buckwalter import buckwalter_to_arabic, space_root

# ------------------------------------------------------------------------
# Config
# ------------------------------------------------------------------------

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "quran.db")
POETRY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "poetry")
DEFAULT_MUALLAQAT_JSON = os.path.join(POETRY_DIR, "muallaqat.json")

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-opus-4-8"
MAX_TOKENS = 4000
MAX_ATTEMPTS = 3
LINES_PER_CHUNK = 80  # how many abyāt per extraction call
EXTRACT_MODEL = "claude-sonnet-4-6"  # extraction is mechanical; Sonnet is plenty + cheap

TIER_RANK = {"A": 3, "B": 2, "C": 1, "D": 0}

# Distinctive (normalized) name tokens for the Muʿallaqāt poets, used by the
# `tiers` command to promote scraped poems. Matching is substring-on-normalized
# so it tolerates al-/ibn/diacritic variants. Combined with era=jahili this is
# safe enough for a heuristic promotion; the human reviewer is the final gate.
MUALLAQAT_POET_KEYS = [
    "القيس",    # Imruʾ al-Qays
    "طرفه",     # Ṭarafa b. al-ʿAbd
    "زهير",     # Zuhayr b. Abī Sulmā
    "لبيد",     # Labīd b. Rabīʿa
    "كلثوم",    # ʿAmr b. Kulthūm
    "عنتره",    # ʿAntara b. Shaddād
    "حلزه",     # al-Ḥārith b. Ḥilliza
    "النابغه",  # al-Nābigha al-Dhubyānī  (the "extra" odes)
    "الاعشي",   # al-Aʿshā
    "الابرص",   # ʿAbīd b. al-Abraṣ
]

# Broader major Jahilī poets -> Tier B (anthology-grade attribution).
MAJOR_JAHILI_POET_KEYS = [
    "السموال",  # al-Samawʾal
    "الشنفري",  # al-Shanfarā
    "تابط",     # Taʾabbaṭa Sharrā
    "المهلهل",  # al-Muhalhil
    "دريد",     # Durayd b. al-Ṣimma
    "الخنساء",  # al-Khansāʾ
    "حاتم",     # Ḥātim al-Ṭāʾī
    "الحطيئه",  # al-Ḥuṭayʾa
    "علقمه",    # ʿAlqama al-Faḥl
    "المتلمس",  # al-Mutalammis
]

# Common bare (diacritic-free) surface forms per pilot root — used as a
# tight, high-precision prefilter for the AGENT-DRIVEN indexing loop so each
# batch is mostly real candidates (works for weak/doubled roots too, unlike
# the ordered-subsequence prefilter). Substring match on bare line text.
SURFACE_FORMS = {
    "kfr": ["كفر", "كافر", "كوافر", "كفار", "كفور", "كفرة", "تكفر", "يكفر",
            "نكفر", "اكفر", "مكفر", "كفران", "الكفر", "كفرت", "كافرين"],
    "wqy": ["وقى", "يقي", "تقي", "اتقى", "يتقي", "تتقي", "اتقوا", "تقوى",
            "التقوى", "تقاة", "واق", "وقاية", "اوقى", "توقى", "متقي", "المتقين", "اتقاء"],
    "dhr": ["دهر", "الدهر", "دهور"],
    "krm": ["كرم", "كريم", "كرام", "الكرام", "اكرم", "مكرم", "مكارم", "كرماء",
            "تكرم", "يكرم", "كرامة", "اكرام", "مكرمة", "كريمة"],
    "jnn": ["جنون", "مجنون", "جنة", "جنان", "اجن", "يجن", "تجن", "استجن",
            "جنين", "اجتن", "مجن", "الجن", "جان", "جنه"],
}

JAHILI_ERA_VALUES = {
    "جاهلي", "الجاهلي", "العصر الجاهلي", "ما قبل الاسلام", "ماقبلالاسلام",
    "pre-islamic", "preislamic", "jahili", "jahiliyya", "al-jahili",
}

# Candidate CSV header names (Arabic + English) for auto-detection.
COL_CANDIDATES = {
    "era":   ["العصر", "poet_era", "era", "age", "period", "epoch"],
    "poet":  ["الشاعر", "اسم الشاعر", "poet_name", "poet", "author", "name"],
    "text":  ["القصيدة", "الابيات", "الأبيات", "البيت", "النص", "الشعر",
              "poem_text", "poem", "text", "poetry", "verse", "bayt", "content"],
    "title": ["عنوان القصيدة", "العنوان", "poem_title", "title", "subject"],
    "tags":  ["poem_tags", "tags", "الوسوم", "poem_tag", "tag"],
    "meter": ["البحر", "بحر", "meter", "bahr"],
    "rhyme": ["القافية", "قافية", "rhyme", "qafia", "qafiya"],
}

TASHKEEL_RE = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")


# ------------------------------------------------------------------------
# DB helpers
# ------------------------------------------------------------------------

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Idempotently create the three corpus tables + index."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS poetry_poems (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            poet        TEXT,
            poet_latin  TEXT,
            era         TEXT,
            title       TEXT,
            meter       TEXT,
            rhyme       TEXT,
            tags        TEXT,
            auth_tier   TEXT NOT NULL DEFAULT 'C',
            source      TEXT,
            source_ref  TEXT,
            full_text   TEXT,
            notes       TEXT,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS poetry_lines (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            poem_id     INTEGER NOT NULL REFERENCES poetry_poems(id),
            line_no     INTEGER,
            hemistich1  TEXT,
            hemistich2  TEXT,
            text_plain  TEXT,
            UNIQUE(poem_id, line_no)
        );

        CREATE TABLE IF NOT EXISTS poetry_line_roots (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            line_id         INTEGER NOT NULL REFERENCES poetry_lines(id),
            root_buckwalter TEXT NOT NULL,
            root_arabic     TEXT,
            surface_word    TEXT,
            sense_hint      TEXT,
            extractor_model TEXT,
            confidence      REAL,
            verified        INTEGER DEFAULT 0,
            created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(line_id, root_buckwalter)
        );
        CREATE INDEX IF NOT EXISTS idx_poetry_line_roots_root
            ON poetry_line_roots(root_buckwalter);
        CREATE INDEX IF NOT EXISTS idx_poetry_lines_poem
            ON poetry_lines(poem_id);

        -- Which (root, line) pairs the indexer has already examined, so the
        -- agent-driven loop never re-offers a line it has judged (whether or
        -- not it matched). Populated by `index-add`.
        CREATE TABLE IF NOT EXISTS poetry_root_scanned (
            root_buckwalter TEXT NOT NULL,
            line_id         INTEGER NOT NULL,
            PRIMARY KEY (root_buckwalter, line_id)
        );
        """
    )
    # Idempotent column adds — for DBs created before a column existed.
    have = {r[1] for r in conn.execute("PRAGMA table_info(poetry_poems)")}
    if "tags" not in have:
        conn.execute("ALTER TABLE poetry_poems ADD COLUMN tags TEXT")
    if "title_en" not in have:
        conn.execute("ALTER TABLE poetry_poems ADD COLUMN title_en TEXT")
    have_l = {r[1] for r in conn.execute("PRAGMA table_info(poetry_lines)")}
    if "translation_en" not in have_l:
        conn.execute("ALTER TABLE poetry_lines ADD COLUMN translation_en TEXT")
    conn.commit()


def get_claude_api_key(explicit: str | None = None) -> str | None:
    """admin_preferences.claude_api_key, else CLAUDE_API_KEY env. Mirrors
    app._get_claude_api_key without importing the heavy Flask app."""
    if explicit:
        return explicit
    try:
        conn = get_conn()
        try:
            row = conn.execute(
                "SELECT value FROM admin_preferences WHERE key = 'claude_api_key'"
            ).fetchone()
            if row and row["value"]:
                return row["value"]
        finally:
            conn.close()
    except Exception:
        pass
    return os.environ.get("CLAUDE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")


# ------------------------------------------------------------------------
# Arabic normalization
# ------------------------------------------------------------------------

def bare(s: str | None) -> str:
    """Strip ALL combining marks (category Mn) + tatweel — robust diacritic
    removal for substring/subsequence matching. Keeps base letters intact."""
    s = (s or "").replace("ـ", "")
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


def ordered_subseq(needle: str, hay: str) -> bool:
    """True if every char of `needle` appears in `hay` in order (gaps allowed).
    Recall-safe for SOUND roots: a derivative always contains the radicals in
    order. NOT safe for weak (و/ي) or doubled roots, which can metathesize."""
    it = iter(hay)
    return all(ch in it for ch in needle)


def normalize_ar(s: str) -> str:
    """Strip diacritics/tatweel, fold hamza/alef/ya/ta-marbuta variants, drop
    spaces — for fuzzy name matching only (never for display)."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = TASHKEEL_RE.sub("", s)
    trans = {
        "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
        "ؤ": "و", "ئ": "ي", "ء": "",
        "ة": "ه", "ى": "ي",
    }
    s = "".join(trans.get(ch, ch) for ch in s)
    s = re.sub(r"\s+", "", s)
    return s


def root_arabic_for(conn: sqlite3.Connection, root_bw: str) -> str:
    """Spaced Arabic root for display, e.g. 'kfr' -> 'ك ف ر'. Prefer the
    morphology table's own spelling; fall back to the buckwalter map."""
    row = conn.execute(
        "SELECT root_arabic FROM morphology WHERE root_buckwalter = ? AND root_arabic IS NOT NULL LIMIT 1",
        (root_bw,),
    ).fetchone()
    if row and row["root_arabic"]:
        return row["root_arabic"]
    try:
        return space_root(buckwalter_to_arabic(root_bw))
    except Exception:
        return root_bw


# ------------------------------------------------------------------------
# Insertion
# ------------------------------------------------------------------------

def clean_line(s: str | None) -> str | None:
    """Remove tatweel (kashida U+0640 — decorative elongation, never semantic)
    and collapse whitespace. Applied to every stored hemistich so source
    artifacts (Wikisource justification, scrape noise) don't pollute the text
    or the root extractor."""
    if not s:
        return s
    s = s.replace("ـ", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s or None


def split_hemistichs(bayt: str) -> tuple[str, str | None]:
    """Best-effort split of a full bayt into ṣadr + ʿajuz. Datasets variously
    separate the two hemistichs by a run of spaces, a tab, '...', '،', or
    common ASCII markers. If we can't split, keep the whole line as ṣadr."""
    s = bayt.strip()
    for sep in ["\t", " *** ", " ** ", " ... ", "...", " ـ ", " — ", " – "]:
        if sep in s:
            a, _, b = s.partition(sep)
            return a.strip(), (b.strip() or None)
    m = re.split(r"\s{2,}", s)
    if len(m) == 2:
        return m[0].strip(), m[1].strip()
    return s, None


def insert_poem(conn: sqlite3.Connection, p: dict, lines: list[dict]) -> int:
    cur = conn.execute(
        """INSERT INTO poetry_poems
           (poet, poet_latin, era, title, meter, rhyme, tags, auth_tier,
            source, source_ref, full_text, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            p.get("poet"), p.get("poet_latin"), p.get("era"), p.get("title"),
            p.get("meter"), p.get("rhyme"), p.get("tags"),
            (p.get("auth_tier") or "C").upper(),
            p.get("source"), p.get("source_ref"), p.get("full_text"), p.get("notes"),
        ),
    )
    poem_id = cur.lastrowid
    for i, ln in enumerate(lines, start=1):
        h1 = ln.get("hemistich1")
        h2 = ln.get("hemistich2")
        if h1 is None and ln.get("text"):
            h1, h2 = split_hemistichs(ln["text"])
        h1, h2 = clean_line(h1), clean_line(h2)
        text_plain = clean_line(ln.get("text_plain")) or " ".join(x for x in [h1, h2] if x)
        conn.execute(
            """INSERT OR IGNORE INTO poetry_lines
               (poem_id, line_no, hemistich1, hemistich2, text_plain)
               VALUES (?,?,?,?,?)""",
            (poem_id, ln.get("line_no", i), h1, h2, text_plain),
        )
    return poem_id


def delete_poem(conn: sqlite3.Connection, poem_id: int) -> None:
    line_ids = [r["id"] for r in conn.execute(
        "SELECT id FROM poetry_lines WHERE poem_id = ?", (poem_id,))]
    if line_ids:
        qmarks = ",".join("?" * len(line_ids))
        conn.execute(f"DELETE FROM poetry_line_roots WHERE line_id IN ({qmarks})", line_ids)
    conn.execute("DELETE FROM poetry_lines WHERE poem_id = ?", (poem_id,))
    conn.execute("DELETE FROM poetry_poems WHERE id = ?", (poem_id,))


# ------------------------------------------------------------------------
# load-muallaqat
# ------------------------------------------------------------------------

def cmd_load_muallaqat(args) -> int:
    path = args.file or DEFAULT_MUALLAQAT_JSON
    if not os.path.exists(path):
        print(f"ERROR: seed file not found: {path}", file=sys.stderr)
        return 1
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    poems = data.get("poems") if isinstance(data, dict) else data
    if not poems:
        print("No poems in seed file.")
        return 0

    conn = get_conn()
    ensure_schema(conn)
    added = skipped = replaced = 0
    try:
        for p in poems:
            ref = p.get("source_ref") or f"{p.get('poet')}|{p.get('title')}"
            existing = conn.execute(
                "SELECT id FROM poetry_poems WHERE source_ref = ?", (ref,)
            ).fetchone()
            if existing:
                if not args.force:
                    skipped += 1
                    continue
                delete_poem(conn, existing["id"])
                replaced += 1
            p.setdefault("source", "muallaqat")
            p.setdefault("source_ref", ref)
            p.setdefault("auth_tier", "A")
            insert_poem(conn, p, p.get("lines") or [])
            added += 1
        conn.commit()
    finally:
        conn.close()
    print(f"load-muallaqat: {added} loaded ({replaced} replaced), {skipped} skipped "
          f"(already present; --force to overwrite). Source: {path}")
    return 0


# ------------------------------------------------------------------------
# load-kaggle
# ------------------------------------------------------------------------

def parse_tags(tags: str | None) -> tuple[str | None, str | None, bool]:
    """From an aldiwan-style tag string like
    'قصائد المعلقات, عموديه, بحر الطويل,  قافية اللام (ل)' pull out the
    meter (بحر …), the rhyme (قافية …), and whether it's a Muʿallaqa."""
    if not tags:
        return None, None, False
    meter = rhyme = None
    m = re.search(r"بحر\s+([^,]+)", tags)
    if m:
        meter = m.group(1).strip()
    rq = re.search(r"قافية\s+([^,]+)", tags)
    if rq:
        rhyme = rq.group(1).strip()
    is_muallaqa = "معلق" in normalize_ar(tags)
    return meter, rhyme, is_muallaqa


def detect_column(header: list[str], kind: str, override: str | None) -> str | None:
    if override:
        return override if override in header else None
    norm_header = {normalize_ar(h): h for h in header}
    lower_header = {h.lower().strip(): h for h in header}
    for cand in COL_CANDIDATES[kind]:
        if cand in header:
            return cand
        if cand.lower() in lower_header:
            return lower_header[cand.lower()]
        nc = normalize_ar(cand)
        if nc in norm_header:
            return norm_header[nc]
    return None


def cmd_load_kaggle(args) -> int:
    path = args.csv
    if not os.path.exists(path):
        print(f"ERROR: CSV not found: {path}\n"
              f"  Download mdanok/arabic-poetry-dataset from Kaggle and place it there.",
              file=sys.stderr)
        return 1
    csv.field_size_limit(10_000_000)  # some qaṣīdas are long

    if args.eras:
        want_eras = {normalize_ar(e) for e in args.eras.split(",") if e.strip()}
    else:
        want_eras = {normalize_ar(v) for v in JAHILI_ERA_VALUES}

    conn = get_conn()
    ensure_schema(conn)
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames or []
            cols = {k: detect_column(header, k, getattr(args, f"{k}_col", None))
                    for k in COL_CANDIDATES}
            if not cols["text"]:
                print(f"ERROR: could not find a poem-text column. Header: {header}\n"
                      f"  Pass --text-col <name>.", file=sys.stderr)
                return 1
            if not cols["era"]:
                print("WARNING: no era column detected — would load ALL rows. "
                      "Pass --era-col <name>.", file=sys.stderr)
            print(f"load-kaggle: columns -> { {k: v for k, v in cols.items() if v} }")

            source = f"kaggle:{os.path.basename(path)}"
            existing = {r["source_ref"] for r in conn.execute(
                "SELECT source_ref FROM poetry_poems WHERE source = ?", (source,))
                if r["source_ref"]}

            added = lines_total = skipped_era = skipped_dup = 0
            for row in reader:
                era_val = (row.get(cols["era"]) or "").strip() if cols["era"] else ""
                if cols["era"] and normalize_ar(era_val) not in want_eras:
                    skipped_era += 1
                    continue
                text = (row.get(cols["text"]) or "").strip()
                if not text:
                    continue
                poet = (row.get(cols["poet"]) or "").strip() if cols["poet"] else None
                title = (row.get(cols["title"]) or "").strip() if cols["title"] else None
                tags = (row.get(cols["tags"]) or "").strip() if cols["tags"] else None
                ref = f"{source}|{poet}|{title}"
                if ref in existing and not args.force:
                    skipped_dup += 1
                    continue

                meter, rhyme, _is_m = parse_tags(tags)
                shatrs = [s.strip() for s in re.split(r"[\r\n]+", text) if s.strip()]
                if not shatrs:
                    continue
                if args.granularity == "line":
                    lines = [{"text": s} for s in shatrs]
                else:  # 'pairs': aldiwan stores one hemistich per line -> (ṣadr, ʿajuz)
                    lines = [
                        {"hemistich1": shatrs[i],
                         "hemistich2": shatrs[i + 1] if i + 1 < len(shatrs) else None}
                        for i in range(0, len(shatrs), 2)
                    ]
                p = {
                    "poet": poet, "era": era_val or "jahili", "title": title,
                    "meter": meter, "rhyme": rhyme, "tags": tags, "auth_tier": "C",
                    "source": source, "source_ref": ref, "full_text": text,
                }
                insert_poem(conn, p, lines)
                existing.add(ref)
                added += 1
                lines_total += len(lines)
                if args.limit and added >= args.limit:
                    break
            conn.commit()
    finally:
        conn.close()
    print(f"load-kaggle: {added} poems ({lines_total} abyāt) loaded as Tier C "
          f"[skipped {skipped_era} off-era, {skipped_dup} already-loaded]. "
          f"Run `tiers` next to promote Muʿallaqāt / major poets.")
    return 0


# ------------------------------------------------------------------------
# tiers  (promote authentication tiers)
# ------------------------------------------------------------------------

def cmd_tiers(args) -> int:
    conn = get_conn()
    ensure_schema(conn)
    changed = {"A": 0, "B": 0}
    try:
        rows = conn.execute(
            "SELECT id, poet, title, tags, auth_tier FROM poetry_poems").fetchall()
        for r in rows:
            poet_n = normalize_ar(r["poet"] or "")
            marker_n = normalize_ar((r["title"] or "") + " " + (r["tags"] or ""))
            cur_tier = (r["auth_tier"] or "C").upper()
            target = None
            is_muallaqa_poet = any(k in poet_n for k in MUALLAQAT_POET_KEYS)
            is_major = any(k in poet_n for k in MAJOR_JAHILI_POET_KEYS)
            # The Muʿallaqa marker lives in the tags ('قصائد المعلقات') for the
            # scraped corpus, and in the title for the hand-curated seed.
            if is_muallaqa_poet and "معلق" in marker_n:
                target = "A"
            elif is_muallaqa_poet:
                target = "B"
            elif is_major:
                target = "B"
            if target and TIER_RANK[target] > TIER_RANK[cur_tier]:
                conn.execute("UPDATE poetry_poems SET auth_tier = ? WHERE id = ?",
                             (target, r["id"]))
                changed[target] += 1
        conn.commit()
    finally:
        conn.close()
    print(f"tiers: promoted {changed['A']} poem(s) to A, {changed['B']} to B "
          f"(never downgrades; hand-curated A stays A).")
    return 0


# ------------------------------------------------------------------------
# index-root  (LLM root extraction)
# ------------------------------------------------------------------------

EXTRACT_SYSTEM = """\
You are a classical-Arabic morphology specialist. You will be given ONE
triliteral (or quadriliteral) Arabic root and a numbered list of lines of
pre-Islamic poetry. Your job: find every line that contains a word
DERIVED from that exact root — and ignore coincidental letter overlap.

Rules:
  - Judge by the genuine morphological root, not surface letters. A word
    shares the root only if its consonantal skeleton genuinely derives from
    it under normal Arabic derivation (counting weak-letter elision,
    assimilation, gemination, hamza shifts).
  - Do NOT include a line just because the three letters appear; e.g. a
    different word that merely contains ك, ف, ر in sequence is not K-F-R
    unless it really derives from كفر.
  - For each genuine match, give the surface word as it appears and a
    one-line sense of how it is used IN THAT LINE (physical? metaphor?).
  - Return STRICT JSON only. If no line matches, return an empty array.

Output ONLY a JSON array, no preamble:
[
  {"line_id": <int from the list>, "surface_word": "<word as written>",
   "sense_hint": "<≤12 words: how it's used here>", "confidence": 0.0-1.0},
  ...
]
"""


def call_claude(model: str, system: str, user: str, api_key: str) -> str:
    last_err = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = requests.post(
                ANTHROPIC_URL,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": model,
                    "max_tokens": MAX_TOKENS,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
                timeout=300,
            )
        except requests.RequestException as e:
            last_err = f"request error: {e}"
        else:
            if resp.status_code == 200:
                blocks = resp.json().get("content") or []
                return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
            last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"
        if attempt < MAX_ATTEMPTS:
            time.sleep((2 ** attempt) + 1)
    raise RuntimeError(f"Claude failed after {MAX_ATTEMPTS} attempts: {last_err}")


def parse_json_array(raw: str) -> list:
    """Robustly extract a JSON array even if the model wraps it in fences or
    adds a stray sentence. Bracket-matches from the first '[' to its partner so
    trailing prose can't cause an 'Extra data' failure (which would silently
    drop a chunk's matches)."""
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text).strip()
    try:
        v = json.loads(text)
        return v if isinstance(v, list) else []
    except Exception:
        pass
    start = text.find("[")
    if start < 0:
        return []
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                try:
                    v = json.loads(text[start:i + 1])
                    return v if isinstance(v, list) else []
                except Exception:
                    return []
    return []


def cmd_index_root(args) -> int:
    root_bw = args.root
    tiers = [t.upper() for t in args.tiers]
    conn = get_conn()
    ensure_schema(conn)
    try:
        root_ar = root_arabic_for(conn, root_bw)
        qmarks = ",".join("?" * len(tiers))
        lines = conn.execute(
            f"""SELECT pl.id, pl.text_plain, pp.poet, pp.auth_tier
                FROM poetry_lines pl JOIN poetry_poems pp ON pp.id = pl.poem_id
                WHERE pp.auth_tier IN ({qmarks})
                ORDER BY pp.auth_tier DESC, pl.poem_id, pl.line_no""",
            tiers,
        ).fetchall()
        if not lines:
            print(f"index-root {root_bw}: no poetry lines in tiers {tiers}. "
                  f"Load + tier the corpus first.")
            return 0

        if not args.force:
            done = {r["line_id"] for r in conn.execute(
                "SELECT line_id FROM poetry_line_roots WHERE root_buckwalter = ?",
                (root_bw,))}
            lines = [l for l in lines if l["id"] not in done]

        prefiltered = len(lines)
        if args.prefilter:
            radicals = bare(root_ar).replace(" ", "")
            lines = [l for l in lines if ordered_subseq(radicals, bare(l["text_plain"]))]
            print(f"  prefilter (subsequence {radicals}): {prefiltered} -> {len(lines)} "
                  f"candidate lines. (Recall-safe for SOUND roots only.)")
        if args.limit:
            lines = lines[: args.limit]

        print(f"index-root {root_bw} ({root_ar}): scanning {len(lines)} lines "
              f"in tiers {tiers} with {args.model} ...")

        api_key = get_claude_api_key(args.api_key)
        if not api_key and not args.dry_run:
            print("ERROR: no Claude API key (admin_preferences/CLAUDE_API_KEY/--api-key).",
                  file=sys.stderr)
            return 1

        total_found = 0
        for start in range(0, len(lines), LINES_PER_CHUNK):
            chunk = lines[start:start + LINES_PER_CHUNK]
            listing = "\n".join(f"  [{l['id']}] {l['text_plain']}" for l in chunk)
            user = (f"ROOT: {root_ar}  (Buckwalter: {root_bw})\n\n"
                    f"LINES (each prefixed with its line_id in brackets):\n{listing}\n\n"
                    f"Return the JSON array of lines that genuinely use this root.")
            if args.dry_run:
                print(f"\n--- chunk {start//LINES_PER_CHUNK + 1} prompt ({len(chunk)} lines) ---")
                print(user[:1200])
                print("  ...(dry-run: not calling Claude)")
                continue

            raw = call_claude(args.model, EXTRACT_SYSTEM, user, api_key)
            try:
                matches = parse_json_array(raw)
            except Exception as e:
                print(f"  chunk {start//LINES_PER_CHUNK + 1}: parse error {e}", file=sys.stderr)
                continue

            valid_ids = {l["id"] for l in chunk}
            for m in matches:
                if isinstance(m, int):            # model returned bare line_ids
                    m = {"line_id": m}
                if not isinstance(m, dict):
                    continue
                lid = m.get("line_id")
                if lid not in valid_ids:
                    continue  # reject hallucinated/foreign line ids
                conn.execute(
                    """INSERT OR REPLACE INTO poetry_line_roots
                       (line_id, root_buckwalter, root_arabic, surface_word,
                        sense_hint, extractor_model, confidence, verified)
                       VALUES (?,?,?,?,?,?,?,
                               COALESCE((SELECT verified FROM poetry_line_roots
                                         WHERE line_id=? AND root_buckwalter=?), 0))""",
                    (lid, root_bw, root_ar, m.get("surface_word"),
                     m.get("sense_hint"), args.model, m.get("confidence"),
                     lid, root_bw),
                )
                total_found += 1
            conn.commit()
            print(f"  chunk {start//LINES_PER_CHUNK + 1}/"
                  f"{(len(lines)+LINES_PER_CHUNK-1)//LINES_PER_CHUNK}: "
                  f"{len(matches)} match(es)")

        if not args.dry_run:
            print(f"index-root {root_bw}: {total_found} candidate occurrence(s) indexed "
                  f"(verified=0). Run `verify-root {root_bw}` to confirm quotable lines.")
    finally:
        conn.close()
    return 0


# ------------------------------------------------------------------------
# index-next / index-add  (AGENT-DRIVEN indexing — no API; Claude Code judges)
# ------------------------------------------------------------------------

def cmd_index_next(args) -> int:
    """Emit the next batch of un-scanned candidate lines for a root, as JSON,
    for the Claude Code indexing loop to judge. Prefilters to likely candidates
    (surface forms by default) so batches aren't mostly noise."""
    conn = get_conn()
    ensure_schema(conn)
    try:
        tiers = [t.upper() for t in args.tiers]
        root_ar = root_arabic_for(conn, args.root)
        qmarks = ",".join("?" * len(tiers))
        rows = conn.execute(
            f"""SELECT pl.id, pl.text_plain
                FROM poetry_lines pl JOIN poetry_poems pp ON pp.id = pl.poem_id
                WHERE pp.auth_tier IN ({qmarks})
                  AND pl.id NOT IN (SELECT line_id FROM poetry_root_scanned
                                    WHERE root_buckwalter = ?)
                ORDER BY pp.auth_tier DESC, pl.poem_id, pl.line_no""",
            (*tiers, args.root),
        ).fetchall()

        forms = None
        if args.forms:
            forms = [bare(f) for f in args.forms.split(",") if f.strip()]
        elif not args.no_prefilter:
            forms = [bare(f) for f in (SURFACE_FORMS.get(args.root) or [])]
        if forms:
            rows = [r for r in rows if any(f in bare(r["text_plain"]) for f in forms)]
        elif args.subseq:
            rad = bare(root_ar).replace(" ", "")
            rows = [r for r in rows if ordered_subseq(rad, bare(r["text_plain"]))]

        batch = rows[: args.count]
        out = {
            "root": args.root, "root_arabic": root_ar, "tiers": tiers,
            "remaining": len(rows), "batch": len(batch),
            "lines": [{"id": r["id"], "text": r["text_plain"]} for r in batch],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    finally:
        conn.close()
    return 0


def cmd_index_add(args) -> int:
    """Store the agent's verdicts. Payload JSON:
       {"scanned": [<all line_ids in the judged batch>],
        "matches": [{"line_id", "surface_word", "sense_hint", "confidence"}, ...]}
    Every scanned line is marked done (so it's never re-offered); only genuine
    matches go into poetry_line_roots. A match must be among the scanned ids."""
    with open(args.file, encoding="utf-8") as f:
        payload = json.load(f)
    scanned = [int(x) for x in (payload.get("scanned") or [])]
    matches = payload.get("matches") or []
    conn = get_conn()
    ensure_schema(conn)
    try:
        root_ar = root_arabic_for(conn, args.root)
        scanned_set = set(scanned)
        for lid in scanned:
            conn.execute(
                "INSERT OR IGNORE INTO poetry_root_scanned (root_buckwalter, line_id) VALUES (?,?)",
                (args.root, lid))
        stored = rejected = 0
        for m in matches:
            lid = m.get("line_id")
            if lid not in scanned_set:
                rejected += 1
                continue  # a match must be a line we were actually given
            conn.execute(
                """INSERT OR REPLACE INTO poetry_line_roots
                   (line_id, root_buckwalter, root_arabic, surface_word, sense_hint,
                    extractor_model, confidence, verified)
                   VALUES (?,?,?,?,?,?,?,
                           COALESCE((SELECT verified FROM poetry_line_roots
                                     WHERE line_id=? AND root_buckwalter=?), 0))""",
                (lid, args.root, root_ar, m.get("surface_word"), m.get("sense_hint"),
                 "claude-code", m.get("confidence"), lid, args.root))
            stored += 1
        conn.commit()
        rej = f", {rejected} rejected (not in batch)" if rejected else ""
        print(f"index-add {args.root}: {len(scanned)} scanned, {stored} match(es) stored{rej}.")
    finally:
        conn.close()
    return 0


# ------------------------------------------------------------------------
# verify-root
# ------------------------------------------------------------------------

def cmd_verify_root(args) -> int:
    conn = get_conn()
    ensure_schema(conn)
    try:
        if args.set:
            ids = [int(x) for x in args.set]
            qmarks = ",".join("?" * len(ids))
            conn.execute(
                f"UPDATE poetry_line_roots SET verified = 1 WHERE id IN ({qmarks})", ids)
            conn.commit()
            print(f"verify-root: marked {len(ids)} line_root id(s) verified.")
            return 0
        if args.all:
            n = conn.execute(
                "UPDATE poetry_line_roots SET verified = 1 WHERE root_buckwalter = ?",
                (args.root,)).rowcount
            conn.commit()
            print(f"verify-root {args.root}: marked all {n} candidate(s) verified.")
            return 0

        rows = conn.execute(
            """SELECT plr.id, plr.surface_word, plr.sense_hint, plr.confidence,
                      plr.verified, pp.poet, pp.auth_tier, pl.text_plain
               FROM poetry_line_roots plr
               JOIN poetry_lines pl ON pl.id = plr.line_id
               JOIN poetry_poems pp ON pp.id = pl.poem_id
               WHERE plr.root_buckwalter = ?
               ORDER BY pp.auth_tier DESC, plr.confidence DESC""",
            (args.root,)).fetchall()
        if not rows:
            print(f"verify-root {args.root}: no candidates indexed yet.")
            return 0
        print(f"verify-root {args.root}: {len(rows)} candidate(s). "
              f"Mark good ones with: verify-root {args.root} --set <id> [--set <id> ...]\n")
        for r in rows:
            mark = "✓" if r["verified"] else " "
            print(f"  [{mark}] id={r['id']:<5} tier={r['auth_tier']} "
                  f"conf={r['confidence']}  «{r['surface_word']}» — {r['sense_hint']}")
            print(f"        {r['poet'] or '?'}: {r['text_plain']}")
    finally:
        conn.close()
    return 0


# ------------------------------------------------------------------------
# stats
# ------------------------------------------------------------------------

PILOT_ROOTS = ["kfr", "wqy", "dhr", "krm", "jnn"]


def cmd_stats(args) -> int:
    conn = get_conn()
    ensure_schema(conn)
    try:
        print("━━━━━ poetry corpus ━━━━━")
        tier_rows = conn.execute(
            "SELECT auth_tier, COUNT(*) n FROM poetry_poems GROUP BY auth_tier ORDER BY auth_tier"
        ).fetchall()
        npoems = conn.execute("SELECT COUNT(*) n FROM poetry_poems").fetchone()["n"]
        nlines = conn.execute("SELECT COUNT(*) n FROM poetry_lines").fetchone()["n"]
        print(f"poems: {npoems}   lines: {nlines}")
        for r in tier_rows:
            print(f"  tier {r['auth_tier']}: {r['n']} poem(s)")

        print("\n━━━━━ root index ━━━━━")
        idx_rows = conn.execute(
            """SELECT root_buckwalter,
                      COUNT(*) n,
                      SUM(verified) v
               FROM poetry_line_roots GROUP BY root_buckwalter
               ORDER BY n DESC""").fetchall()
        if not idx_rows:
            print("  (no roots indexed yet — run index-root <bw>)")
        for r in idx_rows:
            print(f"  {r['root_buckwalter']:<6} {r['n']:>4} candidate(s), "
                  f"{r['v'] or 0} verified")

        print("\n━━━━━ pilot roots ━━━━━")
        for rb in PILOT_ROOTS:
            row = conn.execute(
                "SELECT COUNT(*) n, SUM(verified) v FROM poetry_line_roots WHERE root_buckwalter = ?",
                (rb,)).fetchone()
            print(f"  {rb:<6} {root_arabic_for(conn, rb):<10} "
                  f"poetry: {row['n']} cand / {row['v'] or 0} verified")
    finally:
        conn.close()
    return 0


# ------------------------------------------------------------------------
# main
# ------------------------------------------------------------------------

# ------------------------------------------------------------------------
# Full-poem translation (Phase 3) — only the poems quoted by an approved
# comparison/note get translated. Agent-driven loop, no API.
# ------------------------------------------------------------------------

def quoted_poem_ids(conn) -> set:
    """Poem ids referenced by any quoted line in the approved comparisons/notes."""
    lrids = set()
    for tbl in ("root_poetry_comparisons", "verse_poetry_notes"):
        try:
            for r in conn.execute(f"SELECT quoted_lines_json FROM {tbl} "
                                  "WHERE quoted_lines_json IS NOT NULL"):
                try:
                    for q in json.loads(r["quoted_lines_json"]):
                        if q.get("line_root_id"):
                            lrids.add(q["line_root_id"])
                except Exception:
                    pass
        except sqlite3.OperationalError:
            pass  # table not present yet
    if not lrids:
        return set()
    qmarks = ",".join("?" * len(lrids))
    rows = conn.execute(
        f"""SELECT DISTINCT pl.poem_id FROM poetry_line_roots plr
            JOIN poetry_lines pl ON pl.id = plr.line_id
            WHERE plr.id IN ({qmarks})""", list(lrids)).fetchall()
    return {r["poem_id"] for r in rows}


def cmd_trans_next(args) -> int:
    conn = get_conn(); ensure_schema(conn)
    try:
        todo = []
        for pid in sorted(quoted_poem_ids(conn)):
            tot = conn.execute("SELECT COUNT(*) n FROM poetry_lines WHERE poem_id=?",
                               (pid,)).fetchone()["n"]
            done = conn.execute("SELECT COUNT(*) n FROM poetry_lines WHERE poem_id=? "
                                "AND translation_en IS NOT NULL AND translation_en!=''",
                                (pid,)).fetchone()["n"]
            if done < tot:
                poet = conn.execute("SELECT poet FROM poetry_poems WHERE id=?",
                                    (pid,)).fetchone()["poet"]
                todo.append({"poem_id": pid, "poet": poet, "lines": tot, "translated": done})
        print(json.dumps({
            "poems_remaining": len(todo),
            "lines_remaining": sum(t["lines"] - t["translated"] for t in todo),
            "poems": todo[: args.count],
        }, ensure_ascii=False, indent=2))
    finally:
        conn.close()
    return 0


def cmd_trans_context(args) -> int:
    conn = get_conn(); ensure_schema(conn)
    try:
        pid = int(args.poem)
        p = conn.execute("SELECT poet, title, meter, rhyme, era FROM poetry_poems WHERE id=?",
                         (pid,)).fetchone()
        lines = conn.execute(
            "SELECT id, line_no, hemistich1, hemistich2, text_plain, translation_en "
            "FROM poetry_lines WHERE poem_id=? ORDER BY line_no", (pid,)).fetchall()
        untrans = [ln for ln in lines if not ln["translation_en"]]
        L = [f"# Poem {pid} — {p['poet']} · {p['title'] or ''}  (meter {p['meter'] or '?'}, "
             f"rhyme {p['rhyme'] or '?'})",
             f"Untranslated lines: {len(untrans)} of {len(lines)} (showing up to {args.limit}).",
             "Translate each line into clear, faithful, readable English — one English line per "
             "bayt. Keep the line_id.", ""]
        for ln in untrans[: args.limit]:
            arabic = ln["text_plain"] or " / ".join(x for x in [ln["hemistich1"], ln["hemistich2"]] if x)
            L.append(f"[{ln['id']}] (bayt {ln['line_no']}) {arabic}")
        print("\n".join(L))
    finally:
        conn.close()
    return 0


def cmd_trans_add(args) -> int:
    with open(args.file, encoding="utf-8") as f:
        payload = json.load(f)
    items = payload.get("translations") if isinstance(payload, dict) else payload
    conn = get_conn(); ensure_schema(conn)
    try:
        n = 0
        for it in (items or []):
            lid, en = it.get("line_id"), (it.get("english") or "").strip()
            if lid and en:
                conn.execute("UPDATE poetry_lines SET translation_en=? WHERE id=?", (en, lid))
                n += 1
        conn.commit()
        print(f"trans-add: stored {n} line translation(s).")
    finally:
        conn.close()
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="create the corpus schema only")

    sp = sub.add_parser("load-muallaqat", help="load the hand-curated Tier-A seed JSON")
    sp.add_argument("--file", default=None, help=f"default: {DEFAULT_MUALLAQAT_JSON}")
    sp.add_argument("--force", action="store_true", help="overwrite existing poems")

    sp = sub.add_parser("load-kaggle", help="load a scraped CSV, filtered to Jahilī (Tier C)")
    sp.add_argument("csv", help="path to the Kaggle CSV")
    sp.add_argument("--eras", default=None,
                    help="comma-separated era values to keep (default: Jahilī only). "
                         "e.g. --eras 'العصر الجاهلي,المخضرمون'")
    sp.add_argument("--granularity", choices=["pairs", "line"], default="pairs",
                    help="'pairs' (default): one hemistich per source line -> pair into "
                         "abyāt. 'line': each source line is a full bayt.")
    sp.add_argument("--limit", type=int, default=0, help="cap poems (for testing)")
    sp.add_argument("--force", action="store_true", help="reload poems already present")
    for k in COL_CANDIDATES:
        sp.add_argument(f"--{k}-col", default=None, help=f"override the {k} column name")

    sub.add_parser("tiers", help="promote Muʿallaqāt / major-poet poems to A/B")

    sp = sub.add_parser("index-root", help="LLM-extract a root's occurrences in the poetry")
    sp.add_argument("root", help="Buckwalter root, e.g. kfr")
    sp.add_argument("--tiers", default="AB", help="which tiers to scan (default AB)")
    sp.add_argument("--model", default=EXTRACT_MODEL,
                    help=f"default {EXTRACT_MODEL} (extraction is mechanical & cheap)")
    sp.add_argument("--prefilter", action="store_true",
                    help="only send lines whose bare text contains the radicals as an "
                         "ordered subsequence — big cost saver, RECALL-SAFE FOR SOUND "
                         "ROOTS ONLY (not weak و/ي or doubled roots like wqy, jnn)")
    sp.add_argument("--limit", type=int, default=0, help="cap lines (for testing)")
    sp.add_argument("--force", action="store_true", help="re-index already-scanned lines")
    sp.add_argument("--dry-run", action="store_true", help="print prompts, don't call Claude")
    sp.add_argument("--api-key", default=None)

    sp = sub.add_parser("index-next",
                        help="emit next batch of candidate lines (JSON) for the Claude Code loop")
    sp.add_argument("root", help="Buckwalter root")
    sp.add_argument("--tiers", default="AB", help="tiers to scan (default AB)")
    sp.add_argument("--count", type=int, default=40, help="lines per batch (default 40)")
    sp.add_argument("--forms", default=None,
                    help="comma-separated bare surface forms to prefilter by (overrides defaults)")
    sp.add_argument("--subseq", action="store_true",
                    help="prefilter by ordered-subsequence of radicals (sound roots) "
                         "if no surface forms are used")
    sp.add_argument("--no-prefilter", action="store_true", help="scan all lines, no prefilter")

    sp = sub.add_parser("index-add", help="store the loop's verdicts (scanned + matches)")
    sp.add_argument("root", help="Buckwalter root")
    sp.add_argument("--file", required=True, help="JSON: {scanned:[...], matches:[...]}")

    sp = sub.add_parser("verify-root", help="list / confirm a root's candidate lines")
    sp.add_argument("root", help="Buckwalter root")
    sp.add_argument("--set", action="append", default=[], help="line_root id(s) to mark verified")
    sp.add_argument("--all", action="store_true", help="mark ALL candidates verified (use with care)")

    sub.add_parser("stats", help="corpus + index coverage")

    sp = sub.add_parser("trans-next", help="next quoted poem(s) needing full translation")
    sp.add_argument("--count", type=int, default=1)
    sp = sub.add_parser("trans-context", help="a poem's untranslated lines, for the loop to translate")
    sp.add_argument("poem", help="poem_id")
    sp.add_argument("--limit", type=int, default=40, help="max lines per batch (long poems chunk)")
    sp = sub.add_parser("trans-add", help="store per-line English translations")
    sp.add_argument("poem", help="poem_id (for logging)")
    sp.add_argument("--file", required=True)

    args = p.parse_args()

    if args.cmd == "init":
        conn = get_conn(); ensure_schema(conn); conn.close()
        print(f"Schema ready in {DB}")
        return 0
    return {
        "load-muallaqat": cmd_load_muallaqat,
        "load-kaggle": cmd_load_kaggle,
        "tiers": cmd_tiers,
        "index-root": cmd_index_root,
        "index-next": cmd_index_next,
        "index-add": cmd_index_add,
        "verify-root": cmd_verify_root,
        "stats": cmd_stats,
        "trans-next": cmd_trans_next,
        "trans-context": cmd_trans_context,
        "trans-add": cmd_trans_add,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
