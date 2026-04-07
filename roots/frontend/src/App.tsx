import { useState, useRef, useEffect, useMemo } from 'react';
import type { VerseData, SearchTerm, WordSearchResponse } from './types';
import { fetchVerse, searchWords } from './api/quran';
import { verseUrl } from './utils/urls';
import SearchBar from './components/SearchBar';
import VerseDisplay from './components/VerseDisplay';
import SurroundingContext from './components/SurroundingContext';
import RelatedVerses from './components/RelatedVerses';
import WordSearchResults from './components/WordSearchResults';
import RootPage from './components/RootPage';
import WordAnalysisPage from './components/WordAnalysisPage';
import NotFound from './components/NotFound';
import ExtensionPrivacyPage from './components/ExtensionPrivacyPage';
import LearningPage from './components/learning/LearningPage';
import LearningPromo from './components/LearningPromo';
import RootSearch from './components/RootSearch';
import SettingsPage from './components/SettingsPage';
import AskAssistant from './components/AskAssistant';
import { buildVerseContext, buildWordContext } from './utils/context-builders';

const CHROME_EXTENSION_URL = 'https://chromewebstore.google.com/detail/quran-research-tool/jbalbedmilokgefgknhieckdidnlikdm';
const CHROME_EXTENSION_ID = 'jbalbedmilokgefgknhieckdidnlikdm';

function getVerseFromPath(): { surah: number; ayah: number } | null {
  const match = window.location.pathname.match(/^\/verse\/(\d+):(\d+)$/);
  return match ? { surah: parseInt(match[1]), ayah: parseInt(match[2]) } : null;
}

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

function isExtensionPrivacyPath(): boolean {
  return /^\/privacy\/extension\/?$/.test(window.location.pathname);
}

function isLearningPath(): boolean {
  return /^\/learning(\/root\/.+|\/mnemonic-sheet)?\/?$/.test(window.location.pathname);
}

function isKnownRoute(): boolean {
  const path = window.location.pathname;
  if (path === '/') return true;
  if (/^\/privacy\/extension\/?$/.test(path)) return true;
  if (/^\/verse\/\d+:\d+$/.test(path)) return true;
  if (/^\/root\/.+$/.test(path)) return true;
  if (/^\/word\/\d+:\d+\/\d+$/.test(path)) return true;
  if (/^\/learning(\/root\/.+|\/mnemonic-sheet)?\/?$/.test(path)) return true;
  if (/^\/settings\/?$/.test(path)) return true;
  return false;
}

function isMobileUserAgent(): boolean {
  const ua = navigator.userAgent || '';
  return /Android|iPhone|iPad|iPod|Mobile/i.test(ua);
}

async function detectExtensionInstalled(): Promise<boolean> {
  const chromeObj = (window as unknown as { chrome?: { runtime?: { sendMessage?: Function; lastError?: { message?: string } } } }).chrome;
  const runtime = chromeObj?.runtime;
  const sendMessage = runtime?.sendMessage;
  if (!sendMessage) return false;

  return new Promise<boolean>((resolve) => {
    let done = false;
    const timer = setTimeout(() => {
      if (done) return;
      done = true;
      resolve(false);
    }, 700);

    try {
      sendMessage(
        CHROME_EXTENSION_ID,
        { type: 'QURAN_RESEARCH_TOOL_PING' },
        (response: unknown) => {
          if (done) return;
          done = true;
          clearTimeout(timer);
          const hasError = !!runtime.lastError;
          const ok =
            !!response &&
            typeof response === 'object' &&
            (
              (response as { installed?: boolean }).installed === true ||
              (response as { ok?: boolean }).ok === true ||
              (response as { type?: string }).type === 'QURAN_RESEARCH_TOOL_PONG'
            );
          resolve(!hasError && ok);
        },
      );
    } catch {
      if (done) return;
      done = true;
      clearTimeout(timer);
      resolve(false);
    }
  });
}

