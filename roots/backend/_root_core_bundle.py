#!/usr/bin/env python3
"""Assemble everything we know about ONE root into an evidence bundle.

This is the INPUT side of the root core-meaning pipeline. It is deliberately a
separate module from the prompt and the runner: the bundle is what we can prove
we know, and it must be reproducible byte-for-byte on a re-run, so the only way
to change a generated passage is to change the prompt or the model -- never a
silent difference in what the model was shown.

DETERMINISM. No randomness anywhere. Verse selection is by a fixed rule (below),
dictionaries come in a fixed priority order, and every section is truncated at a
fixed cap. Re-running on the same DB yields the same bytes.
"""
import sqlite3
import os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'quran.db')

# Ibn Faris FIRST and with the most room: his Maqayis is the method the owner
# asked for, not merely one dictionary among sixteen. Mufradat is next because
# it is Quran-specific. Lane is the richest English. Asas al-Balagha carries
# metaphorical/idiomatic usage, which is often where a unifying sense shows
# itself. Lisan and Taj are enormous (4.8k / 5.2k chars average) and mostly
# repeat the others, so they come last on a tight cap.
# Mirrors app.py's _BW_TO_SR so the bundle resolves exactly the cognate rows the
# site itself shows for a root.
BW_TO_SR = {
    "'": 'ʔ', '>': 'ʔ', '<': 'ʔ', '&': 'ʔ', '}': 'ʔ', '|': 'ʔ', 'A': 'ʔ',
    'b': 'b', 't': 't', 'v': 'ṯ', 'j': 'g', 'H': 'ḥ', 'x': 'ḫ', 'd': 'd',
    '*': 'ḏ', 'r': 'r', 'z': 'z', 's': 's¹', '$': 's²', 'S': 'ṣ', 'D': 'ḍ',
    'T': 'ṭ', 'Z': 'ẓ', 'E': 'ʿ', 'g': 'ġ', 'f': 'f', 'q': 'q', 'k': 'k',
    'l': 'l', 'm': 'm', 'n': 'n', 'h': 'h', 'w': 'w', 'y': 'y', 'Y': 'y',
    'p': 't',
}


def _cognates(c, bw, cap=700):
    """Semitic cognate rows for this root, or None.

    Fed to the generator because the owner wants the sister languages to inform
    the prose. WITHOUT this the prompt still asked for a cognates sentence and
    supplied no evidence for it -- and the model duly invented one, citing
    "Hebrew zakar and Akkadian zikaru" for dh-k-r from its own memory. Asking
    for a station and providing nothing to fill it is an invitation to fabricate.
    """
    tr = "-".join(BW_TO_SR.get(ch, ch) for ch in bw)
    rows = c.execute("SELECT id, concept FROM semitic_roots WHERE transliteration=?", (tr,)).fetchall()
    if not rows:
        return None
    out = []
    for r in rows:
        ds = c.execute("SELECT language, COALESCE(meaning, concept) m FROM semitic_derivatives "
                       "WHERE root_id=? AND COALESCE(meaning, concept) IS NOT NULL "
                       "ORDER BY language LIMIT 12", (r['id'],)).fetchall()
        if r['concept']:
            out.append("  shared concept: %s" % r['concept'])
        out += ["    %-16s %s" % (d['language'], d['m']) for d in ds]
    txt = "\n".join(out).strip()
    return ("%s  (reconstructed root %s)\n%s" % (bw, tr, txt))[:cap] if txt else None


DICTS = [
    ('ibn-faris-maqayis-al-lugha',                      'Ibn Faris, Maqayis al-Lugha', 3000),
    ('al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran', 'al-Raghib, Mufradat',    1600),
    ('william-edward-lane-arabic-english-lexicon',       'Lane, Arabic-English Lexicon', 1600),
    ('al-zamakhshari-asas-al-balagha',                   'al-Zamakhshari, Asas al-Balagha', 1000),
    ('al-khalil-b-ahmad-al-farahidi-kitab-al-ain',       'al-Khalil, Kitab al-Ayn',     900),
    ('ibn-manzur-lisan-al-arab',                         'Ibn Manzur, Lisan al-Arab',  1200),
]
MAQAYIS = DICTS[0][0]
N_VERSES = 12
import os as _os
SHOW_EXISTING = _os.environ.get('SHOW_EXISTING', '1') == '1'


def _cap(s, n):
    s = (s or '').strip()
    return s if len(s) <= n else s[:n].rsplit(' ', 1)[0] + ' ...[truncated]'


