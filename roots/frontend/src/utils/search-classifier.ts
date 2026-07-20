/**
 * Classify user input into a SEARCH PLAN for the unified search bar.
 *
 * The plan decides which result categories fire and which one leads the
 * dropdown — never what is *forbidden*. Root search always runs for text
 * (the backend resolves English meanings + Arabic + transliteration), and
 * semantic (by-meaning) search fires for anything that reads like a concept
 * word or phrase, not just long multi-word English.
 *
 * Phase A note: Arabic queries fan out to ROOT only. Semantic search for
 * Arabic is held for Phase B, when a multilingual (Arabic-aware) embedding
 * index exists — today's index is over English translations only, so an
 * Arabic query embedded against it returns noise.
 */

export interface ParsedVerseRef {
  surah: number;
  ayah: number;
  partial: boolean; // true if user typed "2:" (no ayah yet)
}

/** Which result categories the plan fires (surah-name match runs
 *  unconditionally in the hook and isn't gated here). */
export interface SearchPlan {
  /** Non-null when the input parses as a verse reference. */
  verseRef: ParsedVerseRef | null;
  fire: { root: boolean; semantic: boolean };
  /** Which of root vs semantic leads the dropdown (after verse-ref/surahs). */
  lead: 'root' | 'semantic';
  script: 'empty' | 'digits' | 'arabic' | 'latin' | 'mixed';
  /** Debounce (ms) for the semantic request — longer for likely-transliteration. */
  semanticDebounce: number;
  /** Reads like a natural-language question (drives an Ask-the-Qur'an handoff). */
  looksLikeQuestion: boolean;
}

const VERSE_REF_RE = /^\d{1,3}(?::(\d{0,3}))?$/;
const ARABIC_RE = /[؀-ۿ]/;
const LATIN_RE = /[a-zA-Z]/;
// Buckwalter uses ASCII letters plus these special chars.
const BUCKWALTER_SPECIAL_RE = /[$<>{}'~&*]/;
const VOWEL_RE = /[aeiouAEIOU]/;
// Arabic combining marks + tatweel — stripped for length checks.
const AR_MARKS_RE = /[ً-ْٰـ]/g;

const EN_QUESTION_RE =
  /^(why|how|whats?|when|whos?|whom|where|which|did|does|do|is|are|was|were|can|could|should|would|will)\b/i;
const AR_QUESTION_RE = /^(لماذا|كيف|ماذا|ما|من|هل|متى|أين|أي)\b/;

const SEMANTIC_DEBOUNCE = 400;
const SEMANTIC_DEBOUNCE_SLOW = 600; // likely-transliteration / mid-typing shapes

const EMPTY_PLAN: SearchPlan = {
  verseRef: null,
  fire: { root: false, semantic: false },
  lead: 'root',
  script: 'empty',
  semanticDebounce: SEMANTIC_DEBOUNCE,
  looksLikeQuestion: false,
};

/**
 * Try to parse a verse reference from the input.
 * Returns null if not a verse reference pattern.
 */
export function parseVerseRef(input: string): ParsedVerseRef | null {
  const trimmed = input.trim();
  const m = trimmed.match(VERSE_REF_RE);
  if (!m) return null;
  const surah = parseInt(trimmed.split(':')[0], 10);
  if (surah < 1 || surah > 114) return null;
  const ayahStr = m[1];
  if (ayahStr === undefined) {
    // Just a number like "36" — treat as surah:1
    return { surah, ayah: 1, partial: false };
  }
  if (ayahStr === '') {
    // "2:" — partial, waiting for ayah
    return { surah, ayah: 1, partial: true };
  }
  const ayah = parseInt(ayahStr, 10);
  if (ayah < 1) return null;
  return { surah, ayah, partial: false };
}

function looksLikeQuestion(trimmed: string): boolean {
  return (
    /[?؟]\s*$/.test(trimmed) ||
    EN_QUESTION_RE.test(trimmed) ||
    AR_QUESTION_RE.test(trimmed)
  );
}

/**
 * Classify the input into a fan-out plan.
 */
export function classifyInput(input: string): SearchPlan {
  const trimmed = input.trim();
  if (!trimmed) return EMPTY_PLAN;

  const question = looksLikeQuestion(trimmed);

  // 1. Verse reference — the ref preview owns it; nothing else fires.
  const verseRef = parseVerseRef(trimmed);
  if (verseRef) {
    return { ...EMPTY_PLAN, verseRef, script: 'digits', looksLikeQuestion: question };
  }

  const hasArabic = ARABIC_RE.test(trimmed);
  const hasLatin = LATIN_RE.test(trimmed);
  const wordCount = trimmed.split(/\s+/).filter(Boolean).length;

  // 2. Arabic (or Arabic+Latin) → ROOT only for Phase A. Semantic held for Phase B.
  if (hasArabic) {
    const arabicLen = trimmed.replace(AR_MARKS_RE, '').length;
    return {
      ...EMPTY_PLAN,
      script: hasLatin ? 'mixed' : 'arabic',
      fire: { root: arabicLen >= 2, semantic: false },
      lead: 'root',
      looksLikeQuestion: question,
    };
  }

  // 3. Latin-only.
  const len = trimmed.length;

  // Single very short token (≤2) → root only (autocomplete-ish).
  if (wordCount === 1 && len <= 2) {
    return {
      ...EMPTY_PLAN,
      script: 'latin',
      fire: { root: true, semantic: false },
      lead: 'root',
      looksLikeQuestion: question,
    };
  }

  // Single 3–4 char token: fire semantic only if it reads like a real word
  // (has a vowel, no Buckwalter specials) — otherwise it's a transliterated
  // root attempt and semantic over the English index would be noise.
  if (wordCount === 1 && len <= 4) {
    const buckwalterish = BUCKWALTER_SPECIAL_RE.test(trimmed) || !VOWEL_RE.test(trimmed);
    return {
      ...EMPTY_PLAN,
      script: 'latin',
      fire: { root: true, semantic: !buckwalterish },
      lead: buckwalterish ? 'root' : 'semantic',
      semanticDebounce: SEMANTIC_DEBOUNCE_SLOW,
      looksLikeQuestion: question,
    };
  }

  // Single word ≥5 chars ("mercy", "patience"), or any multi-word English
  // phrase → root + semantic, semantic leads. This is the headline fix:
  // single-word concepts now reach by-meaning search.
  return {
    ...EMPTY_PLAN,
    script: 'latin',
    fire: { root: true, semantic: true },
    lead: 'semantic',
    semanticDebounce: SEMANTIC_DEBOUNCE,
    looksLikeQuestion: question,
  };
}
