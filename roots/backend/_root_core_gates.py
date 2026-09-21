#!/usr/bin/env python3
"""Deterministic gates on a generated root core-meaning passage.

The lesson this project has learned five separate times: a verifier's raw flags
are HYPOTHESES, not verdicts. So every check here is arithmetic or lookup --
nothing that needs judgement -- and a fired gate routes the row to a human
queue, it does not silently rewrite or delete.

  G1  passage longer than the tooltip can hold            (hard)
  G2  post-Quranic vocabulary in our own assertive voice   (hard, use-mention exempt)
  G3  a cited verse does not exist, or does not contain    (hard)
      the root the passage is about
  G4  the verdict contradicts Ibn Faris's own stated       (soft - a real
      structure for this root                               disagreement may be right)
  G5  the passage only restates the glosses the reader      (soft - the
      already sees                                           usefulness bar)
  G6  Arabic script in a passage we asked to transliterate  (hard)
  G7  verdict/passage disagree (no_insight with text, or    (hard)
      a verdict with an empty passage)
"""
import difflib
import json
import os
import re
import sqlite3
import sys

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'quran.db')
# Single source of truth: the prompt sets the budget, the gate enforces the same
# number. These drifted apart once already (gate 260 vs prompt 400) and every
# passage failed a limit no longer in force.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _root_core_prompt as _P  # noqa: E402
import _root_core_terms as _T  # noqa: E402
MAX_CHARS = _P.MAX_CHARS

# Terms that must not appear in OUR assertive voice. Mirrors the project's
# established lists (qa_gen.BANNED_TERMS / _terminology_fix.py), including the
# owner's ruling that Islam renders as "submission".
BANNED = re.compile(
    r'\b(islam|islamic|muslims?|hadith|sunnah|sharia|shariah|fiqh|jurisprudence|'
    r'halal|haram|madhhab|caliph|imam|mosque|ulama|tafsir)\b', re.I)
# Use-mention exemption: a passage may NAME a later term in order to EXCLUDE it,
# and that sentence is the insight, not the violation ("this is not ritual
# prayer", "the root does not mean jurisprudence"). Only sentences that deny or
# distance are spared -- an assertive use is still a violation.
META = re.compile(r'\b(not|never|no|nor|rather than|unlike|before|pre-|later|'
                  r'only later|does not|isn\'t|is not)\b', re.I)
ARABIC = re.compile(r'[؀-ۿݐ-ݿ]')
VERSE_REF = re.compile(r'\b(\d{1,3}):(\d{1,3})\b')
# Words a vacuous unity hides behind, and the concrete vocabulary a real one uses.
CEILING = re.compile(r'\b(transfer|movement|moving|change|changing|process|state|'
                     r'condition|notion|concept|idea of|quality|aspect|action|'
                     r'relation|separation|connection|intensity)\b', re.I)
FILLER = set("""this that these those there here what which when where while with
from into onto upon over under about above after before between through during
root roots word words means meaning sense senses said says same also then than
thus hence only just even both each every some most more less much many other
another thing things something anything such very often always never still yet
gives give given takes taken comes come used uses using itself their them they
have having been being does doing done will would could should must may might
name names named call called calls idea image picture note notes
""".split())
# The owner's first complaint: "I don't like it when it sounds AI generated".
# That fault was measurable -- across 36 v1 passages, 12 opened with one of two
# identical sentences. Two gates follow: G9 bans the formulas outright, and the
# corpus-level duplicate_openers() catches any NEW formula the model settles
# into, which a fixed banned-list never could.
FORMULA = re.compile(
    r'^\s*(two unrelated roots share|one idea\b|one image\b|one act\b|one sense\b|'
    r'one word for|at its core|the root conveys|this root (?:means|exhibits|carries))'
    r'|\b(gives all the senses|one idea throughout|the kernel is|that one (?:posture|image|sense)'
    r'|this root exhibits|gives us all)\b', re.I)
# Sentences about the analysis instead of the thing.
META_TALK = re.compile(r'\b(the (?:core|central|underlying) (?:notion|idea|sense) (?:here )?is'
                       r'|what unites (?:them|these)|all of these (?:share|go back)'
                       r'|taken together,? (?:they|these))\b', re.I)
