#!/usr/bin/env python3
"""Richer hover notes for the dictionary highlights (dictionary_highlights).

A highlight's note says what the highlight is ("Imruʾ al-Qays, pre-Islamic"). This
writes a fuller one that helps the reader understand the root, WITHOUT letting the
model supply facts:

  1. code gathers the facts for each highlight from the site's own data: the verses
     where the Qur'anic word occurs (with the site's translation), the reviewed era
     of a poet and, on an exact name match, their poems on al-nuqta, and the dates of
     authorities from a hand-written table (HIGHLIGHT_AUTHORITIES below);
  2. deepseek-v4-pro turns them into one sentence (Ollama Cloud);
  3. a checker rejects any verse, number, quotation, name or Arabic word the facts and
     the entry don't contain, filler words, and notes that only repeat the phrase;
  4. kimi-k3 (thinking) must confirm every claim is supported and adds something.
Anything that fails keeps the old note. Accepted notes are stored as "detail".

  python3 _highlight_notes.py run [--workers 4] [--roots a,b]
  python3 _highlight_notes.py status
  python3 _highlight_notes.py merge          write "detail" into dictionary_highlights (local)
Then: ./sync_tables_to_prod.sh dictionary_highlights

Needs OLLAMA_KEY_FILE (see _default_dict_pick.py); results cache in
data/_highlight_notes/notes.jsonl keyed by root and text hash, so a rerun resumes.
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import re
import sqlite3
import threading
import unicodedata

import _default_dict_pick as P   # chat(), parse_json(), pkey()

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "data", "quran.db")
OUT = os.path.join(HERE, "data", "_highlight_notes")
CACHE = os.path.join(OUT, "notes.jsonl")
VERSION = "n1"

# Death dates (CE) of the authorities the dictionary entries cite most, with a few
# words on who they were. Written by hand; "c." marks an estimate.
HIGHLIGHT_AUTHORITIES = {
    "al-Zajjāj": ("923", "grammarian and exegete, author of a book on the meanings of the Qur'an"),
    "al-Farrāʾ": ("822", "Kufan grammarian, author of a book on the meanings of the Qur'an"),
    "Ibn ʿAbbās": ("c. 687", "Companion of the Prophet, the earliest named exegete"),
    "ʿUmar": ("644", "Companion and second caliph"),
    "ʿAlī": ("661", "Companion and fourth caliph"),
    "Abū Bakr": ("634", "Companion and first caliph"),
    "ʿĀʾisha": ("678", "wife of the Prophet"),
    "Ibn Masʿūd": ("c. 653", "Companion of the Prophet"),
    "Abū Hurayra": ("c. 678", "Companion of the Prophet"),
    "Muʿādh": ("639", "Companion of the Prophet"),
    "Mujāhid": ("c. 722", "Successor and exegete, student of Ibn ʿAbbās"),
    "ʿIkrima": ("c. 723", "Successor and exegete, student of Ibn ʿAbbās"),
    "Qatāda": ("c. 736", "Successor and exegete"),
    "al-Ḥasan": ("728", "al-Ḥasan al-Baṣrī, Successor and preacher"),
    "Ibn Jubayr": ("714", "Saʿīd ibn Jubayr, Successor and exegete"),
    "al-Ḍaḥḥāk": ("c. 723", "Successor and exegete"),
    "al-Suddī": ("c. 745", "Successor and exegete"),
    "Muqātil": ("767", "Muqātil ibn Sulaymān, exegete"),
    "al-Aʿmash": ("765", "Kufan reader of the Qur'an and transmitter"),
    "al-Kisāʾī": ("c. 805", "Kufan grammarian and Qur'an reader"),
    "Abū ʿUbayda": ("c. 825", "philologist, author of Majāz al-Qurʾān"),
    "Abū ʿUbayd": ("838", "philologist and jurist"),
    "Thaʿlab": ("904", "Kufan grammarian"),
    "al-Mubarrad": ("898", "Basran grammarian"),
    "al-Ṭabarī": ("923", "exegete and historian"),
    "al-Azharī": ("980", "lexicographer, author of the Tahdhīb al-Lugha"),
    "al-Fārisī": ("987", "Abū ʿAlī al-Fārisī, grammarian"),
    "al-Jawharī": ("c. 1003", "lexicographer, author of the Ṣiḥāḥ"),
    "Ibn Fāris": ("1004", "lexicographer, author of the Maqāyīs al-Lugha"),
    "Ibn Sīda": ("1066", "lexicographer, author of the Muḥkam"),
    "al-Zamakhsharī": ("1144", "exegete and lexicographer"),
    "Ibn al-Athīr": ("1210", "author of al-Nihāya, a dictionary of rare words in hadith"),
    "Ibn Manẓūr": ("1311", "compiler of the Lisān al-ʿArab"),
    "al-Shāfiʿī": ("820", "jurist, founder of a school of law"),
    "Mālik": ("795", "jurist, founder of a school of law"),
    "Sībawayh": ("c. 796", "Basran grammarian"),
    "al-Khalīl": ("c. 786", "author of the first Arabic dictionary, the Kitāb al-ʿAyn"),
    "al-Aṣmaʿī": ("c. 828", "philologist and collector of poetry"),
    "Ibn al-Aʿrābī": ("846", "Kufan philologist"),
    "Ibn Durayd": ("933", "lexicographer, author of the Jamhara"),
    "Qāḍī ʿIyāḍ": ("1149", "jurist and hadith scholar"),
}

FLUFF = re.compile(r"\b(crucial|profound|rich(ly)?|fascinating|deeply|vital|highlights? (the|how)|worth noting|"
                   r"it is important|significant(ly)?|beautiful(ly)?|timeless|underscor|captures? the essence|"
                   r"interestingly|notably|in essence|plays? a (key|central) role)\b", re.I)
AR_WORD = re.compile(r"[؀-ۿ][؀-ۿً-ٰ]*")
AR_MARKS = re.compile(r"[ً-ْٰـ]")

PROMPT = """You write the short note a reader sees when hovering over a highlighted phrase in a classical Arabic dictionary entry on a Qur'an study site. The note must help the reader understand the root. Use ONLY the entry text and the FACTS given for that highlight: never add a date, verse, name, number or claim that is not in them. If the facts add nothing useful, answer "" for that highlight.

