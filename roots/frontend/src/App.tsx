import { useState, useRef, useEffect } from 'react';
import type { VerseData, SearchTerm, WordSearchResponse } from './types';
import type { SemanticSearchResponse } from './api/quran';
import { fetchVerse, searchWords, semanticSearch } from './api/quran';
import { verseUrl } from './utils/urls';
import UnifiedSearch from './components/UnifiedSearch';
import NavBar from './components/home/NavBar';
import PageBackground from './components/home/PageBackground';
import HomePage from './components/home/HomePage';
import VerseDisplay from './components/VerseDisplay';
import SurroundingContext from './components/SurroundingContext';
import RelatedVerses from './components/RelatedVerses';
import GrammarNotes from './components/GrammarNotes';
import WordSearchResults from './components/WordSearchResults';
import SemanticSearchResults from './components/SemanticSearchResults';
import RootPage from './components/RootPage';
import WordAnalysisPage from './components/WordAnalysisPage';
import NotFound from './components/NotFound';
import ApiPage from './components/ApiPage';
import MethodologyPage from './components/MethodologyPage';
import ExtensionPrivacyPage from './components/ExtensionPrivacyPage';
import PrivacyPage from './components/PrivacyPage';
import TermsPage from './components/TermsPage';
import LearningPage from './components/learning/LearningPage';
import SettingsPage from './components/SettingsPage';
import AskAssistant from './components/AskAssistant';
import SavedItemsPanel from './components/SavedItemsPanel';
import AdminPage from './components/admin/AdminPage';
import { buildVerseContext } from './utils/context-builders';

// Fallback values used until /api/public/chrome-extension-info resolves.
// Admin can change these at runtime from Admin Settings — useful when
// the Chrome Web Store issues a new ID after a resubmission.
const CHROME_EXTENSION_URL_FALLBACK = 'https://chromewebstore.google.com/detail/quran-research-tool/jbalbedmilokgefgknhieckdidnlikdm';
const CHROME_EXTENSION_ID_FALLBACK = 'jbalbedmilokgefgknhieckdidnlikdm';

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

function isPrivacyPath(): boolean {
  return /^\/privacy\/?$/.test(window.location.pathname);
}

function isTermsPath(): boolean {
  return /^\/terms\/?$/.test(window.location.pathname);
}

function isLearningPath(): boolean {
  return /^\/learning(\/root\/.+|\/mnemonic-sheet)?\/?$/.test(window.location.pathname);
}

function isKnownRoute(): boolean {
  const path = window.location.pathname;
  if (path === '/') return true;
  if (/^\/privacy\/extension\/?$/.test(path)) return true;
  if (/^\/privacy\/?$/.test(path)) return true;
  if (/^\/terms\/?$/.test(path)) return true;
  if (/^\/verse\/\d+:\d+$/.test(path)) return true;
  if (/^\/root\/.+$/.test(path)) return true;
  if (/^\/word\/\d+:\d+\/\d+$/.test(path)) return true;
  if (/^\/learning(\/root\/.+|\/mnemonic-sheet)?\/?$/.test(path)) return true;
  if (/^\/settings\/?$/.test(path)) return true;
  if (/^\/developers\/?$/.test(path)) return true;
  if (/^\/methodology\/?$/.test(path)) return true;
  if (/^\/admin(\/settings|\/scheduler|\/media(\/recitations|\/resources|\/music|\/generate|\/explanations|\/generate-explanation|\/pipelines)?)?\/?$/.test(path)) return true;
  return false;
}

function isMobileUserAgent(): boolean {
  const ua = navigator.userAgent || '';
  return /Android|iPhone|iPad|iPod|Mobile/i.test(ua);
}

