"""Turn mined candidates (expressions_mine.py) into explained Qur'anic expressions.

    triage   pick the N most rewarding candidates per kind (one call per kind)
    write    write each one up, Qur'an-only, citing only the verses it is given
    verify   a reasoning model checks every claim against those verses
    revise   the writer applies the verifier's confirmed issues

All steps append to JSONL and resume. Needs OLLAMA_KEY_FILE.

    python expressions_ai.py triage --candidates c.json --out triage.json --per-kind 5
    python expressions_ai.py write  --triage triage.json --out written.jsonl
    python expressions_ai.py verify --inputs written.jsonl --out verified.jsonl
    python expressions_ai.py revise --written written.jsonl --verified verified.jsonl --out final.jsonl
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.request

from alt_translations_ai import OUR_CONFIG_ID, grammar_of, strip_basmala

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "quran.db")
OLLAMA_URL = "https://ollama.com/api/chat"
WRITER = ("glm-5.3", "low")
VERIFIER = ("glm-5.3", None)  # the model's own (full) reasoning
TRIAGE = ("glm-5.3", "low")
ANTONYM = ("deepseek-v4-pro", "false")
PROMPT_VERSION = "expr-v2"

KINDS = {
    "mirror": "one verb root used twice in a single verse, the action passing between "
              "parties (e.g. 2:152 'remember Me, I will remember you')",
    "family": "two content words that keep appearing together across different contexts, "
              "so that reading the occurrences side by side shows something none shows alone",
    "twin": "two near-identical verses that differ by a word or two; the interest is what "
            "the difference does in each context",
    "closing": "the pair of divine names/attributes that closes a verse (including the same "
               "pair in reversed order elsewhere); the interest is how the pair fits what the "
               "verse has just said",
    "contrast": "two roots the Qur'an keeps setting against each other in one verse "
                "(opposites or complementary poles)",
    "frame": "a fixed formula with a changing slot; the interest is the set of fillers and "
             "what the formula does to them",
}
# The owner's own examples go in the pilot so the output can be judged against them.
SEEDS = {"mirror": ["2:152:"], "family": ["faD~ala|baEoD"]}


# ---------------------------------------------------------------- model call

def chat(model, think, system, user, key, timeout=1800):
    body = {"model": model, "stream": False, "format": "json",
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "options": {"temperature": 0.2}}
    if think is not None:
        body["think"] = False if think == "false" else think
    req = urllib.request.Request(OLLAMA_URL, data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}",
                                          "Content-Type": "application/json"})
    last = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.load(r)
            m = re.search(r"\{.*\}", d["message"]["content"], re.S)
            if not m:
                raise ValueError("no JSON in reply")
            return json.loads(m.group(0)), d.get("prompt_eval_count") or 0, d.get("eval_count") or 0
        except urllib.error.HTTPError as e:
            last = e
            time.sleep(20 * (attempt + 1) if e.code == 429 else 5)
        except (ValueError, json.JSONDecodeError, OSError) as e:
            last = e
            time.sleep(5)
    raise RuntimeError(f"{model}: {last}")


def key_():
    return open(os.environ["OLLAMA_KEY_FILE"]).read().strip()


# ---------------------------------------------------------------- verse data

def verse(conn, ref):
    ch, v = map(int, ref.split(":"))
    ar = conn.execute("SELECT text_uthmani FROM verses WHERE chapter=? AND verse=?", (ch, v)).fetchone()
    en = conn.execute(
        "SELECT COALESCE(revised_text, translation_text) FROM ai_translations "
        "WHERE chapter=? AND verse=? AND config_id=?", (ch, v, OUR_CONFIG_ID)).fetchone()
    return (strip_basmala(conn, ar[0], ch, v) if ar else ""), (en[0] if en else "")


def sample_refs(refs, cap=14):
    """Up to `cap` refs spread across the Qur'an (closing pairs run to 90+)."""
    if len(refs) <= cap:
        return refs
    step = len(refs) / cap
    return [refs[int(i * step)] for i in range(cap)]


# ---------------------------------------------------------------- triage