def _verses(c, bw, lemmas=None):
    """A representative, DETERMINISTIC sample of the root's occurrences.

    Rule, in order:
      1. the FIRST occurrence (by chapter, verse) of each distinct lemma -- this
         guarantees every morphological shape the root takes is represented,
         which is what a claim about the root's core sense has to answer to;
      2. top up to N_VERSES by walking the remaining occurrences spread across
         DIFFERENT suras, so a root concentrated in one passage still shows its
         range;
      3. ties broken by (chapter, verse). No sampling, no randomness.
    """
    if lemmas:
        qs = ",".join("?" * len(lemmas))
        rows = c.execute(
            "SELECT DISTINCT m.chapter, m.verse, m.lemma_arabic lem FROM morphology m "
            "WHERE m.root_buckwalter=? AND m.lemma_arabic IN (%s) "
            "ORDER BY m.chapter, m.verse" % qs, (bw, *lemmas)).fetchall()
    else:
        rows = c.execute(
            "SELECT DISTINCT m.chapter, m.verse, m.lemma_arabic lem "
            "FROM morphology m WHERE m.root_buckwalter=? ORDER BY m.chapter, m.verse", (bw,)).fetchall()
    picked, seen_lemma, seen_sura = [], set(), set()
    for r in rows:                                   # pass 1: lemma coverage
        if r['lem'] and r['lem'] not in seen_lemma:
            seen_lemma.add(r['lem']); seen_sura.add(r['chapter'])
            picked.append((r['chapter'], r['verse']))
    for r in rows:                                   # pass 2: sura spread
        if len(picked) >= N_VERSES: break
        if (r['chapter'], r['verse']) in picked or r['chapter'] in seen_sura: continue
        seen_sura.add(r['chapter']); picked.append((r['chapter'], r['verse']))
    for r in rows:                                   # pass 3: fill
        if len(picked) >= N_VERSES: break
        if (r['chapter'], r['verse']) not in picked: picked.append((r['chapter'], r['verse']))
    picked = sorted(set(picked))[:N_VERSES]
    out = []
    for ch, v in picked:
        tr = c.execute("SELECT text_en FROM translations WHERE chapter=? AND verse=? LIMIT 1", (ch, v)).fetchone()
        forms = [x[0] for x in c.execute(
            "SELECT DISTINCT form_arabic FROM morphology WHERE chapter=? AND verse=? AND root_buckwalter=?",
            (ch, v, bw))]
        out.append("%d:%d  [%s]  %s" % (ch, v, ', '.join(f for f in forms if f),
                                        _cap(tr['text_en'] if tr else '', 240)))
    return out


