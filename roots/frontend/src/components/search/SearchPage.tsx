import { useState, useEffect, useMemo, useCallback } from 'react';
import UnifiedSearch from '../UnifiedSearch';
import SaveButton from '../SaveButton';
import { searchV2, type SearchV2Result } from '../../api/quran';
import { wrapArabicRuns } from '../../utils/arabic-runs';
import { useSEO } from '../../hooks/useSEO';
import { addRecentSearch, SUGGESTED_QUERIES } from '../../utils/recent-searches';

const PAGE_SIZE = 15;
type SortMode = 'relevance' | 'mushaf';

function readQueryFromUrl(): string {
  return new URLSearchParams(window.location.search).get('q')?.trim() ?? '';
}

/** Bold words in `text` that appear in the query (3+ chars). */
function highlight(text: string, query: string): { text: string; bold: boolean }[] {
  const words = query.toLowerCase().split(/\s+/).filter((w) => w.length >= 3);
  if (words.length === 0) return [{ text, bold: false }];
  const escaped = words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const re = new RegExp(`(${escaped.join('|')})`, 'gi');
  const parts: { text: string; bold: boolean }[] = [];
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push({ text: text.slice(last, m.index), bold: false });
    parts.push({ text: m[0], bold: true });
    last = re.lastIndex;
  }
  if (last < text.length) parts.push({ text: text.slice(last), bold: false });
  return parts.length ? parts : [{ text, bold: false }];
}

