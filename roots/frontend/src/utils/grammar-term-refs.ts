/**
 * Detects and links references to specific grammar-glossary terms inside
 * Translation Notes prose (e.g. "...causative form IV (أَغْنَىٰ)...").
 *
 * Translation Notes are free-form AI prose with no [[term]] markers (unlike
 * the dedicated Grammar Notes pipeline), so terms are found by scanning for
 * a curated allowlist of glossary entries — not the full ~600-term glossary,
 * which is dominated by generic English words (root, verb, noun, object,
 * person, case, aspect, emphasis, ...) that read fine unglossed and would
 * otherwise get tooltipped on every incidental appearance. This list was
 * built by sampling ~80 real translation-notes entries and keeping only the
 * terms that (a) actually occur and/or (b) are unambiguous, specialized
 * grammar jargon (Arabic-transliterated particles, verb-form numerals, case
 * names) with no everyday-English reading to collide with.
 */
export const GRAMMAR_TERM_ALLOWLIST: string[] = [
  // Verb forms (I–X) — the paradigm case: opaque without a gloss.
  'form i', 'form ii', 'form ii passive', 'form ii verb',
  'form iii', 'form iii verb',
  'form iv', 'form iv causative', 'form iv verb',
  'form v', "form v (tafa'ala)", 'form v verb',
  'form vi', 'form vii',
  'form viii', 'form viii verb',
  'form ix',
  'form x', 'form x (istafʿala)', 'form x verb',
  'verb form ii', 'verb form iii', 'verb form iv', 'verb form v',
  'verb form vi', 'verb form vii', 'verb form viii', 'verb form x',

  // Voice, mood, case — specialized grammatical vocabulary.
  'passive voice', 'active voice', 'jussive', 'subjunctive',
  'accusative', 'accusative case', 'genitive', 'vocative',
  'elative', 'elative noun', 'superlative', 'comparative form',

  // Verb-form semantic categories.
  'causative', 'causative form', 'causative verb', 'causative verb form',
  'reflexive', 'reflexive verb form', 'reciprocal', 'reciprocity',
  'intensive', 'intensive form', 'intensive verb',
  'prohibition', 'prohibitive lā', 'imperative', 'negative imperative',
  'dual', 'dual form', 'dual imperative',

  // Syntax roles specific enough to be unambiguous.
  'object pronoun', 'direct object', 'double object',
  'verbal noun', 'active participle', 'passive participle',
  'circumstantial', 'circumstantial accusative', 'circumstantial qualifier',
  'circumstantial clause', 'cognate accusative', 'construct phrase',
  'idāfa', 'conditional particle', 'emphatic negation',
  'exception particle', 'vocative particle', 'oath particle',
  'conditional sentence', 'nominal sentence', 'verbal sentence',
  'broken plural', "person shift (iltifāt)",

  // Arabic-transliterated particles/structures — no everyday-English
  // reading to collide with.
  'mubtada', 'khabar', 'hal', 'halah', 'idha', 'iltifat',
  'tanwīn', 'waw', 'kāna', 'kāna and its sisters',
  'inna', 'inna particle', 'sisters of inna', 'anna',
  'laysa', 'lawla', 'hasr', 'qad', 'thumma', 'sīn', 'sawfa',
  'lā', 'lā al-nāfiya li-l-jins',
];

/**
 * Spellings that mean a glossary term but aren't how the glossary spells it.
 * Transliteration is not standardized, and free prose (above all Ask-the-Quran
 * answers, which are written fresh each time rather than by a fixed pipeline)
 * reaches for whichever form its author favours: "iḍāfa" for the glossary's
 * "idāfa", "mubtadaʾ" for "mubtada". Without these, the terms most likely to
 * need a gloss are exactly the ones that silently miss.
 *
 * variant (lowercase) -> the allowlisted term it resolves to. Only variants
 * actually observed in real prose are listed; a variant whose target isn't in
 * the glossary simply never resolves, same as any other unmatched term.
 */
const GRAMMAR_TERM_ALIASES: Record<string, string> = {
  'iḍāfa': 'idāfa', 'iḍāfah': 'idāfa', 'idāfah': 'idāfa', 'idafa': 'idāfa',
  'mubtadaʾ': 'mubtada', 'mubtadaʼ': 'mubtada', "mubtada'": 'mubtada',
  'iltifāt': 'iltifat',
  'tanwin': 'tanwīn', 'tanween': 'tanwīn',
  'ḥāl': 'hal', 'ḥālah': 'halah',
};

const ALLOWLIST_SET = new Set(GRAMMAR_TERM_ALLOWLIST);

