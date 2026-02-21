import type { VerseData, SurahInfo, RelatedVersesResponse, ContextResponse, SearchTerm, WordSearchResponse } from '../types';

const BASE = '/api';

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
