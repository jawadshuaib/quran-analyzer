/**
 * Classify user input into a SEARCH PLAN for the unified search bar.
 *
 * The plan decides which result categories fire and which one leads the
 * dropdown — never what is *forbidden*. Root search always runs for text
 * (the backend resolves English meanings + Arabic + transliteration), and
 * semantic (by-meaning) search fires for anything that reads like a concept
 * word or phrase, not just long multi-word English.
 *
 * Phase B: Arabic queries now fan out to BOTH root and semantic — the v2
 * engine (Voyage multilingual dense ar+en + lexical roots) understands Arabic,
 * so a concept query like "آيات عن الصبر" reaches by-meaning search.
 */

import { getSurahMaxAyah } from './surah-names';

export interface ParsedVerseRef {
  surah: number;
  ayah: number;
  partial: boolean; // true if user typed "2:" (no ayah yet)
  /** Last verse of a range ("2:238-239"), when the input names one. A range
   *  has no single verse page to open, so it goes to the reader instead —
   *  the same destination the /2:238-239 shorthand URL already resolves to. */
  endAyah?: number;
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
  /** Spells a root letter by letter ("S-W-M", "ص و م"): no surah name to match. */
  spelledRoot: boolean;
}

const VERSE_REF_RE = /^\d{1,3}(?::(\d{0,3}))?$/;
// "2:238-239" — a range. Hyphen or en-dash, the latter because a ref pasted
// from prose usually carries one.
const VERSE_RANGE_RE = /^(\d{1,3}):(\d{1,3})\s*[-\u2013]\s*(\d{1,3})$/;
const ARABIC_RE = /[؀-ۿ]/;
const LATIN_RE = /[a-zA-Z]/;
// Buckwalter uses ASCII letters plus these special chars.
const BUCKWALTER_SPECIAL_RE = /[$<>{}'~&*]/;
const VOWEL_RE = /[aeiouAEIOU]/;
// Arabic combining marks + tatweel — stripped for length checks.
const AR_MARKS_RE = /[ً-ْٰـ]/g;

// A root spelled out letter by letter: "S-W-M", "s w m", "ṣ.w.m", "sh-k-r",
// "3-l-m", "ص و م". Each part is one letter (Latin, a dotted transliteration
// letter, a hamza/ʿayn mark, an Arabizi digit) or a two-letter spelling of
// one (sh, th, dh, kh, gh), and there are three or four parts, as a root has
// three or four letters (two, "T H", is left to name Ṭā-Hā). Mirrors
// root_query.spelled_roots on the server, which answers these with the root's
// own verses.
const ROOT_SEP_RE = /[\s\-‐‑‒–—―.·•_/,+،]+/;
const ROOT_LETTER_RE = /^(?:[a-zA-Zṣḍṭẓḥḫḵẖṯḏšġǧǰāʾʿ'’ʼˀ‘`ʕˁ$*2-79]|sh|th|dh|kh|gh)$/i;
const AR_LETTER_RE = /^[ء-ي]$/;

function spellsRootLetters(trimmed: string): boolean {
  const parts = trimmed.replace(AR_MARKS_RE, '').split(ROOT_SEP_RE).filter(Boolean);
  if (parts.length < 3 || parts.length > 4) return false;
  if (parts.every((p) => /^\d+$/.test(p))) return false;
  return parts.every((p) => AR_LETTER_RE.test(p)) || parts.every((p) => ROOT_LETTER_RE.test(p));
}

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
  spelledRoot: false,
};

/**
 * Try to parse a verse reference from the input.
 * Returns null if not a verse reference pattern.
 */
export function parseVerseRef(input: string): ParsedVerseRef | null {
  const trimmed = input.trim();

  const range = trimmed.match(VERSE_RANGE_RE);
  if (range) {
    const surah = parseInt(range[1], 10);
    const start = parseInt(range[2], 10);
    const max = getSurahMaxAyah(surah);
    if (!max || start < 1 || start > max) return null;
    // Clamp the end to the surah's length, matching the shorthand URL: 36:32-100
    // reads from 32 to the end rather than refusing. A backwards or degenerate
    // range ("2:5-3", "2:5-5") is just the single verse.
    const end = Math.min(parseInt(range[3], 10), max);
    return end > start
      ? { surah, ayah: start, partial: false, endAyah: end }
      : { surah, ayah: start, partial: false };
  }

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

  // 2. A root spelled letter by letter reads as nothing else: roots lead, and
  // the verse list is that root's verses (the server skips meaning search).
  if (spellsRootLetters(trimmed)) {
    return {
      ...EMPTY_PLAN,
      script: ARABIC_RE.test(trimmed) ? 'arabic' : 'latin',
      fire: { root: true, semantic: true },
      lead: 'root',
      looksLikeQuestion: false,
      spelledRoot: true,
    };
  }

  const hasArabic = ARABIC_RE.test(trimmed);
  const hasLatin = LATIN_RE.test(trimmed);
  const wordCount = trimmed.split(/\s+/).filter(Boolean).length;

  // 3. Arabic (or Arabic+Latin). Phase B: the multilingual v2 engine (Voyage
  // dense + lexical roots) makes Arabic → semantic work, so both arms fire. A
  // single short word reads like a root lookup (root leads); a longer word or
  // a phrase reads like a concept query (meaning leads).
  if (hasArabic) {
    const arabicLen = trimmed.replace(AR_MARKS_RE, '').length;
    const conceptual = wordCount >= 2 || arabicLen >= 5;
    return {
      ...EMPTY_PLAN,
      script: hasLatin ? 'mixed' : 'arabic',
      fire: { root: arabicLen >= 2, semantic: arabicLen >= 2 },
      lead: conceptual ? 'semantic' : 'root',
      semanticDebounce: SEMANTIC_DEBOUNCE,
      looksLikeQuestion: question,
    };
  }

  // 4. Latin-only.
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
