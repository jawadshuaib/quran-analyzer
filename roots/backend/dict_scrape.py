"""The Lexicon Library — respectful scraper for arabiclexicon.hawramani.com.

Fetches per-ROOT pages (one page = one root = all dictionaries) and stores each
selected dictionary's raw Arabic entry into `dictionary_entries` (pending). A
later /loop drafts the English translation + harmonized definition.

Etiquette: strictly serial, 1 request / SCRAPE_DELAY s, exponential backoff,
raw-HTML disk cache (pages are static since 2015 — never re-fetched), transparent
User-Agent with contact. See docs/lexicon-library-plan.md.

Usage:
    python dict_scrape.py init                 # create tables + seed dictionaries
    python dict_scrape.py sitemap              # build root_slug_index from the sitemaps
    python dict_scrape.py resolve Amn qwl      # debug: show resolved page slugs
    python dict_scrape.py scrape Amn rHm ktb   # scrape these Buckwalter roots
    python dict_scrape.py top 50               # scrape the 50 most frequent Qur'anic roots
    python dict_scrape.py pilot                # scrape the 10 pilot roots
    python dict_scrape.py show Amn             # print what was stored for a root
"""

import hashlib
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

from app import get_db  # noqa: E402
import buckwalter as bw  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(HERE, "data", "dict_cache")
SITEMAP_CACHE_DIR = os.path.join(HERE, "data", "dict_sitemap_cache")
BASE = "https://arabiclexicon.hawramani.com"
UA = ("al-nuqta-root-scraper/1.0 (+https://al-nuqta.com; jawad.php@gmail.com) "
      "respectful 1req/4s")
SCRAPE_DELAY = 4.0          # seconds between root-page requests (serial)
SITEMAP_DELAY = 1.5         # sitemaps are static XML (cheap) — a touch faster
REQ_TIMEOUT = (10, 90)      # connect, read — server is slow
SITEMAP_TIMEOUT = (10, 45)
PILOT_ROOTS = ["Amn", "rHm", "ktb", "Elm", "xlq", "Hmd", "slm", "qwl", "Sbr", "$kr"]