TRIAGE_SYSTEM = """You curate a pilot for an "Expressions" section of a Qur'an research website. The site reads the Qur'an through the Qur'an itself (its own usage, context and grammar), not through later tradition.

You get mined candidates of ONE kind: {kind_desc}.

Pick the {n} candidates that would most reward a careful researcher. Prefer ones where reading the occurrences together reveals something real: a pattern, a precise distinction, a development, a surprising pairing, a reciprocity. Avoid stock formulas whose only interest is that they repeat, near-duplicates of each other, and candidates that are artefacts of the mining (unrelated words that merely sit near each other). Spread your picks across different themes.

Reply with JSON only: {{"picks": [{{"id": "<candidate id>", "why": "one sentence"}}]}}"""


def _overlaps(c, taken):
    """Same expression already picked (any kind): shared phrase, or most verses shared."""
    s = set(c["refs"])
    for t in taken:
        if c.get("phrase") and c.get("phrase") == t.get("phrase"):
            return True
        u = set(t["refs"])
        if len(s) > 1 and len(s & u) / len(s | u) >= 0.6:
            return True
    return False


def triage(a):
    cands = json.load(open(a.candidates))
    counts = json.loads(a.counts) if a.counts else {}
    taken = []
    exclude = set()
    for path in a.exclude or []:
        for k, cs in json.load(open(path)).items():
            for c in cs:
                exclude.add(c["key"])
                taken.append(c)
    conn = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    key = key_()
    out = {}
    if os.path.exists(a.out):
        out = json.load(open(a.out))
    for kind, desc in KINDS.items():
        if kind in out:
            continue
        pool = [c for c in cands[kind] if c["key"] not in exclude and not _overlaps(c, taken)][:400]
        seeds = [] if exclude else [c for c in pool if any(c["key"].startswith(s) for s in SEEDS.get(kind, []))]
        want = counts.get(kind, a.per_kind)
        n = min(len(pool), want + (6 if exclude else 0)) - len(seeds)  # spare picks absorb de-duplication
        lines = []
        for i, c in enumerate(pool):
            refs = c["refs"]
            line = f"{i}. {c.get('phrase', '')} | {len(refs)} verse(s): {', '.join(refs[:8])}"
            if kind == "mirror":
                line += " | " + verse(conn, refs[0])[1][:160]
            if kind == "closing" and c.get("flip_refs"):
                line += f" | reversed as {c['flip_phrase']} in {len(c['flip_refs'])}"
            if kind == "frame":
                line += " | slot fillers: " + " ".join(c.get("fills", [])[:12])
            lines.append(line)
        system = TRIAGE_SYSTEM.format(kind_desc=desc, n=n)
        res, pin, pout = chat(*TRIAGE, system, "CANDIDATES:\n" + "\n".join(lines), key)
        picks = []
        for p in res.get("picks", []):
            try:
                c = pool[int(str(p["id"]).strip().rstrip("."))]
            except (ValueError, IndexError, KeyError, TypeError):
                continue
            if c not in seeds and c not in picks and not _overlaps(c, taken + picks):
                picks.append(dict(c, why=p.get("why", "")))
        out[kind] = [dict(s, why="owner's example") for s in seeds] + picks[:want - len(seeds)]
        taken += out[kind]
        print(f"{kind:9} picked {len(out[kind])}  ({pin} in / {pout} out tokens)", flush=True)
        json.dump(out, open(a.out, "w"), ensure_ascii=False, indent=1)


# ---------------------------------------------------------------- antonym filter

ANTONYM_SYSTEM = """Each line is a pair of Arabic roots (letters spaced) that appear together in several Qur'an verses. Keep only pairs whose meanings are set against each other: opposites (life / death, guidance / straying) or complementary poles (night / day, apparent / hidden, ease / hardship). Drop pairs that merely co-occur in a phrase (flowing / rivers, selling / price) and near-synonyms.

Reply with JSON only: {"keep": [<line numbers>]}"""


