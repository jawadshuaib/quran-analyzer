"""Alternative-translation picker: for each verse, judge the openly available
quran.com English translations against the Arabic, pick the one most faithful
to the Qur'an itself (no tafsir/hadith/fiqh imports), and grade how much it
adds to our own root-based translation (ai_translations config 10).

Value tiers (drive the UI):
  3  show automatically under our translation
  2  "See translation by X" link, dark gray
  1  same link, light gray
  0  hide (adds nothing, or only adds post-Qur'anic material)

The judge sees the candidates blind (letters A-H, shuffled per verse with a
fixed seed) so translator reputation and position cannot sway it.

  python alt_translations_ai.py fetch --cache-dir DIR
  python alt_translations_ai.py judge --cache-dir DIR --verses 2:3,4:34 \
      --models glm-5.3 --think low --out glm.jsonl
  python alt_translations_ai.py judge --cache-dir DIR --verses 2:3,4:34 \
      --models deepseek-v4-pro --think false --out deepseek.jsonl

Use those exact think settings: glm-5.3 ignores think=false (~27k tokens
per verse) and deepseek-v4-pro at think=low still spends 8-13k. The two
judges are combined by eval/alt_translations_pilot/ensemble.py; the plan
and pilot results are in docs/alt-translations-plan.md.

Needs OLLAMA_KEY_FILE (a file holding the ollama.com key; never printed).
"""
import argparse
import concurrent.futures as cf
import html
import json
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

DB_PATH = os.environ.get(
    "QURAN_DB", os.path.join(os.path.dirname(__file__), "data", "quran.db"))
OLLAMA_URL = "https://ollama.com/api/chat"
OUR_CONFIG_ID = 10
PROMPT_VERSION = "alt-v7"

# quran.com resource id -> display name (the openly served English set)
TRANSLATORS = {
    85: "M.A.S. Abdel Haleem",
    149: "Fadel Soliman (Bridges)",
    84: "Mufti Taqi Usmani",
    95: "Abul Ala Maududi",
    19: "Marmaduke Pickthall",
    22: "Abdullah Yusuf Ali",
    20: "Saheeh International",
    203: "Hilali & Khan",
}
# Only these are republished on the site for now: the others are copyrighted
# and quran.com serves them under its own agreements.
PUBLIC_DOMAIN = (19, 22)


# ---------------------------------------------------------------- sources

def fetch(cache_dir):
    os.makedirs(cache_dir, exist_ok=True)
    for rid in TRANSLATORS:
        path = os.path.join(cache_dir, f"{rid}.json")
        if os.path.exists(path):
            continue
        url = f"https://api.quran.com/api/v4/quran/translations/{rid}"
        with urllib.request.urlopen(url, timeout=120) as r:
            data = json.load(r)
        assert len(data["translations"]) == 6236, (rid, len(data["translations"]))
        with open(path, "w") as f:
            json.dump(data, f, ensure_ascii=False)
        print("fetched", rid, TRANSLATORS[rid])


