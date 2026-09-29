#!/usr/bin/env python3
"""Pick, root by root, which classical dictionary entry opens first on a root page.

Criteria (agreed 2026-09-28): open the entry that best shows what the root meant in
the Qur'an's time, and on what evidence.
  root sense (3)      the author says what the root's words share and how the senses
                      branch from it; a definition of one word is not enough
  early usage (3)     poetry, rajaz, proverbs, Bedouin speech, graded by the poet's date
                      (pre-Islamic and early count most, Umayyad less, later least);
                      credit stops rising after a few witnesses
  the Qur'an (2)      verses explained through the word's ordinary sense; an exegete's
                      reported gloss counts like hadith, not as Qur'anic evidence
  covers (1)          the words the Qur'an uses from this root
  origin (bonus 0.5)  foreign origin or relatives in other languages
  penalty (to -3)     hadith, exegetes' glosses and legal/theological definitions that
                      carry the explanation
A model LISTS the evidence in each entry's readable version with quotes (it does not
score); code checks every quote is in the text, dates poets from one table, and scores.
A root leaves its current default (the app's ranking) only when a challenger wins
clearly AND two other models, asked in both orders, both prefer it.

  pilot-select            choose the pilot roots and their answer key
  extract [--pilot|--all] [--roots a,b] [--workers N]
  poets                   date every poet named in the inventories (one table)
  score [--pilot|--all]   scores and proposed switches
  pairs [--pilot|--all]   second opinion on the proposed switches
  plant                   planted tests on pilot entries
  report [--pilot|--all]
  status

The Ollama key is read from the file named by OLLAMA_KEY_FILE (never printed); without
it, or if it stops working, calls go through the local Ollama app (<model>:cloud).
"""
import argparse
import collections
import concurrent.futures as cf
import hashlib
import json
import math
import os
import random
import re
import sqlite3
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.request
from difflib import SequenceMatcher

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "data", "quran.db")
OUT = os.path.join(HERE, "data", "_default_dict")
PROMPT_VERSION = "x2"

# ---------------------------------------------------------------------------
# The app's current rule (kept in step with app.py): ranking, works that never
# open first, stubs.
PRIORITY = [
    "ibn-faris-maqayis-al-lugha",
    "al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran",
    "abdullah-ibn-abbas-gharib-al-quran-fi-shir-al-arab",
    "al-khalil-b-ahmad-al-farahidi-kitab-al-ain",
    "abu-hayyan-al-gharnati-tuhfat-al-arib-bi-ma-fi-l-quran-min-al-gharib",
    "al-zamakhshari-asas-al-balagha",
    "ibn-manzur-lisan-al-arab",
    "william-edward-lane-arabic-english-lexicon",
    "ismail-bin-hammad-al-jawhari-taj-al-lugha-wa-sihah-al-arabiya",
    "ibn-sida-al-mursi-al-muhkam-wa-l-muhit-al-aazam",
    "firuzabadi-al-qamus-al-muhit",
    "murtada-al-zabidi-taj-al-arus-fi-jawahir-al-qamus",
    "al-fayyumi-al-misbah-al-munir-fi-gharib-al-sharh-al-kabir",
    "al-sahib-bin-abbad-al-muhit-fi-l-lugha",
    "zayn-al-din-al-razi-mukhtar-al-sihah",
    "habib-anthony-salmone-an-advanced-learners-arabic-english-dictionary",
]
RANK = {s: i for i, s in enumerate(PRIORITY)}
NEVER_FIRST = {
    "abu-hayyan-al-gharnati-tuhfat-al-arib-bi-ma-fi-l-quran-min-al-gharib",
    "habib-anthony-salmone-an-advanced-learners-arabic-english-dictionary",
    "firuzabadi-al-qamus-al-muhit",
    "zayn-al-din-al-razi-mukhtar-al-sihah",
}
ENGLISH_ORIGINAL = {
    "william-edward-lane-arabic-english-lexicon",
    "habib-anthony-salmone-an-advanced-learners-arabic-english-dictionary",
}
SHORT = {
    "ibn-faris-maqayis-al-lugha": "Ibn Fāris",
    "al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran": "Mufradāt",
    "abdullah-ibn-abbas-gharib-al-quran-fi-shir-al-arab": "Ibn ʿAbbās",
    "al-khalil-b-ahmad-al-farahidi-kitab-al-ain": "ʿAyn",
    "abu-hayyan-al-gharnati-tuhfat-al-arib-bi-ma-fi-l-quran-min-al-gharib": "Tuḥfa",
    "al-zamakhshari-asas-al-balagha": "Asās",
    "ibn-manzur-lisan-al-arab": "Lisān",
    "william-edward-lane-arabic-english-lexicon": "Lane",
    "ismail-bin-hammad-al-jawhari-taj-al-lugha-wa-sihah-al-arabiya": "Ṣiḥāḥ",
    "ibn-sida-al-mursi-al-muhkam-wa-l-muhit-al-aazam": "Muḥkam",
    "firuzabadi-al-qamus-al-muhit": "Qāmūs",
    "murtada-al-zabidi-taj-al-arus-fi-jawahir-al-qamus": "Tāj",
    "al-fayyumi-al-misbah-al-munir-fi-gharib-al-sharh-al-kabir": "Miṣbāḥ",
    "al-sahib-bin-abbad-al-muhit-fi-l-lugha": "Muḥīṭ",
    "zayn-al-din-al-razi-mukhtar-al-sihah": "Mukhtār",
    "habib-anthony-salmone-an-advanced-learners-arabic-english-dictionary": "Salmoné",
}
STUB_CHARS, POINTER_CHARS = 120, 250
AR_MARKS = re.compile(r"[ً-ْٰـ]")
POINTER_RE = re.compile(r"وقد (?:ذكر|ذكرت|ذكرناه)|قد مضى ذكره")


def is_stub(ar):
    ar = ar or ""
    if len(ar) < STUB_CHARS:
        return True
    return len(ar) < POINTER_CHARS and bool(POINTER_RE.search(AR_MARKS.sub("", ar)))


def app_default(entries):
    """The entry the app opens today (ranking, passing over stubs and NEVER_FIRST)."""
    pool = [e for e in entries if e["slug"] not in NEVER_FIRST and not is_stub(e["ar"])] or entries
    return min(pool, key=lambda e: (RANK.get(e["slug"], 999), e["order"]))


# ---------------------------------------------------------------------------
# Scoring weights (the agreed criteria).
W_ROOT, W_EARLY, W_QURAN, W_COVERS, W_ORIGIN, PENALTY_CAP = 3.0, 3.0, 2.0, 1.0, 0.5, 3.0
EARLY_FULL, QURAN_FULL = 3.0, 2.0          # witnesses needed for full credit
ERA_WEIGHT = {"pre-islamic": 1.0, "mukhadram": 1.0, "umayyad": 0.5, "later": 0.2,
              "unknown": 0.5, None: 0.4}   # None = the entry names no poet
SPEECH_WEIGHT = 0.5
PEN_DEFINES, PEN_GLOSS, PEN_LATER, PEN_INCIDENTAL = 0.75, 0.75, 0.75, 0.1
MARGIN = 1.5        # a challenger must beat the current default by this much
CONFIRM_SLACK = 2.5 # re-read rivals within this much of the margin
NEAR = 0.5          # challengers this close to the best go to the shorter entry
# The author states a root sense (checked in the original, not the readable framing).
CORE_AR = re.compile(r"يدل علي|اصل واحد|اصلان|اصول|اصل صحيح|قياس|معظم الباب|الباب كله|كلمه واحده|واصل ال|"
                     r"اصله من|في اللغه|سمي بذلك|وسمي|ومن المجاز")