def antonyms(a):
    cands = json.load(open(a.candidates))
    pool = sorted(cands["contrast"], key=lambda c: -len(c["refs"]))
    key = key_()
    keep = []
    for start in range(0, len(pool), 120):
        batch = pool[start:start + 120]
        lines = "\n".join(f"{i}. {c['phrase']} ({len(c['refs'])} verses)" for i, c in enumerate(batch))
        res, _, _ = chat(*ANTONYM, ANTONYM_SYSTEM, lines, key)
        for i in res.get("keep", []):
            try:
                keep.append(batch[int(i)])
            except (ValueError, IndexError, TypeError):
                pass
        print(f"{start + len(batch)}/{len(pool)} checked, {len(keep)} kept", flush=True)
    cands["contrast"] = keep
    json.dump(cands, open(a.out, "w"), ensure_ascii=False)


# ---------------------------------------------------------------- write

WRITE_SYSTEM = """You write one entry for an "Expressions" section of a Qur'an research website.

The site reads the Qur'an through the Qur'an itself: a word means what the Qur'an's own usage, context and grammar show, read with Arabic usage contemporary with it. Never use tafsir, hadith, sira, occasions of revelation, fiqh, later theology, or traditional technical definitions (do not assume, say, that ṣalāh means the later ritual prayer). English quotations use OUR TRANSLATION's wording, given with each verse.

Hard rules:
- Cite only the verses provided below, as (2:152). Do not cite or quote any other verse.
- Every claim must be visible in the cited verse's words. Describe what the verses say and do; do not add what they do not say.
- Neutral, precise voice for researchers. No preaching, no devotional formulas, no "beautiful"/"profound".
- Claims are about the VERSES GIVEN, never about "the Qur'an" as a whole. Do not write "always", "never", "only", "every", "consistently", "nearly always" or "each time" unless you have checked every given verse and the statement holds for each; say "in the verses given" and count exactly. A sample is not the whole.
- Grammar: describe a word's form (person, number, voice, mood, case, verb form) only as the WORD DATA shows it.
- Wording: call two passages identical only if their Arabic is identical; otherwise name the exact difference.
- Do not date verses or surahs (early/late, Meccan/Medinan), do not name a person, group or place the verse leaves unnamed, and do not describe events behind a verse.
- Do not introduce theological or legal distinctions (e.g. will versus permission) that the verse's own words do not draw.
- "for_researchers" items are open questions, not claims in disguise.
- If on reading the verses the candidate is not worth an entry (a stock formula, words that only happen to sit together, or a pair that does not fit its KIND, such as a "contrast" whose words are not set against each other), set "reject" to true and say why in "reject_reason".

Reply with JSON only:
{"reject": false,
 "reject_reason": "",
 "title": "a short English name for the expression (at most 8 words)",
 "expression_ar": "the expression in Arabic, copied exactly from one of the verses",
 "transliteration": "its transliteration",
 "gloss": "its English rendering, in OUR TRANSLATION's wording",
 "summary": "one or two sentences: what reading these verses together shows",
 "explanation": "150-300 words, citing verses as (2:152)",
 "occurrences": [{"ref": "2:152", "role": "one sentence: what the expression does in this verse"}],
 "variation": "what changes between occurrences and what the change does; empty if nothing",
 "for_researchers": ["two or three short pointers or open questions, each tied to cited verses"]}"""


def focus(c):
    """The lemmas / roots the entry is about, for the per-verse WORD DATA."""
    k = c["kind"]
    if k == "mirror":
        return set(), {c["root"]}
    if k == "contrast":
        return set(), set(c["roots"])
    if k == "family":
        return set(c["lemmas"]), set()
    return set(c["key"].split("|")) if k in ("closing", "frame") else set(), set()


