import type { VerseData, SurahInfo, RelatedVersesResponse } from '../types';

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