# A root sense counts when the readable version attributes it to the author or an
# authority he quotes ("Ibn Fāris derives…", "…said al-Azharī"), not its own summary.
ATTRIB = re.compile(
    r"\b(?:ibn|abu|lane|sibawayh|thalab|al-(?:raghib|zamakhshari|jawhari|azhari|khalil|layth|laith|farra|asmai|"
    r"fayyumi|zabidi|sahib|firuzabadi|kisai|zajjaj|mubarrad|harbi|razi|akhfash|jahiz|qali|sijistani))\b"
    r"|\b(?:say|says|said|state|states|stated|note|notes|noted|holds?|held|explains?|explained|derives?|derived|"
    r"treats?|treated|classif\w*|reports?|reported|records?|recorded|according to|traces?|traced|considers?|"
    r"regards?|attributes?)\b")
CORE_EN = re.compile(r"primary signification|\bprimarily\b|\boriginally\b|\bproperly\b|radical|\borigin", re.I)


def ar_norm(t):
    t = AR_MARKS.sub("", t or "")
    t = re.sub("[أإآٱ]", "ا", t)
    return t.replace("ى", "ي").replace("ة", "ه")


# ---------------------------------------------------------------------------
# Ollama Cloud access.
KEY_FILE = os.environ.get("OLLAMA_KEY_FILE")
DIRECT_URL, LOCAL_URL = "https://ollama.com/api/chat", "http://localhost:11434/api/chat"
MODELS = {  # role: (direct name, local-app name)
    "extract": ("deepseek-v4-pro:0813", "deepseek-v4-pro:cloud"),
    "kimi": ("kimi-k3", "kimi-k3:cloud"),
    "glm": ("glm-5.3", "glm-5.3:cloud"),
    "deepseek": ("deepseek-v4-pro:0813", "deepseek-v4-pro:cloud"),
}
_route = {"direct": bool(KEY_FILE and os.path.exists(KEY_FILE))}
_route_lock = threading.Lock()
USAGE = collections.Counter()
_usage_lock = threading.Lock()


def _key():
    return open(KEY_FILE).read().strip()


def chat(role, prompt, think=False, timeout=600, tries=6, fmt=None, num_predict=None, temperature=0.1):
    """One chat call; returns (content, usage dict). Retries rate limits and 5xx."""
    last = None
    for attempt in range(tries):
        direct = _route["direct"]
        model = MODELS[role][0 if direct else 1]
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}],
                   "stream": False, "think": think,
                   "options": {"temperature": temperature, "num_ctx": 65536}}
        if temperature == 0:
            payload["options"]["seed"] = 42
        if fmt:
            payload["format"] = fmt
        if num_predict:
            payload["options"]["num_predict"] = num_predict
        headers = {"Content-Type": "application/json"}
        if direct:
            headers["Authorization"] = "Bearer " + _key()
        req = urllib.request.Request(DIRECT_URL if direct else LOCAL_URL,
                                     data=json.dumps(payload).encode(), headers=headers)
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                j = json.loads(r.read())
            out = re.sub(r"(?s)<think>.*?</think>", "", j["message"].get("content") or "").strip()
            use = {"model": model, "in": j.get("prompt_eval_count") or 0,
                   "out": j.get("eval_count") or 0, "sec": round(time.time() - t0, 1)}
            with _usage_lock:
                USAGE[role + ":in"] += use["in"]; USAGE[role + ":out"] += use["out"]; USAGE[role + ":calls"] += 1
            if out:
                return out, use
            last = "empty reply"
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in (401, 403) and direct:
                with _route_lock:
                    _route["direct"] = False      # key revoked or expired: use the local app
                print(f"[route] direct key refused ({e.code}); switching to the local Ollama app", flush=True)
                continue
            if e.code == 400 and fmt:
                fmt = None                          # model rejects the format option
                continue
        except Exception as e:  # timeouts, resets
            last = type(e).__name__ + ": " + str(e)[:120]
        time.sleep(min(120, 10 * (attempt + 1)) + random.random() * 5)
    raise RuntimeError(f"{role}: {last}")


def parse_json(text):
    s, e = text.find("{"), text.rfind("}")
    if s < 0 or e <= s:
        raise ValueError("no JSON object")
    body = text[s:e + 1]
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return json.loads(re.sub(r",\s*([}\]])", r"\1", body))


# ---------------------------------------------------------------------------
# Data.
def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def load_entries():
    c = db()
    rows = c.execute(
        "SELECT e.id, e.root_buckwalter, e.root_arabic, e.dictionary_slug, e.original_text_ar, e.harmonized_en, "
        "d.name_en, d.author_death_year, d.sort_order "
        "FROM dictionary_entries e JOIN dictionaries d ON d.slug = e.dictionary_slug "
        "WHERE e.review_status = 'approved' AND COALESCE(e.hidden,0) = 0 "
        "AND e.harmonized_en IS NOT NULL AND e.harmonized_en <> '' "
        "ORDER BY d.author_death_year, d.sort_order").fetchall()
    roots = collections.OrderedDict()
    for i, r in enumerate(rows):
        e = {"id": r["id"], "root": r["root_buckwalter"], "root_ar": r["root_arabic"], "slug": r["dictionary_slug"],
             "ar": r["original_text_ar"] or "", "en": r["harmonized_en"], "name": r["name_en"], "order": i}
        e["hash"] = hashlib.sha1((e["en"] + "\x00" + e["ar"]).encode()).hexdigest()[:12]
        roots.setdefault(e["root"], []).append(e)
    return roots


def candidates(entries):
    """Entries that could open first: not a stub, not one of the NEVER_FIRST works."""
    return [e for e in entries if e["slug"] not in NEVER_FIRST and not is_stub(e["ar"])]


_lemma_cache = {}


def quran_words(root):
    """The Qur'an's words from this root: [(id, arabic, occurrences, typical gloss)]."""
    if root in _lemma_cache:
        return _lemma_cache[root]
    c = db()
    occ = collections.defaultdict(set)
    ar = {}
    for r in c.execute("SELECT chapter, verse, word_pos, lemma_buckwalter, lemma_arabic FROM morphology "
                       "WHERE root_buckwalter = ? AND lemma_buckwalter IS NOT NULL", (root,)):
        occ[r["lemma_buckwalter"]].add((r["chapter"], r["verse"], r["word_pos"]))
        ar[r["lemma_buckwalter"]] = re.sub(r"[^؀-ۿ]", "", r["lemma_arabic"] or "")
    out = []
    for i, (lb, locs) in enumerate(sorted(occ.items(), key=lambda kv: -len(kv[1]))[:12]):
        glosses = collections.Counter()
        for ch, v, wp in list(locs)[:40]:
            g = c.execute("SELECT translation_en FROM word_glosses WHERE chapter=? AND verse=? AND word_pos=?",
                          (ch, v, wp)).fetchone()
            if g and g[0]:
                glosses[g[0].strip().lower()] += 1
        out.append((f"L{i + 1}", ar[lb], len(locs), glosses.most_common(1)[0][0] if glosses else ""))
    _lemma_cache[root] = out
    return out


