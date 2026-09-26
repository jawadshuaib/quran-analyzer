import { useState, useEffect, useMemo, type ReactNode } from 'react';
import { useSEO } from '../hooks/useSEO';
import { fetchDictionaryRoots, searchDictionary } from '../api/quran';
import type {
  DictionaryRootItem,
  DictionarySearchReason,
  DictionarySearchResponse,
  DictionarySearchResult,
} from '../types';
import { rootDictionaryEntryUrl } from '../content/dictionary-guides/registry';
import { wrapArabicRuns } from '../utils/arabic-runs';

/**
 * /dictionary — the Qur'anic Dictionary index. Every root that has at least
 * one approved, harmonized classical-dictionary entry, grouped alphabetically
 * by its first Arabic radical (the classic lexicon arrangement). Each root
 * links to its /root/<buckwalter> page, where the definitions render via
 * DictionaryPanel.
 *
 * Typing searches /api/dictionary/search (dictionary_search.py): a root in any
 * notation (kfr, k-f-r, ك ف ر, ʿ-l-m, 3lm), a word of the Qur'an in Arabic or
 * transliteration, or an English meaning — matched against glosses, the
 * dictionaries' own English and, where available, semantic vectors. Results
 * are ranked, each with the reason it matched. If the search API fails the
 * page falls back to filtering the list it already has.
 *
 * Sibling of /grammar-glossary and /quran-vocabulary: sticky search at top,
 * a jump-index (here the Arabic alphabet), and a static noscript render on
 * the backend so crawlers see every root link without running JavaScript.
 */

const EXAMPLES = ['k-f-r', 'ر ح م', 'ʿ-l-m', 'kafara', 'يعلمون', 'forgive', 'smoke', "camel's hump"];

function setUrlQuery(q: string) {
  const url = new URL(window.location.href);
  if (q) url.searchParams.set('q', q);
  else url.searchParams.delete('q');
  window.history.replaceState({}, '', url.toString());
}

/** «…» marks the matched words in a dictionary snippet. */
function Snippet({ text }: { text: string }) {
  const parts = text.split(/(«[^»]*»)/g);
  return (
    <>
      {parts.map((p, i) =>
        p.startsWith('«') ? (
          <mark key={i} className="rounded-sm bg-amber-100 px-0.5 text-inherit">
            {wrapArabicRuns(p.slice(1, -1))}
          </mark>
        ) : (
          <span key={i}>{wrapArabicRuns(p)}</span>
        ),
      )}
    </>
  );
}

function ReasonChip({ r, rootBw }: { r: DictionarySearchReason; rootBw: string }) {
  let body: ReactNode;
  let tone = 'bg-stone-100 text-stone-600';
  switch (r.kind) {
    case 'root':
      tone = 'bg-emerald-50 text-emerald-800';
      body = <>{wrapArabicRuns(r.label)}</>;
      break;
    case 'word':
      tone = 'bg-emerald-50 text-emerald-800';
      body = <>{wrapArabicRuns(r.label)}</>;
      break;
    case 'alias':
      tone = 'bg-sky-50 text-sky-800';
      body = <>Means {r.label}</>;
      break;
    case 'gloss':
      return null; // the gloss is already shown on the card
    case 'dictionary':
      tone = 'bg-amber-50 text-amber-900';
      body = (
        <>
          <span className="font-medium">{r.label}</span>
          {r.snippet ? (
            <>
              : <Snippet text={r.snippet} />
            </>
          ) : null}
          {r.detail ? <span className="text-amber-700/70"> · in {r.detail}</span> : null}
        </>
      );
      break;
    case 'semantic':
      tone = 'bg-violet-50 text-violet-800';
      body = r.label ? <>Close in meaning to the {r.label} entry</> : <>Close in meaning</>;
      break;
    case 'guess':
      tone = 'bg-stone-50 text-stone-500';
      body = <>{wrapArabicRuns(r.label)}</>;
      break;
  }
  const cls = `relative z-10 inline-block max-w-full rounded-md px-2 py-0.5 text-[11.5px] leading-snug ${tone}`;
  if (r.dictionary_slug) {
    return (
      <a
        href={rootDictionaryEntryUrl(rootBw, r.dictionary_slug)}
        className={`${cls} hover:underline`}
        title="Open this dictionary's entry for the root"
      >
        {body}
      </a>
    );
  }
  return <span className={cls}>{body}</span>;
}