// Longest-first so e.g. "form iv causative" is tried before bare "form iv".
const SORTED_TERMS = [...GRAMMAR_TERM_ALLOWLIST, ...Object.keys(GRAMMAR_TERM_ALIASES)].sort(
  (a, b) => b.length - a.length,
);

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// One alternation of all curated terms, longest-first, wrapped in Unicode-
// aware boundary lookarounds — plain \b doesn't recognize word edges next to
// macron'd transliteration letters (ā, ī, ū, ʿ, ʾ, …), so this uses \p{L}
// instead (requires the "u" flag).
const MATCH_RE = new RegExp(
  `(?<![\\p{L}])(${SORTED_TERMS.map(escapeRegExp).join('|')})(?![\\p{L}])`,
  'giu',
);

/** Cheap pre-check so callers can skip fetching the glossary entirely for
 * the (majority of) verses whose translation notes mention no grammar term. */
export function mentionsGrammarTerm(text: string): boolean {
  MATCH_RE.lastIndex = 0;
  return MATCH_RE.test(text);
}

// Letters and clitics that transliterated Arabic carries and English prose
// never does: long vowels, dotted and emphatic consonants, ʿayn and hamza in
// their several encodings, and a hyphenated proclitic (wa-, fa-, l-, al-, …).
const TRANSLIT_MARK =
  /[āīūḥṣḍṭẓḏṯġšǧḫẖʿʾʼʻ]|(?<![\p{L}])(?:wa|fa|bi|li|la|ka|al|l|a)-\p{L}/iu;

// The same tokens renderInline splits on (FormattedText.tsx), so both agree on
// what an italic run is: existing markers first, then **bold**, then *italic*.
const INLINE_TOKEN = /(\[\[[^\]]*\]\]|\*\*[^*]+\*\*|\*[^*\n]+\*)/g;

function wrapTerms(text: string): string {
  return text.replace(MATCH_RE, (m) => `[[gt|${m}]]`);
}

/** Is this italic run a transliterated quotation, rather than prose that
 *  names a grammar term? The notes cite the Arabic as *inna l-ḥasanāti
 *  yudhhibna l-sayyiʾāt*, and a particle inside a quotation is part of the
 *  quotation, not a reference to the glossary. A run that is nothing BUT the
 *  term (*kāna*, *lā*) stays linkable: that is the prose naming the particle
 *  ("the predicate of *kāna*", "negated by *lā*"). English grammar talk in
 *  italics (*intensive Form II*) carries no transliteration marks, so it keeps
 *  its chips too. */
function isTransliteratedQuotation(inner: string): boolean {
  const run = inner.trim();
  MATCH_RE.lastIndex = 0;
  const whole = MATCH_RE.exec(run);
  MATCH_RE.lastIndex = 0;
  if (whole && whole.index === 0 && whole[0].length === run.length) return false;
  return TRANSLIT_MARK.test(run);
}

/** Wrap each curated-term occurrence in raw prose with the [[gt|...]] marker
 * FormattedText/renderInline understand (see FormattedText.tsx).
 * Case-insensitive; preserves the original casing found in the text.
 *
 * Quotations are left alone. Before this, the linker ran over the whole
 * string and wrapped the inna in *inna l-ḥasanāti yudhhibna l-sayyiʾāt*, which
 * both put a glossary chip on a word of scripture and broke the run's exact
 * match against the verse-word anchor, so the citation lost its link to the
 * words it quotes. That hit ~2,900 quotations across the exegesis notes. */
export function linkifyGrammarTermRefs(text: string): string {
  return text
    .split(INLINE_TOKEN)
    .map((part) => {
      if (part.startsWith('[[')) return part; // another marker's own text
      if (part.length > 4 && part.startsWith('**') && part.endsWith('**')) {
        return `**${wrapTerms(part.slice(2, -2))}**`;
      }
      if (part.length > 2 && part.startsWith('*') && part.endsWith('*')) {
        const inner = part.slice(1, -1);
        return isTransliteratedQuotation(inner) ? part : `*${wrapTerms(inner)}*`;
      }
      return wrapTerms(part);
    })
    .join('');
}

/** Build a lowercased lookup (term_english.toLowerCase() -> term) from a
 * fetched glossary, restricted to the curated allowlist — so even if the
 * bulk glossary fetch succeeds, only terms this module actually scans for
 * can ever resolve to a chip. */
export function buildGrammarTermLookup<T extends { term_english: string }>(
  allTerms: T[],
): Record<string, T> {
  const out: Record<string, T> = {};
  for (const t of allTerms) {
    const key = t.term_english.toLowerCase();
    if (ALLOWLIST_SET.has(key)) out[key] = t;
  }
  // Variant spellings resolve to the same term. Keyed by the variant, since
  // lookups are done on the text as written ("iḍāfa"), not on the glossary's
  // own spelling. A variant never shadows a real term of its own name.
  for (const [variant, canonical] of Object.entries(GRAMMAR_TERM_ALIASES)) {
    const term = out[canonical];
    if (term && !out[variant]) out[variant] = term;
  }
  return out;
}