# ---------------------------------------------------------------------------
# Step 1: the evidence inventory.
EXTRACT_PROMPT = """You are cataloguing the evidence in one dictionary entry. The entry below is the readable English version, shown on a Qur'an study site, of what one classical dictionary says about the Arabic root {root_ar}. Do not judge or summarise the entry: list what is in it. Every item needs "q", a short exact quote (4 to 15 words) copied character for character from the entry, so that it can be checked.

The Qur'an uses this root in these words (id: lemma, occurrences, typical translation):
{lemmas}

Return one JSON object with these keys:

"root_sense": does the entry report that the dictionary's author, or an authority he quotes, says what the root's words share: an underlying or original sense from which its other senses come ("Ibn Fāris says the root indicates…", "its origin is…, said al-Azharī", "X is so called because…", "two separate origins…")? Only a statement the entry attributes to the dictionary or its sources counts. The readable version's own summaries and headings ("Core sense:", "The senses cluster around…") do not, and neither does a definition of the main word alone. Give {{"stated": true or false, "q": quote or null, "branches": true or false}}; "branches" is true when the entry shows how several derived words or senses follow from that shared sense.

"poetry": each line of poetry or rajaz cited as evidence: {{"q": quote, "poet": the poet's name exactly as the entry gives it, or null if the entry names none}}.

"speech": each proverb, saying of the Arabs, or report of how the Arabs or Bedouin speak, cited as evidence (not poetry, not the Qur'an, not hadith): {{"q": quote}}.

"quran": each Qur'anic verse cited or quoted: {{"q": quote, "ref": "sura:verse" if the entry gives it else null, "use": "explains" or "gloss" or "mention"}}. "explains": the entry explains the word in the verse through its ordinary meaning in Arabic. "gloss": the entry reports what an exegete, Companion or other authority said the word in the verse means. "mention": cited with no explanation.

"hadith": each hadith, prophetic report, or saying of a Companion or early Muslim authority cited: {{"q": quote, "defines": true or false}}; "defines" is true when a meaning, sense or distinction of the word is drawn from the report, false when the report only illustrates a sense the entry establishes otherwise.

"later": each definition drawn from law (fiqh), theology, Sufism or later technical usage: {{"q": quote, "kind": "legal" or "theological" or "technical"}}.

"origin": each statement that a word is foreign (Persian, Syriac, Hebrew, Nabataean, Greek, Ethiopic…) or related to a word in another language: {{"q": quote, "language": name}}.

"covers": the ids (L1, L2…) of the Qur'an's words above that the entry discusses.

"defects": {{"truncated": true if the entry visibly stops mid-way, "pointer": true if it mainly sends the reader to another root instead of explaining this one, "other_root": true if most of it is about a different root or a list of unrelated words}}.

Use empty lists where there is nothing. Return only the JSON object.

ENTRY:
<<<
{text}
>>>"""


def lemma_lines(root):
    ws = quran_words(root)
    if not ws:
        return "(none recorded)"
    return "\n".join(f"{i}: {a}, {n}×, \"{g}\"" for i, a, n, g in ws)


def extract_one(e, text=None, tag=""):
    text = text if text is not None else e["en"]
    prompt = EXTRACT_PROMPT.format(root_ar=e["root_ar"] or e["root"], lemmas=lemma_lines(e["root"]), text=text)
    err = None
    for attempt in range(3):
        out, use = chat("extract", prompt + ("" if attempt == 0 else "\n\nReturn only a valid JSON object."),
                        fmt="json", temperature=0)
        try:
            inv = parse_json(out)
            return {"id": e["id"], "root": e["root"], "slug": e["slug"], "hash": e["hash"], "pv": PROMPT_VERSION,
                    "tag": tag, "inv": inv, "use": use}
        except Exception as ex:
            err = f"{ex}: {out[:200]}"
    raise RuntimeError("unparseable: " + err)


def inv_path(name="extract"):
    return os.path.join(OUT, name + ".jsonl")


def load_inventories(name="extract"):
    got = {}
    if os.path.exists(inv_path(name)):
        for line in open(inv_path(name), encoding="utf-8"):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("pv") == PROMPT_VERSION:
                got[(r["id"], r["hash"], r.get("tag", ""))] = r
    return got


_write_lock = threading.Lock()


def append(name, rec):
    with _write_lock:
        with open(inv_path(name), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def run_pool(jobs, fn, workers, label):
    done = fail = 0
    t0 = time.time()
    with cf.ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(fn, j): j for j in jobs}
        for f in cf.as_completed(futs):
            try:
                f.result()
                done += 1
            except Exception as e:
                fail += 1
                print(f"[{label}] failed: {str(e)[:160]}", flush=True)
            if (done + fail) % 25 == 0 or done + fail == len(jobs):
                rate = (done + fail) / max(1e-9, time.time() - t0) * 60
                print(f"[{label}] {done + fail}/{len(jobs)} ({fail} failed) {rate:.1f}/min "
                      f"tokens in {USAGE['extract:in'] + USAGE['kimi:in'] + USAGE['glm:in'] + USAGE['deepseek:in']:,} "
                      f"out {USAGE['extract:out'] + USAGE['kimi:out'] + USAGE['glm:out'] + USAGE['deepseek:out']:,}",
                      flush=True)
    return done, fail


def cmd_extract(args):
    os.makedirs(OUT, exist_ok=True)
    roots = load_entries()
    todo_roots = select_roots(args, roots)
    have = load_inventories()
    jobs = []
    for r in todo_roots:
        cands = candidates(roots[r])
        if len(cands) < 2:
            continue
        for e in cands:
            if (e["id"], e["hash"], "") not in have:
                jobs.append(e)
    jobs.sort(key=lambda e: -len(e["en"]))     # long ones first so the tail is short
    print(f"{len(jobs)} entries to read across {len(todo_roots)} roots", flush=True)

    def work(e):
        append("extract", extract_one(e))
    run_pool(jobs, work, args.workers, "extract")
    print("usage:", dict(USAGE), flush=True)


def select_roots(args, roots):
    if args.roots:
        names = (open(args.roots[1:], encoding="utf-8").read().split() if args.roots.startswith("@")
                 else args.roots.split(","))
        return [r for r in names if r in roots]
    if args.pilot:
        return list(json.load(open(os.path.join(OUT, "pilot.json")))["roots"])
    return list(roots)


# ---------------------------------------------------------------------------
# Quote checking.
def txt_norm(t):
    t = unicodedata.normalize("NFKD", t or "")
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = AR_MARKS.sub("", t)
    t = re.sub(r"[ʿʾ'’‘`´\"“”«»*_#]", "", t)
    t = re.sub(r"[‐-―−]", "-", t)
    return " ".join(t.lower().split())


def attributed(q, norm_text):
    """Is the quote (or the 160 characters before it) attributed to a named authority?"""
    qn = txt_norm(q)
    i = norm_text.find(qn[:40]) if qn else -1
    if i < 0:
        m = SequenceMatcher(None, norm_text, qn, autojunk=False).find_longest_match(0, len(norm_text), 0, len(qn))
        i = max(0, m.a - m.b)
    return bool(ATTRIB.search(norm_text[max(0, i - 160): i + len(qn)]))