def word_data(conn, ref, lemmas, roots, positions=None):
    ch, v = map(int, ref.split(":"))
    rows = conn.execute(
        "SELECT word_pos, tag, lemma_buckwalter, root_buckwalter, root_arabic, features_raw "
        "FROM morphology WHERE chapter=? AND verse=? ORDER BY word_pos, segment", (ch, v)).fetchall()
    toks = strip_basmala(conn, conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter=? AND verse=?", (ch, v)).fetchone()[0], ch, v).split()
    stems, pron = {}, {}
    for wp, tag, lem, root, root_ar, feats in rows:
        if tag == "SUFFIX" and "PRON:" in (feats or ""):
            pron.setdefault(wp, []).append(feats.split("PRON:")[1].split("|")[0])
        elif tag not in ("PREFIX", "SUFFIX") and wp not in stems:
            stems[wp] = (tag, lem, root, root_ar, feats)
    lines = []
    for wp, (tag, lem, root, root_ar, feats) in sorted(stems.items()):
        if (positions is not None and wp in positions) or lem in lemmas or root in roots:
            word = toks[wp - 1] if wp - 1 < len(toks) else "?"
            extra = f" + pronoun {', '.join(pron[wp])}" if wp in pron else ""
            lines.append(f"  word {wp}: {word} | root {root_ar or '-'} | {tag} {grammar_of(feats)}{extra}")
    return "\n".join(lines)


def twin_diff_positions(conn, a, b):
    """Word positions in each twin verse where the lemma sequences differ."""
    import difflib
    seq = {}
    for r in (a, b):
        ch, v = map(int, r.split(":"))
        seq[r] = [(wp, lem) for wp, lem in conn.execute(
            "SELECT word_pos, lemma_buckwalter FROM morphology WHERE chapter=? AND verse=? "
            "AND tag NOT IN ('PREFIX','SUFFIX') GROUP BY word_pos ORDER BY word_pos", (ch, v))]
    sm = difflib.SequenceMatcher(None, [l for _, l in seq[a]], [l for _, l in seq[b]])
    pa, pb = set(), set()
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != "equal":
            pa.update(seq[a][i][0] for i in range(i1, i2))
            pb.update(seq[b][j][0] for j in range(j1, j2))
    return {a: pa, b: pb}


def build_write_msg(conn, c):
    kind = c["kind"]
    refs = list(c["refs"])
    extra = ""
    if kind == "closing":
        refs = sample_refs(refs) + sample_refs(c.get("flip_refs", []), 8)
        extra = (f"Order A ({c['phrase']}) closes {len(c['refs'])} verses; "
                 + (f"order B ({c['flip_phrase']}) closes {len(c['flip_refs'])}. " if c.get("flip_refs") else "")
                 + "A sample is given.\n")
    elif kind == "contrast":
        extra = f"{len(refs)} verses contain both roots; a sample is given.\n"
        refs = sample_refs(refs)
    elif kind == "frame":
        extra = f"Slot fillers seen: {' '.join(c.get('fills', []))}\n"
        refs = sample_refs(refs)
    parts = [f"KIND: {kind} = {KINDS[kind]}",
             f"CANDIDATE: {c.get('phrase', c['key'])}",
             extra.strip()]
    ctx_refs = set()
    if kind == "twin":  # the difference is read against each verse's neighbours
        for r in c["refs"]:
            ch, v = map(int, r.split(":"))
            ctx_refs.update(f"{ch}:{x}" for x in (v - 1, v + 1) if x > 0)
    lemmas, roots = focus(c)
    diffs = twin_diff_positions(conn, *c["refs"]) if kind == "twin" else {}
    for r in refs + sorted(ctx_refs - set(refs)):
        ar, en = verse(conn, r)
        if not ar:
            continue
        tag = " (context)" if r in ctx_refs and r not in refs else ""
        block = f"VERSE {r}{tag}\nARABIC: {ar}\nOUR TRANSLATION: {en}"
        if not tag:
            wd = word_data(conn, r, lemmas, roots, diffs.get(r))
            if wd:
                block += ("\nWORD DATA (the words that differ from its twin):\n" if kind == "twin"
                          else "\nWORD DATA:\n") + wd
        parts.append(block)
    return "\n\n".join(p for p in parts if p), refs + sorted(ctx_refs - set(refs))


def run_jobs(jobs, out_path, fn, workers):
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            r = json.loads(line)
            if "error" not in r:
                done.add(r["id"])
    lock = threading.Lock()

    def go(job):
        rec = fn(job)
        with lock:
            with open(out_path, "a") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"{rec['id']:40} {rec.get('error') or rec.get('status', 'ok')}", flush=True)

    todo = [j for j in jobs if j["id"] not in done]
    print(f"{len(todo)} jobs", flush=True)
    with cf.ThreadPoolExecutor(workers) as ex:
        list(ex.map(go, todo))