def clean(text):
    """Drop footnote markers and markup, keep the translator's own words."""
    text = re.sub(r"<sup\b[^>]*>.*?</sup>", "", text, flags=re.S)
    text = re.sub(r"<a\b[^>]*>.*?</a>", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def load_candidates(cache_dir, conn, rids=PUBLIC_DOMAIN):
    keys = [tuple(r) for r in conn.execute(
        "SELECT chapter, verse FROM verses ORDER BY chapter, verse")]
    assert len(keys) == 6236
    out = {k: {} for k in keys}
    for rid in rids:
        with open(os.path.join(cache_dir, f"{rid}.json")) as f:
            rows = json.load(f)["translations"]
        for k, row in zip(keys, rows):
            out[k][rid] = clean(row["text"])
    return out


# ---------------------------------------------------------------- context

def _skeleton(text):
    return [c for c in text if not unicodedata.combining(c) and not c.isspace()]


def strip_basmala(conn, text, ch, v):
    """Verse 1 of each surah carries the basmala in text_uthmani; the judge
    must not see it, or it reports our translation as "omitting" it. Same
    letter-skeleton match as app._strip_bismillah (variant pointing on 95:1)."""
    if v != 1 or ch == 1:
        return text
    basmala = _skeleton(conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter=1 AND verse=1").fetchone()[0])
    ti = 0
    for i, c in enumerate(text):
        if unicodedata.combining(c) or c.isspace():
            continue
        if ti < len(basmala) and c == basmala[ti]:
            ti += 1
            if ti == len(basmala):
                j = i + 1
                while j < len(text) and unicodedata.combining(text[j]):
                    j += 1
                return text[j:].strip()
        else:
            return text
    return text


FEATURE_NAMES = {
    "NOM": "nominative", "ACC": "accusative", "GEN": "genitive",
    "PERF": "perfect", "IMPF": "imperfect", "IMPV": "imperative",
    "PASS": "passive", "ACT": "active", "PCPL": "participle", "VN": "verbal noun",
    "INDEF": "indefinite", "MOOD:SUBJ": "subjunctive", "MOOD:JUS": "jussive",
    "MOOD:IND": "indicative",
}
SKIP_FEATURES = ("STEM", "PREFIX", "SUFFIX")


def grammar_of(features_raw):
    """'STEM|POS:V|IMPV|LEM:..|ROOT:..|2MP' -> 'imperative 2MP'."""
    out = []
    for f in (features_raw or "").split("|"):
        if not f or f in SKIP_FEATURES or f.startswith(("POS:", "LEM:", "ROOT:", "SP:")):
            continue
        out.append(FEATURE_NAMES.get(f, f))
    return " ".join(out)


def word_lines(conn, ch, v):
    """One line per word: form, root, lemma, POS, grammar (case, person,
    voice, mood, verb form) and attached pronouns, then the gloss. Case and
    person are what let the judge catch e.g. a noun attached to the wrong
    verb, so they come from the morphology table, not the model's memory."""
    segs = conn.execute(
        "SELECT word_pos, form_arabic, pos, root_arabic, lemma_arabic, tag, features_raw "
        "FROM morphology WHERE chapter=? AND verse=? ORDER BY word_pos, segment",
        (ch, v)).fetchall()
    gloss = dict(conn.execute(
        "SELECT word_pos, translation_en FROM word_glosses "
        "WHERE chapter=? AND verse=?", (ch, v)).fetchall())
    words = {}
    for pos, form, ptag, root, lemma, tag, feats in segs:
        w = words.setdefault(pos, {"form": "", "root": "", "lemma": "", "pos": "",
                                   "gram": "", "pron": []})
        w["form"] += form or ""
        if tag == "SUFFIX" and "PRON:" in (feats or ""):
            w["pron"].append(feats.split("PRON:")[1].split("|")[0])
        elif tag not in ("PREFIX", "SUFFIX") and not w["pos"]:
            w["root"], w["lemma"], w["pos"] = root or "", lemma or "", ptag or ""
            w["gram"] = grammar_of(feats)
    lines = []
    for pos in sorted(words):
        w = words[pos]
        bits = [f"{pos}. {w['form']}"]
        if w["root"]:
            bits.append(f"root {w['root']}")
        if w["lemma"]:
            bits.append(f"lemma {w['lemma']}")
        if w["pos"]:
            bits.append(w["pos"] + (f" ({w['gram']})" if w["gram"] else ""))
        if w["pron"]:
            bits.append("+ pronoun " + ", ".join(w["pron"]))
        bits.append(f"gloss: {gloss.get(pos, '?')}")
        lines.append(" | ".join(bits))
    return "\n".join(lines)


def our_translation(conn, ch, v):
    row = conn.execute(
        "SELECT COALESCE(revised_text, translation_text), departure_notes "
        "FROM ai_translations WHERE chapter=? AND verse=? AND config_id=?",
        (ch, v, OUR_CONFIG_ID)).fetchone()
    return (row[0], row[1] or "") if row else (None, "")


# ---------------------------------------------------------------- prompt

SYSTEM = """You assess English translations of a single Qur'an verse.

The website you serve translates the Qur'an from the Qur'an itself: the meaning of a word comes from how the Qur'an uses that root elsewhere, the verse's context, its grammar, and Arabic usage contemporaneous with the Qur'an. It deliberately does NOT import meanings from later sources: tafsir, hadith, sira/biography, asbab al-nuzul, fiqh (law), or later theology and sectarian terminology.

You will get the Arabic verse, a word-by-word morphology table, OUR translation (with the notes explaining where and why it departs from conventional renderings), and several CANDIDATE translations labelled with letters. Translator names are hidden on purpose.

TASK 1 - Fidelity. Score every candidate 1-5 for how honestly it renders THIS Arabic verse and nothing more:
- Accuracy: every meaning-bearing word and grammatical relation of the Arabic is represented (tense/aspect, person, number, negation, conditionals, emphasis); nothing is dropped.
- No post-Qur'anic imports. Penalise: parenthetical or bracketed additions that carry content not in the Arabic (identifying unnamed people or groups, e.g. "(the Jews)", a prophet's name the verse does not give; tafsir explanations; legal specifics); honorifics and pious formulas absent from the Arabic; transliterated technical terms glossed with a later definition; "Islam"/"Muslim" as the name of a religion where the Arabic is the ordinary verbal noun/participle of s-l-m (submission, one who submits); renderings that narrow a word to one school's technical sense.
- Brackets that only make the English grammatical are fine. A conventional rendering is NOT penalised merely for being conventional when the Arabic supports it; penalise it only when it imports a later definition the verse itself does not support.
- Readability is a tie-breaker only.
5 = faithful and complete, no imports; 4 = minor looseness; 3 = noticeable paraphrase or one content-carrying insertion; 2 = several insertions or a real inaccuracy; 1 = substantially wrong or interpretive.

Then pick BEST: the most faithful candidate (ties: the one that adds more to our translation).

TASK 2 - Audit OUR translation on its own, before looking at BEST. Walk the WORD BY WORD table in order and check each meaning-bearing word, phrase and grammatical relation against OUR translation. Record in "ours_check" anything the Arabic has that OUR translation leaves out (a word, a clause, a purpose "so that...", a destination, a preposition phrase, an object) or renders against the grammar (case, person, number, tense, voice, negation, the attachment of a word to the wrong verb). Do NOT record word-sense choices that OUR notes argue for (e.g. "trust" for آمن, "connection" for صلاة): those are deliberate and out of scope here. An empty list is fine when nothing is missing.

TASK 3 - Compare BEST (only BEST, not the other candidates) with OUR translation. List each concrete difference in MEANING once. Types:
- "ours_omits": the Arabic has it, BEST conveys it, OUR translation leaves it out.
- "ours_mistranslates": OUR rendering breaks the Arabic grammar or syntax (case, person, number, tense, voice, negation, which verb a word belongs to) and BEST gets it right. Never use this for a choice of word sense.
- "conventional_sense": BEST keeps the conventional/traditional sense of a word where OUR notes deliberately chose a different sense from Qur'anic usage (e.g. believe/trust, prayer/connection, religion/way of judgment, righteous/sound, Islam/self-surrender). Use this even if the conventional sense is also defensible.
- "alt_reading": a materially different construal of the Arabic's grammar or syntax (who does what to whom, what a pronoun refers to, how clauses connect), defensible from the Arabic itself, that a careful reader should weigh.
- "nuance": a real shade of meaning a reader would notice and learn from: BEST brings out something in the Arabic (an emphasis, an aspect of the verb, a relation between clauses, a concrete sense of the root) that our wording leaves dim.
- "alt_imports": the difference comes from post-Qur'anic material.
- "alt_worse": BEST is less accurate than ours on this point.
Leave out pure wording differences entirely; they are NOT nuance: synonyms ("painful"/"grievous", "harmed"/"molested"), articles, "and"/"then", "or"/"nor", noun vs verb phrasing of the same idea, punctuation, archaic vs modern English.

Reply with JSON only, exactly this shape:
{"scores": {"A": {"fidelity": 1-5, "issues": "short; empty if none"}, ...every letter...},
 "best": "<letter>",
 "best_why": "one sentence",
 "ours_check": [{"arabic": "the Arabic word(s)", "problem": "missing" or "grammar", "why": "one sentence"}],
 "differences": [{"arabic": "the Arabic word(s)", "ours": "our words", "best": "BEST's words", "type": "<one type above>", "why": "one sentence"}],
 "summary": "one sentence for the reviewer: what BEST shows that ours does not (empty if nothing)",
 "reader_note": "for a website visitor who has just read OUR translation: at most 25 words on what BEST brings out, starting with a verb (e.g. Makes explicit..., Reads ... as ...) and quoting BEST's words. Never criticise it, never mention letters, BEST, candidates or OUR. Empty string if it brings out nothing"}"""


def build_user_msg(conn, ch, v, candidates, ours_text, ours_notes, seed):
    rids = sorted(candidates)
    random.Random(f"{seed}:{ch}:{v}").shuffle(rids)
    letters = {chr(65 + i): rid for i, rid in enumerate(rids)}
    arabic = strip_basmala(conn, conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter=? AND verse=?",
        (ch, v)).fetchone()[0], ch, v)
    notes = ours_notes.strip()
    if len(notes) > 3000:
        notes = notes[:3000] + " ..."
    parts = [
        f"VERSE {ch}:{v}",
        f"ARABIC: {arabic}",
        "WORD BY WORD:\n" + word_lines(conn, ch, v),
        f"OUR TRANSLATION: {ours_text}",
        "OUR NOTES:\n" + (notes or "(none)"),
        "CANDIDATES:\n" + "\n".join(f"{L}: {candidates[rid]}" for L, rid in letters.items()),
    ]
    return "\n\n".join(parts), letters


# ---------------------------------------------------------------- model call

def call_model(model, user_msg, key, think=None, timeout=600):
    body = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": user_msg}],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1},
    }
    if think is not None:  # "false" / "low" / "medium" / "high"
        body["think"] = False if think == "false" else think
    req = urllib.request.Request(
        OLLAMA_URL, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    last = None
    for attempt in range(3):
        try:
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.load(r)
            d["_secs"] = round(time.time() - t0, 1)
            return d
        except Exception as e:  # noqa: BLE001 - retry any transport error
            last = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"{model}: {last}")


