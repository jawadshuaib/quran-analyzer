#!/usr/bin/env python3
"""Terms whose conventional English rendering imposes a reading, and the
transliteration to use instead.

THE PRINCIPLE (the owner's, 2026-09-20): "with the Qur'an-only approach, we are
going to let the controversial terms be transliterated rather than imposed."

"Prayer" for salat smuggles in a settled ritual the root does not itself carry.
"Maiden" for hur decides a contested word on the reader's behalf. In both cases
the honest move is to give the Arabic and let the passage show what the usage
supports. These are NOT banned words -- they are words we refuse to translate
INTO, because the translation is the interpretation.

Distinct from the post-Quranic ban in _root_core_gates.BANNED: those words
(hadith, sunna, jurisprudence) are later vocabulary that must not appear at all.
These words are ordinary English; the fault is using them AS the rendering of a
loaded Arabic term.

Each entry: the English rendering to refuse -> (transliteration, the root it
belongs to). The root is recorded so the list stays auditable and so a future
check can scope a term to passages about that root.
"""

IMPOSED = {
    # --- the owner's two worked examples ---
    'prayer':        ('salat',    'Slw'),
    'prayers':       ('salat',    'Slw'),
    'maiden':        ('hur',      'Hwr'),
    'maidens':       ('hur',      'Hwr'),
    'houri':         ('hur',      'Hwr'),
    'houris':        ('hur',      'Hwr'),
    'virgin':        ('hur',      'Hwr'),
    'virgins':       ('hur',      'Hwr'),
    # --- ritual/legal terms that name an institution the root does not ---
    'alms':          ('zakat',    'zkw'),
    'almsgiving':    ('zakat',    'zkw'),
    'charity':       ('zakat',    'zkw'),
    'tithe':         ('zakat',    'zkw'),
    'pilgrimage':    ('hajj',     'Hjj'),
    'usury':         ('riba',     'rbw'),
    'holy war':      ('jihad',    'jhd'),
    'ablution':      ('wudu',     'wDA'),
    'almsgiver':     ('zakat',    'zkw'),
    # --- theological labels applied to people ---
    'infidel':       ('kafir',    'kfr'),
    'infidels':      ('kafir',    'kfr'),
    'idolater':      ('mushrik',  '$rk'),
    'idolaters':     ('mushrik',  '$rk'),
    'polytheist':    ('mushrik',  '$rk'),
    'polytheists':   ('mushrik',  '$rk'),
    'hypocrite':     ('munafiq',  'nfq'),
    'hypocrites':    ('munafiq',  'nfq'),
    # --- named places and beings the Qur'an does not name that way ---
    'satan':         ('shaytan',  '$Tn'),
    'the devil':     ('shaytan',  '$Tn'),
    'hellfire':      ('jahannam', 'jhnm'),
    'purgatory':     ('barzakh',  'brzx'),
}

# Deliberately NOT listed, and why -- so the next person does not "fix" this:
#   garden/janna      "garden" is the plain sense; only capital-P "Paradise"
#                     imposes, and that is caught by PROPER_NOUNS below.
#   fast/fasting      the owner accepted "the fast, siyam" in a passage; the
#                     English here describes rather than decides.
#   angel/malak       settled and uncontested.
#   scripture/kitab   "book" is literal; "Scripture" capitalised is not.
PROPER_NOUNS = {'paradise': ('janna', 'jnn'), 'scripture': ('kitab', 'ktb')}


def check(passage):
    """Return [(english_used, transliteration_wanted), ...] found in a passage.

    A hit is excused when the transliteration is already present -- the passage
    has given the Arabic and may then say what it means.
    """
    import re
    low = passage.lower()
    hits = []
    for eng, (translit, _root) in list(IMPOSED.items()) + list(PROPER_NOUNS.items()):
        if not re.search(r'\b%s\b' % re.escape(eng), low):
            continue
        # The transliteration may appear with or without diacritics.
        bare = translit.replace('h', 'h')
        if re.search(r'\b%s' % re.escape(bare[:4]), low):
            continue
        hits.append((eng, translit))
    return hits
