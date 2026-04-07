import type { VerseData, SurahInfo, RelatedVersesResponse, ContextResponse, SearchTerm, WordSearchResponse, RootDetailData, AITranslationData, WordMeaningsResponse, WordAnalysisData, ThematicContextResponse, SurahContextResponse, GrammarInsightsResponse } from '../types';

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

export async function fetchSurahs(): Promise<SurahInfo[]> {
  const res = await fetch(`${BASE}/surahs`);
  if (!res.ok) throw new Error('Failed to load surah list');
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

export async function searchRoots(query: string, limit = 10): Promise<RootSearchResult[]> {
  if (!query.trim()) return [];
  const res = await fetch(`${BASE}/roots/search?q=${encodeURIComponent(query.trim())}&limit=${limit}`);
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
