#!/usr/bin/env python3
"""Collect the dictionary articles the first scrape never reached.

hawramani files some articles under spellings dict_scrape.py never looked up:
  - doubled roots on the two-letter page (رب for ربب, حق for حقق);
  - wāw-final roots under the alif spelling (دعا for دعو, صلا for صلو);
  - hollow roots under the alif spelling (كان for كون);
  - variant pages past dict_scrape's six-page cap.
It also lacks some Lisān articles altogether (سلم, قبل, دين …). Those come from the
OpenITI text of the same edition (Shamela book 1687, Dār Ṣādir), linked to the
matching Shamela page.

A candidate article is taken only if it opens with its own headword spelled as one
of the root's filing spellings (hamza kept apart from alif, so قرأ is never taken for
قرا) and no other Qur'anic root files under that spelling. Everything else goes to a
review list. Existing rows are never changed, except the Ṣiḥāḥ أيد repair (its text
was cut at a stray heading; the rest sits on the آد page).

  python3 dict_gap_fill.py plan             # pages to fetch -> data/gap_fill/plan.json
  python3 dict_gap_fill.py fetch            # fetch them (disk cache, 1 request / 4 s)
  python3 dict_gap_fill.py match            # -> data/gap_fill/candidates.json + review.json
  python3 dict_gap_fill.py insert [--apply] # new rows (pending, or deferred by site policy)
  python3 dict_gap_fill.py export           # translation worklist -> data/gap_fill/worklist.json
  python3 dict_gap_fill.py import F… [--apply]   # drafted + reviewed English back in
  python3 dict_gap_fill.py spec             # every gap-fill row, for another host
  python3 dict_gap_fill.py apply-spec F [--apply] --backup B   # insert them there, by key
"""
import argparse
import bisect
import collections
import datetime
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
import types
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "gap_fill")
DB = os.path.join(HERE, "data", "quran.db")


def _get_db():
    conn = sqlite3.connect(DB, timeout=60)
    conn.row_factory = sqlite3.Row
    return conn


# dict_scrape does `from app import get_db`; a stub keeps app.py's scheduler threads out of this process
_stub = types.ModuleType("app")
_stub.get_db = _get_db
sys.modules.setdefault("app", _stub)

import buckwalter as bw  # noqa: E402
import dict_scrape as DS  # noqa: E402

TAG = "gap_fill_2026_09"
LISAN = "ibn-manzur-lisan-al-arab"
SIHAH = "ismail-bin-hammad-al-jawhari-taj-al-lugha-wa-sihah-al-arabiya"
SALMONE = "habib-anthony-salmone-an-advanced-learners-arabic-english-dictionary"
# site policy (_dict_defer_redundant.py, agreed 2026-08-07)
PRIORITY = {
    "ibn-faris-maqayis-al-lugha", "al-khalil-b-ahmad-al-farahidi-kitab-al-ain",
    "al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran", LISAN, "al-zamakhshari-asas-al-balagha",
}
ALWAYS_KEEP = {
    "william-edward-lane-arabic-english-lexicon", "abdullah-ibn-abbas-gharib-al-quran-fi-shir-al-arab",
    "abu-hayyan-al-gharnati-tuhfat-al-arib-bi-ma-fi-l-quran-min-al-gharib",
}
RANK = [
    "murtada-al-zabidi-taj-al-arus-fi-jawahir-al-qamus", "ibn-sida-al-mursi-al-muhkam-wa-l-muhit-al-aazam",
    SIHAH, "al-sahib-bin-abbad-al-muhit-fi-l-lugha", "al-fayyumi-al-misbah-al-munir-fi-gharib-al-sharh-al-kabir",
    "firuzabadi-al-qamus-al-muhit", "zayn-al-din-al-razi-mukhtar-al-sihah",
]

# dictionaries whose stored doubled roots show they file them under two letters (رب for ربب);
# the rest spell them in full, so a two-letter page article of theirs goes to review
TWO_LETTER_OK = {
    "ibn-faris-maqayis-al-lugha", "william-edward-lane-arabic-english-lexicon",
    "al-khalil-b-ahmad-al-farahidi-kitab-al-ain", "al-sahib-bin-abbad-al-muhit-fi-l-lugha",
    "al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran", "firuzabadi-al-qamus-al-muhit",
    "ibn-sida-al-mursi-al-muhkam-wa-l-muhit-al-aazam", "abdullah-ibn-abbas-gharib-al-quran-fi-shir-al-arab",
}
# two-letter spellings that are also particles (مِنْ, عَنْ, أَمْ …): never taken without review
PARTICLES = {"من", "عن", "ءن", "لم", "ثم", "قد", "بل", "هل", "ءم", "ءل", "ءو", "ءي", "في", "كي", "لو", "ءذ"}

# letter names in the Lisān's chapter (حرف) and section (فصل) headings; hamza and alif sections
# hold roots spelt with either
LETTER = {"الهمزة": set("ءا"), "الألف": set("ءاوي"), "الباء": set("ب"), "التاء": set("ت"), "الثاء": set("ث"),
          "الجيم": set("ج"), "الحاء": set("ح"), "الخاء": set("خ"), "الدال": set("د"), "الذال": set("ذ"),
          "الراء": set("ر"), "الزاي": set("ز"), "السين": set("س"), "الشين": set("ش"), "الصاد": set("ص"),
          "الضاد": set("ض"), "الضأب": set("ض"), "الطاء": set("ط"), "الظاء": set("ظ"), "الظار": set("ظ"),
          "العين": set("ع"), "الغين": set("غ"), "الفاء": set("ف"), "القاف": set("ق"), "الكاف": set("ك"),
          "اللام": set("ل"), "الميم": set("م"), "النون": set("ن"), "الهاء": set("ه"), "الواو": set("و"),
          "الياء": set("ي")}