# Tier is computed from the typed differences, not asked for, so it is
# auditable and can be re-tuned without re-running the model.
TYPE_TIER = {"ours_omits": 3, "ours_mistranslates": 3, "alt_reading": 2,
             "nuance": 1, "conventional_sense": 0, "wording": 0,
             "alt_imports": 0, "alt_worse": 0}


def tier_of(differences):
    tier = max([TYPE_TIER.get(d.get("type"), 0) for d in differences] or [0])
    # A claimed error in OUR translation is a fix candidate for us as much
    # as a reason to show the alternative: queue it for a human.
    needs_review = any(d.get("type") in ("ours_omits", "ours_mistranslates")
                       for d in differences)
    return tier, needs_review


def parse(content, letters):
    m = re.search(r"\{.*\}", content, re.S)
    if not m:
        raise ValueError("no JSON in reply")
    d = json.loads(m.group(0))
    if d.get("best") not in letters:
        raise ValueError(f"bad best {d.get('best')!r}")
    diffs = d.get("differences") or []
    if not isinstance(diffs, list):
        raise ValueError("differences is not a list")
    norm = lambda t: re.sub(r"[^a-z0-9]+", " ", str(t).lower()).strip()
    d["differences"] = [x for x in diffs if isinstance(x, dict)
                        and norm(x.get("ours", "")) != norm(x.get("best", ""))]
    d["value"], d["needs_review"] = tier_of(d["differences"])
    return d