def quote_found(q, norm_text):
    qn = txt_norm(q)
    if len(qn) < 6:
        return False
    if qn in norm_text:
        return True
    sm = SequenceMatcher(None, norm_text, qn, autojunk=False)
    m = sm.find_longest_match(0, len(norm_text), 0, len(qn))
    if m.size < min(12, len(qn) // 2):
        return False
    start = max(0, m.a - m.b - 8)
    window = norm_text[start:start + len(qn) + 16]
    matched = sum(b.size for b in SequenceMatcher(None, window, qn, autojunk=False).get_matching_blocks())
    return matched / len(qn) >= 0.85


# ---------------------------------------------------------------------------
# Poets: one table, seeded from the site's own dated poets.
POETS_FILE = os.path.join(OUT, "poets.json")
LATER_SEED = {  # well-known poets the lexicographers quote, by era (site transliteration)
    "mukhadram": ["Labīd", "Labīd ibn Rabīʿa", "al-Ḥuṭayʾa", "Ḥassān ibn Thābit", "Ḥassān", "Kaʿb ibn Zuhayr",
                  "al-Nābigha al-Jaʿdī", "Abū Dhuʾayb", "Abū Dhuʾayb al-Hudhalī", "al-Shammākh", "Ibn Muqbil",
                  "Tamīm ibn Muqbil", "Mutammim ibn Nuwayra", "ʿAmr ibn Maʿdīkarib", "Ḥumayd ibn Thawr",
                  "al-Aʿshā", "Maymūn al-Aʿshā", "al-Khansāʾ", "Abū Khirāsh", "Suḥaym ʿAbd Banī al-Ḥasḥās",
                  "al-Zibriqān", "ʿAbda ibn al-Ṭabīb", "Ibn Aḥmar", "Ḍābiʾ ibn al-Ḥārith", "Abū Miḥjan"],
    "umayyad": ["Jarīr", "al-Farazdaq", "al-Akhṭal", "Dhū al-Rumma", "Ruʾba", "Ruʾba ibn al-ʿAjjāj", "al-ʿAjjāj",
                "al-Kumayt", "al-Ṭirimmāḥ", "al-Rāʿī", "al-Rāʿī al-Numayrī", "Kuthayyir", "Kuthayyir ʿAzza",
                "Jamīl", "Jamīl Buthayna", "ʿUmar ibn Abī Rabīʿa", "al-Qaṭāmī", "Abū al-Najm", "Abū al-Najm al-ʿIjlī",
                "Ibn Harma", "Ibrāhīm ibn Harma", "Majnūn Laylā", "Laylā al-Akhyaliyya", "Tawba ibn al-Ḥumayyir",
                "Abū Ṣakhr al-Hudhalī", "Nuṣayb", "al-Aḥwaṣ", "ʿUbayd Allāh ibn Qays al-Ruqayyāt",
                "Ibn Qays al-Ruqayyāt"],
    "later": ["Bashshār", "Bashshār ibn Burd", "Abū Nuwās", "Abū Tammām", "al-Buḥturī", "al-Mutanabbī",
              "Ibn al-Rūmī", "Abū al-ʿAlāʾ al-Maʿarrī", "al-Maʿarrī", "Ibn al-Muʿtazz", "Abū al-ʿAtāhiya",
              "Muslim ibn al-Walīd", "al-Ḥarīrī", "Ibn Durayd", "al-Ṣāḥib ibn ʿAbbād"],
}


def pkey(name):
    s = unicodedata.normalize("NFKD", (name or "").lower())
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[ʿʾ'’‘`´]", "", s)
    s = re.sub(r"\b(?:al|el|[a-z]{1,2}h?)-(?=[a-z])", "", s)      # the article, assimilated or not
    s = re.sub(r"(?<=[a-z])ah\b", "a", s)                          # Ruʾbah = Ruʾba, al-Nābighah = al-Nābigha
    s = re.sub(r"\bb\.|\bbin\b|\bibn\b", " ibn ", s)
    s = re.sub(r"\b(?:the|a|an|poet|poetess|said|says|of|tribe|banu|bani|verse|rajaz|rajiz)\b", " ", s)
    s = re.sub(r"[^a-z ]", " ", s)
    return " ".join(s.split())


def seed_poets():
    table = {}
    c = db()
    for (name,) in c.execute("SELECT DISTINCT poet_latin FROM poetry_poems WHERE poet_latin IS NOT NULL"):
        table[pkey(name)] = "pre-islamic"
    for era, names in LATER_SEED.items():
        for n in names:
            table[pkey(n)] = era
    return table


# Philologists who recite a line are its transmitters, not its poets: the line counts
# as unattributed.
RECITERS = {pkey(n) for n in (
    "Ibn al-Aʿrābī", "Thaʿlab", "al-Farrāʾ", "al-Azharī", "al-Khalīl", "al-Aṣmaʿī", "Abū ʿAmr", "Abū ʿAmr ibn al-ʿAlāʾ",
    "Abū Zayd", "Abū ʿUbayda", "Abū ʿUbayd", "al-Layth", "Ibn Barrī", "Ibn Sīda", "Ibn Sīdah", "al-Jawharī", "Sībawayh",
    "Ibn al-Sikkīt", "Abū Ḥanīfa", "Abū Ḥanīfa al-Dīnawarī", "al-Kisāʾī", "al-Mubarrad", "Ibn Durayd", "al-Zajjāj",
    "Ibn al-Athīr", "al-Fayyūmī", "al-Zabīdī", "Ibn Manẓūr", "Ibn Fāris", "Lane", "al-Rāghib", "al-Zamakhsharī",
    "Ibn Jinnī", "al-Akhfash", "Abū Ḥātim", "al-Liḥyānī", "Ibn Buzurj", "Shamir", "Abū al-Haytham", "al-Mufaḍḍal",
    "Ibn al-Anbārī", "Ibn Qutayba", "Abū ʿAlī al-Qālī", "al-Tawwazī", "al-Qālī", "al-Ṣāghānī", "al-Fārābī")}


def poet_era(name, table):
    if not name:
        return None
    k = pkey(name)
    if not k or k in RECITERS:
        return None
    if k in table:
        return table[k]
    toks = k.split()
    table = {kk: v for kk, v in table.items() if isinstance(v, str)}   # head matches use dated poets only
    # "Zuhayr" alone, "Ṭarafa ibn al-ʿAbd" vs "Ṭarafa": accept a match on the leading
    # name when every table poet sharing it has the same era.
    for n in (3, 2, 1):
        if len(toks) >= n:
            head = " ".join(toks[:n])
            eras = {v for kk, v in table.items() if kk == head or kk.startswith(head + " ")}
            if eras and eras <= {"pre-islamic", "mukhadram"}:
                return "pre-islamic" if "pre-islamic" in eras else "mukhadram"   # same weight either way
            if len(eras) == 1:
                return eras.pop()
    if "hudhal" in k:
        return "mukhadram"        # the Hudhalī poets are overwhelmingly pre-Islamic and early
    return "unknown"


POET_PROMPT = """For each name below, say when the Arabic poet lived. Answer with one of: pre-islamic (died before about 610), mukhadram (lived across the coming of Islam), umayyad (active about 660-750), later (Abbasid or after), unknown (cannot tell who is meant, or not a poet). Return one JSON object mapping each name exactly as given to its answer.

{names}"""


def cmd_poets(args):
    table = seed_poets()
    saved = json.load(open(POETS_FILE, encoding="utf-8")) if os.path.exists(POETS_FILE) else {}
    table.update(saved.get("llm", {}))
    names = collections.Counter()
    for r in load_inventories().values():
        for p in r["inv"].get("poetry") or []:
            if isinstance(p, dict) and p.get("poet"):
                if poet_era(p["poet"], table) == "unknown":
                    names[p["poet"].strip()] += 1
    todo = [n for n, _ in names.most_common()]
    # Known poets hidden among the unknowns check the model on every batch.
    checks = {"Imruʾ al-Qays": "pre-islamic", "Jarīr": "umayyad", "Abū Nuwās": "later", "Labīd": "mukhadram",
              "Dhū al-Rumma": "umayyad", "Ṭarafa": "pre-islamic"}
    llm = dict(saved.get("llm", {}))
    wrong = collections.Counter()
    batches = [todo[i:i + 40] for i in range(0, len(todo), 40)]

    def ask(job):
        role, batch = job
        out, _ = chat(role, POET_PROMPT.format(names="\n".join(batch + list(checks))), think=False, fmt="json",
                      temperature=0, timeout=180 if role == "glm" else 300, tries=1 if role == "glm" else 4)
        return role, batch, parse_json(out)
    votes = collections.defaultdict(list)
    with cf.ThreadPoolExecutor(8) as ex:
        for fut in cf.as_completed([ex.submit(ask, (role, b)) for b in batches for role in ("kimi", "deepseek")]):
            try:
                role, batch, ans = fut.result()
            except Exception as e:
                print("[poets] a batch failed:", str(e)[:120])
                continue
            ans = {str(k).strip(): str(v).strip().lower() for k, v in ans.items()}
            for n, want in checks.items():
                wrong[role] += ans.get(n) != want
            for n in batch:
                votes[n].append(ans.get(n, "unknown"))
    for n in todo:
        known = [v for v in votes[n] if v in ERA_WEIGHT and v not in ("unknown", None)]
        if not known:
            llm[pkey(n)] = "unknown"
        elif len({ERA_WEIGHT[v] for v in known}) == 1:
            llm[pkey(n)] = known[0]              # agreement (pre-Islamic and mukhadram weigh the same)
        else:                                     # the models disagree: the average weight
            llm[pkey(n)] = round(sum(ERA_WEIGHT[v] for v in known) / len(known), 2)
    json.dump({"llm": llm, "check_errors": dict(wrong), "names_seen": names.most_common(),
               "votes": {n: votes[n] for n in todo}},
              open(POETS_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(todo)} unmatched poet names dated; check errors by model {dict(wrong)}")


def poet_table():
    table = seed_poets()
    if os.path.exists(POETS_FILE):
        table.update(json.load(open(POETS_FILE, encoding="utf-8")).get("llm", {}))
    return table


# ---------------------------------------------------------------------------
# Step 2: scoring.
def items(inv, key):
    v = inv.get(key) or []
    return [x for x in v if isinstance(x, dict)]


def score_entry(e, rec, table):
    """Score one entry from its verified inventory. Returns a dict with the parts."""
    inv = rec["inv"]
    nt = txt_norm(e["en"])
    seen = set()
    stats = collections.Counter()

    def ok(x):
        q = x.get("q") or ""
        stats["claimed"] += 1
        if not quote_found(q, nt):
            return False
        k = txt_norm(q)[:60]
        if k in seen:
            return False
        seen.add(k)
        stats["verified"] += 1
        return True

    rs = inv.get("root_sense") if isinstance(inv.get("root_sense"), dict) else {}
    root = 0.0
    if rs.get("stated") and ok({"q": rs.get("q")}):
        # Full credit when the statement is attributed AND the original has the
        # wording of a root-sense statement; half with one of the two; none without.
        orig = e["ar"] if e["slug"] in ENGLISH_ORIGINAL else ar_norm(e["ar"])
        checks = attributed(rs.get("q"), nt) + bool((CORE_EN if e["slug"] in ENGLISH_ORIGINAL else CORE_AR).search(orig))
        root = (2.0 + (1.0 if rs.get("branches") else 0.0)) * checks / 2
    early_sum, eras = 0.0, collections.Counter()
    for p in items(inv, "poetry"):
        if ok(p):
            era = poet_era(p.get("poet"), table)
            if isinstance(era, (int, float)):
                eras["disputed"] += 1
                early_sum += era
            else:
                eras[era or "unnamed"] += 1
                early_sum += ERA_WEIGHT[era]
    n_speech = sum(1 for s in items(inv, "speech") if ok(s))
    early_sum += SPEECH_WEIGHT * n_speech
    q_sum, uses = 0.0, collections.Counter()
    for q in items(inv, "quran"):
        if ok(q):
            u = q.get("use") if q.get("use") in ("explains", "gloss", "mention") else "mention"
            uses[u] += 1
            q_sum += {"explains": 1.0, "mention": 0.5, "gloss": 0.0}[u]
    n_def = n_inc = 0
    for h in items(inv, "hadith"):
        if ok(h):
            if h.get("defines"):
                n_def += 1
            else:
                n_inc += 1
    n_later = sum(1 for x in items(inv, "later") if ok(x))
    n_origin = sum(1 for x in items(inv, "origin") if ok(x))
    ws = quran_words(e["root"])
    total_occ = sum(n for _, _, n, _ in ws) or 1
    covered = {str(c).strip().upper() for c in (inv.get("covers") or [])}
    covers = sum(n for i, _, n, _ in ws if i in covered) / total_occ if ws else 1.0
    pen = min(PENALTY_CAP, PEN_DEFINES * n_def + PEN_GLOSS * uses["gloss"] + PEN_LATER * n_later
              + PEN_INCIDENTAL * n_inc)
    parts = {
        "root": round(root, 2),
        "early": round(W_EARLY * min(1.0, early_sum / EARLY_FULL), 2),
        "quran": round(W_QURAN * min(1.0, q_sum / QURAN_FULL), 2),
        "covers": round(W_COVERS * covers, 2),
        "origin": W_ORIGIN if n_origin else 0.0,
        "penalty": round(-pen, 2),
    }
    d = inv.get("defects") if isinstance(inv.get("defects"), dict) else {}
    return {"id": e["id"], "slug": e["slug"], "score": round(sum(parts.values()), 2), "parts": parts,
            "eras": dict(eras), "speech": n_speech, "quran_uses": dict(uses), "hadith_defines": n_def,
            "hadith_incidental": n_inc, "later": n_later,
            "defects": [k for k in ("truncated", "pointer", "other_root") if d.get(k)],
            "verified": f"{stats['verified']}/{stats['claimed']}", "len": len(e["en"])}


def decide(entries, scored):
    """The agreed selection rule. Returns (incumbent, best, proposal) where proposal is
    the challenger to put to the second opinion, or None to keep the incumbent."""
    inc = app_default(entries)
    s_inc = scored.get(inc["id"])
    pool = [e for e in candidates(entries) if e["id"] in scored and not scored[e["id"]]["defects"]]
    if not pool or s_inc is None:
        return inc, None, None
    top = max(scored[e["id"]]["score"] for e in pool)
    near = [e for e in pool if scored[e["id"]]["score"] >= top - NEAR]
    best = min(near, key=lambda e: len(e["en"]))
    if best["id"] == inc["id"]:
        return inc, best, None
    beats = scored[best["id"]]["score"] >= s_inc["score"] + MARGIN
    flawed = bool(s_inc["defects"]) and scored[best["id"]]["score"] >= s_inc["score"]
    return inc, best, (best if (beats or flawed) else None)


def cmd_score(args, quiet=False):
    roots = load_entries()
    todo = select_roots(args, roots)
    invs = load_inventories()
    table = poet_table()
    res = {}
    for r in todo:
        entries = roots[r]
        scored = {}
        for e in candidates(entries):
            s = median_score(e, invs, table)
            if s:
                scored[e["id"]] = s
        inc, best, prop = decide(entries, scored)
        res[r] = {"incumbent": inc["slug"], "incumbent_id": inc["id"], "best": best["slug"] if best else None,
                  "proposal": prop["slug"] if prop else None, "proposal_id": prop["id"] if prop else None,
                  "scores": {SHORT.get(v["slug"], v["slug"]): v for v in scored.values()}}
    json.dump(res, open(os.path.join(OUT, "scores.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if not quiet:
        n = sum(1 for v in res.values() if v["proposal"])
        print(f"{len(res)} roots scored; {n} proposed switches")
        print(collections.Counter(f"{SHORT[v['incumbent']]} -> {SHORT[v['proposal']]}"
                                  for v in res.values() if v["proposal"]).most_common(20))
    return res


RUN_TAGS = ("", "r1", "r2")


def median_score(e, invs, table):
    """Score an entry from every reading we have (1 or 3); the median reading decides."""
    runs = [invs[(e["id"], e["hash"], t)] for t in RUN_TAGS if (e["id"], e["hash"], t) in invs]
    if not runs:
        return None
    ss = sorted((score_entry(e, x, table) for x in runs), key=lambda v: v["score"])
    out = ss[len(ss) // 2]
    out["runs"] = [v["score"] for v in ss]
    return out


def cmd_confirm(args):
    """Read the entries that decide each root twice more: the current default and the
    two best challengers after the first reading."""
    roots = load_entries()
    invs = load_inventories()
    table = poet_table()
    jobs = []
    for r in select_roots(args, roots):
        es = roots[r]
        cands = candidates(es)
        if len(cands) < 2:
            continue
        first = {e["id"]: score_entry(e, invs[(e["id"], e["hash"], "")], table)
                 for e in cands if (e["id"], e["hash"], "") in invs}
        inc = app_default(es)
        if inc["id"] not in first:
            continue
        # Only where a switch is within reach: a rival no more than CONFIRM_SLACK short of
        # the margin (single readings moved by more than 1 point in 4 of 20 repeats).
        bar = first[inc["id"]]["score"] + MARGIN - CONFIRM_SLACK
        rivals = sorted((e for e in cands if e["id"] in first and e["id"] != inc["id"]
                         and first[e["id"]]["score"] >= bar),
                        key=lambda e: -first[e["id"]]["score"])[:2]
        if not rivals and not first[inc["id"]]["defects"]:
            continue
        for e in [inc] + rivals:
            for tag in RUN_TAGS[1:]:
                if (e["id"], e["hash"], tag) not in invs:
                    jobs.append((e, tag))
    print(f"{len(jobs)} further readings", flush=True)
    run_pool(jobs, lambda j: append("extract", extract_one(j[0], tag=j[1])), args.workers, "confirm")


# ---------------------------------------------------------------------------
# Step 3: second opinion on each proposed switch.
PAIR_PROMPT = """A reader opens the page for the Arabic root {root_ar} on a Qur'an study site. The page lists what the classical Arabic dictionaries say about the root, and one entry opens automatically. Which of these two entries should open first?

The site reads the Qur'an's words from evidence. Prefer the entry that
1. explains the root: says what its words share and shows how the senses branch from it (a definition of one word is not enough);
2. shows the words in use in the Qur'an's time: poetry (pre-Islamic and early poets count most, Umayyad poets less, later poets least), proverbs, the speech of the Arabs;
3. explains the root's Qur'anic verses through the word's ordinary sense (an exegete's reported interpretation does not count);
4. covers the words the Qur'an uses from this root: {words};
and does not rest its explanation on hadith, exegetes' interpretations, or legal or theological definitions. A few well-chosen witnesses are worth more than a long list: do not prefer an entry for being longer. When the two are close, prefer the shorter.

ENTRY A:
<<<
{a}
>>>

ENTRY B:
<<<
{b}
>>>

Give your reasons in two or three sentences, then a final line that is exactly "CHOICE: A" or "CHOICE: B"."""


# The pilot's position check (both models, both orders, 18 pairs): kimi-k3 kept its
# verdict when the order flipped in 15/18 but nearly always preferred the richer, longer
# entry; deepseek-v4-pro flipped in 7/18, six times toward whichever entry it read first,
# and when consistent mostly preferred the shorter default. So a switch needs BOTH models
# to prefer the challenger in BOTH orders, asked in this order with an early exit:
#   1. deepseek, challenger first: picks the default anyway -> keep (1 call)
#   2. deepseek, default first;  3-4. kimi, both orders
# All four for the challenger -> switch. kimi both orders for it but deepseek following
# the order -> "split" (listed for the owner, default kept).
# (glm-5.3 is not used: it hangs, and a request the client abandons keeps holding one of
# the key's few concurrent slots.)
VOTE_ORDER = (("deepseek", "PI"), ("deepseek", "IP"), ("kimi", "IP"), ("kimi", "PI"))


def judge(role, root_ar, words, a, b):
    prompt = PAIR_PROMPT.format(root_ar=root_ar, words=words, a=a, b=b)
    out, use = chat(role, prompt, think=True, timeout=1500, tries=3, temperature=0)
    m = re.findall(r"CHOICE:\s*\**\s*([AB])\b", out)
    return (m[-1] if m else "?"), out[-700:], use


def load_votes():
    out = {}
    if os.path.exists(inv_path("votes")):
        for line in open(inv_path("votes"), encoding="utf-8"):
            v = json.loads(line)
            out[(v["root"], v["inc"], v["prop"], v["role"], v["order"])] = v
    return out


def verdict(r, inc_id, prop_id, votes):
    """'switch', 'split', 'keep', or None while votes are still missing."""
    g = lambda role, order: (votes.get((r, inc_id, prop_id, role, order)) or {}).get("pick")
    d_pi = g("deepseek", "PI")
    if d_pi is None:
        return None
    if d_pi != "challenger":
        return "keep"
    d_ip, k_ip, k_pi = g("deepseek", "IP"), g("kimi", "IP"), g("kimi", "PI")
    if None in (d_ip, k_ip, k_pi):
        return None
    if k_ip == k_pi == "challenger":
        return "switch" if d_ip == "challenger" else "split"
    return "keep"


def switch_decision(r, inc_id, prop_id, votes):
    v = verdict(r, inc_id, prop_id, votes)
    return None if v is None else v == "switch"


def cmd_pairs(args):
    res = json.load(open(os.path.join(OUT, "scores.json"), encoding="utf-8"))
    roots = load_entries()
    by_id = {e["id"]: e for es in roots.values() for e in es}
    todo = [r for r in select_roots(args, roots) if res.get(r, {}).get("proposal_id")]
    votes = load_votes()
    todo = [r for r in todo if verdict(r, res[r]["incumbent_id"], res[r]["proposal_id"], votes) is None]
    print(f"{len(todo)} proposed switches to judge", flush=True)

    def work(r):
        inc, prop = by_id[res[r]["incumbent_id"]], by_id[res[r]["proposal_id"]]
        words = "; ".join(f"{a} ({n}×)" for _, a, n, _ in quran_words(r)[:8]) or "(none recorded)"
        for role, order in VOTE_ORDER:
            vs = load_votes()
            if verdict(r, inc["id"], prop["id"], vs) is not None:
                return
            if (r, inc["id"], prop["id"], role, order) in vs:
                continue
            a, b = (inc, prop) if order == "IP" else (prop, inc)
            ch, tail, use = judge(role, inc["root_ar"] or r, words, a["en"], b["en"])
            pick = "?" if ch == "?" else ("incumbent" if (ch == "A") == (order == "IP") else "challenger")
            append("votes", {"root": r, "inc": inc["id"], "prop": prop["id"], "role": role, "order": order,
                             "pick": pick, "tail": tail, "use": use})
    run_pool(todo, work, args.workers, "pairs")


def evidence_line(x):
    """One plain line summarising an entry's scored evidence."""
    parts, bits = x["parts"], []
    if parts["root"] >= 2:
        bits.append("states the root sense")
    elif parts["root"] > 0:
        bits.append("root sense, partly")
    eras = x.get("eras") or {}
    early = eras.get("pre-islamic", 0) + eras.get("mukhadram", 0)
    poems = sum(eras.values())
    if poems:
        bits.append(f"{poems} poem{'s' * (poems != 1)}" + (f" ({early} pre-Islamic or early)" if early else ""))
    if x.get("speech"):
        bits.append(f"{x['speech']} saying{'s' * (x['speech'] != 1)} of the Arabs")
    q = x.get("quran_uses") or {}
    if q.get("explains"):
        bits.append(f"explains {q['explains']} verse{'s' * (q['explains'] != 1)}")
    if q.get("gloss"):
        bits.append(f"{q['gloss']} exegete's gloss{'es' * (q['gloss'] != 1)}")
    if x.get("hadith_defines"):
        bits.append(f"{x['hadith_defines']} hadith carrying a sense")
    if x.get("later"):
        bits.append(f"{x['later']} legal/theological definition{'s' * (x['later'] != 1)}")
    return "; ".join(bits) or "no evidence listed"


def cmd_switchlist(args):
    roots = load_entries()
    res = json.load(open(os.path.join(OUT, "scores.json"), encoding="utf-8"))
    votes = load_votes()
    rows = []
    for r in select_roots(args, roots):
        v = res.get(r)
        if not v or not v["proposal_id"]:
            continue
        vd = verdict(r, v["incumbent_id"], v["proposal_id"], votes)
        sw = None if vd is None else vd == "switch"
        inc, prop = SHORT[v["incumbent"]], SHORT[v["proposal"]]
        si, sp = v["scores"].get(inc), v["scores"].get(prop)
        reasons = {}
        for role, order in VOTE_ORDER:
            vt = votes.get((r, v["incumbent_id"], v["proposal_id"], role, order))
            if vt:
                txt = re.sub(r"\s*CHOICE:.*$", "", vt["tail"].strip(), flags=re.S)
                reasons[f"{role} {'default first' if order == 'IP' else 'challenger first'}"] = {
                    "pick": vt["pick"], "why": txt[-420:]}
        rows.append({"root": r, "root_ar": roots[r][0]["root_ar"], "from": inc, "to": prop,
                     "score_from": si["score"] if si else None, "score_to": sp["score"] if sp else None,
                     "evidence_from": evidence_line(si) if si else "", "evidence_to": evidence_line(sp) if sp else "",
                     "len_from": si["len"] if si else None, "len_to": sp["len"] if sp else None,
                     "switch": sw, "verdict": vd, "judges": reasons})
    json.dump(rows, open(os.path.join(OUT, "switchlist.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    c = collections.Counter(x["verdict"] or "pending" for x in rows)
    print(dict(c))
    print(collections.Counter(f"{x['from']} -> {x['to']}" for x in rows if x["switch"]).most_common(20))


def cmd_ship(args):
    """Write the approved switches into root_default_dictionary in the local DB. Rows
    name the dictionary rather than the entry id, so they mean the same on production.
    --include adds roots from the "split" list that the owner chose."""
    rows = json.load(open(os.path.join(OUT, "switchlist.json"), encoding="utf-8"))
    extra = {r for r in (args.include or "").split(",") if r}
    unknown = extra - {x["root"] for x in rows}
    if unknown:
        raise SystemExit(f"not on the switch list: {sorted(unknown)}")
    chosen = [x for x in rows if x["verdict"] == "switch" or x["root"] in extra]
    slug_of = {v: k for k, v in SHORT.items()}
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS root_default_dictionary (root_buckwalter TEXT PRIMARY KEY, "
              "dictionary_slug TEXT NOT NULL, decided_at TEXT, method TEXT)")
    for x in chosen:
        c.execute("INSERT OR REPLACE INTO root_default_dictionary VALUES (?, ?, datetime('now'), ?)",
                  (x["root"], slug_of[x["to"]],
                   "evidence review 2026-09" + (" (split, reviewed by Claude at the owner's request)" if x["verdict"] != "switch" else "")))
    c.commit()
    print(f"{len(chosen)} rows written ({sum(x['verdict'] == 'switch' for x in chosen)} agreed, "
          f"{len(chosen) - sum(x['verdict'] == 'switch' for x in chosen)} switched from the split list)")


# ---------------------------------------------------------------------------
# Pilot: roots and answer key.
PRE_NAMES = re.compile(r"Imruʾ al-Qays|Imru.? al-Qays|Ṭarafa|Zuhayr|Labīd|al-Nābigha|al-Aʿshā|ʿAntara|"
                       r"ʿAbīd|ʿAlqama|Aws ibn Ḥajar|al-Muthaqqib|al-Muraqqish|Ḥātim|al-Khansāʾ|al-Shanfarā|"
                       r"Hudhal|Umayya ibn Abī al-Ṣalt|ʿAdī ibn Zayd|Bishr ibn Abī Khāzim")


def cmd_pilot_select(args):
    os.makedirs(OUT, exist_ok=True)
    roots = load_entries()
    rng = random.Random(20260928)
    keep, switch, hard, noif = [], [], [], []
    for r, es in roots.items():
        cands = candidates(es)
        if len(cands) < 4:
            continue
        inc = app_default(es)
        other = [e for e in cands if e["id"] != inc["id"]]
        rich_other = [e for e in other if PRE_NAMES.search(e["en"]) and re.search(r"Qur|Q\s?\d+:\d+", e["en"])]
        if inc["slug"] != PRIORITY[0]:
            noif.append(r)
            continue
        n = len(inc["ar"])
        if n >= 900 and PRE_NAMES.search(inc["en"]) and re.search(r"Qur|Q\s?\d+:\d+", inc["en"]) \
                and re.search(r"indicat|core|single|origin|root", inc["en"], re.I):
            keep.append(r)
        elif 120 <= n <= 350 and not re.search(r"poet|verse|Qur|shāhid|rajaz", inc["en"], re.I) and rich_other:
            switch.append(r)
        elif 400 <= n <= 1500 and len(cands) >= 8:
            hard.append(r)
    pick = lambda xs, k: sorted(rng.sample(xs, min(k, len(xs))))
    sel = {"keep": pick(keep, 10), "switch": pick(switch, 10), "hard": pick(hard, 15), "no_ibn_faris": pick(noif, 5)}
    allr = sel["keep"] + sel["switch"] + sel["hard"] + sel["no_ibn_faris"]
    json.dump({"roots": allr, "groups": sel, "pool_sizes": {"keep": len(keep), "switch": len(switch),
               "hard": len(hard), "no_ibn_faris": len(noif)}},
              open(os.path.join(OUT, "pilot.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(sel, ensure_ascii=False))
    print("pool sizes:", len(keep), len(switch), len(hard), len(noif))


# ---------------------------------------------------------------------------
# Planted tests: change an entry in a known way and check the pipeline reacts.
def _sentences(text):
    return re.split(r"(?<=[.!?])\s+|\n+", text)


def _without(text, quotes):
    qs = [txt_norm(q) for q in quotes if q]
    kept = [s for s in _sentences(text) if not any(q[:40] in txt_norm(s) for q in qs if len(q) >= 6)]
    return "\n".join(kept)


def cmd_plant(args):
    roots = load_entries()
    pilot = json.load(open(os.path.join(OUT, "pilot.json")))["roots"]
    invs = load_inventories()
    table = poet_table()
    have = load_inventories("plant")
    tests = []
    for r in pilot:
        es = roots[r]
        lis = next((e for e in es if e["slug"] == "ibn-manzur-lisan-al-arab"), None)
        # Salmoné: a plain list of senses with no evidence, so padding with it must not help.
        pad = next((e for e in es if e["slug"] == PRIORITY[-1] and len(e["en"]) > 400), None)
        for e in candidates(es):
            rec = invs.get((e["id"], e["hash"], ""))
            if not rec:
                continue
            s = score_entry(e, rec, table)
            inv = rec["inv"]
            poems = [p.get("q") for p in items(inv, "poetry") if quote_found(p.get("q") or "", txt_norm(e["en"]))]
            if len(poems) >= 3:
                tests.append(("no_poems", e, _without(e["en"], poems), s))
            rs = inv.get("root_sense") if isinstance(inv.get("root_sense"), dict) else {}
            if e["slug"] == PRIORITY[0] and s["parts"]["root"] > 0 and rs.get("q"):
                tests.append(("no_root_sense", e, _without(e["en"], [rs.get("q")]), s))
            if e["slug"] == PRIORITY[0] and lis and not items(inv, "hadith"):
                paras = [p for p in lis["en"].split("\n\n") if re.search(r"hadith|ḥadīth|prophetic|the Prophet", p, re.I)]
                if paras:
                    head, _, tail = e["en"].partition("\n\n")
                    tests.append(("add_hadith", e, head + "\n\n" + "\n\n".join(paras[:2]) + "\n\n" + tail, s))
            if pad and s["score"] >= 3:
                tests.append(("pad", e, e["en"] + "\n\n" + pad["en"], s))
    by_kind = collections.defaultdict(list)
    for t in tests:
        by_kind[t[0]].append(t)
    rng = random.Random(7)
    chosen = [t for k, ts in by_kind.items() for t in rng.sample(ts, min(6, len(ts)))]
    jobs = [t for t in chosen if (t[1]["id"], t[1]["hash"], t[0]) not in have]
    print(f"{len(chosen)} planted tests ({ {k: min(6, len(v)) for k, v in by_kind.items()} }); {len(jobs)} to run")

    def work(t):
        kind, e, text, _ = t
        rec = extract_one(e, text=text, tag=kind)
        rec["text"] = text
        append("plant", rec)
    run_pool(jobs, work, args.workers, "plant")
    have = load_inventories("plant")
    rows = []
    for kind, e, text, before in chosen:
        rec = have.get((e["id"], e["hash"], kind))
        if not rec:
            continue
        after = score_entry(dict(e, en=text), rec, table)
        b, a = before["parts"], after["parts"]
        if kind == "no_poems":
            ok = a["early"] <= 0.5 * b["early"] + 1e-9
        elif kind == "no_root_sense":
            ok = a["root"] < b["root"]
        elif kind == "add_hadith":
            ok = a["penalty"] < b["penalty"]
        else:
            ok = after["score"] <= before["score"] + 0.5
        rows.append({"kind": kind, "root": e["root"], "dict": SHORT[e["slug"]], "pass": ok,
                     "before": b, "after": a, "score_before": before["score"], "score_after": after["score"]})
    json.dump(rows, open(os.path.join(OUT, "plant.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    agg = collections.defaultdict(lambda: [0, 0])
    for x in rows:
        agg[x["kind"]][0] += x["pass"]; agg[x["kind"]][1] += 1
    print({k: f"{p}/{n}" for k, (p, n) in agg.items()})


POETRY_SENT = re.compile(r"\bpoet|\bverses?\b|\bline of\b|\blines\b|rajaz|\bpoem|recit|hemistich|couplet|shāhid|shahid|"
                         r"\bsings\b|\bqaṣīda|Imruʾ|Ṭarafa|Zuhayr|Labīd|Nābigha|Aʿshā|ʿAntara|Jarīr|Farazdaq|"
                         r"Dhū al-Rumma|Ruʾba|ʿAjjāj|Hudhal", re.I)


def cmd_plant2(args):
    """Second round of planted tests: remove every poetry sentence; add an unattributed
    or an attributed root-sense statement; re-read unchanged entries (run-to-run spread)."""
    roots = load_entries()
    pilot = json.load(open(os.path.join(OUT, "pilot.json")))["roots"]
    invs = load_inventories()
    table = poet_table()
    have = load_inventories("plant")
    author = {r["slug"]: r["author"] for r in db().execute("SELECT slug, author FROM dictionaries")}
    pool = collections.defaultdict(list)
    for r in pilot:
        ws = quran_words(r)
        gloss = (ws[0][3] if ws else "") or "its first meaning"
        for e in candidates(roots[r]):
            rec = invs.get((e["id"], e["hash"], ""))
            if not rec:
                continue
            s0 = score_entry(e, rec, table)
            pool["repeat"].append(("repeat", e, e["en"], s0))
            if s0["parts"]["early"] >= 2.0:
                kept = [x for x in _sentences(e["en"]) if not POETRY_SENT.search(x)]
                pool["no_poetry"].append(("no_poetry", e, "\n".join(kept), s0))
            if s0["parts"]["root"] == 0 and e["slug"] != PRIORITY[0]:
                pool["unattributed_sense"].append((
                    "unattributed_sense", e,
                    f"Core sense: the senses of this root cluster around \"{gloss}\", and its other meanings branch from it.\n\n" + e["en"], s0))
                who = (author.get(e["slug"]) or "The author").split(",")[0]
                pool["attributed_sense"].append((
                    "attributed_sense", e,
                    f"{who} says that the origin of this root is \"{gloss}\", and that its other senses branch from it.\n\n" + e["en"], s0))
    rng = random.Random(11)
    want = {"repeat": 20, "no_poetry": 8, "unattributed_sense": 6, "attributed_sense": 6}
    chosen = [t for k, n in want.items() for t in rng.sample(pool[k], min(n, len(pool[k])))]
    jobs = [t for t in chosen if (t[1]["id"], t[1]["hash"], t[0]) not in have]
    print(f"{len(chosen)} tests; {len(jobs)} to run", flush=True)

    def work(t):
        kind, e, text, _ = t
        rec = extract_one(e, text=text, tag=kind)
        rec["text"] = text
        append("plant", rec)
    run_pool(jobs, work, args.workers, "plant2")
    have = load_inventories("plant")
    rows, spread = [], []
    for kind, e, text, before in chosen:
        rec = have.get((e["id"], e["hash"], kind))
        if not rec:
            continue
        after = score_entry(dict(e, en=text), rec, table)
        b, a = before["parts"], after["parts"]
        if kind == "repeat":
            spread.append(abs(after["score"] - before["score"]))
            ok = abs(after["score"] - before["score"]) <= 1.0
        elif kind == "no_poetry":
            ok = a["early"] <= 0.5 * b["early"] + 1e-9
        elif kind == "unattributed_sense":
            ok = a["root"] <= 1.5
        else:
            ok = a["root"] >= 1.0
        rows.append({"kind": kind, "root": e["root"], "dict": SHORT[e["slug"]], "pass": ok, "before": b, "after": a,
                     "score_before": before["score"], "score_after": after["score"]})
    json.dump(rows, open(os.path.join(OUT, "plant2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    agg = collections.defaultdict(lambda: [0, 0])
    for x in rows:
        agg[x["kind"]][0] += x["pass"]; agg[x["kind"]][1] += 1
    print({k: f"{p}/{n}" for k, (p, n) in agg.items()})
    if spread:
        spread.sort()
        print(f"repeat |Δscore|: median {spread[len(spread)//2]:.2f}, max {spread[-1]:.2f}, "
              f"over 1.0: {sum(x > 1.0 for x in spread)}/{len(spread)}")


# ---------------------------------------------------------------------------
def cmd_report(args):
    roots = load_entries()
    res = cmd_score(args, quiet=True)
    votes = load_votes()
    todo = select_roots(args, roots)
    lines = []
    final = {}
    for r in todo:
        v = res[r]
        sw = None
        if v["proposal_id"]:
            sw = switch_decision(r, v["incumbent_id"], v["proposal_id"], votes)
        final[r] = v["proposal"] if sw else v["incumbent"]
        sc = v["scores"]
        top = sorted(sc.items(), key=lambda kv: -kv[1]["score"])[:3]
        lines.append(f"{r:6} now {SHORT[v['incumbent']]:9} best {SHORT.get(v['best'], '-'):9} "
                     f"{'-> ' + SHORT[v['proposal']] if v['proposal'] else '':12} "
                     f"{'' if sw is None else ('SWITCH' if sw else 'kept by 2nd opinion'):20} "
                     + "  ".join(f"{k} {x['score']:.1f}" for k, x in top))
    open(os.path.join(OUT, "report.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    if args.pilot:
        g = json.load(open(os.path.join(OUT, "pilot.json")))["groups"]
        keep_ok = sum(final[r] == PRIORITY[0] for r in g["keep"])
        sw_ok = sum(final[r] != PRIORITY[0] for r in g["switch"])
        print(f"\nanswer key: keep Ibn Fāris {keep_ok}/{len(g['keep'])}; move off Ibn Fāris {sw_ok}/{len(g['switch'])}")
    json.dump(final, open(os.path.join(OUT, "final.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def cmd_status(args):
    for name in ("extract", "pairs", "plant"):
        p = inv_path(name)
        n = sum(1 for _ in open(p, encoding="utf-8")) if os.path.exists(p) else 0
        print(f"{name}: {n} records")
    tot = collections.Counter()
    if os.path.exists(inv_path("extract")):
        for line in open(inv_path("extract"), encoding="utf-8"):
            u = json.loads(line).get("use") or {}
            tot["in"] += u.get("in", 0); tot["out"] += u.get("out", 0); tot["sec"] += u.get("sec", 0)
    print("extract tokens:", dict(tot))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--roots")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--include", help="ship: roots from the split list to switch as well")
    args = ap.parse_args()
    {"pilot-select": cmd_pilot_select, "extract": cmd_extract, "confirm": cmd_confirm, "poets": cmd_poets, "score": cmd_score,
     "pairs": cmd_pairs, "plant": cmd_plant, "plant2": cmd_plant2, "report": cmd_report, "status": cmd_status, "switchlist": cmd_switchlist, "ship": cmd_ship}[args.cmd](args)


if __name__ == "__main__":
    main()
