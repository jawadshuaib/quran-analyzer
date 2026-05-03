import type { VerseData, SurahInfo, SurahData, RelatedVersesResponse, ContextResponse, SearchTerm, WordSearchResponse, RootDetailData, AITranslationData, WordMeaningsResponse, WordAnalysisData, ThematicContextResponse, SurahContextResponse, GrammarInsightsResponse, GrammarNotesData } from '../types';

export const API_BASE = '';
const BASE = '/api';
const SURAH_CONTEXT_CONFIG = 'surah-context-quran-only-v2-summary';
const GRAMMAR_INSIGHTS_CONFIG = 'grammar-insights-quran-only-v7-unified';

export async function fetchVerse(surah: number, ayah: number): Promise<VerseData> {
  const res = await fetch(`${BASE}/verse/${surah}:${ayah}`);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.error ?? `Verse ${surah}:${ayah} not found`);
  }
  return res.json();
}

export interface DefaultReciter {
  id: number;
  name: string;
  folder: string;
  audio_base: string;
}

export async function fetchDefaultReciter(): Promise<DefaultReciter> {
  const res = await fetch(`${BASE}/reciter/default`);
  if (!res.ok) throw new Error('Failed to load default reciter');
  return res.json();
}

/** Build the per-verse audio URL for the configured default reciter. */
export function reciterAudioUrl(r: DefaultReciter, surah: number, ayah: number): string {
  const s = String(surah).padStart(3, '0');
  const a = String(ayah).padStart(3, '0');
  return `${r.audio_base}/${r.folder}/${s}${a}.mp3`;
}

export async function fetchSurahs(): Promise<SurahInfo[]> {
  const res = await fetch(`${BASE}/surahs`);
  if (!res.ok) throw new Error('Failed to load surah list');
  return res.json();
}

export async function fetchSurah(
  surah: number,
  opts: { includeWords?: boolean; includeSurveyedRoots?: boolean } = {},
): Promise<SurahData> {
  const include: string[] = [];
  if (opts.includeWords) include.push('words');
  if (opts.includeSurveyedRoots) include.push('surveyed_roots');
  const qs = include.length ? `?include=${include.join(',')}` : '';
  const res = await fetch(`${BASE}/surah/${surah}${qs}`);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.error ?? `Failed to load surah ${surah}`);
  }
  return res.json();
}