function ResultCard({ r, query }: { r: SearchV2Result; query: string }) {
  const verseKey = `${r.surah}:${r.ayah}`;
  const [copied, setCopied] = useState(false);
  const parts = useMemo(() => highlight(r.translation, query), [r.translation, query]);
  // The visible "% match" is the dense (semantic) cosine, not the tiny RRF
  // fusion score. Chips say WHY a verse matched: its Arabic vector, or its roots.
  const dense = r.matched_because?.dense;
  const hasLexical = !!r.matched_because?.lexical;
  const pct = dense ? Math.round(dense.score * 100) : null;

  async function copy(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    const text = `${r.text_uthmani}\n\n${r.translation}\n\n— ${r.surah_name} ${verseKey}`;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <div className="group rounded-lg border border-stone-200 bg-white p-4 transition-colors hover:border-violet-300 hover:bg-violet-50/20">
      <div className="flex items-start gap-3">
        <a href={`/verse/${verseKey}`} className="min-w-0 flex-1 block">
          <span className="text-xs font-medium text-violet-600">
            {r.surah_name} {verseKey}
          </span>
          <p dir="rtl" lang="ar" className="mt-1.5 text-right font-arabic text-lg leading-loose text-stone-800">
            {r.text_uthmani}
          </p>
          {r.translation && (
            <p className="mt-1 text-sm leading-relaxed text-stone-600">
              {parts.map((seg, i) =>
                seg.bold ? (
                  <span key={i} className="font-semibold text-violet-800">{seg.text}</span>
                ) : (
                  <span key={i}>{wrapArabicRuns(seg.text)}</span>
                ),
              )}
            </p>
          )}
        </a>
        <div className="flex shrink-0 flex-col items-end gap-1">
          {pct !== null && (
            <span className="rounded-full bg-violet-100 px-2 py-0.5 text-[10px] font-medium text-violet-700">
              {pct}%
            </span>
          )}
          <div className="flex gap-1">
            {dense?.doc_type === 'ar' && (
              <span className="rounded-full border border-sky-200 bg-sky-50 px-1.5 py-0.5 text-[9px] font-medium text-sky-600">
                Arabic
              </span>
            )}
            {hasLexical && (
              <span className="rounded-full border border-emerald-200 bg-emerald-50 px-1.5 py-0.5 text-[9px] font-medium text-emerald-600">
                root
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="mt-2 flex items-center gap-3 pl-0.5">
        <div className="rounded-full bg-white">
          <SaveButton
            type="verse"
            itemKey={verseKey}
            label={`Surah ${r.surah_name} ${verseKey}`}
            href={`/verse/${verseKey}`}
            subtitle={r.translation}
            arabic={r.text_uthmani}
            translation={r.translation}
          />
        </div>
        <button
          type="button"
          onClick={copy}
          className="inline-flex items-center gap-1 text-[11px] text-stone-400 hover:text-emerald-600 transition-colors cursor-pointer"
          title="Copy verse"
        >
          <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="5.5" y="5.5" width="8" height="8" rx="1.5" />
            <path d="M3.5 10.5H3A1.5 1.5 0 011.5 9V3A1.5 1.5 0 013 1.5h6A1.5 1.5 0 0110.5 3v.5" strokeLinecap="round" />
          </svg>
          {copied ? 'Copied' : 'Copy'}
        </button>
        <a
          href={`/read/${r.surah}:${r.ayah}`}
          className="ml-auto text-[11px] text-stone-400 hover:text-violet-600 transition-colors"
        >
          Read in context →
        </a>
      </div>
    </div>
  );
}

export default function SearchPage() {
  const [query, setQuery] = useState(readQueryFromUrl);
  const [results, setResults] = useState<SearchV2Result[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [ran, setRan] = useState(false);
  const [sort, setSort] = useState<SortMode>('relevance');
  const [surahFilter, setSurahFilter] = useState<number | null>(null);
  const [visible, setVisible] = useState(PAGE_SIZE);

  useSEO({
    title: query ? `Search: ${query}` : 'Search',
    description: query
      ? `Verses of the Qur'an matching “${query}”, searched by meaning.`
      : 'Search the Qur’an by meaning, root, or reference.',
    path: '/search',
    noindex: true,
  });

  const runSearch = useCallback(async (q: string) => {
    const trimmed = q.trim();
    setSurahFilter(null);
    setVisible(PAGE_SIZE);
    if (!trimmed) {
      setResults([]);
      setRan(false);
      setError('');
      return;
    }
    setLoading(true);
    setError('');
    addRecentSearch(trimmed);
    try {
      const data = await searchV2(trimmed, 50);
      setResults(data.results);
      setRan(true);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Search failed';
      setError(
        msg.includes('404') || msg.includes('Failed to fetch')
          ? 'Search is not available right now. Please try again in a moment.'
          : msg,
      );
      setResults([]);
      setRan(true);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial search from the URL.
  useEffect(() => {
    runSearch(query);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Browser back/forward → re-read ?q= and re-search.
  useEffect(() => {
    function onPop() {
      const q = readQueryFromUrl();
      setQuery(q);
      runSearch(q);
    }
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, [runSearch]);

  const submit = useCallback(
    (q: string) => {
      const trimmed = q.trim();
      if (!trimmed) return;
      setQuery(trimmed);
      window.history.pushState(null, '', `/search?q=${encodeURIComponent(trimmed)}`);
      runSearch(trimmed);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    },
    [runSearch],
  );

  const navigateVerse = useCallback((surah: number, ayah: number) => {
    window.location.href = `/verse/${surah}:${ayah}`;
  }, []);

  // Surah facets for the filter row.
  const facets = useMemo(() => {
    const counts = new Map<number, { name: string; count: number }>();
    for (const r of results) {
      const cur = counts.get(r.surah);
      if (cur) cur.count += 1;
      else counts.set(r.surah, { name: r.surah_name, count: 1 });
    }
    return [...counts.entries()]
      .map(([surah, v]) => ({ surah, ...v }))
      .sort((a, b) => b.count - a.count || a.surah - b.surah);
  }, [results]);

  const filtered = useMemo(() => {
    let r = surahFilter ? results.filter((x) => x.surah === surahFilter) : results;
    if (sort === 'mushaf') {
      r = [...r].sort((a, b) => a.surah - b.surah || a.ayah - b.ayah);
    }
    return r;
  }, [results, surahFilter, sort]);

  const shown = filtered.slice(0, visible);
  const showControls = ran && results.length > 0;

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8">
      <div className="mb-6">
        <UnifiedSearch
          onNavigateVerse={navigateVerse}
          onFullSemanticSearch={submit}
          initialQuery={query}
        />
      </div>

      {loading && (
        <div className="space-y-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="rounded-lg border border-stone-200 bg-white p-4 animate-pulse">
              <span className="block h-3 w-24 rounded bg-stone-100" />
              <span className="mt-2 block h-6 w-full rounded bg-stone-100" />
              <span className="mt-2 block h-3 w-3/4 rounded bg-stone-100" />
            </div>
          ))}
        </div>
      )}

      {!loading && error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center text-red-700">{error}</div>
      )}

      {!loading && !error && showControls && (
        <>
          {/* Header + sort */}
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm text-stone-500">
              <span className="font-semibold text-stone-700">{filtered.length}</span>
              {' '}verse{filtered.length !== 1 ? 's' : ''} matching{' '}
              <span className="text-stone-700">&ldquo;{query}&rdquo;</span>
              {' '}&middot;{' '}
              <span className="text-violet-500">by meaning</span>
            </p>
            <div className="flex items-center gap-1 text-xs">
              {(['relevance', 'mushaf'] as SortMode[]).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setSort(m)}
                  className={`rounded-full px-2.5 py-1 font-medium transition-colors cursor-pointer ${
                    sort === m ? 'bg-stone-800 text-white' : 'text-stone-400 hover:text-stone-600 hover:bg-stone-100'
                  }`}
                >
                  {m === 'relevance' ? 'Relevance' : 'Mushaf order'}
                </button>
              ))}
            </div>
          </div>

          {/* Surah filter chips */}
          {facets.length > 1 && (
            <div className="mb-4 flex items-center gap-1 overflow-x-auto pb-1">
              <button
                type="button"
                onClick={() => setSurahFilter(null)}
                className={`flex-shrink-0 rounded-full px-2.5 py-1 text-xs font-medium transition-colors cursor-pointer ${
                  surahFilter === null ? 'bg-violet-100 text-violet-700' : 'text-stone-400 hover:bg-stone-100'
                }`}
              >
                All <span className="opacity-70">{results.length}</span>
              </button>
              {facets.slice(0, 10).map((f) => (
                <button
                  key={f.surah}
                  type="button"
                  onClick={() => setSurahFilter((cur) => (cur === f.surah ? null : f.surah))}
                  className={`flex-shrink-0 rounded-full px-2.5 py-1 text-xs font-medium whitespace-nowrap transition-colors cursor-pointer ${
                    surahFilter === f.surah ? 'bg-violet-100 text-violet-700' : 'text-stone-400 hover:bg-stone-100'
                  }`}
                >
                  {f.name} <span className="opacity-70">{f.count}</span>
                </button>
              ))}
            </div>
          )}

          {/* Results */}
          <div className="space-y-3">
            {shown.map((r) => (
              <ResultCard key={`${r.surah}:${r.ayah}`} r={r} query={query} />
            ))}
          </div>

          {visible < filtered.length && (
            <div className="mt-5 text-center">
              <button
                type="button"
                onClick={() => setVisible((v) => v + PAGE_SIZE)}
                className="rounded-lg border border-stone-200 bg-white px-4 py-2 text-xs font-semibold text-stone-600 hover:border-violet-300 hover:text-violet-700 transition-colors cursor-pointer"
              >
                Show more ({filtered.length - visible})
              </button>
            </div>
          )}
        </>
      )}

      {/* Empty state */}
      {!loading && !error && ran && results.length === 0 && (
        <div className="rounded-xl border border-stone-200 bg-white px-4 py-12 text-center">
          <p className="text-sm text-stone-500">No verses matched &ldquo;{query}&rdquo;</p>
          <p className="mt-1 text-xs text-stone-400">Try a broader phrase, or ask a question.</p>
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            {SUGGESTED_QUERIES.slice(0, 4).map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => submit(s)}
                className="rounded-full border border-stone-200 bg-stone-50 px-3 py-1 text-xs text-stone-600 hover:border-violet-300 hover:text-violet-700 transition-colors cursor-pointer"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Idle (no query yet) */}
      {!loading && !error && !ran && (
        <div className="rounded-xl border border-stone-200 bg-white px-4 py-12 text-center">
          <p className="text-sm text-stone-500">Search the Qur&rsquo;an by meaning, root, or reference.</p>
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            {SUGGESTED_QUERIES.slice(0, 5).map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => submit(s)}
                className="rounded-full border border-stone-200 bg-stone-50 px-3 py-1 text-xs text-stone-600 hover:border-violet-300 hover:text-violet-700 transition-colors cursor-pointer"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