What each kind of note should do:
- core: connect the root's shared sense to one or two of the Qur'an's words listed in the facts ("hence ..."), in plain words.
- quran: name one verse from the facts where the word carries the highlighted sense, with a few words quoted exactly from that verse's translation.
- early: say who the witness is and when they lived (era from the facts), what the line shows, and mention their poems on al-nuqta if the facts list them.
- later: say who the authority was and when they died (from the facts) and that this is a reading from after the Qur'an.

Rules: at most 200 characters; plain English; no praise or filler words (crucial, profound, rich, highlights, worth noting, ...); do not just repeat the highlighted phrase; verse references as "Q 2:30"; quotations in double quotes and copied exactly.

ROOT: {root}   DICTIONARY: {dictionary}
ENTRY:
<<<
{entry}
>>>

HIGHLIGHTS:
{items}

Return JSON: {{"notes": [{{"i": 1, "note": "..."}}, ...]}}"""

VERIFY = """Check notes written for highlighted phrases in a dictionary entry. For each note answer OK only if (a) every statement in it is supported by the ENTRY or the FACTS for that highlight (no invented dates, verses, names, numbers or claims), and (b) it tells the reader something useful about the root beyond repeating the highlighted phrase. Otherwise answer REJECT with a short reason.

ENTRY:
<<<
{entry}
>>>

{items}

Return JSON: {{"verdicts": [{{"i": 1, "verdict": "OK" or "REJECT", "reason": "..."}}]}}"""


def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(ch for ch in s if not unicodedata.combining(ch)).lower()


def squash(s):
    s = norm(s).replace("[", "").replace("]", "")
    s = re.sub(r"[“”«»\"'‘’`]", "", s)
    return " ".join(re.sub(r"[^\w\s]", " ", s).split())


def bare(ar):
    return AR_MARKS.sub("", re.sub(r"[^؀-ۿ]", "", ar or ""))


# ---------------------------------------------------------------------------
# Facts, from the site's own data.
def quran_words(c, root):
    """[(lemma_bw, arabic, count, [(ref, translation), ...])], most frequent first;
    up to five verses per word, spread across the Qur'an."""
    rows = c.execute(
        "SELECT lemma_buckwalter lb, lemma_arabic la, COUNT(DISTINCT chapter||':'||verse||':'||word_pos) n "
        "FROM morphology WHERE root_buckwalter = ? AND lemma_buckwalter IS NOT NULL "
        "GROUP BY lemma_buckwalter ORDER BY n DESC LIMIT 8", (root,)).fetchall()
    out = []
    for r in rows:
        refs = [f"{ch}:{v}" for ch, v in c.execute(
            "SELECT DISTINCT chapter, verse FROM morphology WHERE root_buckwalter = ? AND lemma_buckwalter = ? "
            "ORDER BY chapter, verse", (root, r["lb"]))]
        pick = refs if len(refs) <= 5 else [refs[round(i * (len(refs) - 1) / 4)] for i in range(5)]
        verses = []
        for ref in dict.fromkeys(pick):
            ch, v = ref.split(":")
            t = c.execute("SELECT text_en FROM translations WHERE chapter = ? AND verse = ?", (ch, v)).fetchone()
            if t and t[0]:
                verses.append((ref, t[0][:240]))
        out.append((r["lb"], re.sub(r"[^؀-ۿ]", "", r["la"] or ""), r["n"], verses))
    return out