async function detectExtensionInstalled(extensionId: string): Promise<boolean> {
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
        extensionId,
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

function TopExtensionBar({ storeUrl }: { storeUrl: string }) {
  return (
    <div className="sticky top-0 z-40 w-full border-b border-stone-300 bg-stone-100">
      <div className="w-full px-4 py-2 flex justify-center">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-center gap-2 text-center">
          <p className="text-sm text-stone-700">
            Bring deeper analysis to the Quran without leaving your browser.
          </p>
          <a
            href={storeUrl}
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
    <footer className="py-6 border-t border-card-border text-center text-[11.5px] text-ink-muted tracking-wide">
      <div>open corpus &middot; non-commercial &middot; built by and for students of the text</div>
      <div className="mt-1.5">
        <a href="/privacy" className="hover:text-ink-secondary">Privacy</a>
        <span className="mx-2">&middot;</span>
        <a href="/terms" className="hover:text-ink-secondary">Terms</a>
      </div>
    </footer>
  );
}

export default function App() {
  const [extensionInstalled, setExtensionInstalled] = useState(false);
  const [extensionCheckDone, setExtensionCheckDone] = useState(false);
  const [extensionConfig, setExtensionConfig] = useState<{ id: string; storeUrl: string }>({
    id: CHROME_EXTENSION_ID_FALLBACK,
    storeUrl: CHROME_EXTENSION_URL_FALLBACK,
  });
  const currentPath = window.location.pathname;
  const isHomepage = currentPath === '/' || currentPath === '';
  const showTopBar =
    !isMobileUserAgent() &&
    extensionCheckDone &&
    !extensionInstalled &&
    !isHomepage;

  if (isLearningPath()) {
    return (
      <div className="min-h-screen flex flex-col">
        <PageBackground />
        {showTopBar && <TopExtensionBar storeUrl={extensionConfig.storeUrl} />}
        <NavBar currentPath={currentPath} />
        <LearningPage />
        <SiteFooter />
        <SavedItemsPanel />
      </div>
    );
  }

  const wordParams = getWordFromPath();
  if (wordParams) {
    return (
      <div className="min-h-screen flex flex-col">
        <PageBackground />
        {showTopBar && <TopExtensionBar storeUrl={extensionConfig.storeUrl} />}
        <NavBar currentPath={currentPath} />
        <div className="flex-1">
          <WordAnalysisPage surah={wordParams.surah} ayah={wordParams.ayah} pos={wordParams.pos} />
        </div>
        <SiteFooter />
        <SavedItemsPanel />
      </div>
    );
  }

  const rootBw = getRootFromPath();
  if (rootBw) {
    return (
      <div className="min-h-screen flex flex-col">
        <PageBackground />
        {showTopBar && <TopExtensionBar storeUrl={extensionConfig.storeUrl} />}
        <NavBar currentPath={currentPath} />
        <RootPage rootBw={rootBw} />
        <SavedItemsPanel />
      </div>
    );
  }

  if (isExtensionPrivacyPath()) {
    return (
      <div className="min-h-screen flex flex-col">
        <PageBackground />
        {showTopBar && <TopExtensionBar storeUrl={extensionConfig.storeUrl} />}
        <NavBar currentPath={currentPath} />
        <ExtensionPrivacyPage />
        <SiteFooter />
      </div>
    );
  }

  if (isPrivacyPath()) {
    return (
      <div className="min-h-screen flex flex-col">
        <PageBackground />
        {showTopBar && <TopExtensionBar storeUrl={extensionConfig.storeUrl} />}
        <NavBar currentPath={currentPath} />
        <PrivacyPage />
        <SiteFooter />
      </div>
    );
  }

  if (isTermsPath()) {
    return (
      <div className="min-h-screen flex flex-col">
        <PageBackground />
        {showTopBar && <TopExtensionBar storeUrl={extensionConfig.storeUrl} />}
        <NavBar currentPath={currentPath} />
        <TermsPage />
        <SiteFooter />
      </div>
    );
  }

  if (/^\/methodology\/?$/.test(currentPath)) {
    return (
      <div className="min-h-screen flex flex-col">
        <PageBackground />
        {showTopBar && <TopExtensionBar storeUrl={extensionConfig.storeUrl} />}
        <NavBar currentPath={currentPath} />
        <MethodologyPage />
        <SiteFooter />
        <SavedItemsPanel />
      </div>
    );
  }

  if (/^\/developers\/?$/.test(currentPath)) {
    return <ApiPage />;
  }

  if (/^\/admin(\/settings|\/scheduler|\/media(\/recitations|\/resources|\/music|\/generate|\/explanations|\/generate-explanation|\/pipelines)?)?\/?$/.test(currentPath)) {
    return <AdminPage />;
  }

  if (/^\/settings\/?$/.test(currentPath)) {
    return (
      <div className="min-h-screen flex flex-col">
        <PageBackground />
        {showTopBar && <TopExtensionBar storeUrl={extensionConfig.storeUrl} />}
        <NavBar currentPath={currentPath} />
        <SettingsPage />
      </div>
    );
  }

  if (!isKnownRoute()) {
    return (
      <div className="min-h-screen flex flex-col">
        <PageBackground />
        {showTopBar && <TopExtensionBar storeUrl={extensionConfig.storeUrl} />}
        <NavBar currentPath={currentPath} />
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
  const [semanticResults, setSemanticResults] = useState<SemanticSearchResponse | null>(null);
  const [semanticLoading, setSemanticLoading] = useState(false);
  const [semanticError, setSemanticError] = useState('');
  const semanticRef = useRef<HTMLDivElement>(null);

  // featuredVerses removed — now handled by VerseOfTheDay in HomePage

  async function handleSearch(surah: number, ayah: number) {
    setLoading(true);
    setError('');
    setData(null);
    setWordSearchResults(null);
    setWordSearchError('');
    setSemanticResults(null);
    setSemanticError('');
    try {
      const result = await fetchVerse(surah, ayah);
      setData(result);
      document.title = `Surah ${result.surah_name} (${surah}:${ayah}) | al-nuqta`;
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
      return;
    }

    // Fetch the live extension id/store URL (admin-configurable) before
    // pinging — so a resubmission to the Chrome Web Store that changes
    // the ID only needs an Admin Settings update, not a code deploy.
    (async () => {
      let id = CHROME_EXTENSION_ID_FALLBACK;
      let storeUrl = CHROME_EXTENSION_URL_FALLBACK;
      try {
        const res = await fetch('/api/public/chrome-extension-info');
        if (res.ok) {
          const data = (await res.json()) as { id?: string; store_url?: string };
          if (data.id) id = data.id;
          if (data.store_url) storeUrl = data.store_url;
        }
      } catch {
        // Fallback constants are already set — continue silently.
      }
      if (cancelled) return;
      setExtensionConfig({ id, storeUrl });

      const installed = await detectExtensionInstalled(id);
      if (cancelled) return;
      setExtensionInstalled(installed);
      setExtensionCheckDone(true);
    })();

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

  // Scroll to semantic search results when they load
  useEffect(() => {
    if (semanticResults && semanticRef.current) {
      semanticRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [semanticResults]);

  async function handleSemanticSearch(query: string) {
    setSemanticLoading(true);
    setSemanticError('');
    setSemanticResults(null);
    // Clear verse display when doing semantic search
    setData(null);
    setError('');
    setWordSearchResults(null);
    try {
      const result = await semanticSearch(query, 15);
      setSemanticResults(result);
      document.title = `Search: ${query} | al-nuqta`;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Semantic search failed';
      // Friendly message for 404 (endpoint not deployed yet) or network errors
      if (msg.includes('404') || msg.includes('Failed to fetch')) {
        setSemanticError('Semantic search is not available yet. Please try again later.');
      } else {
        setSemanticError(msg);
      }
    } finally {
      setSemanticLoading(false);
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

  const isIdle = !data && !loading && !error && !semanticResults && !semanticLoading && !semanticError;

  return (
    <div className="min-h-screen flex flex-col">
    <PageBackground />
    {showTopBar && <TopExtensionBar storeUrl={extensionConfig.storeUrl} />}

    {/* NavBar — full-width, spans across */}
    <NavBar currentPath={currentPath} />

    {/* Homepage idle state — show the full redesigned homepage */}
    {isIdle && (
      <div className="flex-1">
        <HomePage
          onNavigateVerse={handleSearch}
          onFullSemanticSearch={handleSemanticSearch}
          loading={loading}
        />
      </div>
    )}

    {/* Active state — searching or viewing a verse */}
    {!isIdle && (
      <div className="mx-auto max-w-3xl px-4 py-10 flex-1 w-full">
        <div className="mb-8">
          <UnifiedSearch
            onNavigateVerse={handleSearch}
            onFullSemanticSearch={handleSemanticSearch}
            loading={loading}
          />
        </div>

        {(loading || semanticLoading) && (
          <div className="flex justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center text-red-700">
            {error}
          </div>
        )}

        {semanticError && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center text-red-700">
            {semanticError}
          </div>
        )}

        {semanticResults && (
          <div ref={semanticRef}>
            <SemanticSearchResults
              data={semanticResults}
              onNavigate={handleSearch}
              onClose={() => setSemanticResults(null)}
            />
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

            <GrammarNotes surah={data.surah} ayah={data.ayah} />
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
      </div>
    )}

      <SiteFooter />
      <SavedItemsPanel />
    </div>
  );
}
