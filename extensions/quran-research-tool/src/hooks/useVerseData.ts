import { useState, useEffect } from 'react';
import type {
  VerseData,
  AITranslationData,
  GrammarNotesData,
  WordMeaningBrief,
  VerseExegesisData,
  VersePoetryNote,
} from '../types/index.ts';
import {
  fetchVerse,
  fetchAITranslation,
  fetchGrammarNotes,
  fetchWordMeanings,
  fetchVerseExegesis,
  fetchVersePoetry,
} from '../api/quran.ts';

interface UseVerseDataResult {
  verse: VerseData | null;
  aiTranslation: AITranslationData | null;
  grammarNotes: GrammarNotesData | null;
  wordMeanings: Record<string, WordMeaningBrief>;
  exegesis: VerseExegesisData | null;
  poetry: VersePoetryNote | null;
  loading: boolean;
  error: string;
}

export function useVerseData(surah: number | null, ayah: number | null): UseVerseDataResult {
  const [verse, setVerse] = useState<VerseData | null>(null);
  const [aiTranslation, setAiTranslation] = useState<AITranslationData | null>(null);
  const [grammarNotes, setGrammarNotes] = useState<GrammarNotesData | null>(null);
  const [wordMeanings, setWordMeanings] = useState<Record<string, WordMeaningBrief>>({});
  const [exegesis, setExegesis] = useState<VerseExegesisData | null>(null);
  const [poetry, setPoetry] = useState<VersePoetryNote | null>(null);
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
      fetchVerseExegesis(surah, ayah).catch(() => null),
      fetchVersePoetry(surah, ayah).catch(() => null),
    ])
      .then(([verseData, aiData, gnData, wmData, exegData, poetryData]) => {
        if (cancelled) return;
        setVerse(verseData);
        setAiTranslation(aiData);
        setGrammarNotes(gnData);
        setWordMeanings(wmData?.meanings ?? {});
        setExegesis(exegData);
        setPoetry(poetryData);
      })
      .catch(() => {
        if (!cancelled) setError('Failed to load verse data');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [surah, ayah]);

  return { verse, aiTranslation, grammarNotes, wordMeanings, exegesis, poetry, loading, error };
}