def write(a):
    conn = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True, check_same_thread=False)
    db_lock = threading.Lock()
    key = key_()
    jobs = [dict(c, id=f"{k}:{c['key']}") for k, cs in json.load(open(a.triage)).items() for c in cs]

    def fn(c):
        with db_lock:
            msg, given = build_write_msg(conn, c)
        rec = {"id": c["id"], "kind": c["kind"], "candidate": c, "given_refs": given,
               "prompt_version": PROMPT_VERSION, "model": WRITER[0]}
        try:
            res, pin, pout = chat(*WRITER, WRITE_SYSTEM, msg, key)
            rec.update(entry=res, prompt_tokens=pin, output_tokens=pout,
                       status="rejected" if res.get("reject") else "written",
                       checks=deterministic_checks(conn, res, given))
        except Exception as e:  # noqa: BLE001
            rec["error"] = str(e)[:300]
        return rec

    run_jobs(jobs, a.out, fn, a.workers)


# ---------------------------------------------------------------- checks

_TASHKEEL = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")


def _bare(s):
    s = _TASHKEEL.sub("", s or "")
    s = re.sub("[ٱأإآ]", "ا", s)
    return re.sub(r"\s+", " ", s).strip()


def deterministic_checks(conn, entry, given):
    """Facts a script can check: cited refs were given, the Arabic is real."""
    if entry.get("reject"):
        return {}
    text = " ".join([entry.get("explanation", ""), entry.get("summary", ""), entry.get("variation", ""),
                     " ".join(entry.get("for_researchers", []) or [])]
                    + [o.get("role", "") for o in entry.get("occurrences", []) or []])
    cited = set(re.findall(r"\b(\d{1,3}:\d{1,3})\b", text))
    cited |= {o.get("ref") for o in entry.get("occurrences", []) or [] if o.get("ref")}
    foreign = sorted(cited - set(given))
    expr = _bare(entry.get("expression_ar", ""))
    found_in = [r for r in given if expr and expr in _bare(verse(conn, r)[0])]
    return {"cited_not_given": foreign, "expression_found_in": found_in}


# ---------------------------------------------------------------- verify

VERIFY_SYSTEM = """You check an entry written for a Qur'an research website against the verses it was given. The site reads the Qur'an through the Qur'an itself; the entry must not import tafsir, hadith, sira, occasions of revelation, fiqh, later theology or traditional technical definitions.

Go through the entry claim by claim. For each claim, find the cited verse below and check that its words (Arabic, and OUR TRANSLATION) actually support it. Flag:
- "unsupported": the cited verse does not say this, or the claim goes further than the verses do
- "wrong_ref": the quote or point belongs to a different verse than the one cited
- "import": the claim relies on something outside the Qur'an (tradition, history, law, later theology)
- "misquote": Arabic or English quoted inaccurately
- "overreach": a generalisation ("always", "only", "every time") the given verses do not establish
Do not flag style. Do not flag a claim just because you would have phrased it differently.

Reply with JSON only:
{"verdict": "pass" | "fix",
 "issues": [{"claim": "the exact words in the entry", "type": "<one type above>", "why": "one sentence", "fix": "a corrected wording, or 'delete'"}]}"""


def verify(a):
    model = a.model or VERIFIER[0]
    think = a.think if a.think else VERIFIER[1]
    conn = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True, check_same_thread=False)
    db_lock = threading.Lock()
    key = key_()
    jobs = []
    for path in a.inputs:
        for line in open(path):
            r = json.loads(line)
            if r.get("status") == "written":
                jobs.append(r)

    def fn(r):
        with db_lock:
            msg, _ = build_write_msg(conn, r["candidate"])
        rec = {"id": r["id"], "model": model, "think": think}
        try:
            entry = {k: r["entry"].get(k) for k in ("title", "expression_ar", "gloss", "summary",
                                                     "explanation", "occurrences", "variation",
                                                     "for_researchers")}
            res, pin, pout = chat(model, think, VERIFY_SYSTEM,
                                  "VERSES GIVEN TO THE WRITER:\n\n" + msg
                                  + "\n\nENTRY:\n" + json.dumps(entry, ensure_ascii=False, indent=1), key)
            rec.update(result=res, prompt_tokens=pin, output_tokens=pout,
                       status=res.get("verdict", "?"))
        except Exception as e:  # noqa: BLE001
            rec["error"] = str(e)[:300]
        return rec

    run_jobs(jobs, a.out, fn, a.workers)


