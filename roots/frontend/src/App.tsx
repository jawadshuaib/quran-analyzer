import { useState, useRef, useEffect, useMemo } from 'react';
import type { VerseData, SearchTerm, WordSearchResponse } from './types';
import { fetchVerse, searchWords } from './api/quran';
import SearchBar from './components/SearchBar';
import VerseDisplay from './components/VerseDisplay';
import SurroundingContext from './components/SurroundingContext';
import RelatedVerses from './components/RelatedVerses';
import WordSearchResults from './components/WordSearchResults';
import RootPage from './components/RootPage';
import WordAnalysisPage from './components/WordAnalysisPage';

function getRootFromPath(): string | null {
  const match = window.location.pathname.match(/^\/root\/(.+)$/);
  return match ? decodeURIComponent(match[1]) : null;
}

function getWordFromPath(): { surah: number; ayah: number; pos: number } | null {
  const match = window.location.pathname.match(/^\/word\/(\d+):(\d+)\/(\d+)$/);
  return match
    ? { surah: parseInt(match[1]), ayah: parseInt(match[2]), pos: parseInt(match[3]) }
    : null;
}

export default function App() {
  const wordParams = getWordFromPath();
  if (wordParams) return <WordAnalysisPage surah={wordParams.surah} ayah={wordParams.ayah} pos={wordParams.pos} />;

  const rootBw = getRootFromPath();
  if (rootBw) return <RootPage rootBw={rootBw} />;
  const [data, setData] = useState<VerseData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [wordSearchResults, setWordSearchResults] = useState<WordSearchResponse | null>(null);
  const [wordSearchLoading, setWordSearchLoading] = useState(false);
  const [wordSearchError, setWordSearchError] = useState('');
  const wordSearchRef = useRef<HTMLDivElement>(null);

  // 15 famous verses — pick 3 at random on each page load
  const featuredVerses = useMemo<[number, number][]>(() => {
    const all: [number, number][] = [
      [1, 1],    // Al-Fatiha
      [2, 255],  // Ayat al-Kursi
      [2, 286],  // Last verse of Al-Baqarah
      [3, 190],  // First verse on just warfare
      [24, 35],  // Ayat an-Nur (Light verse)
      [36, 1],   // Ya-Sin opening
      [55, 13],  // Ar-Rahman refrain
      [59, 22],  // Names of Allah
      [67, 1],   // Al-Mulk opening
      [96, 1],   // First revelation
      [112, 1],  // Al-Ikhlas
      [113, 1],  // Al-Falaq
      [114, 1],  // An-Nas
      [2, 152],  // Remember Me
      [33, 56],  // Salawat verse
      [13, 28],  // Hearts find rest in remembrance
      [94, 5],   // With hardship comes ease
      [49, 13],  // Nations and tribes
      [21, 107], // Mercy to the worlds
      [3, 139],  // Do not weaken
      [18, 10],  // Companions of the Cave
      [56, 77],  // Noble Quran
      [39, 53],  // Do not despair of mercy
      [31, 18],  // Luqman's advice — humility
      [17, 1],   // Isra (Night Journey)
    ];
    const shuffled = [...all].sort(() => Math.random() - 0.5);
    return shuffled.slice(0, 3);
  }, []);

  async function handleSearch(surah: number, ayah: number) {
    setLoading(true);
    setError('');
    setData(null);
    setWordSearchResults(null);
    setWordSearchError('');
    try {
      const result = await fetchVerse(surah, ayah);
      setData(result);
      // Keep URL in sync with the displayed verse
      const url = new URL(window.location.href);
      url.searchParams.set('s', String(surah));
      url.searchParams.set('a', String(ayah));
      window.history.pushState(null, '', url);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }

  // Deep-link: auto-search if ?s= and ?a= query params are present
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const s = params.get('s');
    const a = params.get('a');
    if (s && a) handleSearch(parseInt(s), parseInt(a));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Scroll to word search results when they load
  useEffect(() => {
    if (wordSearchResults && wordSearchRef.current) {
      wordSearchRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [wordSearchResults]);

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
    <div className="min-h-screen flex flex-col">
    <div className="mx-auto max-w-3xl px-4 py-10 flex-1 w-full">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-stone-800 mb-2">
          <a href="/" className="hover:opacity-80 transition-opacity">Quran Root Word Analyzer</a>
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
            <div ref={wordSearchRef}>
              <WordSearchResults
                data={wordSearchResults}
                onNavigate={handleSearch}
                onClose={() => setWordSearchResults(null)}
              />
            </div>
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
            forceCollapse={!!wordSearchResults}
          />
        </div>
      )}

      {!data && !loading && !error && (
        <div className="text-center text-stone-400 py-16">
          <p className="text-lg">Try searching for a verse</p>
          <p className="text-sm mt-1">e.g.{' '}
            {featuredVerses.map(([s, a], i) => (
              <span key={i}>
                {i > 0 && ', '}
                <button
                  className="text-indigo-400 hover:text-indigo-300 underline cursor-pointer"
                  onClick={() => handleSearch(s, a)}
                >
                  {s}:{a}
                </button>
              </span>
            ))}
          </p>
        </div>
      )}
    </div>
      <footer className="py-6 border-t border-stone-200 text-center text-xs text-stone-400">
        Created by{' '}
        <a href="https://www.linkedin.com/in/jawadshuaib/" target="_blank" rel="noopener noreferrer"
           className="text-stone-500 hover:text-stone-700 underline">Jawad Shuaib</a>.
        {' '}Code repo available on{' '}
        <a href="https://github.com/jawadshuaib/quran-analyzer" target="_blank" rel="noopener noreferrer"
           className="text-stone-500 hover:text-stone-700 underline">GitHub</a>.
      </footer>
    </div>
  );
}