export async function fetchRelatedVerses(
  surah: number,
  ayah: number,
  limit = 10,
): Promise<RelatedVersesResponse> {
  const res = await fetch(`${BASE}/related/${surah}:${ayah}?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to load related verses');
  return res.json();
}

export async function fetchContext(
  surah: number,
  ayah: number,
): Promise<ContextResponse> {
  const res = await fetch(`${BASE}/context/${surah}:${ayah}`);
  if (!res.ok) throw new Error('Failed to load surrounding context');
  return res.json();
}

export async function fetchThematicContext(
  surah: number,
  ayah: number,
): Promise<ThematicContextResponse | null> {
  const res = await fetch(`${BASE}/verse/${surah}:${ayah}/thematic-context`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error('Failed to load thematic context');
  return res.json();
}

export async function fetchSurahContext(
  surah: number,
  ayah: number,
): Promise<SurahContextResponse | null> {
  const res = await fetch(
    `${BASE}/verse/${surah}:${ayah}/surah-context?config=${encodeURIComponent(SURAH_CONTEXT_CONFIG)}`
  );
  if (res.status === 404) return null;
  if (!res.ok) throw new Error('Failed to load surah context');
  return res.json();
}

export async function fetchGrammarInsights(
  surah: number,
  ayah: number,
): Promise<GrammarInsightsResponse | null> {
  const res = await fetch(
    `${BASE}/verse/${surah}:${ayah}/grammar-insights?config=${encodeURIComponent(GRAMMAR_INSIGHTS_CONFIG)}`
  );
  if (res.status === 404) return null;
  if (!res.ok) throw new Error('Failed to load grammar insights');
  return res.json();
}

export async function searchWords(
  terms: SearchTerm[],
  queryVerse?: { surah: number; ayah: number },
  limit = 25,
): Promise<WordSearchResponse> {
  const res = await fetch(`${BASE}/search-words`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ terms, query_verse: queryVerse, limit }),
  });
  if (!res.ok) throw new Error('Failed to search words');
  return res.json();
}

export async function fetchRoot(rootBw: string): Promise<RootDetailData> {
  const res = await fetch(`${BASE}/root/${encodeURIComponent(rootBw)}`);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.error ?? `Root '${rootBw}' not found`);
  }
  return res.json();
}

export async function fetchAITranslation(
  surah: number,
  ayah: number,
): Promise<AITranslationData | null> {
  const res = await fetch(`${BASE}/verse/${surah}:${ayah}/ai-translation`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error('Failed to load AI translation');
  return res.json();
}

export async function fetchGrammarNotes(
  surah: number,
  ayah: number,
): Promise<GrammarNotesData | null> {
  const res = await fetch(`${BASE}/verse/${surah}:${ayah}/grammar-notes`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error('Failed to load grammar notes');
  return res.json();
}

export interface GrammarGlossaryResponse {
  categories: string[];
  terms: Array<
    import('../types').GrammarTerm & { category: string | null; updated_at?: string }
  >;
}

export async function fetchAllGrammarTerms(): Promise<GrammarGlossaryResponse> {
  const res = await fetch(`${BASE}/grammar-terms`);
  if (!res.ok) throw new Error('Failed to load grammar glossary');
  return res.json();
}

// ---------- Quran vocabulary (ritualistic terms) ----------

export interface QuranVocabularyTerm {
  root_buckwalter: string;
  root_arabic: string;
  canonical_english: string;
  translation_note: string | null;
  occurrence_count: number;
  confidence: number | null;
  leave_untranslated: boolean;
  hard_cases: Array<{
    ref: string;
    arabic_word: string;
    transliteration: string;
    reason: string;
  }>;
  /** English words that, when found in a translation of a verse
   * containing this root, should be rendered as a glossary chip. */
  chip_word_family: string[];
}

export interface QuranVocabularyResponse {
  terms: QuranVocabularyTerm[];
}

export async function fetchQuranVocabulary(): Promise<QuranVocabularyResponse> {
  const res = await fetch(`${BASE}/quran-vocabulary`);
  if (!res.ok) throw new Error('Failed to load Quran vocabulary');
  return res.json();
}

/** Slug for a vocabulary term — used as anchor on /quran-vocabulary so
 * verse-level chips can deep-link to the right entry. */
export function vocabTermSlug(rootBuckwalter: string): string {
  // Buckwalter has chars like *, $, ', etc. — keep alphanumeric only
  return rootBuckwalter.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase();
}

/** Slug generator — must match the backend anchor scheme so tooltip deep links work. */
export function grammarTermSlug(term: string): string {
  return term
    .toLowerCase()
    .normalize('NFD')
    // Strip combining diacritics
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^\w\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-');
}

export async function fetchWordMeanings(
  surah: number,
  ayah: number,
): Promise<WordMeaningsResponse | null> {
  const res = await fetch(`${BASE}/verse/${surah}:${ayah}/word-meanings`);
  if (!res.ok) return null;
  const data: WordMeaningsResponse = await res.json();
  // Return null if no meanings exist
  if (!data.meanings || Object.keys(data.meanings).length === 0) return null;
  return data;
}

export async function fetchWordAnalysis(
  surah: number,
  ayah: number,
  pos: number,
): Promise<WordAnalysisData> {
  const res = await fetch(`${BASE}/word/${surah}:${ayah}/${pos}`);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.error ?? `Word analysis not found`);
  }
  return res.json();
}

export interface RootSearchResult {
  root_buckwalter: string;
  root_arabic: string;
  meaning: string;
  frequency: number;
  in_curriculum: boolean;
  sample_verse: {
    ref: string;
    words: string[];
    matched_positions: number[];
    starts_truncated?: boolean;
    ends_truncated?: boolean;
    translation: string;
  } | null;
}

// --- Verse preview (lightweight) ---

export interface VersePreview {
  surah: number;
  ayah: number;
  surah_name: string;
  text_uthmani: string;
  translation: string;
}

export async function fetchVersePreview(
  surah: number,
  ayah: number,
  signal?: AbortSignal,
): Promise<VersePreview | null> {
  try {
    const res = await fetch(`${BASE}/verse/${surah}:${ayah}/preview`, { signal });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function searchRoots(query: string, limit = 10, signal?: AbortSignal): Promise<RootSearchResult[]> {
  if (!query.trim()) return [];
  const res = await fetch(`${BASE}/roots/search?q=${encodeURIComponent(query.trim())}&limit=${limit}`, { signal });
  if (!res.ok) return [];
  return res.json();
}

export async function searchWordsCount(
  terms: SearchTerm[],
  queryVerse?: { surah: number; ayah: number },
): Promise<number> {
  const res = await fetch(`${BASE}/search-words`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ terms, query_verse: queryVerse, count_only: true }),
  });
  if (!res.ok) return 0;
  const data = await res.json();
  return data.total_found ?? 0;
}

// --- Semantic (vector) search ---

export interface SemanticSearchResult {
  surah: number;
  ayah: number;
  surah_name: string;
  text_uthmani: string;
  translation: string;
  score: number;
}

export interface SemanticSearchResponse {
  query: string;
  results: SemanticSearchResult[];
  total: number;
}

export async function semanticSearch(
  query: string,
  limit = 10,
  signal?: AbortSignal,
): Promise<SemanticSearchResponse> {
  const res = await fetch(
    `${BASE}/semantic-search?q=${encodeURIComponent(query)}&limit=${limit}`,
    { signal },
  );
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { error?: string })?.error || `Semantic search failed (${res.status})`);
  }
  return res.json();
}

/** Today's verse-of-the-day reference. The pool is admin-curated;
 * backend picks one entry deterministically by day-of-year, so the
 * same verse shows for the whole day across all visitors. The
 * caller fetches the actual verse data via fetchVerse() — keeping
 * this endpoint cheap and cacheable. */
export async function getDailyVerse(): Promise<{ chapter: number; verse: number }> {
  const res = await fetch(`${BASE}/verse-of-the-day`);
  if (!res.ok) throw new Error('Failed to fetch daily verse');
  return res.json();
}