def poet_facts(c, note):
    """The era from the reviewed highlight note; poems on al-nuqta only on an exact,
    unambiguous name match (a loose match once linked the wrong al-Nābigha)."""
    parts = [p.strip() for p in (note or "").split(",")]
    name, era = parts[0], (parts[1] if len(parts) > 1 else "")
    if not name or name.lower().startswith(("unattributed", "proverb", "saying")):
        return [f"witness: {note}"]
    key = P.pkey(name)
    poets = {}
    for r in c.execute("SELECT id, poet_latin FROM poetry_poems WHERE poet_latin IS NOT NULL"):
        if P.pkey(r["poet_latin"]) == key:
            poets.setdefault(r["poet_latin"], []).append(r["id"])
    fact = f"poet {name}; era: {era or 'not given'}"
    if len(poets) == 1:
        (full, ids), = poets.items()
        fact += f"; al-nuqta has {len(ids)} poem(s) by {full}"
    return [fact]


def authority_facts(text):
    return [f"{k}: died {v[0]} CE, {v[1]}" for k, v in HIGHLIGHT_AUTHORITIES.items() if k in text]


def build(c, root, hls):
    words = quran_words(c, root)
    items, facts_by = [], {}
    for n, h in enumerate(hls, 1):
        f = []
        if h["kind"] == "core":
            f += [f"Qur'an word {ar}: {cnt} times" for _, ar, cnt, _ in words]
        elif h["kind"] == "quran":
            said = bare(h["text"] + " " + h.get("note", ""))
            mine = [w for w in words if w[1] and bare(w[1]) in said] or words[:2]
            for _, ar, cnt, verses in mine:
                f.append(f"Qur'an word {ar}: {cnt} times" + "".join(f'\n    Q {r}: "{t}"' for r, t in verses))
        elif h["kind"] == "early":
            f += poet_facts(c, h.get("note", ""))
        elif h["kind"] == "later":
            f += authority_facts(h["text"] + " " + h.get("note", ""))
        facts_by[n] = "\n  ".join(f) if f else "(none)"
        items.append(f'{n}. kind {h["kind"]} | highlighted: "{h["text"]}" | current note: {h.get("note", "")}\n'
                     f"  FACTS:\n  {facts_by[n]}")
    return items, facts_by


def check(note, facts, entry, highlight):
    """Every verse, number, quotation and Arabic word must be in the facts or the entry."""
    errs, src = [], facts + "\n" + entry
    if len(note) > 220:
        errs.append("too long")
    if FLUFF.search(note):
        errs.append("filler word")
    for ref in re.findall(r"\b(\d{1,3}:\d{1,3})", note):
        if ref not in src:
            errs.append(f"verse {ref} not supplied")
    for num in re.findall(r"\b\d{2,4}\b", re.sub(r"\b\d{1,3}:\d{1,3}(?:[–-]\d{1,3})?", "", note)):
        if num not in src:
            errs.append(f"number {num} not supplied")
    for q in re.findall(r'"([^"]+)"|“([^”]+)”', note):
        q = next(x for x in q if x)
        if len(squash(q)) >= 6 and squash(q) not in squash(src):
            errs.append(f"quote not found: {q[:30]}")
    for w in AR_WORD.findall(note):
        if AR_MARKS.sub("", w) not in AR_MARKS.sub("", src):
            errs.append(f"Arabic {w} not supplied")
    if len(set(norm(note).split()) - set(norm(highlight).split())) < 4:
        errs.append("mostly repeats the highlight")
    return errs


# ---------------------------------------------------------------------------
def text_hash(t):
    return hashlib.sha1(t.encode()).hexdigest()[:16]