function ResultCard({ r }: { r: DictionarySearchResult }) {
  return (
    <li className="relative rounded-lg border border-card-border bg-white px-4 py-3 transition-colors hover:border-amber-300 hover:bg-amber-50/30">
      <div className="flex items-baseline gap-3">
        <a
          href={`/root/${encodeURIComponent(r.buckwalter)}`}
          className="shrink-0 font-arabic text-xl text-ink after:absolute after:inset-0 after:rounded-lg"
          dir="rtl"
          lang="ar"
        >
          {r.arabic ? r.arabic.split('').join(' ') : r.buckwalter}
        </a>
        <span className="min-w-0 flex-1">
          {r.gloss && <span className="block text-[13.5px] leading-snug text-ink-secondary">{r.gloss}</span>}
          <span className="mt-0.5 block font-mono text-[11px] text-ink-muted">
            {r.buckwalter} · {r.entries} {r.entries === 1 ? 'entry' : 'entries'}
          </span>
        </span>
      </div>
      {r.reasons.some((x) => x.kind !== 'gloss') && (
        <div className="mt-2 flex flex-wrap gap-1.5 sm:pl-[3.25rem]">
          {r.reasons.map((x, i) => (
            <ReasonChip key={i} r={x} rootBw={r.buckwalter} />
          ))}
        </div>
      )}
    </li>
  );
}