# Languages a passage might name. If one appears that our own cognate rows do
# not record for this root, the model reached outside the evidence -- which is
# how "Hebrew zakar and Akkadian zikaru" got into a dh-k-r passage that was
# shown no cognate data at all.
LANGUAGES = re.compile(r'\b(Hebrew|Aramaic|Syriac|Akkadian|Ugaritic|Phoenician|Ge\'?ez|'
                       r'Geez|Ethiopic|Sabaic|Sabaean|Hadramitic|Minaic|Qatabanic|Amorite|'
                       r'Dadanitic|Safaitic|Nabataean|Palmyrene|Punic|Assyrian|Babylonian|'
                       r'Proto-Semitic|Semitic)\b', re.I)
TACK_ON = re.compile(r'(?:the (?:same )?letters|this root|it) also (?:name|mean|carr)\w*[^.]*\.\s*$'
                     r'|\(\s*(?:gold|and)?[^)]{0,40}unrelated[^)]*\)\s*$', re.I)
CONCRETE = re.compile(r'\b(hand|eye|neck|foot|water|rain|sand|dust|camel|horse|rope|'
                      r'cloth|garment|door|road|path|tree|fire|blood|bone|skin|milk|'
                      r'sun|moon|night|earth|ground|stone|iron|gold|split|cut|pour|'
                      r'tie|bind|stretch|press|rub|strike|dig|carry|lift|halt|stand|'
                      r'edge|rim|surface|hollow|thread|grain|seed|root|branch)\b', re.I)

MULTI_ORIGIN = re.compile(
    r'\b(?:two|three|four)\b[^.]{0,60}\b(?:distinct|separate|unrelated|sound)?\s*'
    r'\b(?:roots|origins|base[- ]meanings|words|senses|principles)\b'
    r'|\bderives?\b[^.]{0,50}\bfrom (?:two|three|four)\b'
    r'|\bplus one further, separate root\b|\banother,? (?:separate|unrelated) root\b', re.I)
SINGLE_ORIGIN = re.compile(r'\b(?:a single|one) (?:sound )?(?:root|meaning|core|idea|base)\b'
                           r'|\bnothing but this one meaning\b|\bsingle sound root\b', re.I)


def _sentences(text):
    return [s for s in re.split(r'(?<=[.;!?])\s+', text or '') if s.strip()]


