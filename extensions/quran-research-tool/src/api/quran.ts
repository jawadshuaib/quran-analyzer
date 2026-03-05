import type {
  RelatedVersesResponse,
  ContextResponse,
  VerseData,
  AITranslationData,
  WordMeaningsResponse,
} from '../types/index.ts';

const BASE = 'http://localhost:5000/api';

export async function fetchRelatedVerses(
  surah: number,
  ayah: number,
  limit = 5,
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

export async function fetchVerse(
  surah: number,
  ayah: number,
): Promise<VerseData> {
  const res = await fetch(`${BASE}/verse/${surah}:${ayah}`);
  if (!res.ok) throw new Error(`Verse ${surah}:${ayah} not found`);
  return res.json();
}

export async function fetchAITranslation(
  surah: number,
  ayah: number,
): Promise<AITranslationData | null> {
  const res = await fetch(`${BASE}/verse/${surah}:${ayah}/ai-translation`);
  if (res.status === 404) return null;
  if (!res.ok) return null;
  return res.json();
}

export async function fetchWordMeanings(
  surah: number,
  ayah: number,
): Promise<WordMeaningsResponse | null> {
  const res = await fetch(`${BASE}/verse/${surah}:${ayah}/word-meanings`);
  if (!res.ok) return null;
  const data: WordMeaningsResponse = await res.json();
  if (!data.meanings || Object.keys(data.meanings).length === 0) return null;
  return data;
}