# ---------------------------------------------------------------- revise

REVISE_SYSTEM = WRITE_SYSTEM + """

You are now REVISING your entry. A checker compared it with the verses and listed issues. Apply each issue's fix (or delete the claim), keep everything else as it is, and return the full corrected entry in the same JSON shape."""


def revise(a):
    conn = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True, check_same_thread=False)
    db_lock = threading.Lock()
    key = key_()
    written = {json.loads(l)["id"]: json.loads(l) for l in open(a.written)}
    verdicts = {}
    for l in open(a.verified):
        v = json.loads(l)
        if "result" in v:
            verdicts[v["id"]] = v
    jobs = [dict(written[i], verdict=verdicts[i]) for i in verdicts if i in written]

    def fn(r):
        issues = list(r["verdict"]["result"].get("issues") or [])
        ck = r.get("checks") or {}
        if ck.get("cited_not_given"):
            issues.append({"claim": ", ".join(ck["cited_not_given"]), "type": "wrong_ref",
                           "why": "these verses were not among those given", "fix": "remove these citations"})
        if ck and not ck.get("expression_found_in"):
            issues.append({"claim": r["entry"].get("expression_ar", ""), "type": "misquote",
                           "why": "expression_ar does not appear verbatim in any given verse",
                           "fix": "copy expression_ar exactly from one of the verses"})
        rec = {"id": r["id"], "kind": r["kind"], "candidate": r["candidate"],
               "given_refs": r["given_refs"], "issues_applied": issues}
        if not issues:
            rec.update(entry=r["entry"], status="final", checks=r.get("checks"))
            return rec
        with db_lock:
            msg, given = build_write_msg(conn, r["candidate"])
        try:
            res, pin, pout = chat(*WRITER, REVISE_SYSTEM,
                                  msg + "\n\nYOUR ENTRY:\n" + json.dumps(r["entry"], ensure_ascii=False, indent=1)
                                  + "\n\nISSUES:\n" + json.dumps(issues, ensure_ascii=False, indent=1), key)
            with db_lock:
                checks = deterministic_checks(conn, res, given)
            rec.update(entry=res, status="final", prompt_tokens=pin, output_tokens=pout, checks=checks)
        except Exception as e:  # noqa: BLE001
            rec["error"] = str(e)[:300]
        return rec

    run_jobs(jobs, a.out, fn, a.workers)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("triage")
    t.add_argument("--candidates", required=True)
    t.add_argument("--out", required=True)
    t.add_argument("--per-kind", type=int, default=5)
    t.add_argument("--counts", help='JSON per-kind counts, e.g. {"mirror": 35}')
    t.add_argument("--exclude", nargs="*", help="earlier triage files whose picks to skip")
    an = sub.add_parser("antonyms", help="keep only contrast pairs that are real opposites")
    an.add_argument("--candidates", required=True)
    an.add_argument("--out", required=True)
    w = sub.add_parser("write")
    w.add_argument("--triage", required=True)
    w.add_argument("--out", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--inputs", nargs="+", required=True)
    v.add_argument("--out", required=True)
    v.add_argument("--model", help=f"default {VERIFIER[0]}")
    v.add_argument("--think", help="false|low|medium|high; default the model's own reasoning")
    r = sub.add_parser("revise")
    r.add_argument("--written", required=True)
    r.add_argument("--verified", required=True)
    r.add_argument("--out", required=True)
    for p in (t, w, v, r, an):
        p.add_argument("--db", default=DB_PATH)
        p.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    {"triage": triage, "write": write, "verify": verify, "revise": revise,
     "antonyms": antonyms}[a.cmd](a)


if __name__ == "__main__":
    main()