# ---------------------------------------------------------------- driver

def parse_refs(spec, conn=None):
    if spec == "all":
        return [tuple(r) for r in conn.execute(
            "SELECT chapter, verse FROM verses ORDER BY chapter, verse")]
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        ch, rest = part.split(":")
        if "-" in rest:
            a, b = rest.split("-")
            out += [(int(ch), x) for x in range(int(a), int(b) + 1)]
        else:
            out.append((int(ch), int(rest)))
    return out


def judge(args):
    key = open(os.environ["OLLAMA_KEY_FILE"]).read().strip()
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True, check_same_thread=False)
    cands = load_candidates(args.cache_dir, conn,
                            tuple(int(x) for x in args.sources.split(",")))

    jobs = []  # (job_id, ch, v, candidates, ours_text, ours_notes, control)
    for ch, v in parse_refs(args.verses, conn):
        ours, notes = our_translation(conn, ch, v)
        jobs.append((f"{ch}:{v}", ch, v, cands[(ch, v)], ours, notes, None))
    if args.controls:
        with open(args.controls) as f:
            for c in json.load(f):
                ch, v = c["ref"]
                ours, notes = our_translation(conn, ch, v)
                cc = dict(cands[(ch, v)])
                if c["kind"] == "planted_bad_candidate":
                    cc[0] = c["text"]  # resource id 0 = planted fake
                elif c["kind"] == "broken_ours":
                    ours, notes = c["text"], ""
                jobs.append((c["id"], ch, v, cc, ours, notes, c))

    done = set()
    if os.path.exists(args.out):
        for line in open(args.out):
            r = json.loads(line)
            if "error" not in r:
                done.add((r["job"], r["model"]))
    lock = threading.Lock()
    db_lock = threading.Lock()

    def run(job, model):
        job_id, ch, v, cc, ours, notes, control = job
        with db_lock:
            msg, letters = build_user_msg(conn, ch, v, cc, ours, notes, args.seed)
        rec = {"job": job_id, "ref": f"{ch}:{v}", "model": model, "think": args.think,
               "prompt_version": PROMPT_VERSION, "letters": letters,
               "control": control}
        try:
            for attempt in (1, 2):
                d = call_model(model, msg, key, args.think)
                rec.update(prompt_tokens=rec.get("prompt_tokens", 0) + (d.get("prompt_eval_count") or 0),
                           output_tokens=rec.get("output_tokens", 0) + (d.get("eval_count") or 0),
                           secs=rec.get("secs", 0) + d["_secs"],
                           thinking_chars=len(d["message"].get("thinking") or ""),
                           attempts=attempt)
                try:
                    res = parse(d["message"]["content"], letters)
                    break
                except (ValueError, json.JSONDecodeError):
                    if attempt == 2:
                        raise
            rec["result"] = res
            rec["best_rid"] = letters[res["best"]]
        except Exception as e:  # noqa: BLE001
            rec["error"] = str(e)[:500]
        with lock:
            with open(args.out, "a") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            tag = rec.get("error") or f"best={TRANSLATORS.get(rec['best_rid'], 'PLANTED')} value={rec['result']['value']}"
            print(f"{model:18} {job_id:16} {tag}", flush=True)

    todo = [(j, m) for m in args.models.split(",") for j in jobs if (j[0], m) not in done]
    print(f"{len(todo)} calls", flush=True)
    with cf.ThreadPoolExecutor(args.workers) as ex:
        list(ex.map(lambda jm: run(*jm), todo))


# ---------------------------------------------------------------- claim verification
#
# A claimed error in OUR translation lifts a verse to tier 3 and into the
# review queue, and the cheap no-reasoning judges get the direction wrong
# often enough (deepseek tags "BEST drops 'Indeed'" as ours_omits) that every
# such claim is re-checked by one reasoning call before it counts.

VERIFY_SYSTEM = """A judge claims that OUR English translation of a Qur'an verse has an error that an alternative translation (ALT) gets right. Check the claim against the Arabic and the word-by-word morphology table only.

Verdicts:
- "confirmed": OUR translation really leaves out this meaning-bearing element of the Arabic, or really breaks the Arabic grammar here (case, person, number, voice, tense where context does not allow it, negation, which verb a word belongs to), and ALT renders it correctly.
- "defensible": both renderings are defensible from the Arabic (e.g. a perfect verb read as past or as prophetic future, a conditional rendered "when", an ambiguous attachment). ALT offers a legitimate alternative; ours is not wrong.
- "rejected": the claim is wrong. OUR translation does contain the element; or it is ALT, not ours, that lacks it; or the difference is a deliberate word-sense choice explained in OUR notes; or ALT is not better here.

Reply with JSON only: {"verdict": "confirmed" | "defensible" | "rejected", "reason": "one sentence"}"""