export default function DictionaryIndexPage() {
  const [data, setData] = useState<{
    roots: DictionaryRootItem[];
    rootCount: number;
    entryCount: number;
  } | null>(null);
  const [error, setError] = useState('');
  // ?q= pre-fills the box, so a search can be shared
  const [query, setQuery] = useState(() => new URLSearchParams(window.location.search).get('q') ?? '');
  // the server's answer, tagged with the query it answers (so a stale answer
  // is never shown for a newer query)
  const [answer, setAnswer] = useState<{ q: string; data: DictionarySearchResponse | null; failed: boolean } | null>(null);

  useSEO({
    title: "Qur'anic Dictionary — Classical Arabic Root Definitions",
    description:
      "Browse the classical Arabic lexicon for every Qur'anic root — Lisān al-ʿArab, al-Mufradāt and other classical works — harmonized into readable English with the original Arabic one click away, ordered alphabetically by root.",
    path: '/dictionary',
  });

  // Load the root index
  useEffect(() => {
    let cancelled = false;
    fetchDictionaryRoots()
      .then((resp) => {
        if (cancelled) return;
        setData({ roots: resp.roots, rootCount: resp.root_count, entryCount: resp.entry_count });
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : 'Failed to load dictionary');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Search as the reader types (debounced; the previous request is cancelled)
  const q = query.trim();
  useEffect(() => {
    if (!q) return;
    const ctrl = new AbortController();
    const t = window.setTimeout(() => {
      searchDictionary(q, ctrl.signal)
        .then((d) => setAnswer({ q, data: d, failed: false }))
        .catch((e: unknown) => {
          if ((e as { name?: string })?.name === 'AbortError') return;
          setAnswer({ q, data: null, failed: true });
        });
    }, 180);
    return () => {
      window.clearTimeout(t);
      ctrl.abort();
    };
  }, [q]);

  const current = answer && answer.q === q ? answer : null;
  const searching = !!q && !current;

  // Fallback when the search API is unreachable: the old literal filter
  const filtered = useMemo(() => {
    if (!data) return null;
    const lq = q.toLowerCase();
    if (!lq) return data.roots;
    return data.roots.filter((r) => {
      if (r.buckwalter.toLowerCase().includes(lq)) return true;
      if (r.arabic && r.arabic.includes(q)) return true;
      if (r.gloss && r.gloss.toLowerCase().includes(lq)) return true;
      return false;
    });
  }, [data, q]);

  // Group by first Arabic letter, preserving the backend's alphabetical order.
  const grouped = useMemo(() => {
    const src = q ? (current?.failed ? filtered : null) : filtered;
    if (!src) return [];
    const out: Array<[string, DictionaryRootItem[]]> = [];
    const idx = new Map<string, DictionaryRootItem[]>();
    for (const r of src) {
      const letter = (r.arabic || r.buckwalter || '?').charAt(0);
      let bucket = idx.get(letter);
      if (!bucket) {
        bucket = [];
        idx.set(letter, bucket);
        out.push([letter, bucket]);
      }
      bucket.push(r);
    }
    return out;
  }, [filtered, q, current]);

  const ranked = q && current && !current.failed ? current.data?.results ?? [] : null;
  // while a new answer is on its way, keep showing the last one (dimmed)
  const previous = searching && answer && !answer.failed ? answer.data?.results ?? null : null;
  const shown = ranked ?? previous;

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-10 flex-1">
      <header className="text-center mb-8">
        <p className="text-xs text-ink-muted tracking-[0.08em] uppercase mb-3">Reference</p>
        <h1 className="font-serif text-2xl sm:text-[34px] font-medium tracking-tight leading-tight text-ink mb-3">
          Qur'anic Dictionary
        </h1>
        <p className="text-sm sm:text-[15px] text-ink-secondary max-w-2xl mx-auto leading-relaxed">
          Classical Arabic dictionary definitions for every Qur'anic root — drawn from
          Lisān al-ʿArab, al-Mufradāt and other classical works, harmonized into readable
          English with the original Arabic one click away. Select a root to read its entries.
        </p>
        <p className="mt-2 text-[13px]">
          <a href="/classical-dictionaries" className="text-emerald-700 underline decoration-emerald-200 underline-offset-2 hover:text-emerald-900">
            About the dictionaries: who wrote them and how to read them →
          </a>
        </p>
        {data && (
          <p className="mt-3 text-[13px] text-ink-muted">
            {data.rootCount} roots · {data.entryCount} dictionary entries
          </p>
        )}
      </header>

      {/* Search */}
      <div className="sticky top-0 z-10 bg-cream/90 backdrop-blur-sm -mx-4 px-4 py-3 mb-4 border-b border-card-border">
        <div className="relative max-w-lg mx-auto">
          <input
            type="search"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setUrlQuery(e.target.value.trim());
            }}
            placeholder="A root (k-f-r, ك ف ر), a word (kafara, يعلمون) or a meaning…"
            className="w-full px-4 py-2.5 pr-10 rounded-lg border border-stone-300 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent"
            aria-label="Search the dictionary by root, word or meaning"
            autoComplete="off"
            spellCheck={false}
          />
          {searching ? (
            <span
              className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin rounded-full border-2 border-amber-200 border-t-amber-600"
              aria-hidden
            />
          ) : (
            <svg
              className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-stone-400 pointer-events-none"
              fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z" />
            </svg>
          )}
        </div>
        {!q && (
          <p className="mx-auto mt-2 flex max-w-lg flex-wrap items-center justify-center gap-x-1.5 gap-y-1 text-[11.5px] text-ink-muted">
            <span>Try</span>
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => {
                  setQuery(ex);
                  setUrlQuery(ex);
                }}
                className="rounded-full border border-stone-200 bg-white px-2 py-0.5 text-stone-600 hover:border-amber-300 hover:text-amber-800"
              >
                {wrapArabicRuns(ex)}
              </button>
            ))}
          </p>
        )}
      </div>

      {/* Arabic-letter jump-index */}
      {grouped.length > 1 && !q && (
        <nav
          aria-label="Jump to letter"
          dir="rtl"
          data-allow-no-font-arabic
          className="flex flex-wrap gap-1.5 justify-center mb-8 text-sm"
        >
          {grouped.map(([letter, items]) => (
            <a
              key={letter}
              href={`#let-${letter}`}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full border border-stone-200 bg-white text-stone-600 hover:bg-amber-50 hover:text-amber-700 hover:border-amber-300 transition-colors"
            >
              <span className="font-arabic text-base leading-none" dir="rtl" lang="ar">{letter}</span>
              <span className="text-[10px] text-stone-400">{items.length}</span>
            </a>
          ))}
        </nav>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {!data && !error && !q && (
        <div className="flex justify-center py-16">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-amber-200 border-t-amber-600" />
        </div>
      )}

      {/* Ranked search results */}
      {q && shown && (
        <section aria-live="polite" className={searching ? 'opacity-60 transition-opacity' : ''}>
          <p className="mb-3 text-xs text-stone-500">
            {searching
              ? 'Searching…'
              : shown.length
                ? `${shown.length} ${shown.length === 1 ? 'root' : 'roots'} for “${q}”, best match first`
                : `No roots match “${q}”. Try a root in letters (ك ت ب, k-t-b), a Qurʾānic word, or a meaning in English.`}
          </p>
          <ul className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
            {shown.map((r) => (
              <ResultCard key={r.buckwalter} r={r} />
            ))}
          </ul>
        </section>
      )}
      {q && !shown && searching && (
        <p className="py-10 text-center text-sm text-stone-400">Searching…</p>
      )}

      {/* Fallback: the API failed, so show the literal filter */}
      {q && current?.failed && (
        <p className="text-xs text-stone-500 mb-3">
          Search is unavailable right now; showing roots whose letters or gloss contain “{q}”.
        </p>
      )}

      {/* Alphabetical list */}
      {(!q || current?.failed) && (
        <div className="space-y-8">
          {grouped.map(([letter, items]) => (
            <section key={letter}>
              <h2
                id={`let-${letter}`}
                className="scroll-mt-20 font-serif text-lg text-ink mb-1 pb-1 border-b border-card-border flex items-baseline gap-2"
              >
                <span className="font-arabic text-xl" dir="rtl" lang="ar">{letter}</span>
                <span className="text-[11px] font-sans font-normal text-ink-muted">
                  {items.length} {items.length === 1 ? 'root' : 'roots'}
                </span>
              </h2>
              <ul className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {items.map((r) => (
                  <li key={r.buckwalter}>
                    <a
                      href={`/root/${encodeURIComponent(r.buckwalter)}`}
                      className="group flex items-baseline gap-3 rounded-lg border border-card-border bg-white px-4 py-3 hover:border-amber-300 hover:bg-amber-50/40 transition-colors"
                    >
                      <span className="font-arabic text-xl text-ink shrink-0" dir="rtl" lang="ar">
                        {r.arabic || r.buckwalter}
                      </span>
                      <span className="min-w-0 flex-1">
                        {r.gloss && (
                          <span className="block text-[13.5px] text-ink-secondary leading-snug group-hover:text-amber-800">
                            {r.gloss}
                          </span>
                        )}
                        <span className="mt-0.5 block text-[11px] text-ink-muted font-mono">
                          {r.buckwalter} · {r.entries} {r.entries === 1 ? 'entry' : 'entries'}
                        </span>
                      </span>
                    </a>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}

      {/* Structured data — the dictionary as an ItemList of root pages */}
      {data && data.roots.length > 0 && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'CollectionPage',
              name: "Qur'anic Dictionary — al-nuqta",
              url: 'https://al-nuqta.com/dictionary',
              mainEntity: {
                '@type': 'ItemList',
                numberOfItems: data.roots.length,
                itemListElement: data.roots.map((r, i) => ({
                  '@type': 'ListItem',
                  position: i + 1,
                  name: r.gloss ? `${r.arabic || r.buckwalter} — ${r.gloss}` : r.arabic || r.buckwalter,
                  url: `https://al-nuqta.com/root/${encodeURIComponent(r.buckwalter)}`,
                })),
              },
            }),
          }}
        />
      )}
    </div>
  );
}
