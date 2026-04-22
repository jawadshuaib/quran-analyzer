import { useState, useEffect } from 'react';
import type { VerseData, AITranslationData, GrammarNotesData, WordMeaningBrief } from '../types/index.ts';
import { fetchVerse, fetchAITranslation, fetchGrammarNotes, fetchWordMeanings } from '../api/quran.ts';

interface UseVerseDataResult {
  verse: VerseData | null;
  aiTranslation: AITranslationData | null;
  grammarNotes: GrammarNotesData | null;
  wordMeanings: Record<string, WordMeaningBrief>;
  loading: boolean;
  error: string;
}

export function useVerseData(surah: number | null, ayah: number | null): UseVerseDataResult {
  const [verse, setVerse] = useState<VerseData | null>(null);
  const [aiTranslation, setAiTranslation] = useState<AITranslationData | null>(null);
  const [grammarNotes, setGrammarNotes] = useState<GrammarNotesData | null>(null);
  const [wordMeanings, setWordMeanings] = useState<Record<string, WordMeaningBrief>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (surah === null || ayah === null) return;

    let cancelled = false;
    setLoading(true);
    setError('');

    Promise.all([
      fetchVerse(surah, ayah),
      fetchAITranslation(surah, ayah),
      fetchGrammarNotes(surah, ayah),
      fetchWordMeanings(surah, ayah),
    ])
      .then(([verseData, aiData, gnData, wmData]) => {
        if (cancelled) return;
        setVerse(verseData);
        setAiTranslation(aiData);
        setGrammarNotes(gnData);
        setWordMeanings(wmData?.meanings ?? {});
      })
      .catch(() => {
        if (!cancelled) setError('Failed to load verse data');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [surah, ayah]);

  return { verse, aiTranslation, grammarNotes, wordMeanings, loading, error };
}