LETTER.update({k[2]: v for k, v in LETTER.items() if len(k) > 2 and k[2] not in ("ه", "أ")})
LETTER["ء"] = set("ءا")

OPENITI_LISAN = ("https://raw.githubusercontent.com/OpenITI/0725AH/master/data/0711IbnManzurIfriqi/"
                 "0711IbnManzurIfriqi.LisanCarab/0711IbnManzurIfriqi.LisanCarab.Shamela0001687-ara1.mARkdown")
SHAMELA_LISAN = "https://shamela.ws/book/1687"
SHAMELA_DELAY = 3.0
AYD_FRAGMENT = "[أيد] أبو زيد:"

# ---------------------------------------------------------------- spelling

_HAMZA = str.maketrans({"أ": "ء", "إ": "ء", "ؤ": "ء", "ئ": "ء", "آ": "ء", "ٱ": "ا", "ى": "ي", "ة": "ه"})


def hz(s):
    """Letter skeleton that keeps hamza apart from alif (norm_root merges them)."""
    s = re.sub(r"-\d+$", "", unquote(s or ""))
    s = DS._TASHKIL_RE.sub("", s).translate(_HAMZA)
    return re.sub("[^ء-ي]", "", s)


def root_skel(root_bw):
    return hz(bw.buckwalter_to_arabic(root_bw).replace("ا", "ء"))   # root "A" is always hamza


def filing_spellings(s, roots):
    """Spellings a dictionary may file root skeleton s under: {label: skeleton}.
    `roots` is the set of Qur'anic root skeletons, for the wāw/yāʾ sibling rule: an
    alif spelling belongs to the wāw root when both exist (دعا is دعو, not دعي)."""
    out = {"exact": s}
    if len(s) == 3 and s[1] == s[2]:
        out["two-letter"] = s[:2]
    if len(s) >= 3 and (s[-1] == "و" or (s[-1] == "ي" and s[:-1] + "و" not in roots)):
        out["alif-final"] = s[:-1] + "ا"
    if len(s) == 3 and (s[1] == "و" or (s[1] == "ي" and s[0] + "و" + s[2] not in roots)):
        out["alif-medial"] = s[0] + "ا" + s[2]
    # a weak final radical may be written with the other weak letter (رضي for رضو) when no
    # Qur'anic root is spelt that way
    if len(s) >= 3 and s[-1] in "وي":
        other = s[:-1] + ("ي" if s[-1] == "و" else "و")
        if other not in roots:
            out["other-weak"] = other
    return out


def headword(text):
    """The article's own headword, as an hz skeleton ('' when none can be read)."""
    t = DS._TASHKIL_RE.sub("", text[:400])
    if t.startswith("باب"):                         # Kitāb al-ʿAyn: "باب … ك ت ب، … مستعملات كتب: …"
        m = re.search(r"([ء-ي]{2,6})\s*:", t)
        return hz(m.group(1)) if m else ""
    t = t.lstrip(" ([{«\"'•*")
    m = re.match(r"((?:[ء-ي]\s+){1,4}[ء-ي])(?![ء-ي])", t)     # spaced letters: د ع و
    if m:
        return hz(m.group(1))
    m = re.match(r"[ء-ي]+", t)
    return hz(m.group(0)) if m else ""


def uses(text, root_skel):
    """Whether the opening of an article uses this hamza root's letters (مرؤ, قرأ …)."""
    return any(root_skel in hz(w) for w in text[:400].split())


def medial_ok(text, root_skel):
    """An alif-spelled hollow article (قال, مال) belongs to the root whose weak letter its opening
    words use: يَقُولُ, قَوْلاً for q-w-l; مَيْلاً for m-y-l. False when the other letter wins."""
    c1, w, c3 = root_skel[0], root_skel[1], root_skel[2]
    other = "ي" if w == "و" else "و"
    words = [hz(x) for x in DS._TASHKIL_RE.sub("", text[:160]).split()]
    mine = sum(1 for x in words if c1 + w + c3 in x)
    theirs = sum(1 for x in words if c1 + other + c3 in x)
    return theirs <= mine


def text_hash(t):
    return hashlib.sha256((t or "").encode()).hexdigest()[:16]


# ---------------------------------------------------------------- state

def quranic_roots(conn):
    freq = {r[0]: r[1] for r in conn.execute(
        "SELECT root_buckwalter, COUNT(*) FROM morphology WHERE root_buckwalter <> '' GROUP BY 1")}
    arabic = {r[0]: r[1].replace(" ", "") for r in conn.execute(
        "SELECT root_buckwalter, MIN(root_arabic) FROM morphology WHERE root_buckwalter <> '' "
        "AND root_arabic <> '' GROUP BY 1")}
    return freq, arabic


def spellings_index(freq):
    skel = {r: root_skel(r) for r in freq}
    roots = set(skel.values())
    forms = {r: filing_spellings(s, roots) for r, s in skel.items()}
    owners = collections.defaultdict(set)
    for r, fs in forms.items():
        for f in fs.values():
            owners[f].add(r)
    # a hamza root's article may be headed without its hamza (قرا for قرأ): such a
    # spelling is shared with that root too
    for r, s in skel.items():
        if "ء" in s:
            owners[s.replace("ء", "ا")].add(r)
    return skel, forms, owners


def containers(html):
    """Each selected dictionary's article container on a page: [(slug, anchor, text)]."""
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for div in soup.select("div.definition-container"):
        slug = DS._slug_from_container(div)
        if slug not in DS.SELECTED_SLUGS:
            continue
        for c in DS._CHROME:
            for el in div.select("." + c):
                el.decompose()
        text = re.sub(r"\s+", " ", DS._HEADER_RE.sub("", div.get_text(" ", strip=True))).strip()
        if len(text) >= 3:
            out.append((slug, div.get("id", ""), text))
    return out