def check(row, conn=None):
    """row: dict with root_bw, verdict, passage, verses_relied_on.
    Returns a list of (gate, severity, message)."""
    c = conn or sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    bw = row['root_bw']
    passage = (row.get('passage') or '').strip()
    verdict = row.get('verdict')
    out = []

    if verdict == 'no_insight':
        if passage:
            out.append(('G7', 'hard', 'verdict=no_insight but passage is not empty'))
        return out                      # nothing else applies to a declined root
    if not passage:
        out.append(('G7', 'hard', 'verdict=%s but passage is empty' % verdict))
        return out

    if len(passage) > MAX_CHARS:
        out.append(('G1', 'hard', 'passage is %d chars, tooltip holds %d' % (len(passage), MAX_CHARS)))

    for s in _sentences(passage):
        m = BANNED.search(s)
        if m and not META.search(s):
            out.append(('G2', 'hard', 'post-Quranic term %r asserted in our own voice: %r'
                        % (m.group(0), s[:90])))

    if ARABIC.search(passage):
        out.append(('G6', 'hard', 'Arabic script in a passage specified as transliteration only'))

    refs = set(row.get('verses_relied_on') or []) | {'%s:%s' % m for m in VERSE_REF.findall(passage)}
    for ref in sorted(refs):
        try:
            ch, v = (int(x) for x in ref.split(':'))
        except ValueError:
            continue
        if not c.execute("SELECT 1 FROM verses WHERE chapter=? AND verse=?", (ch, v)).fetchone():
            out.append(('G3', 'hard', 'cited verse %s does not exist' % ref)); continue
        if not c.execute("SELECT 1 FROM morphology WHERE chapter=? AND verse=? AND root_buckwalter=?",
                         (ch, v, bw)).fetchone():
            out.append(('G3', 'hard', 'cited verse %s does not contain the root %s' % (ref, bw)))

    mq = c.execute("SELECT harmonized_en h FROM dictionary_entries WHERE root_buckwalter=? AND "
                   "dictionary_slug='ibn-faris-maqayis-al-lugha' AND review_status='approved'",
                   (bw,)).fetchone()
    if mq and (mq['h'] or ''):
        head = mq['h'][:400]
        ibn = 'multi' if MULTI_ORIGIN.search(head) else ('single' if SINGLE_ORIGIN.search(head) else None)
        if ibn == 'multi' and verdict == 'unified':
            out.append(('G4', 'soft', 'Ibn Faris states multiple origins; passage claims one unified sense'))
        elif ibn == 'single' and verdict == 'two_origins':
            out.append(('G4', 'soft', 'Ibn Faris states a single root; passage splits it into two'))

    glosses = {g[0].lower().strip() for g in c.execute(
        "SELECT DISTINCT g.translation_en FROM morphology m JOIN word_glosses g "
        "ON g.chapter=m.chapter AND g.verse=m.verse AND g.word_pos=m.word_pos "
        "WHERE m.root_buckwalter=? AND g.translation_en IS NOT NULL", (bw,)) if g[0]}
    # Filler must not count as novelty: "this root means to go, to depart" is a
    # pure restatement, but words like this/root/means/also are absent from the
    # gloss list and were inflating the novelty score past the threshold.
    words = set(re.findall(r"[a-z']{4,}", passage.lower())) - FILLER
    if words:
        gloss_words = {w for g in glosses for w in re.findall(r"[a-z']{4,}", g)} - FILLER
        novel = words - gloss_words
        if len(novel) / len(words) < 0.35:
            out.append(('G5', 'soft', 'only %d%% of the passage is vocabulary the glosses do not '
                        'already use - may be restating what the reader sees'
                        % round(100 * len(novel) / len(words))))
        # Sequence similarity, not just vocabulary overlap: a passage can use new
        # words and still track the gloss list phrase for phrase.
        ratio = difflib.SequenceMatcher(
            None, ' '.join(sorted(gloss_words)), ' '.join(sorted(words))).ratio()
        if ratio >= 0.55:
            out.append(('G5b', 'soft', 'passage is %.0f%% similar to the gloss list the reader '
                                       'already sees' % (100 * ratio)))

    # G9 -- formula and meta-commentary. The reader meets many tooltips; a
    # repeated opener is exactly what reads as machine-written.
    if FORMULA.search(passage):
        out.append(('G9', 'hard', 'stock opener or meta-commentary formula: %r'
                    % FORMULA.search(passage).group(0)[:50]))
    if META_TALK.search(passage):
        out.append(('G9', 'soft', 'sentence is about the analysis rather than the sense'))

    # G10 -- the landing. The arc requires the passage to end on a verse where
    # the physical sense does work. The accepted sawm passage lands on 19:26;
    # the two rejected ones never reached a verse at all.
    if not VERSE_REF.search(passage):
        out.append(('G10', 'hard', 'passage never lands on a verse - a dictionary '
                                   'entry, not a reading aid'))
    payoff = (row.get('payoff_verse') or '').strip()
    if payoff:
        if payoff not in passage:
            out.append(('G10', 'soft', 'declared payoff verse %s is not the verse the passage '
                                       'ends on' % payoff))
    # G11 -- a secondary sense dumped in the final sentence. The owner rejected
    # exactly this ("I don't know why you keep focusing so much on gold"), and it
    # came back on its own for *kr ("The letters also name a male"). It kills the
    # passage: the reader's last impression should be the payoff, not a footnote
    # about a sense they were not asking about.
    if TACK_ON.search(passage):
        out.append(('G11', 'hard', 'ends on a secondary-sense footnote instead of the payoff'))

    # G12 -- a sister language named without evidence.
    named = {m.group(0).lower() for m in LANGUAGES.finditer(passage)}
    if named:
        try:
            import _root_core_bundle as _B
            tr = "-".join(_B.BW_TO_SR.get(ch, ch) for ch in bw)
            have = {r[0].lower() for r in c.execute(
                "SELECT DISTINCT d.language FROM semitic_derivatives d "
                "JOIN semitic_roots s ON s.id=d.root_id WHERE s.transliteration=?", (tr,))}
        except Exception:
            have = set()
        have.add('semitic')          # the generic term needs no row of its own
        unsourced = {n for n in named if not any(n in h or h in n for h in have)}
        if unsourced:
            out.append(('G12', 'hard', 'names %s with no cognate row for this root'
                        % ', '.join(sorted(unsourced))))
        # Naming a real language is not enough: the MEANING attached to it must
        # be the one we actually recorded. For dh-k-r the model wrote "Hebrew
        # zakar and Akkadian zikaru mean the same" in a passage about males,
        # while our rows give both languages the REMEMBER sense and put the ram
        # in Aramaic and Ugaritic. Language right, gloss wrong -- invisible to a
        # presence check.
        try:
            import _root_core_bundle as _B2
            tr2 = "-".join(_B2.BW_TO_SR.get(ch, ch) for ch in bw)
            pwords = {w[:5] for w in re.findall(r"[a-z]{3,}", passage.lower())}
            for lang in named - unsourced:
                gl = [r[0] for r in c.execute(
                    "SELECT COALESCE(d.meaning, d.concept) FROM semitic_derivatives d "
                    "JOIN semitic_roots s ON s.id=d.root_id "
                    "WHERE s.transliteration=? AND LOWER(d.language) LIKE ?",
                    (tr2, '%' + lang + '%')) if r[0]]
                if not gl:
                    continue
                stems = {w[:5] for g in gl for w in re.findall(r"[a-z]{3,}", g.lower())}
                if stems and not (stems & pwords):
                    out.append(('G12', 'hard',
                                '%s is recorded for this root as %r, which the passage does '
                                'not say' % (lang, '; '.join(gl)[:60])))
        except Exception:
            pass

    # G13 -- a contested term rendered into English instead of transliterated.
    # Qur'an-only means we do not decide salat is "prayer" or hur is "maiden" on
    # the reader's behalf; we give the Arabic and let the usage show the sense.
    for eng, translit in _T.check(passage):
        out.append(('G13', 'hard', 'renders a contested term as %r - give %s and let the '
                                   'passage show what it means' % (eng, translit)))

    # The abstraction ceiling: every pair of senses unifies if you climb high
    # enough ("both involve transfer/movement/change"). A unifying claim made
    # ONLY in these words is a vacuous one, and it is the exact shape fabricated
    # unity takes -- fluent, unfalsifiable, and true of half the lexicon.
    if verdict == 'unified':
        core = (row.get('core_sense') or '') + ' ' + passage
        if CEILING.search(core) and not CONCRETE.search(core):
            out.append(('G8', 'soft', 'unifying sense stated only in abstract terms with no '
                                      'concrete image - possible vacuous unity'))
    return out