def load_cache():
    got = {}
    if os.path.exists(CACHE):
        for line in open(CACHE, encoding="utf-8"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("v") == VERSION:
                got[(r["root"], r["hash"])] = r
    return got


_lock = threading.Lock()


def run_root(root):
    c = db()
    row = c.execute("SELECT h.highlights, h.dictionary_slug, e.harmonized_en FROM dictionary_highlights h "
                    "JOIN dictionary_entries e ON e.id = h.entry_id WHERE h.root_buckwalter = ?", (root,)).fetchone()
    hls = json.loads(row["highlights"])
    entry = row["harmonized_en"]
    rec = {"v": VERSION, "root": root, "hash": text_hash(entry), "notes": []}
    if hls:
        items, facts_by = build(c, root, hls)
        out, _ = P.chat("extract", PROMPT.format(root=root, dictionary=P.SHORT.get(row["dictionary_slug"]),
                                                  entry=entry, items="\n\n".join(items)), fmt="json", temperature=0)
        drafts = {int(x["i"]): (x.get("note") or "").strip() for x in P.parse_json(out).get("notes", [])
                  if str(x.get("i", "")).isdigit()}
        checked = {n: check(d, facts_by[n], entry, hls[n - 1]["text"]) for n, d in drafts.items()
                   if d and 1 <= n <= len(hls)}
        to_verify = [n for n, e in checked.items() if not e]
        verdicts = {}
        if to_verify:
            body = "\n\n".join(f'{n}. highlighted: "{hls[n - 1]["text"]}"\n  FACTS:\n  {facts_by[n]}\n'
                               f"  NOTE: {drafts[n]}" for n in to_verify)
            vout, _ = P.chat("kimi", VERIFY.format(entry=entry, items=body), think=True, fmt="json",
                             temperature=0, timeout=1200)
            verdicts = {int(x["i"]): x for x in P.parse_json(vout).get("verdicts", []) if str(x.get("i", "")).isdigit()}
        for n, h in enumerate(hls, 1):
            d = drafts.get(n, "")
            v = verdicts.get(n, {})
            ok = bool(d) and not checked.get(n) and v.get("verdict") == "OK"
            rec["notes"].append({"i": n, "detail": d if ok else None, "draft": d, "checker": checked.get(n, []),
                                 "verdict": v.get("verdict"), "reason": (v.get("reason") or "")[:200]})
    with _lock:
        with open(CACHE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def cmd_run(args):
    os.makedirs(OUT, exist_ok=True)
    c = db()
    rows = c.execute("SELECT h.root_buckwalter r, e.harmonized_en t FROM dictionary_highlights h "
                     "JOIN dictionary_entries e ON e.id = h.entry_id").fetchall()
    want = set(args.roots.split(",")) if args.roots else None
    have = load_cache()
    todo = [r["r"] for r in rows if (want is None or r["r"] in want) and (r["r"], text_hash(r["t"])) not in have]
    print(f"{len(todo)} entries to annotate", flush=True)
    done = fail = 0
    with cf.ThreadPoolExecutor(args.workers) as ex:
        for fut in cf.as_completed({ex.submit(run_root, r): r for r in todo}):
            try:
                fut.result(); done += 1
            except Exception as e:
                fail += 1; print("failed:", str(e)[:150], flush=True)
            if (done + fail) % 50 == 0 or done + fail == len(todo):
                print(f"[notes] {done + fail}/{len(todo)} ({fail} failed)", flush=True)


def cmd_status(args):
    recs = list(load_cache().values())
    notes = [n for r in recs for n in r["notes"]]
    ok = sum(1 for n in notes if n["detail"])
    print(f"{len(recs)} entries, {len(notes)} highlights: {ok} richer notes ({100 * ok / max(1, len(notes)):.0f}%), "
          f"{sum(1 for n in notes if n['draft'] and n['checker'])} failed the checker, "
          f"{sum(1 for n in notes if n['draft'] and not n['checker'] and n['verdict'] != 'OK')} rejected by the verifier, "
          f"{sum(1 for n in notes if not n['draft'])} no draft")


def cmd_merge(args):
    c = db()
    recs = load_cache()
    n_entries = n_notes = 0
    for row in c.execute("SELECT h.entry_id, h.root_buckwalter r, h.highlights, e.harmonized_en t "
                         "FROM dictionary_highlights h JOIN dictionary_entries e ON e.id = h.entry_id").fetchall():
        rec = recs.get((row["r"], text_hash(row["t"])))
        if not rec:
            continue
        hls = json.loads(row["highlights"])
        by_i = {x["i"]: x["detail"] for x in rec["notes"]}
        for n, h in enumerate(hls, 1):
            if by_i.get(n):
                h["detail"] = by_i[n]; n_notes += 1
            else:
                h.pop("detail", None)
        c.execute("UPDATE dictionary_highlights SET highlights = ? WHERE entry_id = ?",
                  (json.dumps(hls, ensure_ascii=False), row["entry_id"]))
        n_entries += 1
    c.commit()
    print(f"{n_notes} richer notes written across {n_entries} entries")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "status", "merge"])
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--roots")
    a = ap.parse_args()
    {"run": cmd_run, "status": cmd_status, "merge": cmd_merge}[a.cmd](a)