# --- Phase-1 (8, PD) + Phase-2 dictionaries. slug = hawramani WP category slug,
#     which is also the join key in each scraped definition-container's link. ---
SEED_DICTS = [
    # slug, cat_id, name_en, author, death_year, lang, quran_specific, phase, name_ar
    ("abdullah-ibn-abbas-gharib-al-quran-fi-shir-al-arab", 41, "Gharīb al-Qurʾān fī Shiʿr al-ʿArab", "ʿAbdullāh ibn ʿAbbās", 687, "ar", 1, 1, "غريب القرآن في شعر العرب"),
    ("al-khalil-b-ahmad-al-farahidi-kitab-al-ain", 5, "Kitāb al-ʿAin", "al-Khalīl al-Farāhīdī", 786, "ar", 0, 1, "كتاب العين"),
    ("al-sahib-bin-abbad-al-muhit-fi-l-lugha", 36, "al-Muḥīṭ fī l-Lugha", "al-Ṣāḥib b. ʿAbbād", 995, "ar", 0, 1, "المحيط في اللغة"),
    ("ibn-faris-maqayis-al-lugha", 9, "Maqāyīs al-Lugha", "Ibn Fāris", 1004, "ar", 0, 1, "مقاييس اللغة"),
    ("al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran", 33, "al-Mufradāt fī Gharīb al-Qurʾān", "al-Rāghib al-Iṣfahānī", 1109, "ar", 1, 1, "المفردات في غريب القرآن"),
    ("al-zamakhshari-asas-al-balagha", 11, "Asās al-Balāgha", "al-Zamakhsharī", 1143, "ar", 0, 1, "أساس البلاغة"),
    ("zayn-al-din-al-razi-mukhtar-al-sihah", 14, "Mukhtār al-Ṣiḥāḥ", "Zayn al-Dīn al-Rāzī", 1268, "ar", 0, 1, "مختار الصحاح"),
    ("ibn-manzur-lisan-al-arab", 3, "Lisān al-ʿArab", "Ibn Manẓūr", 1311, "ar", 0, 1, "لسان العرب"),
    ("al-fayyumi-al-misbah-al-munir-fi-gharib-al-sharh-al-kabir", 19, "al-Miṣbāḥ al-Munīr", "al-Fayyūmī", 1368, "ar", 0, 1, "المصباح المنير"),
    ("william-edward-lane-arabic-english-lexicon", 50, "Arabic-English Lexicon", "Edward William Lane", 1876, "en", 0, 1, "Lane's Lexicon"),
    # Phase 2
    ("ismail-bin-hammad-al-jawhari-taj-al-lugha-wa-sihah-al-arabiya", 8, "al-Ṣiḥāḥ", "al-Jawharī", 1003, "ar", 0, 2, "الصحاح"),
    ("ibn-sida-al-mursi-al-muhkam-wa-l-muhit-al-aazam", 10, "al-Muḥkam wa-l-Muḥīṭ al-Aʿẓam", "Ibn Sīda al-Mursī", 1066, "ar", 0, 2, "المحكم والمحيط الأعظم"),
    ("abu-hayyan-al-gharnati-tuhfat-al-arib-bi-ma-fi-l-quran-min-al-gharib", 18, "Tuḥfat al-Arīb", "Abū Ḥayyān al-Gharnāṭī", 1344, "ar", 1, 2, "تحفة الأريب بما في القرآن من الغريب"),
    ("firuzabadi-al-qamus-al-muhit", 21, "al-Qāmūs al-Muḥīṭ", "Firūzābādī", 1414, "ar", 0, 2, "القاموس المحيط"),
    ("murtada-al-zabidi-taj-al-arus-fi-jawahir-al-qamus", 27, "Tāj al-ʿArūs", "Murtaḍā al-Zabīdī", 1790, "ar", 0, 2, "تاج العروس"),
    ("habib-anthony-salmone-an-advanced-learners-arabic-english-dictionary", 52, "An Advanced Learner's Arabic-English Dictionary", "Habib Anthony Salmoné", 1889, "en", 0, 2, "Salmoné"),
]
SELECTED_SLUGS = {d[0] for d in SEED_DICTS}