VERIFY_MAP = {"confirmed": None, "defensible": "alt_reading", "rejected": "alt_worse"}


def claim_key(job, model, idx):
    return f"{job}|{model}|{idx}"


def verify(args):
    key = open(os.environ["OLLAMA_KEY_FILE"]).read().strip()
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True, check_same_thread=False)
    cands = load_candidates(args.cache_dir, conn, tuple(TRANSLATORS))
    claims = []
    for path in args.inputs:
        for line in open(path):
            r = json.loads(line)
            if "result" not in r:
                continue
            for i, d in enumerate(r["result"]["differences"]):
                if d.get("type") in ("ours_omits", "ours_mistranslates"):
                    claims.append((r, i, d))
    done = set()
    if os.path.exists(args.out):
        for line in open(args.out):
            v = json.loads(line)
            if "verdict" in v:
                done.add(v["key"])
    lock, db_lock = threading.Lock(), threading.Lock()

    def run(r, i, d):
        ch, v = map(int, r["ref"].split(":"))
        k = claim_key(r["job"], r["model"], i)
        with db_lock:
            ours, notes = our_translation(conn, ch, v)
            ctl = r.get("control") or {}
            if ctl.get("kind") == "broken_ours":
                ours, notes = ctl["text"], ""
            alt = ctl["text"] if r["best_rid"] == 0 else cands[(ch, v)][r["best_rid"]]
            arabic = strip_basmala(conn, conn.execute(
                "SELECT text_uthmani FROM verses WHERE chapter=? AND verse=?",
                (ch, v)).fetchone()[0], ch, v)
            msg = "\n\n".join([
                f"VERSE {ch}:{v}", f"ARABIC: {arabic}",
                "WORD BY WORD:\n" + word_lines(conn, ch, v),
                f"OUR TRANSLATION: {ours}",
                "OUR NOTES:\n" + ((notes or "(none)")[:3000]),
                f"ALT: {alt}",
                "CLAIM: " + json.dumps(d, ensure_ascii=False)])
        rec = {"key": k, "job": r["job"], "model": r["model"], "claim": d,
               "verifier": args.model}
        try:
            body = {"model": args.model, "stream": False, "format": "json",
                    "messages": [{"role": "system", "content": VERIFY_SYSTEM},
                                 {"role": "user", "content": msg}],
                    "options": {"temperature": 0.1}}
            if args.think:
                body["think"] = False if args.think == "false" else args.think
            req = urllib.request.Request(
                OLLAMA_URL, data=json.dumps(body).encode(),
                headers={"Authorization": f"Bearer {key}",
                         "Content-Type": "application/json"})
            for attempt in range(6):  # shares the key's concurrency with any live run
                try:
                    with urllib.request.urlopen(req, timeout=900) as resp:
                        out = json.load(resp)
                    break
                except urllib.error.HTTPError as e:
                    if e.code != 429 or attempt == 5:
                        raise
                    time.sleep(20 * (attempt + 1))
            m = re.search(r"\{.*\}", out["message"]["content"], re.S)
            verdict = json.loads(m.group(0)) if m else {}
            if verdict.get("verdict") not in VERIFY_MAP:
                raise ValueError(f"bad verdict {verdict!r}")
            rec.update(verdict=verdict["verdict"], reason=verdict.get("reason", ""),
                       prompt_tokens=out.get("prompt_eval_count"),
                       output_tokens=out.get("eval_count"))
        except Exception as e:  # noqa: BLE001
            rec["error"] = str(e)[:300]
        with lock:
            with open(args.out, "a") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"{r['job']:16} {r['model']:16} {rec.get('verdict', rec.get('error'))}", flush=True)

    todo = [c for c in claims if claim_key(c[0]["job"], c[0]["model"], c[1]) not in done]
    print(f"{len(todo)} claims to verify", flush=True)
    with cf.ThreadPoolExecutor(args.workers) as ex:
        list(ex.map(lambda c: run(*c), todo))


def apply_verdicts(r, verdicts):
    """Re-type a judge record's error claims by the verifier's verdicts and
    recompute its tier. Unverified claims are treated as rejected: an
    unchecked claim must not put a verse in front of readers as tier 3."""
    diffs = []
    for i, d in enumerate(r["result"]["differences"]):
        if d.get("type") in ("ours_omits", "ours_mistranslates"):
            v = verdicts.get(claim_key(r["job"], r["model"], i))
            new_type = VERIFY_MAP.get(v["verdict"]) if v else "alt_worse"
            if new_type:
                d = dict(d, type=new_type, verifier=v["verdict"] if v else "unverified",
                         verifier_reason=v.get("reason", "") if v else "")
            else:
                d = dict(d, verifier="confirmed", verifier_reason=v.get("reason", ""))
        diffs.append(d)
    r["result"]["differences"] = diffs
    r["result"]["value"], r["result"]["needs_review"] = tier_of(diffs)
    return r


# ---------------------------------------------------------------- reader notes
#
# The note under "See translation by X" is written in a separate pass
# from the judges' structured differences, so it can always say whose
# translation, which Arabic word (in the site's own transliteration) and how
# each side renders it, e.g.
#   Pickthall's translation keeps the traditional wording "believed in their
#   Lord" for āmanū and "their story" for nabaʾahum, while our translation
#   renders them as "trusted" and "news".