function TopExtensionBar() {
  return (
    <div className="sticky top-0 z-40 w-full border-b border-stone-300 bg-stone-100">
      <div className="w-full px-4 py-2 flex justify-center">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-center gap-2 text-center">
          <p className="text-sm text-stone-700">
            Bring deeper analysis to the Quran without leaving your browser.
          </p>
          <a
            href={CHROME_EXTENSION_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center rounded-md bg-stone-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-stone-700 transition-colors"
          >
            Get Chrome Extension
          </a>
        </div>
      </div>
    </div>
  );
}

function SiteFooter() {
  return (
    <footer className="py-6 border-t border-stone-200 text-center text-xs text-stone-400">
      <a href="https://github.com/jawadshuaib/quran-analyzer/blob/main/API.md" target="_blank" rel="noopener noreferrer"
         className="text-stone-500 hover:text-stone-700 underline">API Docs</a>
      {' | '}
      <a href="https://github.com/jawadshuaib/quran-analyzer" target="_blank" rel="noopener noreferrer"
         className="text-stone-500 hover:text-stone-700 underline">GitHub</a>
    </footer>
  );
}

export default function App() {
  const [extensionInstalled, setExtensionInstalled] = useState(false);
  const [extensionCheckDone, setExtensionCheckDone] = useState(false);
  const showTopBar =
    window.location.pathname !== '/' &&
    !isMobileUserAgent() &&
    extensionCheckDone &&
    !extensionInstalled;
  if (isLearningPath()) {
    return (
      <div className="min-h-screen flex flex-col">
        <LearningPage />
        <SiteFooter />
      </div>
    );
  }

  const wordParams = getWordFromPath();
  if (wordParams) {
    return (
      <div className="min-h-screen flex flex-col">
        {showTopBar && <TopExtensionBar />}
        <div className="flex-1">
          <WordAnalysisPage surah={wordParams.surah} ayah={wordParams.ayah} pos={wordParams.pos} />
        </div>
        <SiteFooter />
      </div>
    );
  }

  const rootBw = getRootFromPath();
  if (rootBw) {
    return (
      <div className="min-h-screen flex flex-col">
        {showTopBar && <TopExtensionBar />}
        <RootPage rootBw={rootBw} />
      </div>
    );
  }

  if (isExtensionPrivacyPath()) {
    return (
      <div className="min-h-screen flex flex-col">
        {showTopBar && <TopExtensionBar />}
        <ExtensionPrivacyPage />
      </div>
    );
  }

  if (/^\/settings\/?$/.test(window.location.pathname)) {
    return (
      <div className="min-h-screen flex flex-col">
        {showTopBar && <TopExtensionBar />}
        <SettingsPage />
      </div>
    );
  }

  if (!isKnownRoute()) {
    return (
      <div className="min-h-screen flex flex-col">
        {showTopBar && <TopExtensionBar />}
        <NotFound />
      </div>
    );
  }
  const [data, setData] = useState<VerseData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [wordSearchResults, setWordSearchResults] = useState<WordSearchResponse | null>(null);
  const [wordSearchLoading, setWordSearchLoading] = useState(false);
  const [wordSearchError, setWordSearchError] = useState('');
  const wordSearchRef = useRef<HTMLDivElement>(null);
  const [showExtensionSection, setShowExtensionSection] = useState(false);

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
      document.title = `Surah ${result.surah_name} (${surah}:${ayah}) | The Quran Explorer`;
      // Keep URL in sync with the displayed verse
      window.history.pushState(null, '', verseUrl(surah, ayah));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }

  // Deep-link: check /verse/X:Y path first, fall back to ?s=X&a=Y with redirect
  useEffect(() => {
    const verseParams = getVerseFromPath();
    if (verseParams) { handleSearch(verseParams.surah, verseParams.ayah); return; }
    const params = new URLSearchParams(window.location.search);
    const s = params.get('s');
    const a = params.get('a');
    if (s && a) {
      window.history.replaceState(null, '', verseUrl(parseInt(s), parseInt(a)));
      handleSearch(parseInt(s), parseInt(a));
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    let cancelled = false;
    const mobile = isMobileUserAgent();
    if (mobile) {
      setExtensionInstalled(false);
      setExtensionCheckDone(true);
      setShowExtensionSection(false);
      return;
    }
    detectExtensionInstalled().then((installed) => {
      if (cancelled) return;
      setExtensionInstalled(installed);
      setExtensionCheckDone(true);
      setShowExtensionSection(!installed);
    });
    return () => {
      cancelled = true;
    };
  }, []);

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
    {showTopBar && <TopExtensionBar />}
    <div className="mx-auto max-w-3xl px-4 py-10 flex-1 w-full">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-stone-800 mb-2">
          <a href="/" className="hover:opacity-80 transition-opacity">The Quran Explorer</a>
        </h1>
        <p className="text-stone-500">
          Root words, morphology, Semitic etymology, and context based translation
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
            onNavigate={handleSearch}
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

          <AskAssistant
            pageType="verse"
            pageKey={`${data.surah}:${data.ayah}`}
            contextGatherer={() => buildVerseContext(data.surah, data.ayah)}
          />
        </div>
      )}

      {!data && !loading && !error && (
        <div className="text-center text-stone-400 py-16 space-y-8">
          <div>
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

          <hr className="border-stone-200/60 max-w-xs mx-auto" />

          {/* Root search */}
          <div className="mx-auto max-w-2xl rounded-xl border border-stone-200 bg-white p-4 shadow-sm text-left">
            <div className="flex flex-col items-center text-center">
              <p className="text-xs font-semibold tracking-wide text-emerald-700 uppercase">Root Search</p>
              <h2 className="text-lg font-semibold text-stone-800 mt-1">Explore Quranic Root Words</h2>
              <p className="text-sm text-stone-500 mt-1 mb-4">
                Search by Buckwalter, Arabic, romanization, or English meaning
              </p>
              <RootSearch />
            </div>
          </div>

          {showExtensionSection && (
            <div className="mx-auto max-w-2xl rounded-xl border border-stone-200 bg-white p-4 shadow-sm text-left">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                <div className="flex-1">
                  <p className="text-xs font-semibold tracking-wide text-emerald-700 uppercase">Chrome Extension</p>
                  <h2 className="text-lg font-semibold text-stone-800 mt-1">Quran Research Tool</h2>
                  <p className="text-sm text-stone-500 mt-1">
                    Bring deeper analysis to the Quran without leaving your browser.
                  </p>
                  <ul className="mt-2 text-sm text-stone-600 list-disc pl-5 space-y-1">
                    <li>Precise word-level analysis</li>
                    <li>Semitic cognate and root connections</li>
                    <li>Contextually related verses across the Quran</li>
                  </ul>
                  <a
                    href={CHROME_EXTENSION_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center mt-3 rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-700 transition-colors"
                  >
                    Add Chrome Extension
                  </a>
                </div>

                <a
                  href={CHROME_EXTENSION_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="shrink-0 rounded-lg overflow-hidden border border-stone-200 hover:border-emerald-300 transition-colors w-full sm:w-56"
                >
                  <img
                    src="/chrome-extension-screenshot.png"
                    alt="Quran Research Tool Chrome extension screenshot"
                    className="w-full h-auto block"
                    loading="lazy"
                  />
                </a>
              </div>
            </div>
          )}

          <LearningPromo />
        </div>
      )}
    </div>
      <SiteFooter />
    </div>
  );
}
