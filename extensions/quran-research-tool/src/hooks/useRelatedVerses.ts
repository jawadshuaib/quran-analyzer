import { useState, useEffect } from 'react';
import type { RelatedVerse } from '../types/index.ts';
import { fetchRelatedVerses } from '../api/quran.ts';

export interface AyahGroup {
  surah: number;
  ayah: number;
  verses: RelatedVerse[];
}

export function useRelatedVerses(surah: number | null, ayahs: number[]) {
  const [groups, setGroups] = useState<AyahGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (surah === null || ayahs.length === 0) {
      setGroups([]);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError('');

    Promise.all(
      ayahs.map((ayah) => fetchRelatedVerses(surah, ayah)),
    )
      .then((results) => {
        if (cancelled) return;
        setGroups(
          results.map((r) => ({
            surah: r.query.surah,
            ayah: r.query.ayah,
            verses: r.related,
          })),
        );
      })
      .catch(() => {
        if (!cancelled) setError('Failed to load related verses');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [surah, ayahs]);

  return { groups, loading, error };
}