SHORT_NAMES = {19: "Pickthall", 22: "Yusuf Ali", 85: "Abdel Haleem", 149: "Bridges",
               84: "Usmani", 95: "Maududi", 20: "Saheeh International", 203: "Hilali & Khan"}

NOTE_SYSTEM = """You write the one-sentence note shown under a Qur'an verse on a website, beneath a link reading "See translation by {translator}". The reader has just read OUR translation of the verse.

Rules:
- Begin with "{short}'s translation".
- For each POINT, quote the alternative's wording, name the Arabic word it renders using the TRANSLITERATION from the word list (not Arabic script), and quote how our translation renders it. Pattern: {short}'s translation keeps the traditional wording "X" for translit, while our translation renders it as "Y". Group points naturally when there are two or three.
- Describe; do not judge which is better. Exception: a point of type "ours_omits" or "ours_mistranslates" is a confirmed problem in ours, so say it plainly (e.g. "our translation leaves out ...").
- "conventional_sense" points: say it keeps the traditional wording. "alt_reading": say it reads the Arabic differently. "nuance": say what it brings out.
- Use the exact words of the two translations for the quotes. Never write Arabic script; transliteration only. At most 45 words. No preamble.

Reply with JSON only: {"note": "..."}"""

# Traditional-wording differences outrank small nuances: they are what a
# reader most wants named ("believed" for āmanū where ours says "trusted").
POINT_ORDER = {"ours_omits": 0, "ours_mistranslates": 0, "alt_reading": 1,
               "conventional_sense": 2, "nuance": 3}


_QUOTED = re.compile(r'("[^"]*"|“[^”]*”)')
_TOKEN = re.compile(r"[^\s\"“”,.;:()]+")
_TRANSLIT_MARK = re.compile(r"[ʾʿāīūḥṣḍṭẓḏṯḫšġ]|\w-\w")


def mark_translit(note, words):
    """Italicise the transliterations in a note (*nabaʾahum*), the convention
    the exegesis and translation notes use, so align_note_anchors.py turns
    them into hover anchors on the Arabic. A span is marked only when it
    resolves to words of THIS verse, starts and ends on a transliterated token
    (so English is never absorbed) and lies outside quotes."""
    from align_note_anchors import resolve  # local: keeps app.py's import light
    if not note or "*" in note or not words:
        return note
    out = []
    for part in _QUOTED.split(note):
        if _QUOTED.fullmatch(part):
            out.append(part)
            continue
        toks = list(_TOKEN.finditer(part))
        marks = []  # (start, end) char spans to wrap
        i = 0
        while i < len(toks):
            hit = None
            if _TRANSLIT_MARK.search(toks[i].group(0)):
                for j in range(min(i + 6, len(toks)), i, -1):
                    if not _TRANSLIT_MARK.search(toks[j - 1].group(0)):
                        continue
                    span = part[toks[i].start():toks[j - 1].end()]
                    if resolve(span, "translit", words):
                        hit = (toks[i].start(), toks[j - 1].end(), j)
                        break
            if hit:
                marks.append(hit[:2])
                i = hit[2]
            else:
                i += 1
        for a, b in reversed(marks):
            part = f"{part[:a]}*{part[a:b]}*{part[b:]}"
        out.append(part)
    return "".join(out)


def clean_translit(t):
    """word_translit spells a silent final alif ("qālūā", "fiā"); it is a
    search key there, but a note shows it to readers: "qālū", "fī"."""
    return re.sub(r"iā\b", "ī", re.sub(r"ūā\b", "ū", t))


def note_points(judges, translator):
    """The differences worth telling the reader about, most important first.
    Prefer the judges that picked the shown translation; one point per
    Arabic word."""
    picked = [j for j in judges if j.get("best") == translator] or judges
    seen, points = set(), []
    for d in sorted((d for j in picked for d in j.get("differences", [])),
                    key=lambda d: POINT_ORDER.get(d.get("type"), 9)):
        if d.get("type") not in POINT_ORDER:
            continue
        k = re.sub(r"[ً-ْٰ۟-ۭ\s]", "", str(d.get("arabic", "")))
        if k in seen:
            continue
        seen.add(k)
        points.append({k2: d.get(k2) for k2 in ("type", "arabic", "ours", "best")})
    return points[:2]