def duplicate_openers(passages, cap=1):
    """Corpus-level check: which first sentences does the model reuse across
    roots? A banned-phrase list only catches formulas we already know about;
    this catches the next one the model settles into. passages: {root: text}."""
    import collections
    first = collections.defaultdict(list)
    for bw, p in passages.items():
        if not (p or '').strip():
            continue
        s0 = re.split(r'(?<=[.:;])\s', p.strip())[0]
        key = re.sub(r'[^a-z ]', '', s0.lower())[:40].strip()
        first[key].append(bw)
    return {k: v for k, v in first.items() if len(v) > cap}


if __name__ == '__main__':
    data = json.load(open(sys.argv[1]))
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    hard = soft = clean = 0
    for bw, r in (data.get('results') or {}).items():
        if not r.get('ok'):
            print("  %-6s RUN-ERROR %s" % (bw, r.get('error', '')[:70])); continue
        flags = check({**r, 'root_bw': bw}, c)
        h = [f for f in flags if f[1] == 'hard']; s = [f for f in flags if f[1] == 'soft']
        hard += len(h); soft += len(s); clean += (not flags)
        if flags:
            print("  %-6s %-11s %s" % (bw, r.get('verdict'), '; '.join('%s/%s %s' % f for f in flags)[:160]))
    print("\n  clean: %d | hard flags: %d | soft flags: %d" % (clean, hard, soft))
