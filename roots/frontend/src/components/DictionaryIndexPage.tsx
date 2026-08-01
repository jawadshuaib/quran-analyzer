import { useState, useEffect, useMemo } from 'react';
import { useSEO } from '../hooks/useSEO';
import { fetchDictionaryRoots } from '../api/quran';
import type { DictionaryRootItem } from '../types';

/**
 * /dictionary — the Qur'anic Dictionary index. Every root that has at least
 * one approved, harmonized classical-dictionary entry, grouped alphabetically
 * by its first Arabic radical (the classic lexicon arrangement). Each root
 * links to its /root/<buckwalter> page, where the definitions render via
 * DictionaryPanel.
 *
 * Sibling of /grammar-glossary and /quran-vocabulary: sticky search at top,
 * a jump-index (here the Arabic alphabet), and a static noscript render on
 * the backend so crawlers see every root link without running JavaScript.
 */
export default function DictionaryIndexPage() {
  const [data, setData] = useState<{
    roots: DictionaryRootItem[];
    rootCount: number;
    entryCount: number;
  } | null>(null);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');

  useSEO({
    title: "Qur'anic Dictionary — Classical Arabic Root Definitions",
    description:
      "Browse the classical Arabic lexicon for every Qur'anic root — Lisān al-ʿArab, al-Mufradāt and other classical works — harmonized into readable English with the original Arabic one click away, ordered alphabetically by root.",
    path: '/dictionary',
  });

  // Pre-fill query from ?q= for shareable search URLs
  useEffect(() => {
    const p = new URLSearchParams(window.location.search).get('q');
    if (p) setQuery(p);
  }, []);

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

  // Filter by query across Buckwalter, Arabic, and the gloss
  const filtered = useMemo(() => {
    if (!data) return null;
    const q = query.trim().toLowerCase();
    const qAr = query.trim();
    if (!q) return data.roots;
    return data.roots.filter((r) => {
      if (r.buckwalter.toLowerCase().includes(q)) return true;
      if (r.arabic && r.arabic.includes(qAr)) return true;
      if (r.gloss && r.gloss.toLowerCase().includes(q)) return true;
      return false;
    });
  }, [data, query]);

  // Group by first Arabic letter, preserving the backend's alphabetical order.
  const grouped = useMemo(() => {
    if (!filtered) return [];
    const out: Array<[string, DictionaryRootItem[]]> = [];
    const idx = new Map<string, DictionaryRootItem[]>();
    for (const r of filtered) {
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
  }, [filtered]);

  const totalMatching = filtered?.length ?? 0;

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
              const url = new URL(window.location.href);
              if (e.target.value) url.searchParams.set('q', e.target.value);
              else url.searchParams.delete('q');
              window.history.replaceState({}, '', url.toString());
            }}
            placeholder="Search roots (Arabic, transliteration, or meaning)…"
            className="w-full px-4 py-2.5 pr-10 rounded-lg border border-stone-300 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent"
            aria-label="Search dictionary roots"
          />
          <svg
            className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-stone-400 pointer-events-none"
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z" />
          </svg>
        </div>
      </div>

      {/* Arabic-letter jump-index */}
      {grouped.length > 1 && !query && (
        <nav aria-label="Jump to letter" dir="rtl" className="flex flex-wrap gap-1.5 justify-center mb-8 text-sm">
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

      {!data && !error && (
        <div className="flex justify-center py-16">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-amber-200 border-t-amber-600" />
        </div>
      )}

      {data && grouped.length === 0 && (
        <p className="text-center text-stone-400 py-12 text-sm">
          No roots match "{query}".
        </p>
      )}

      {data && query && (
        <p className="text-xs text-stone-500 mb-3">
          {totalMatching} {totalMatching === 1 ? 'root' : 'roots'} matching "{query}"
        </p>
      )}

      {/* Alphabetical list */}
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