def notes(args):
    key = open(os.environ["OLLAMA_KEY_FILE"]).read().strip()
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True, check_same_thread=False)
    rows = conn.execute(
        "SELECT chapter, verse, resource_id, translator, text, judges_json "
        "FROM verse_alt_translations WHERE tier >= 1 AND review_status != 'hidden' "
        "ORDER BY chapter, verse").fetchall()
    done = set()
    if os.path.exists(args.out):
        for line in open(args.out):
            n = json.loads(line)
            if n.get("note"):
                done.add((n["ref"], n["translator"]))
    lock, db_lock = threading.Lock(), threading.Lock()

    def run(row):
        ch, v, rid, translator, alt_text, judges_json = row
        ref, short = f"{ch}:{v}", SHORT_NAMES.get(rid, translator)
        points = note_points(json.loads(judges_json or "[]"), translator)
        rec = {"ref": ref, "translator": translator, "points": points, "model": args.model}
        if not points:
            rec["note"] = ""
        else:
            with db_lock:
                ours, _ = our_translation(conn, ch, v)
                words = "\n".join(f"{p}. {a} = {clean_translit(t)}" for p, a, t in conn.execute(
                    "SELECT word_pos, arabic_plain, translit FROM word_translit "
                    "WHERE chapter=? AND verse=? ORDER BY word_pos", (ch, v)))
            msg = "\n\n".join([
                f"VERSE {ref}", "WORD LIST (Arabic = transliteration):\n" + words,
                f"OUR TRANSLATION: {ours}", f"{short.upper()}'S TRANSLATION: {alt_text}",
                "POINTS:\n" + json.dumps(points, ensure_ascii=False)])
            system = NOTE_SYSTEM.replace("{translator}", translator).replace("{short}", short)
            try:
                for attempt in (1, 2):
                    body = {"model": args.model, "stream": False, "format": "json",
                            "think": False if args.think == "false" else args.think,
                            "messages": [{"role": "system", "content": system},
                                         {"role": "user", "content": msg}],
                            "options": {"temperature": 0.2}}
                    if args.think is None:
                        body.pop("think")
                    req = urllib.request.Request(
                        OLLAMA_URL, data=json.dumps(body).encode(),
                        headers={"Authorization": f"Bearer {key}",
                                 "Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=300) as resp:
                        out = json.load(resp)
                    m = re.search(r"\{.*\}", out["message"]["content"], re.S)
                    note = (json.loads(m.group(0)).get("note") or "").strip() if m else ""
                    # Must name the translator and refer to ours; else retry once.
                    if (note.startswith(f"{short}'s translation") and "our translation" in note
                            and not re.search(r"[\u0600-\u06FF]", note)):
                        break
                    if attempt == 2:
                        raise ValueError(f"note off-format: {note[:120]!r}")
                rec.update(note=note, prompt_tokens=out.get("prompt_eval_count"),
                           output_tokens=out.get("eval_count"))
            except Exception as e:  # noqa: BLE001
                rec["error"] = str(e)[:300]
        with lock:
            with open(args.out, "a") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    only = set(parse_refs(args.verses, conn)) if args.verses else None
    todo = [r for r in rows if (f"{r[0]}:{r[1]}", r[3]) not in done
            and (only is None or (r[0], r[1]) in only)]
    print(f"{len(todo)} notes to write", flush=True)
    with cf.ThreadPoolExecutor(args.workers) as ex:
        list(ex.map(run, todo))


# ---------------------------------------------------------------- serving table

ALT_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS verse_alt_translations (
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
    resource_id INTEGER NOT NULL,
    translator TEXT NOT NULL,
    text TEXT NOT NULL,
    tier INTEGER NOT NULL,              -- 0 hidden, 1 light link, 2 dark link, 3 shown
    reader_note TEXT,
    needs_review INTEGER NOT NULL DEFAULT 0,  -- a judge claims OUR translation errs
    review_status TEXT NOT NULL DEFAULT 'auto',  -- auto | pending | approved | hidden
    judges_json TEXT,
    prompt_version TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    reviewed_at TEXT,
    PRIMARY KEY (chapter, verse)
)"""


def ensure_alt_table(conn):
    conn.execute(ALT_TABLE_DDL)


def ensemble(records):
    """Combine the two judges' verdicts on one verse.

    Either judge at >=2 lifts the tier (one judge can spot a grammar point the
    other misses); below that the lower tier wins, so a light-gray link needs
    both judges to see a real nuance. Tier 3 (an error in OUR translation)
    auto-shows only if the other judge also sees value >=2; otherwise it shows
    as tier 2. The shown text is the pick of the judge that saw the most
    value, so its note describes that text."""
    tiers = [r["result"]["value"] for r in records]
    hi, lo = max(tiers), min(tiers)
    tier = hi if hi >= 2 else lo
    if tier == 3 and lo < 2:
        tier = 2
    needs_review = any(r["result"]["needs_review"] for r in records) and hi == 3

    def fid_sum(rid):
        total = 0
        for r in records:
            inv = {v: k for k, v in r["letters"].items()}
            score = r["result"].get("scores", {}).get(inv.get(rid))
            try:  # judges occasionally return "4" instead of 4
                total += int((score or {}).get("fidelity") or 0)
            except (TypeError, ValueError, AttributeError):
                pass
        return total

    if len(set(tiers)) > 1:
        lead = max(records, key=lambda r: r["result"]["value"])
    else:
        lead = max(records, key=lambda r: fid_sum(r["best_rid"]))
    return tier, needs_review, lead


def load(args):
    written_notes = {}
    for path in args.notes or []:
        for line in open(path):
            n = json.loads(line)
            if "note" in n:
                written_notes[(n["ref"], n["translator"])] = n["note"]
    verdicts = {}
    for path in args.verified or []:
        for line in open(path):
            v = json.loads(line)
            if "verdict" in v:
                verdicts[v["key"]] = v
    by_ref = {}
    for path in args.inputs:
        for line in open(path):
            r = json.loads(line)
            if "result" in r and not r.get("control"):
                by_ref.setdefault(r["ref"], {})[r["model"]] = apply_verdicts(r, verdicts)
    conn = sqlite3.connect(args.db, timeout=60)
    ensure_alt_table(conn)
    cands = load_candidates(args.cache_dir, conn, tuple(TRANSLATORS))
    from align_note_anchors import load_verse_words
    verse_words = load_verse_words(conn)
    locked = {(c, v) for c, v in conn.execute(
        "SELECT chapter, verse FROM verse_alt_translations "
        "WHERE review_status IN ('approved', 'hidden')")}
    n_judges = len(args.inputs)
    written = skipped_partial = skipped_locked = 0
    for ref, per_model in sorted(by_ref.items()):
        if len(per_model) < n_judges:
            skipped_partial += 1
            continue
        ch, v = map(int, ref.split(":"))
        if (ch, v) in locked and not args.force:
            skipped_locked += 1
            continue
        records = list(per_model.values())
        tier, needs_review, lead = ensemble(records)
        rid = lead["best_rid"]
        judges = [{"model": r["model"], "tier": r["result"]["value"],
                   "best": TRANSLATORS.get(r["best_rid"]),
                   "summary": r["result"].get("summary", ""),
                   "differences": r["result"].get("differences", []),
                   "ours_check": r["result"].get("ours_check", []),
                   "scores": {TRANSLATORS.get(r["letters"][L], L): s
                              for L, s in r["result"].get("scores", {}).items()
                              if L in r["letters"]}}  # judges now and then score a phantom letter
                  for r in records]
        conn.execute(
            "INSERT OR REPLACE INTO verse_alt_translations "
            "(chapter, verse, resource_id, translator, text, tier, reader_note, "
            " needs_review, review_status, judges_json, prompt_version) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (ch, v, rid, TRANSLATORS[rid], cands[(ch, v)][rid], tier,
             mark_translit(written_notes.get((ref, TRANSLATORS[rid]),
                                             (lead["result"].get("reader_note") or "").strip()),
                           verse_words.get((ch, v), [])),
             int(needs_review),
             "pending" if needs_review else "auto",
             json.dumps(judges, ensure_ascii=False), lead["prompt_version"]))
        written += 1
    conn.commit()
    dist = dict(conn.execute(
        "SELECT tier, COUNT(*) FROM verse_alt_translations GROUP BY tier").fetchall())
    pending = conn.execute(
        "SELECT COUNT(*) FROM verse_alt_translations WHERE review_status='pending'").fetchone()[0]
    print(f"written {written}, waiting on a judge {skipped_partial}, "
          f"kept reviewed {skipped_locked}; tiers {dist}; pending review {pending}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--cache-dir", required=True)
    j = sub.add_parser("judge")
    j.add_argument("--cache-dir", required=True)
    j.add_argument("--db", default=DB_PATH)
    j.add_argument("--verses", required=True, help='"all" or refs like 2:3,4:34-36')
    j.add_argument("--sources", default=",".join(map(str, PUBLIC_DOMAIN)),
                   help="quran.com resource ids to judge between")
    j.add_argument("--controls")
    j.add_argument("--models", default="glm-5.3")
    j.add_argument("--out", required=True)
    j.add_argument("--seed", default="alt-v1")
    j.add_argument("--workers", type=int, default=6)
    j.add_argument("--think", help="false|low|medium|high (default: model's own)")
    lo = sub.add_parser("load", help="ensemble judge JSONL files into the DB")
    lo.add_argument("--cache-dir", required=True)
    lo.add_argument("--db", default=DB_PATH)
    lo.add_argument("--inputs", nargs="+", required=True, help="one JSONL per judge")
    lo.add_argument("--verified", nargs="*", help="verify JSONL(s); unverified error claims count as rejected")
    lo.add_argument("--notes", nargs="*", help="notes JSONL(s) from the notes command")
    lo.add_argument("--force", action="store_true", help="overwrite reviewed rows too")
    no = sub.add_parser("notes", help="write clear reader notes for shown verses")
    no.add_argument("--db", default=DB_PATH)
    no.add_argument("--out", required=True)
    no.add_argument("--model", default="deepseek-v4-pro")
    no.add_argument("--think", default="false")
    no.add_argument("--workers", type=int, default=8)
    no.add_argument("--verses", help="limit to refs, e.g. 18:13,2:255 (for spot checks)")
    ve = sub.add_parser("verify", help="re-check claimed errors in OUR translation")
    ve.add_argument("--cache-dir", required=True)
    ve.add_argument("--db", default=DB_PATH)
    ve.add_argument("--inputs", nargs="+", required=True)
    ve.add_argument("--out", required=True)
    ve.add_argument("--model", default="glm-5.3")
    ve.add_argument("--think", help="false|low|medium|high (default: model's own)")
    ve.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.cmd == "fetch":
        fetch(a.cache_dir)
    elif a.cmd == "load":
        load(a)
    elif a.cmd == "verify":
        verify(a)
    elif a.cmd == "notes":
        notes(a)
    else:
        judge(a)


if __name__ == "__main__":
    sys.exit(main())