def cached(slug):
    cp = DS._cache_path(slug)
    return open(cp, encoding="utf-8").read() if os.path.exists(cp) else None


# ---------------------------------------------------------------- plan / fetch

def cmd_plan(conn, a):
    freq, _ = quranic_roots(conn)
    skel, forms, _ = spellings_index(freq)
    have = collections.defaultdict(set)
    for r, d in conn.execute("SELECT root_buckwalter, dictionary_slug FROM dictionary_entries"):
        have[r].add(d)
    idx = collections.defaultdict(list)
    for nr, slug in conn.execute("SELECT normalized_root, arabic_slug FROM root_slug_index "
                                 "ORDER BY LENGTH(arabic_slug), arabic_slug"):
        idx[nr].append(slug)
    plan = {}
    for r in sorted(freq, key=lambda x: -freq[x]):
        if not DS.SELECTED_SLUGS - have[r]:
            continue
        pages = []
        for label, f in forms[r].items():
            for slug in idx.get(DS.norm_root(f), []):
                if hz(slug) == f and slug not in pages:
                    # exact-spelling pages the first scrape fetched are already cached and parsed
                    if label == "exact" and cached(slug) is not None:
                        continue
                    pages.append(slug)
        if pages:
            plan[r] = pages
    plan["Ayd"] = sorted(set(plan.get("Ayd", [])) | {"آد"})
    # the spellings that hold most missing articles first; then every page of a root still without
    # Lisān (OpenITI is used for a root only once all its pages are read); variant pages past the cap last
    order = {"two-letter": 0, "alif-final": 0, "alif-medial": 2, "exact": 3}
    rank = {}
    for r, pages in plan.items():
        inv = {f: lab for lab, f in forms.get(r, {}).items()}
        for p in pages:
            k = order.get(inv.get(hz(p)), 0)
            if k and LISAN not in have[r]:
                k = 1
            rank[p] = min(rank.get(p, 9), k)
    todo = sorted({p for ps in plan.values() for p in ps if cached(p) is None}, key=lambda p: (rank[p], p))
    os.makedirs(OUT, exist_ok=True)
    json.dump({"roots": plan, "fetch": todo, "first_batch": sum(1 for p in todo if rank[p] <= 1)},
              open(os.path.join(OUT, "plan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(plan)} roots have pages not yet read; {len(todo)} pages to fetch "
          f"(~{len(todo) * (DS.SCRAPE_DELAY + 3) / 3600:.1f} h at 1 request / {DS.SCRAPE_DELAY:.0f} s)")


def cmd_fetch(conn, a):
    todo = json.load(open(os.path.join(OUT, "plan.json"), encoding="utf-8"))["fetch"]
    session = requests.Session()
    session.headers["User-Agent"] = DS.UA
    got = missing = 0
    t0 = time.time()
    for i, slug in enumerate(todo, 1):
        if cached(slug) is not None:
            got += 1
            continue
        html, _ = DS.fetch_page(slug, session)
        got, missing = (got + 1, missing) if html else (got, missing + 1)
        if i % 25 == 0 or i == len(todo):
            el = time.time() - t0
            print(f"[fetch] {i}/{len(todo)} · {got} cached · {missing} unavailable · {el / 60:.0f} min", flush=True)
    print(f"[fetch] done: {got} pages cached, {missing} unavailable")


# ---------------------------------------------------------------- match

def lisan_openiti():
    """Lisān articles of the OpenITI text: ({hz headword: [(text, (vol, page), ordinal)]}).
    OpenITI puts each PageVxxPyyy marker at the END of its page, so an article starts on
    the page of the first marker after its heading; `ordinal` is that marker's position."""
    path = os.path.join(OUT, "lisan.mARkdown")
    if not os.path.exists(path):
        r = requests.get(OPENITI_LISAN, timeout=(10, 300))
        r.raise_for_status()
        os.makedirs(OUT, exist_ok=True)
        open(path, "w", encoding="utf-8").write(r.text)
    txt = open(path, encoding="utf-8").read()
    marks = [(m.start(), int(m.group(1)), int(m.group(2))) for m in re.finditer(r"PageV(\d+)P(\d+)", txt)]
    pos = [m[0] for m in marks]
    # The OpenITI tagger also marked some quotations as articles ("### $ عمر: أنه سافر …", from
    # "وفي حديث عمر: …"), and left some articles untagged, as a plain paragraph ("# فتح: الفتح: نقيض
    # الإغلاق …"). A real article's headword starts with its section's letter (فصل) and ends with its
    # chapter's letter (the Lisān files by last radical); an untagged one must also fall, in
    # alphabetical order, between the real articles around it. Anything else is folded back into
    # the article before it.
    lines, bab, fasl = [], None, None      # (start, kind, headword skeleton, letter test passed)
    for m in re.finditer(r"(?m)^(### \| |### \|\| |### \$ |### |# |~~)([^\n]*)", txt):
        kind, line = m.group(1), m.group(2)
        if kind == "### | ":
            w = line.split()
            name = (w[1] if w and w[0] in ("حرف", "فصل") and len(w) > 1 else (w[0] if w else ""))
            bab = LETTER.get(name, set(name) if len(name) == 1 else None) if name != "و-" else set("ويا")
            fasl = None
            lines.append((m.start(), "header", "", False))
        elif kind == "### || ":
            w = line.split()
            fasl = LETTER.get(w[1]) if len(w) > 1 and w[0] == "فصل" else None
            lines.append((m.start(), "header", "", False))
        elif kind == "### ":
            lines.append((m.start(), "header", "", False))
        else:
            k = hz(line.split(":", 1)[0]) if ":" in line[:14] else ""
            ok = bool(k) and (fasl is None or k[0] in fasl) and (bab is None or k[-1] in bab)
            lines.append((m.start(), "tag" if kind == "### $ " else "para", k,
                          ok and (kind == "### $ " or (fasl is not None and bab is not None and 2 <= len(k) <= 5))))
    real = [(a, k) for a, kind, k, ok in lines if kind == "tag" and ok]
    rpos = [a for a, _ in real]

    def consonants(w):
        return re.sub("[اويء]", "", w)

    spans, head = [], ""
    for a, kind, k, ok in lines:
        if kind == "header":
            spans.append((a, None))
            head = ""
        elif kind == "tag":
            if ok or not spans or spans[-1][1] is None:
                spans.append((a + 6, "entry"))
                head = k
        elif ok and spans and not (consonants(k) == consonants(head) and len(k) != len(head)):
            # (a derived word of the current article, ظهير inside ظهر, is not a new article; a
            # neighbouring weak root of the same length, قيل after قول, is)
            j = bisect.bisect_right(rpos, a)
            lo = real[j - 1][1] if j else ""
            hi = real[j][1] if j < len(real) else "\uffff"
            if lo < k < hi:
                spans.append((a + (2 if txt.startswith(("# ", "~~"), a) else 0), "entry"))
                head = k
    spans.append((len(txt), None))
    out = collections.defaultdict(list)
    for (a, kind), (b, _) in zip(spans, spans[1:]):
        if kind != "entry":
            continue
        t = re.sub(r"(?m)^### \$ ", "", txt[a:b])
        t = re.sub(r"PageV\d+P\d+|\bms\d+\b", " ", t)
        t = re.sub(r"(?m)^(~~|# )", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        k = bisect.bisect_right(pos, a)
        if k < len(marks):
            out[hz(t.split(":", 1)[0])].append((t, (marks[k][1], marks[k][2]), k))
    return out


def shamela_page(vol, page, ordinal, cache, session):
    """Shamela's page number for print vol/page of the Lisān (book 1687), read back from the
    page title (Shamela numbers pages consecutively; OpenITI's markers drift a little from it)."""
    key = f"{vol}:{page}"
    if key in cache:
        return cache[key]
    n = ordinal + cache.get("_offset", {}).get(str(vol), 4)
    for _ in range(6):
        r = session.get(f"{SHAMELA_LISAN}/{n}", timeout=(10, 60))
        time.sleep(SHAMELA_DELAY)
        m = re.search(r"<title>\s*ج(\d+)\s*-\s*ص(\d+)", r.text)
        if r.status_code != 200 or not m:
            break
        v, p = int(m.group(1)), int(m.group(2))
        if (v, p) == (vol, page):
            cache[key] = n
            cache.setdefault("_offset", {})[str(vol)] = n - ordinal
            return n
        n += (page - p) if v == vol else (30 if v < vol else -30)
    cache[key] = None
    return None


def shamela_text(n, session):
    """The text of Shamela page n of the Lisān (disk-cached), vowel marks included."""
    d = os.path.join(OUT, "shamela_cache")
    os.makedirs(d, exist_ok=True)
    cp = os.path.join(d, f"{n}.html")
    if os.path.exists(cp):
        html = open(cp, encoding="utf-8").read()
    else:
        r = session.get(f"{SHAMELA_LISAN}/{n}", timeout=(10, 60))
        time.sleep(SHAMELA_DELAY)
        if r.status_code != 200:
            return None
        html = r.text
        open(cp, "w", encoding="utf-8").write(html)
    div = BeautifulSoup(html, "html.parser").select_one("div.nass")
    if div is None:
        return None
    # the editor's footnotes (p.hamesh) and their «٣» markers are not part of the article (hawramani's
    # and OpenITI's copies leave them out too)
    for el in div.select("a.btn_tag, p.hamesh"):
        el.decompose()
    for el in div.select("span.c2"):
        if re.fullmatch(r"\s*«[\d٠-٩]+»\s*", el.get_text()):
            el.decompose()
    return re.sub(r"\s+", " ", " ".join(p.get_text(" ") for p in div.find_all("p"))).strip()


def hz_map(text):
    """hz() of a text, with the position in `text` of each letter kept."""
    letters, where = [], []
    for i, ch in enumerate(text):
        if DS._TASHKIL_RE.match(ch):
            continue
        ch = ch.translate(_HAMZA)
        if "ء" <= ch <= "ي":
            letters.append(ch)
            where.append(i)
    return "".join(letters), where


def shamela_article(openiti_text, n, session, max_pages=60):
    """The vowelled Shamela text of an article, cut where OpenITI's unvowelled copy starts and ends."""
    target = hz(openiti_text)
    buf = ""
    for k in range(max_pages):
        t = shamela_text(n + k, session)
        if t is None:
            return None
        buf += " " + t
        letters, where = hz_map(buf)
        for size in (40, 25, 15):
            start = letters.find(target[:size])
            if start < 0:
                continue
            end = letters.find(target[-size:], start + len(target) * 9 // 10 - size)
            if end < 0:
                break           # the end is on a later page
            got = letters[start:end + size]
            if abs(len(got) - len(target)) <= max(20, len(target) * 3 // 100):
                stop = where[end + size - 1] + 1
                while stop < len(buf) and (DS._TASHKIL_RE.match(buf[stop]) or buf[stop] in ".،؛:!؟"):
                    stop += 1           # the last letter's vowel marks and the closing full stop
                return buf[where[start]:stop].strip()
            return None
        if k == 0 and all(letters.find(target[:size]) < 0 for size in (40, 25, 15)):
            return None             # the article does not start on this page
    return None


def cmd_match(conn, a):
    planfile = json.load(open(os.path.join(OUT, "plan.json"), encoding="utf-8"))
    plan = planfile["roots"]
    log = os.path.join(OUT, "fetch.log")
    # once the fetch has finished, a page still missing was tried and is unavailable
    done = os.path.exists(log) and "[fetch] done" in open(log, encoding="utf-8").read()
    attempted = set(planfile["fetch"]) if done else set()
    freq, arabic = quranic_roots(conn)
    skel, forms, owners = spellings_index(freq)
    have = collections.defaultdict(set)
    stored = collections.defaultdict(dict)       # slug -> first 200 letters of stored text -> root
    for r in conn.execute("SELECT root_buckwalter, dictionary_slug, original_text_ar FROM dictionary_entries"):
        have[r[0]].add(r[1])
        stored[r[1]][hz((r[2] or "")[:600])[:200]] = r[0]
    found, review, notes = {}, [], collections.Counter()
    # decisions on review items: {"root", "dictionary_slug", "take": [opening words of each article to
    # take, joined in that order] or [] to take nothing}
    dpath = os.path.join(OUT, "decisions.json")
    decided = {(d["root"], d["dictionary_slug"]): d["take"] for d in
               (json.load(open(dpath, encoding="utf-8")) if os.path.exists(dpath) else []) if "take" in d}

    def chosen(key, text):
        """For a decided item: whether this article is one of those taken."""
        return any(re.sub(r"\s+", " ", text).startswith(re.sub(r"\s+", " ", w)) for w in decided[key])

    for root, pages in plan.items():
        want = DS.SELECTED_SLUGS - have[root]
        spell = {f: lab for lab, f in forms[root].items()}
        for page in pages:
            html = cached(page)
            if html is None:
                continue
            for slug, anchor, text in containers(html):
                if slug not in want:
                    continue
                h = headword(text)
                item = {"root": root, "dictionary_slug": slug, "page": page, "anchor": anchor,
                        "headword": h, "text": text}
                if (root, slug) in decided:
                    if chosen((root, slug), text):      # a decision may take an article stored elsewhere too
                        item["found_via"] = spell.get(h, "decided")
                        prev = found.get((root, slug))
                        if prev and prev["text"] != text and prev["page"] == page and text not in prev["text"]:
                            prev["text"] += "\n\n" + text
                        elif not prev:
                            found[(root, slug)] = item
                    continue
                if not h:
                    review.append({**item, "why": "no headword at the start"})
                    continue
                if h not in spell:
                    notes["headword is another root's"] += 1
                    continue
                if spell[h] == "alif-medial" and not medial_ok(text, skel[root]):
                    notes["alif spelling of the other weak root"] += 1
                    continue
                rivals = owners[h] - {root}
                # a hamza root written without its hamza (قرا for قرأ) shares the wāw root's alif
                # spelling; when every such rival already has its own, different, article from this
                # dictionary and this text never uses the hamza form, the article is this root's
                if rivals and not all("ء" in skel[x] and slug in have[x] and not uses(text, skel[x])
                                      for x in rivals):
                    review.append({**item, "why": "spelling shared with " + ", ".join(sorted(rivals))})
                    continue
                if spell[h] == "two-letter" and (slug not in TWO_LETTER_OK or h in PARTICLES):
                    review.append({**item, "why": "two-letter page (particle, or a dictionary that spells "
                                                  "doubled roots in full)"})
                    continue
                dup = stored[slug].get(hz(text[:600])[:200])
                if dup:
                    notes["already stored under " + ("the same root" if dup == root else "another root")] += 1
                    continue
                item["found_via"] = spell[h]
                key = (root, slug)
                prev = found.get(key)
                if prev and prev["text"] != text:
                    if text in prev["text"]:
                        continue
                    if prev["page"] == page:          # two articles of one dictionary on one page
                        prev["text"] += "\n\n" + text
                        continue
                    if len(text) <= len(prev["text"]):
                        continue
                found[key] = item
    # Lisān articles hawramani lacks: the OpenITI text of the same edition
    ol = lisan_openiti()
    cache_path = os.path.join(OUT, "shamela_pages.json")
    spage = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
    session = requests.Session()
    session.headers["User-Agent"] = DS.UA
    lisan_from_openiti = 0
    for root in sorted(freq, key=lambda x: -freq[x]):
        if LISAN in have[root] or (root, LISAN) in found:
            continue
        if any(cached(p) is None and p not in attempted for p in plan.get(root, [])):
            continue        # hawramani's (vowelled) copy may still turn up on a page not yet fetched
        spell = {f: lab for lab, f in forms[root].items()}
        hits = [(f, t, p, k) for f in spell for t, p, k in ol.get(f, [])]
        if (root, LISAN) in decided:
            hits = [x for x in hits if chosen((root, LISAN), x[1])]
            hits.sort(key=lambda x: next(i for i, w in enumerate(decided[(root, LISAN)])
                                         if re.sub(r"\s+", " ", x[1]).startswith(re.sub(r"\s+", " ", w))))
            if len(hits) > 1:        # one article that OpenITI split in two
                hits = [(hits[0][0], " ".join(x[1] for x in hits), hits[0][2], hits[0][3])]
        if not hits:
            continue
        rivals = {x for f, _, _, _ in hits for x in owners[f] - {root}}
        clear = all("ء" in skel[x] and LISAN in have[x] and not uses(t, skel[x])
                    for x in rivals for _, t, _, _ in hits)
        if (root, LISAN) not in decided and (len(hits) > 1 or (rivals and not clear)):
            for f, t, p, _ in hits:
                review.append({"root": root, "dictionary_slug": LISAN, "page": f"OpenITI vol. {p[0]} p. {p[1]}",
                               "anchor": "", "headword": f, "text": t,
                               "why": "several OpenITI articles" if len(hits) > 1 else
                               "spelling shared with " + ", ".join(sorted(owners[f] - {root}))})
            continue
        f, t, (vol, pg), k = hits[0]
        n = None if a.no_shamela else shamela_page(vol, pg, k, spage, session)
        json.dump(spage, open(cache_path, "w"))
        # Shamela's page shows the same text with its vowel marks: take it, cut at OpenITI's boundaries
        vowelled = shamela_article(t, n, session) if n else None
        found[(root, LISAN)] = {"root": root, "dictionary_slug": LISAN, "headword": f, "text": vowelled or t,
                                "found_via": spell[f], "openiti": True, "vowelled": bool(vowelled),
                                "print": f"vol. {vol} p. {pg}",
                                "page": f"{SHAMELA_LISAN}/{n}" if n else SHAMELA_LISAN, "anchor": ""}
        lisan_from_openiti += 1
    # the Lisān (and others) treat the wāw and yāʾ roots in one article: نسا covers النسيان
    for d in (json.load(open(dpath, encoding="utf-8")) if os.path.exists(dpath) else []):
        src = d.get("share_from")
        key = (d["root"], d["dictionary_slug"])
        if not src or key in found or d["dictionary_slug"] in have[d["root"]]:
            continue
        if (src, d["dictionary_slug"]) in found:
            it = dict(found[(src, d["dictionary_slug"])])
        else:
            r = conn.execute("SELECT original_text_ar, source_url, source_anchor FROM dictionary_entries "
                             "WHERE root_buckwalter = ? AND dictionary_slug = ?", (src, d["dictionary_slug"])).fetchone()
            if not r:
                continue
            it = {"text": r[0], "page": r[1].split("/#")[0].rsplit("/", 1)[-1], "anchor": r[2] or ""}
        it.update(root=d["root"], dictionary_slug=d["dictionary_slug"], shared_with=src,
                  found_via=f"shared article (also {src}'s)")
        found[key] = it
    # Ṣiḥāḥ أيد: the stored text stops at a stray heading; the article continues on the آد page
    ayd = conn.execute("SELECT id, original_text_ar FROM dictionary_entries WHERE root_buckwalter='Ayd' "
                       "AND dictionary_slug=?", (SIHAH,)).fetchone()
    html = cached("آد")
    if ayd and ayd["original_text_ar"].strip() == AYD_FRAGMENT and html:
        rest = [t for s, _, t in containers(html) if s == SIHAH and hz(t.split("]", 1)[0]) == "ءد"]
        if rest:
            found[("Ayd", SIHAH)] = {"root": "Ayd", "dictionary_slug": SIHAH, "page": "آد", "anchor": "",
                                     "headword": "ءيد", "found_via": "repair",
                                     "text": AYD_FRAGMENT + " " + rest[0].split("]", 1)[1].strip(),
                                     "repair_of": ayd["id"]}
    for it in found.values():
        it["root_arabic"] = arabic.get(it["root"]) or bw.buckwalter_to_arabic(it["root"])
        it["freq"] = freq.get(it["root"], 0)
    cands = sorted(found.values(), key=lambda x: (-x["freq"], x["root"], x["dictionary_slug"]))
    json.dump(cands, open(os.path.join(OUT, "candidates.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    seen = set()
    review = [x for x in review if not ((x["root"], x["dictionary_slug"], x["text"]) in seen
                                        or seen.add((x["root"], x["dictionary_slug"], x["text"])))]
    json.dump(review, open(os.path.join(OUT, "review.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    by = collections.Counter(c["dictionary_slug"] for c in cands)
    print(f"{len(cands)} articles found ({lisan_from_openiti} Lisān from OpenITI); {len(review)} need a decision")
    for d, n in by.most_common():
        print(f"  {n:4}  {d}")
    print("skipped:", dict(notes))


# ---------------------------------------------------------------- insert (site policy)

def policy(conn, items):
    """review_status for new articles, (root, slug) -> 'pending' | 'deferred'.

    Roots whose panel shows every dictionary (the top 300, and roots harmonized before the
    one-slot policy of 2026-08-07) take every new article. On roots where the policy deferred
    general dictionaries, a general one only fills an empty slot (Tāj > Muḥkam > Ṣiḥāḥ > Muḥīṭ >
    Miṣbāḥ > Qāmūs > Mukhtār; two slots when the root has no priority entry) and Salmoné
    only when no other non-priority dictionary covers the root. Priority dictionaries, Lane
    and the two Qur'an glossaries are always taken."""
    new_by_root = collections.defaultdict(set)
    for root, slug in items:
        new_by_root[root].add(slug)
    covered, general, nonpriority, trimmed = set(), collections.Counter(), collections.defaultdict(set), set()
    for r in conn.execute("SELECT root_buckwalter, dictionary_slug, review_status, hidden, harmonized_en "
                          "FROM dictionary_entries"):
        root, slug = r["root_buckwalter"], r["dictionary_slug"]
        if slug in new_by_root.get(root, ()):
            continue
        if slug in PRIORITY and (r["harmonized_en"] or "").strip():
            covered.add(root)
        if slug in RANK and r["review_status"] in ("approved", "pending") and not r["hidden"]:
            general[root] += 1
        if slug not in PRIORITY:
            nonpriority[root].add(slug)
        if r["review_status"] == "deferred":
            trimmed.add(root)
    status = {}
    for root, slugs in new_by_root.items():
        free = (2 if root not in covered and not slugs & PRIORITY else 1) - general[root]
        for s in RANK:
            if s in slugs:
                status[(root, s)] = "pending" if root not in trimmed or free > 0 else "deferred"
                free -= 1
        for s in slugs:
            if s in PRIORITY or s in ALWAYS_KEEP:
                status[(root, s)] = "pending"
            elif s == SALMONE:
                alone = not ((nonpriority[root] | slugs) - {SALMONE})
                status[(root, s)] = "pending" if root not in trimmed or alone else "deferred"
    return status


def cmd_insert(conn, a):
    cands = json.load(open(os.path.join(OUT, "candidates.json"), encoding="utf-8"))
    # rows scraped after the policy pass (2026-08-28) that were never translated are judged the same way
    older = conn.execute("SELECT id, root_buckwalter, dictionary_slug FROM dictionary_entries "
                         "WHERE review_status = 'pending' AND COALESCE(harmonized_en, '') = '' "
                         "AND COALESCE(gen_meta, '') NOT LIKE ?", (f"%{TAG}%",)).fetchall()
    status = policy(conn, [(c["root"], c["dictionary_slug"]) for c in cands if not c.get("repair_of")]
                    + [(r["root_buckwalter"], r["dictionary_slug"]) for r in older])
    now = datetime.datetime.now().replace(microsecond=0).isoformat()
    n = collections.Counter()
    with conn:
        for r in older:
            if status[(r["root_buckwalter"], r["dictionary_slug"])] == "deferred":
                n["older pending row deferred"] += 1
                if a.apply:
                    conn.execute("UPDATE dictionary_entries SET review_status = 'deferred' WHERE id = ? "
                                 "AND review_status = 'pending' AND COALESCE(harmonized_en, '') = ''", (r["id"],))
        for c in cands:
            if c.get("repair_of"):
                cur = conn.execute(
                    "UPDATE dictionary_entries SET original_text_ar = ?, translation_en = NULL, harmonized_en = NULL, "
                    "review_status = 'pending', hidden = 0, confidence = NULL, gen_meta = ?, edited_at = ? "
                    "WHERE id = ? AND TRIM(original_text_ar) = ?",
                    (c["text"], json.dumps({TAG: {"repair": "rest of the article from the آد page"}},
                                           ensure_ascii=False), now, c["repair_of"], AYD_FRAGMENT)) if a.apply else None
                n["repaired" if (cur is None or cur.rowcount) else "repair skipped"] += 1
                continue
            st = status[(c["root"], c["dictionary_slug"])]
            if c.get("openiti"):
                url, anchor = c["page"], c["print"]
                meta = {TAG: {"found_via": "Shamela book 1687 (hawramani lacks the article)",
                              "text": ("Shamela page text, cut at the article boundaries of OpenITI "
                                       "0711IbnManzurIfriqi.LisanCarab.Shamela0001687-ara1") if c.get("vowelled")
                              else "OpenITI 0711IbnManzurIfriqi.LisanCarab.Shamela0001687-ara1 (no vowel marks)",
                              "print": c["print"]}}
            else:
                url, anchor = f"{DS.BASE}/{c['page']}/#{c['anchor']}", c["anchor"]
                meta = {TAG: {"found_via": c["found_via"] + ("" if c.get("shared_with") else " page"),
                              "page": c["page"]}}
            if a.apply:
                cur = conn.execute(
                    "INSERT INTO dictionary_entries (root_buckwalter, root_arabic, dictionary_slug, original_text_ar, "
                    "source_url, source_anchor, scrape_hash, review_status, gen_meta, edited_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(root_buckwalter, dictionary_slug) DO NOTHING",
                    (c["root"], c["root_arabic"], c["dictionary_slug"], c["text"], url, anchor, text_hash(c["text"]),
                     st, json.dumps(meta, ensure_ascii=False), now))
                n[st if cur.rowcount else "already there"] += 1
            else:
                n[st] += 1
    print(dict(n), "" if a.apply else "(dry run)")


# ---------------------------------------------------------------- translation worklist / results

def gap_rows(conn, where="1=1", args=()):
    return conn.execute(
        "SELECT e.*, d.name_en, d.author, d.author_death_year, d.date_approx, d.date_note, d.language, "
        "d.is_quran_specific FROM dictionary_entries e JOIN dictionaries d ON d.slug = e.dictionary_slug "
        f"WHERE (e.gen_meta LIKE '%{TAG}%' OR (e.review_status = 'pending' AND COALESCE(e.harmonized_en, '') = '')) "
        f"AND {where}", args).fetchall()


def cmd_export(conn, a):
    freq, _ = quranic_roots(conn)
    rows = [r for r in gap_rows(conn, "e.review_status = 'pending' AND COALESCE(e.harmonized_en, '') = ''")]
    if a.only:          # e.g. --only priority,keep   (general = the seven general dictionaries + Salmoné)
        groups = {"priority": PRIORITY, "keep": ALWAYS_KEEP, "general": set(RANK) | {SALMONE}}
        want = set().union(*(groups[g] for g in a.only.split(",")))
        rows = [r for r in rows if r["dictionary_slug"] in want or '"repair"' in (r["gen_meta"] or "")]
    rows.sort(key=lambda r: (-freq.get(r["root_buckwalter"], 0), r["root_buckwalter"], r["author_death_year"]))
    items = [{
        "key": f"{r['root_buckwalter']}|{r['dictionary_slug']}", "text_hash": text_hash(r["original_text_ar"]),
        "root": r["root_buckwalter"], "root_arabic": r["root_arabic"], "dictionary": r["name_en"],
        "author": r["author"], "date": r["date_note"] or ("d. " + ("c. " if r["date_approx"] else "")
                                                         + f"{r['author_death_year']} CE"),
        "language": r["language"], "quran_specific": bool(r["is_quran_specific"]),
        "unvowelled": "(no vowel marks)" in (r["gen_meta"] or ""), "original_text_ar": r["original_text_ar"],
    } for r in rows]
    path = a.out or os.path.join(OUT, "worklist.json")
    json.dump(items, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    size = sum(len(i["original_text_ar"]) for i in items)
    print(f"{len(items)} articles, {size:,} characters -> {path}")


_STUBS = {"placeholder", "unused", "n/a", "na", "see above", "see harmonized", "todo", "..."}


def cmd_import(conn, a):
    now = datetime.datetime.now().replace(microsecond=0).isoformat()
    n, problems = collections.Counter(), []
    results = []
    for path in a.files:
        data = json.load(open(path, encoding="utf-8"))
        results += data if isinstance(data, list) else [data]
    with conn:
        for res in results:
            root, slug = res["key"].split("|")
            r = conn.execute("SELECT * FROM dictionary_entries WHERE root_buckwalter = ? AND dictionary_slug = ?",
                             (root, slug)).fetchone()
            if r is None or text_hash(r["original_text_ar"]) != res["text_hash"]:
                problems.append(f"{res['key']}: no row with that text")
                continue
            if r["review_status"] != "pending" or (r["harmonized_en"] or "").strip():
                n["already done"] += 1
                continue
            rv = res.get("review") or {}
            dec = rv.get("decision")
            english = conn.execute("SELECT language FROM dictionaries WHERE slug = ?", (slug,)).fetchone()[0] == "en"
            tr = (rv.get("translation_en") or "").strip() if dec == "edit" else ""
            ha = (rv.get("harmonized_en") or "").strip() if dec == "edit" else ""
            tr = tr if len(tr) >= 40 and tr.lower() not in _STUBS else (res.get("translation_en") or "").strip()
            ha = ha if len(ha) >= 40 and ha.lower() not in _STUBS else (res.get("harmonized_en") or "").strip()
            if english and len(tr) < 40:        # Lane, Salmoné: the author's own text is the faithful version
                tr = re.sub(r"[ \t]+", " ", r["original_text_ar"]).strip()
            if dec not in ("approve", "edit", "reject", "defer") or len(ha) < 40 or len(tr) < 40 \
                    or {ha.lower(), tr.lower()} & _STUBS:
                problems.append(f"{res['key']}: incomplete result")
                continue
            meta = json.loads(r["gen_meta"] or "{}")
            meta.setdefault(TAG, {})["translated"] = now
            meta["issues"] = res.get("issues", [])
            meta["ai_review"] = {"decision": dec, "severity": rv.get("severity"), "reason": rv.get("reason", ""),
                                 "at": now}
            status = {"approve": "approved", "edit": "approved", "reject": "rejected"}.get(dec, "pending")
            conn.execute("UPDATE dictionary_entries SET translation_en = ?, harmonized_en = ?, confidence = ?, "
                         "gen_meta = ?, review_status = ?, hidden = ?, edited_at = ? WHERE id = ?",
                         (tr, ha, res.get("confidence"), json.dumps(meta, ensure_ascii=False), status,
                          1 if dec == "reject" else r["hidden"], now, r["id"]))
            n[dec] += 1
        if not a.apply:
            conn.rollback()
    print(dict(n), "" if a.apply else "(dry run)")
    if problems:
        print("PROBLEMS:\n  " + "\n  ".join(problems))


COPY = ("root_buckwalter", "root_arabic", "dictionary_slug", "original_text_ar", "translation_en", "harmonized_en",
        "source_url", "source_anchor", "scrape_hash", "review_status", "hidden", "confidence", "gen_meta")


def cmd_spec(conn, a):
    rows = gap_rows(conn, f"e.gen_meta LIKE '%{TAG}%'")
    spec = [{k: r[k] for k in COPY} for r in rows]
    path = a.out or os.path.join(OUT, "spec.json")
    json.dump(spec, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{len(spec)} rows -> {path}")


def cmd_apply_spec(conn, a):
    """Make another host's rows match the spec, by (root, dictionary) — ids differ between hosts."""
    spec = json.load(open(a.files[0], encoding="utf-8"))
    now = datetime.datetime.now().replace(microsecond=0).isoformat()
    n, backup = collections.Counter(), []
    for s in spec:
        r = conn.execute("SELECT * FROM dictionary_entries WHERE root_buckwalter = ? AND dictionary_slug = ?",
                         (s["root_buckwalter"], s["dictionary_slug"])).fetchone()
        if r is None:
            n["insert"] += 1
            if a.apply:
                conn.execute("INSERT INTO dictionary_entries (" + ", ".join(COPY) + ", edited_at) VALUES ("
                             + ", ".join("?" * len(COPY)) + ", ?)", [s[k] for k in COPY] + [now])
        elif all(r[k] == s[k] for k in COPY):
            n["same"] += 1
        elif (TAG in (r["gen_meta"] or "")
              # the same article, still untranslated on this host (e.g. the split-off خطف row)
              or (r["review_status"] == "pending" and not (r["harmonized_en"] or "").strip()
                  and r["original_text_ar"] == s["original_text_ar"])
              or ((s["root_buckwalter"], s["dictionary_slug"]) == ("Ayd", SIHAH)
                  and r["original_text_ar"].strip() in (AYD_FRAGMENT, s["original_text_ar"]))):
            n["update"] += 1
            backup.append(dict(r))
            if a.apply:
                conn.execute("UPDATE dictionary_entries SET " + ", ".join(f"{k} = ?" for k in COPY)
                             + ", edited_at = ? WHERE id = ?", [s[k] for k in COPY] + [now, r["id"]])
        else:
            n["left alone (row differs and is not a gap-fill row)"] += 1
    if a.apply:
        json.dump(backup, open(a.backup, "w", encoding="utf-8"), ensure_ascii=False)
        conn.commit()
    print(dict(n), "" if a.apply else "(dry run)")


def main():
    global DB
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["plan", "fetch", "match", "insert", "export", "import", "spec", "apply-spec"])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--db", default=DB)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--backup")
    ap.add_argument("--no-shamela", action="store_true")
    ap.add_argument("--only", help="export: dictionary groups, e.g. priority,keep")
    a = ap.parse_args()
    if a.cmd == "apply-spec" and a.apply and not a.backup:
        sys.exit("apply-spec --apply needs --backup")
    DB = a.db
    conn = _get_db()
    {"plan": cmd_plan, "fetch": cmd_fetch, "match": cmd_match, "insert": cmd_insert, "export": cmd_export,
     "import": cmd_import, "spec": cmd_spec, "apply-spec": cmd_apply_spec}[a.cmd](conn, a)
    conn.close()


if __name__ == "__main__":
    main()
