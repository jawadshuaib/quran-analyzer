import type { RelatedVersesResponse, ContextResponse } from '../types/index.ts';

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