def build(bw, conn=None, lemma_group=None):
    c = conn or sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    ar = (c.execute("SELECT root_arabic FROM morphology WHERE root_buckwalter=? AND root_arabic!='' LIMIT 1",
                    (bw,)).fetchone() or [''])[0]
    nverses = c.execute("SELECT COUNT(DISTINCT chapter||':'||verse) FROM morphology WHERE root_buckwalter=?",
                        (bw,)).fetchone()[0]
    lemmas = c.execute(
        "SELECT lemma_arabic lem, pos, COUNT(*) n FROM morphology WHERE root_buckwalter=? AND lemma_arabic!='' "
        "GROUP BY lem, pos ORDER BY n DESC LIMIT 14", (bw,)).fetchall()
    # WHERE THE WEIGHT ACTUALLY FALLS. A lexicon gives a root's senses equal
    # billing; the Qur'an does not. *hb is 46 verses of the VERB (going away)
    # against 8 of the noun (gold), yet an evenly-weighted passage opens with
    # gold -- and the reader who triggered the tooltip was looking at a verb.
    # This line makes the imbalance impossible for the generator to miss.
    top = lemmas[0] if lemmas else None
    weight = ""
    if top and nverses:
        weight = ("WHERE THE QUR'AN PUTS THE WEIGHT: the most frequent form is %s (%s, %d of %d "
                  "verses = %d%%). Your passage must be about what the root does in the Qur'an, "
                  "in that proportion -- not an even split across a lexicon's sense list."
                  % (top['lem'], top['pos'] or '?', top['n'], nverses, round(100 * top['n'] / nverses)))
    focus = ""
    if lemma_group:
        nf = c.execute(
            "SELECT COUNT(DISTINCT chapter||':'||verse) FROM morphology WHERE root_buckwalter=? "
            "AND lemma_arabic IN (%s)" % ",".join("?" * len(lemma_group)),
            (bw, *lemma_group)).fetchone()[0]
        focus = (
            "*** YOU ARE EXPLAINING ONE SENSE OF THIS ROOT, NOT THE WHOLE ROOT. ***\n"
            "These radicals carry more than one word. Write ONLY about the sense carried by\n"
            "these forms: %s  (%d verses).\n"
            "The Qur'anic occurrences listed below are only that sense's. Do not explain the\n"
            "root's other senses, do not mention them, and do not contrast them with this one.\n"
            "A reader who hovers one of these words wants this word explained.\n"
            % (", ".join(lemma_group), nf))
    parts = [
        focus,
        "ROOT: %s  (Buckwalter %s)" % (ar, bw),
        "Occurs in %d verses of the Qur'an." % nverses,
        weight,
        "",
        "LEMMAS (form, part of speech, occurrences):",
        "\n".join("  %s  %s  %dx" % (r['lem'], r['pos'] or '?', r['n']) for r in lemmas) or "  (none recorded)",
        "",
        "QUR'ANIC OCCURRENCES (representative sample; [] lists the actual forms used):",
        "\n".join("  " + v for v in _verses(c, bw, lemma_group)),
        "",
    ]
    have_maqayis = False
    for slug, label, cap in DICTS:
        r = c.execute("SELECT harmonized_en h FROM dictionary_entries WHERE root_buckwalter=? "
                      "AND dictionary_slug=? AND review_status='approved'", (bw, slug)).fetchone()
        if r and (r['h'] or '').strip():
            if slug == MAQAYIS: have_maqayis = True
            parts += ["%s:" % label.upper(), _cap(r['h'], cap), ""]
    if not have_maqayis:
        parts += ["IBN FARIS, MAQAYIS AL-LUGHA:",
                  "(NO ENTRY. This root is absent from Maqayis -- you have no ready-made "
                  "statement of a unifying sense and must reason from the other evidence, "
                  "or report that no unifying sense is evident.)", ""]
    # ai_root_meanings is deliberately NOT fed to the generator. It is our own
    # earlier, pre-doctrine summary, and it carries exactly the codified readings
    # this pipeline exists to avoid: its Slw row says "Prayer/worship ritual ... a
    # specific ritualized form of worship involving physical postures". Showing it
    # as a foil ("do not restate this") still puts the words in front of the model.
    # Only the SHORT gloss list goes in, as the bar to clear -- no prose framing.
    if not SHOW_EXISTING:
        pass
    else:
        arm = c.execute("SELECT primary_meaning p, detailed_meaning d, semantic_field s FROM ai_root_meanings "
                        "WHERE root_buckwalter=?", (bw,)).fetchone()
        if arm:
            parts += ["OUR SITE'S EXISTING ROOT SUMMARY (what the reader can already see -- your "
                      "passage must add something this does NOT say):",
                      "  primary: %s" % (arm['p'] or ''), "  semantic field: %s" % (arm['s'] or ''),
                      "  detailed: %s" % _cap(arm['d'], 900), ""]
    pl = c.execute("SELECT lexicon_markdown m FROM root_poetic_lexicon WHERE root_buckwalter=? "
                   "AND review_status='approved'", (bw,)).fetchone()
    if pl and (pl['m'] or '').strip():
        parts += ["PRE-ISLAMIC POETIC ATTESTATION (contemporaneous usage):", _cap(pl['m'], 1200), ""]
    cog = _cognates(c, bw)
    if cog:
        parts += ["SISTER LANGUAGES (Semitic cognates recorded for these radicals). Use ONLY what "
                  "is listed here; if a language is not named below you have no evidence for it:",
                  cog, ""]
    else:
        parts += ["SISTER LANGUAGES: no cognate rows exist for these radicals. Say NOTHING about "
                  "other Semitic languages -- you have no evidence, and naming one would be "
                  "invention.", ""]
    return {"root_bw": bw, "root_ar": ar, "n_verses": nverses, "has_cognates": bool(cog),
            "has_maqayis": have_maqayis, "text": "\n".join(parts)}


if __name__ == '__main__':
    import sys
    for bw in (sys.argv[1:] or ['*hb']):
        b = build(bw)
        print("=" * 70)
        print("%s (%s)  maqayis=%s  bundle=%d chars (~%d tokens)"
              % (bw, b['root_ar'], b['has_maqayis'], len(b['text']), len(b['text']) // 4))
