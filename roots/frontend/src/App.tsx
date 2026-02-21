import { useState } from 'react';
import type { VerseData, SearchTerm, WordSearchResponse } from './types';
import { fetchVerse, searchWords } from './api/quran';
import SearchBar from './components/SearchBar';
import VerseDisplay from './components/VerseDisplay';
import SurroundingContext from './components/SurroundingContext';
import RelatedVerses from './components/RelatedVerses';
import WordSearchResults from './components/WordSearchResults';

export default function App() {
  const [data, setData] = useState<VerseData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [wordSearchResults, setWordSearchResults] = useState<WordSearchResponse | null>(null);
  const [wordSearchLoading, setWordSearchLoading] = useState(false);
  const [wordSearchError, setWordSearchError] = useState('');

  async function handleSearch(surah: number, ayah: number) {
    setLoading(true);
    setError('');
    setData(null);
    setWordSearchResults(null);
    setWordSearchError('');
    try {
      const result = await fetchVerse(surah, ayah);
      setData(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }

  async function handleWordSearch(terms: SearchTerm[], queryVerse: { surah: number; ayah: number }) {
    setWordSearchLoading(true);
    setWordSearchError('');
    setWordSearchResults(null);
    try {
      const result = await searchWords(terms, queryVerse);
      setWordSearchResults(result);
    } catch (err: unknown) {
      setWordSearchError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setWordSearchLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-stone-800 mb-2">
          Quran Root Word Analyzer
        </h1>
        <p className="text-stone-500">
          Search any verse to see its root words and morphological breakdown
        </p>
      </header>

      <div className="flex justify-center mb-8">
        <SearchBar onSearch={handleSearch} loading={loading} />
      </div>

      {loading && (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center text-red-700">
          {error}
        </div>
      )}

      {data && (
        <div className="space-y-8">
          <VerseDisplay
            data={data}
            onWordSearch={handleWordSearch}
            wordSearchLoading={wordSearchLoading}
          />

          {wordSearchError && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center text-red-700 text-sm">
              {wordSearchError}
            </div>
          )}

          {wordSearchResults && (
            <WordSearchResults
              data={wordSearchResults}
              onNavigate={handleSearch}
              onClose={() => setWordSearchResults(null)}
            />
          )}

          <SurroundingContext
            surah={data.surah}
            ayah={data.ayah}
            onNavigate={handleSearch}
          />
          <RelatedVerses
            surah={data.surah}
            ayah={data.ayah}
            onNavigate={handleSearch}
          />
        </div>
      )}

      {!data && !loading && !error && (
        <div className="text-center text-stone-400 py-16">
          <p className="text-lg">Try searching for a verse</p>
          <p className="text-sm mt-1">e.g. 1:1, 2:255, 112:1</p>
        </div>
      )}
    </div>
  );
}