def ensure_schema(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS dictionaries (
        id INTEGER PRIMARY KEY, slug TEXT UNIQUE NOT NULL,
        hawramani_category_id INTEGER, name_en TEXT, name_ar TEXT,
        author TEXT, author_death_year INTEGER, language TEXT,
        is_quran_specific INTEGER DEFAULT 0, phase INTEGER DEFAULT 1,
        sort_order INTEGER, description_en TEXT
    );
    CREATE TABLE IF NOT EXISTS dictionary_entries (
        id INTEGER PRIMARY KEY,
        root_buckwalter TEXT NOT NULL, root_arabic TEXT,
        dictionary_slug TEXT NOT NULL,
        original_text_ar TEXT, translation_en TEXT, harmonized_en TEXT,
        source_url TEXT, source_anchor TEXT, scrape_hash TEXT,
        review_status TEXT DEFAULT 'pending', hidden INTEGER DEFAULT 0,
        confidence REAL, gen_meta TEXT, raw_response TEXT,
        created_at TEXT DEFAULT (datetime('now')), edited_at TEXT,
        UNIQUE(root_buckwalter, dictionary_slug)
    );
    CREATE INDEX IF NOT EXISTS idx_dictentry_root ON dictionary_entries(root_buckwalter);
    CREATE TABLE IF NOT EXISTS root_slug_index (
        normalized_root TEXT, arabic_slug TEXT, page_url TEXT,
        PRIMARY KEY (normalized_root, arabic_slug)
    );
    CREATE INDEX IF NOT EXISTS idx_slug_norm ON root_slug_index(normalized_root);
    """)
    conn.commit()


def seed_dictionaries(conn):
    for i, (slug, cat, name_en, author, dy, lang, quran, phase, name_ar) in enumerate(SEED_DICTS):
        conn.execute(
            "INSERT INTO dictionaries (slug, hawramani_category_id, name_en, name_ar, author, "
            "author_death_year, language, is_quran_specific, phase, sort_order) "
            "VALUES (?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(slug) DO UPDATE SET hawramani_category_id=excluded.hawramani_category_id, "
            "name_en=excluded.name_en, name_ar=excluded.name_ar, author=excluded.author, "
            "author_death_year=excluded.author_death_year, language=excluded.language, "
            "is_quran_specific=excluded.is_quran_specific, phase=excluded.phase, sort_order=excluded.sort_order",
            (slug, cat, name_en, name_ar, author, dy, lang, quran, phase, dy),  # sort by death year
        )
    conn.commit()


# --------------------------------------------------------------------------
# Root → hawramani slug (handle the hamza-carrier mismatch: DB "Amn" = ا م ن
# bare-alef; the site uses أمن hamza-alef). Try candidate carriers, verify by fetch.
# --------------------------------------------------------------------------
def root_candidates(root_bw):
    """Ordered candidate Arabic slugs for a Buckwalter root. Alef-initial roots
    get the bare-alef and hamza-alef spellings (the two pages the site actually
    splits entries across); the OVERNIGHT run should resolve via the sitemap
    slug-index instead of probing, to avoid slow 404 lookups."""
    ar = bw.buckwalter_to_arabic(root_bw)          # e.g. Amn -> امن (bare)
    cands = [ar]
    if ar and ar[0] == "ا":                        # bare alef -> also try hamza-alef
        cands.append("أ" + ar[1:])
    seen, out = set(), []
    for c in cands:
        if c not in seen:
            seen.add(c); out.append(c)
    return out


# --------------------------------------------------------------------------
# Sitemap slug-index — deterministic Buckwalter-root → hawramani-page resolution.
# Built once from the ~149 static XML sitemaps; avoids blind 404-probing the slow
# server at scrape time and captures every spelling variant a root is split across.
# --------------------------------------------------------------------------
from urllib.parse import unquote, quote  # noqa: E402

# Strip Arabic diacritics: harakat (064B-0652), superscript alef (0670), tatweel
# (0640), hamza/madda combining marks (0653-0655). Then unify carriers so a root's
# spelling variants share ONE skeleton (bare أمن/امن → امن).
_TASHKIL_RE = re.compile("[ً-ٰٕـ]")
_CARRIER_MAP = {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ؤ": "و", "ئ": "ي", "ى": "ي", "ة": "ه"}
_ARABIC_LETTER_RE = re.compile("[^ء-ي]")


def norm_root(s):
    """Consonantal skeleton of an Arabic string: url-decode, strip tashkil, unify
    hamza carriers, keep only Arabic letters. Applied identically to sitemap slugs
    and to a query root so spelling variants collapse to the same key."""
    if not s:
        return ""
    s = unquote(s)
    s = _TASHKIL_RE.sub("", s)
    s = "".join(_CARRIER_MAP.get(ch, ch) for ch in s)
    return _ARABIC_LETTER_RE.sub("", s)


def _slug_from_sitemap_url(u):
    """Extract the url-decoded Arabic slug from a hawramani page URL, or None for
    non-content pages (feeds, wp-*, category/author/page listings, latin-only)."""
    m = re.search(r"hawramani\.com/([^/]+)/?$", u.strip())
    if not m:
        return None
    slug = unquote(m.group(1))
    if slug.startswith(("wp-", "?", "category", "author", "page", "feed", "comments")):
        return None
    if not re.search("[ء-ي]", slug):   # must contain Arabic
        return None
    return slug


def _sitemap_cache_path(url):
    safe = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    return os.path.join(SITEMAP_CACHE_DIR, f"sm_{safe}.xml")


def fetch_xml(url, session):
    """GET a sitemap XML, cached on disk. Returns text or None."""
    os.makedirs(SITEMAP_CACHE_DIR, exist_ok=True)
    cp = _sitemap_cache_path(url)
    if os.path.exists(cp):
        return open(cp, encoding="utf-8").read()
    delay = 6.0
    for _ in range(3):
        try:
            r = session.get(url, timeout=SITEMAP_TIMEOUT)
            if r.status_code == 404:
                return None
            if r.status_code == 200 and len(r.text) > 50:
                with open(cp, "w", encoding="utf-8") as f:
                    f.write(r.text)
                time.sleep(SITEMAP_DELAY)
                return r.text
            time.sleep(min(delay, 30)); delay *= 2
        except requests.RequestException:
            time.sleep(min(delay, 30)); delay *= 2
    return None


def _locs(xml):
    return re.findall(r"<loc>\s*(.*?)\s*</loc>", xml, re.S)


def discover_sitemaps(session):
    """Seed sitemap URLs from robots.txt (Sitemap: lines), falling back to the
    conventional /sitemap.xml index."""
    seeds = []
    try:
        r = session.get(f"{BASE}/robots.txt", timeout=SITEMAP_TIMEOUT)
        if r.status_code == 200:
            seeds = re.findall(r"(?im)^\s*Sitemap:\s*(\S+)", r.text)
        time.sleep(SITEMAP_DELAY)
    except requests.RequestException:
        pass
    if not seeds:
        seeds = [f"{BASE}/sitemap.xml"]
    return list(dict.fromkeys(seeds))


def build_sitemap_index(conn, session, max_skeleton_len=6):
    """BFS the sitemap tree → root_slug_index. Keeps only short skeletons (≤6
    letters) so root pages are captured but long word/form pages are skipped."""
    conn.execute("DROP TABLE IF EXISTS root_slug_index")   # clean rebuild
    ensure_schema(conn)
    frontier = discover_sitemaps(session)
    seen_maps, page_urls = set(), []
    print(f"discovering from {len(frontier)} seed sitemap(s)...")
    while frontier:
        sm = frontier.pop(0)
        if sm in seen_maps:
            continue
        seen_maps.add(sm)
        xml = fetch_xml(sm, session)
        if not xml:
            print(f"  ! {sm} — unreachable")
            continue
        locs = _locs(xml)
        if "<sitemapindex" in xml[:3000]:
            new = [l for l in locs if l not in seen_maps]
            frontier.extend(new)
            print(f"  index {sm.split('/')[-1]} -> {len(locs)} child sitemaps")
        else:
            page_urls.extend(locs)
            print(f"  {sm.split('/')[-1]} -> {len(locs)} urls  (pages so far: {len(page_urls)})")
    rows = {}    # (normalized_root, slug) -> page_url
    for u in page_urls:
        slug = _slug_from_sitemap_url(u)
        if not slug:
            continue
        nr = norm_root(slug)
        if not (2 <= len(nr) <= max_skeleton_len):
            continue
        rows.setdefault((nr, slug), u)
    conn.executemany(
        "INSERT OR IGNORE INTO root_slug_index (normalized_root, arabic_slug, page_url) VALUES (?,?,?)",
        [(k[0], k[1], v) for k, v in rows.items()])
    conn.commit()
    distinct = len({k[0] for k in rows})
    print(f"\nsitemap index built: {len(seen_maps)} sitemaps fetched, {len(page_urls)} page URLs, "
          f"{len(rows)} slugs across {distinct} distinct root skeletons.")
    return len(rows)


MAX_VARIANT_PAGES = 6      # cap fetches per root (typical root has 2-5 variants)


def resolve_slugs(conn, root_bw):
    """Deterministic root → all page slugs via the sitemap index.

    hawramani splits a single root's dictionary entries across several vocalized
    headword pages (bare علم, sign عَلَم, maṣdar عِلْم, verb عَلِمَ, plus hamza
    carriers) — each page carrying a DIFFERENT subset of dictionaries. A keystone
    like Maqāyīs may sit only on the verb page, not the bare one. So we return every
    exact-skeleton variant (the WHERE-clause already excludes derived/suffixed forms,
    which have longer skeletons) and let scrape_root MERGE them, keeping the fullest
    text per dictionary. Sense-pages carry excluded dicts too, but SELECTED_SLUGS
    filters those out. Clean bare/hamza spellings first; fall back to probing on a miss."""
    nr = norm_root(bw.buckwalter_to_arabic(root_bw))
    idx = [r["arabic_slug"] for r in conn.execute(
        "SELECT arabic_slug FROM root_slug_index WHERE normalized_root=? "
        "ORDER BY LENGTH(arabic_slug), arabic_slug", (nr,)).fetchall()]
    if not idx:
        return root_candidates(root_bw)                        # index miss → probe
    prefer = [c for c in root_candidates(root_bw) if c in idx]  # bare + hamza-alef, first
    rest = [s for s in idx if s not in prefer]
    return (prefer + rest)[:MAX_VARIANT_PAGES]


def top_roots(conn, n):
    """Top-N Qur'anic roots by word-occurrence count (most load-bearing first)."""
    rows = conn.execute(
        "SELECT root_buckwalter, COUNT(*) c FROM morphology "
        "WHERE root_buckwalter IS NOT NULL AND root_buckwalter!='' "
        "GROUP BY root_buckwalter ORDER BY c DESC LIMIT ?", (n,)).fetchall()
    return [r["root_buckwalter"] for r in rows]


def _cache_path(slug):
    safe = hashlib.sha1(slug.encode("utf-8")).hexdigest()[:16]
    return os.path.join(CACHE_DIR, f"{safe}.html")


def fetch_page(arabic_slug, session):
    """GET the root page; cached on disk. Returns (html, url) or (None, None)."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cp = _cache_path(arabic_slug)
    if os.path.exists(cp):
        return open(cp, encoding="utf-8").read(), f"{BASE}/{arabic_slug}/"
    from urllib.parse import quote
    url = f"{BASE}/{quote(arabic_slug)}/"
    delay = 8.0
    for attempt in range(3):                        # fail fast on absent/slow candidates
        try:
            r = session.get(url, timeout=REQ_TIMEOUT)
            if r.status_code == 404:
                return None, None
            if r.status_code == 200 and len(r.text) > 2000:
                with open(cp, "w", encoding="utf-8") as f:
                    f.write(r.text)
                time.sleep(SCRAPE_DELAY)             # be polite AFTER a real fetch
                return r.text, url
            time.sleep(min(delay, 30)); delay *= 2
        except requests.RequestException:
            time.sleep(min(delay, 30)); delay *= 2
    return None, None


# --------------------------------------------------------------------------
# Parse a root page → {dictionary_slug: {text, anchor}} for SELECTED dictionaries.
# Each dictionary entry is a div.definition-container linking to its category page;
# a dictionary may appear under several headword spellings — concatenate them.
# --------------------------------------------------------------------------
_CHROME = ["voting-container", "sectionpermacontainer", "credits", "entry-meta",
           "nextprevlinks", "symbol", "scoreholder"]
_HEADER_RE = re.compile(r"^.*?Permalink\s*\([^)]*\)\s*", re.S)


def _slug_from_container(div):
    for a in div.find_all("a", href=True):
        m = re.search(r"hawramani\.com/([a-z0-9-]{8,})/", a["href"])
        if m and not m.group(1).startswith(("wp-", "?")):
            return m.group(1)
    return None


def parse_page(html):
    soup = BeautifulSoup(html, "html.parser")
    out = {}
    for div in soup.select("div.definition-container"):
        slug = _slug_from_container(div)
        if slug not in SELECTED_SLUGS:
            continue
        anchor = div.get("id", "")
        for c in _CHROME:
            for el in div.select("." + c):
                el.decompose()
        text = div.get_text(" ", strip=True)
        text = _HEADER_RE.sub("", text)            # drop "Author, Work (d.YYYY) title Permalink (..)"
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 3:
            continue
        if slug in out:
            out[slug]["text"] += "\n\n" + text
        else:
            out[slug] = {"text": text, "anchor": anchor}
    return out


def scrape_root(conn, root_bw, session):
    row = conn.execute(
        "SELECT root_arabic FROM morphology WHERE root_buckwalter=? AND root_arabic!='' LIMIT 1",
        (root_bw,)).fetchone()
    root_ar = (row["root_arabic"].replace(" ", "") if row else bw.buckwalter_to_arabic(root_bw))
    # The site splits a root's entries across spelling-variant pages (bare-alef
    # /امن/ vs hamza /أمن/), each with a DIFFERENT subset of dictionaries. Fetch
    # every existing variant and MERGE, keeping the fullest entry per dictionary.
    merged = {}          # slug -> {text, anchor, src_slug}
    used_slugs = []
    for cand in resolve_slugs(conn, root_bw):
        html, _ = fetch_page(cand, session)
        if not html:
            continue
        used_slugs.append(cand)
        for slug, info in parse_page(html).items():
            if slug not in merged or len(info["text"]) > len(merged[slug]["text"]):
                merged[slug] = {**info, "src_slug": cand}
    if not merged:
        print(f"  {root_bw:6} ({root_ar}) -> NO PAGE FOUND")
        return 0
    n = 0
    for slug, info in merged.items():
        used_slug = info["src_slug"]
        conn.execute(
            "INSERT INTO dictionary_entries (root_buckwalter, root_arabic, dictionary_slug, "
            "original_text_ar, source_url, source_anchor, scrape_hash) VALUES (?,?,?,?,?,?,?) "
            "ON CONFLICT(root_buckwalter, dictionary_slug) DO UPDATE SET "
            "original_text_ar=excluded.original_text_ar, source_url=excluded.source_url, "
            "source_anchor=excluded.source_anchor, scrape_hash=excluded.scrape_hash, edited_at=datetime('now')",
            (root_bw, root_ar, slug, info["text"], f"{BASE}/{used_slug}/#{info['anchor']}",
             info["anchor"], hashlib.sha256(info["text"].encode()).hexdigest()[:16]),
        )
        n += 1
    conn.commit()
    print(f"  {root_bw:6} ({'+'.join(used_slugs)}) -> {n} dicts")
    return n


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    conn = get_db()
    if cmd == "init":
        ensure_schema(conn); seed_dictionaries(conn)
        print(f"schema ready; {len(SEED_DICTS)} dictionaries seeded.")
    elif cmd == "sitemap":
        ensure_schema(conn); seed_dictionaries(conn)
        session = requests.Session(); session.headers["User-Agent"] = UA
        build_sitemap_index(conn, session)
    elif cmd == "resolve":                      # debug: root -> resolved slugs
        for root in sys.argv[2:]:
            print(f"{root:6} {norm_root(bw.buckwalter_to_arabic(root)):8} -> {resolve_slugs(conn, root)}")
    elif cmd in ("scrape", "pilot", "top"):
        ensure_schema(conn); seed_dictionaries(conn)
        if cmd == "pilot":
            roots = PILOT_ROOTS
        elif cmd == "top":
            roots = top_roots(conn, int(sys.argv[2]) if len(sys.argv) > 2 else 50)
        else:
            roots = sys.argv[2:]
        session = requests.Session(); session.headers["User-Agent"] = UA
        print(f"scraping {len(roots)} roots (1 req / {SCRAPE_DELAY}s, cached)...")
        total = sum(scrape_root(conn, r, session) for r in roots)
        print(f"done: {total} dictionary entries stored (pending).")
    elif cmd == "show":
        root = sys.argv[2]
        rows = conn.execute(
            "SELECT d.name_en, d.author, d.author_death_year, e.original_text_ar "
            "FROM dictionary_entries e JOIN dictionaries d ON d.slug=e.dictionary_slug "
            "WHERE e.root_buckwalter=? ORDER BY d.sort_order", (root,)).fetchall()
        print(f"=== {root}: {len(rows)} dictionary entries ===")
        for r in rows:
            print(f"\n--- {r['name_en']} — {r['author']} (d.{r['author_death_year']}) ---")
            print(r["original_text_ar"][:500])
    else:
        print(__doc__)
    conn.close()


if __name__ == "__main__":
    main()
