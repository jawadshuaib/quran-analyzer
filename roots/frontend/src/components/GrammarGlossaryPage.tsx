import { useState, useEffect, useMemo, useRef } from 'react';
import { useSEO } from '../hooks/useSEO';
import { fetchAllGrammarTerms, grammarTermSlug } from '../api/quran';
import type { GrammarTerm } from '../types';
import { wrapArabicRuns } from '../utils/arabic-runs';

/**
 * /grammar-glossary — every grammatical term used across al-nuqta's
 * verse-level grammar notes, grouped pedagogically by function rather
 * than alphabetically. Search (sticky at top) handles direct lookup;
 * the category jump-index gives a structural overview.
 *
 * Categories, their order, and each term's assigned category all come
 * from the backend (GRAMMAR_CATEGORIES + stored per-row). That way the
 * page, noscript render, and sitemap all see identical labels.
 *
 * Each term has a stable anchor (#<slug>) so tooltip "View in glossary"
 * deep-links scroll directly to the right row.
 */

type GlossaryTerm = GrammarTerm & { category: string | null };

export default function GrammarGlossaryPage() {
  const [data, setData] = useState<{ categories: string[]; terms: GlossaryTerm[] } | null>(null);
  const [error, setError] = useState<string>('');
  const [query, setQuery] = useState('');
  const termRefs = useRef<Record<string, HTMLElement | null>>({});
  const catRefs = useRef<Record<string, HTMLElement | null>>({});

  useSEO({
    title: 'Grammar Glossary — Arabic Grammar Terms Used in Quranic Analysis',
    description:
      'Definitions and examples for every Arabic grammar term referenced in al-nuqta\'s verse-level grammar notes, organized by function — cases, particles, rhetorical devices, and 600+ more.',
    path: '/grammar-glossary',
  });

  // Pre-fill query from ?q= for shareable search URLs
  useEffect(() => {
    const p = new URLSearchParams(window.location.search).get('q');
    if (p) setQuery(p);
  }, []);

  // Load all terms
  useEffect(() => {
    let cancelled = false;
    fetchAllGrammarTerms()
      .then((resp) => {
        if (cancelled) return;
        setData({
          categories: resp.categories,
          terms: resp.terms.map((t) => ({
            term_english: t.term_english,
            term_arabic: t.term_arabic,
            plain_explanation: t.plain_explanation,
            example_sentence: t.example_sentence,
            example_translation: t.example_translation,
            category: t.category,
          })),
        });
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : 'Failed to load glossary');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // After terms load, scroll to the fragment if one was in the URL
  useEffect(() => {
    if (!data) return;
    const hash = decodeURIComponent(window.location.hash.replace(/^#/, ''));
    if (!hash) return;
    // Try term first, then category
    const el = termRefs.current[hash] || catRefs.current[hash];
    if (el) {
      requestAnimationFrame(() => {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        el.classList.add('ring-2', 'ring-amber-400', 'ring-offset-2');
        setTimeout(() => {
          el.classList.remove('ring-2', 'ring-amber-400', 'ring-offset-2');
        }, 2200);
      });
    }
  }, [data]);

  // Filter by query across English, Arabic, and explanation
  const filtered = useMemo(() => {
    if (!data) return null;
    const q = query.trim().toLowerCase();
    if (!q) return data.terms;
    return data.terms.filter((t) => {
      if (t.term_english.toLowerCase().includes(q)) return true;
      if (t.term_arabic && t.term_arabic.includes(query.trim())) return true;
      if (t.plain_explanation.toLowerCase().includes(q)) return true;
      return false;
    });
  }, [data, query]);

  // Group by category in the backend-provided display order.
  // Within each category, sort alphabetically (case-insensitive).
  const grouped = useMemo(() => {
    if (!data || !filtered) return [];
    const byCat = new Map<string, GlossaryTerm[]>();
    for (const t of filtered) {
      const c = t.category || 'Other';
      if (!byCat.has(c)) byCat.set(c, []);
      byCat.get(c)!.push(t);
    }
    // Sort each bucket
    for (const arr of byCat.values()) {
      arr.sort((a, b) =>
        a.term_english.localeCompare(b.term_english, undefined, { sensitivity: 'base' }),
      );
    }
    // Emit in the authoritative order from the server
    const out: Array<[string, GlossaryTerm[]]> = [];
    for (const cat of data.categories) {
      const items = byCat.get(cat);
      if (items && items.length > 0) out.push([cat, items]);
    }
    // Any surprise categories not in the canonical list (future-proof)
    for (const [cat, items] of byCat) {
      if (!data.categories.includes(cat)) out.push([cat, items]);
    }
    return out;
  }, [data, filtered]);

  const totalMatching = filtered?.length ?? 0;

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10 flex-1">
      <header className="text-center mb-8">
        <p className="text-xs text-ink-muted tracking-[0.08em] uppercase mb-3">Reference</p>
        <h1 className="font-serif text-2xl sm:text-[34px] font-medium tracking-tight leading-tight text-ink mb-3">
          Grammar Glossary
        </h1>
        <p className="text-sm sm:text-[15px] text-ink-secondary max-w-2xl mx-auto leading-relaxed">
          Every grammatical term referenced in al-nuqta's verse-level{' '}
          <a href="/verse/2:255" className="underline hover:text-amber-700">Notes on Grammar</a>,
          grouped by grammatical function. This is a living glossary — new entries
          appear as new verses are analyzed.
        </p>
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
            placeholder="Search terms (English or Arabic)…"
            className="w-full px-4 py-2.5 pr-10 rounded-lg border border-stone-300 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent"
            aria-label="Search glossary"
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

      {/* Category jump-index */}
      {grouped.length > 1 && !query && (
        <nav aria-label="Jump to category" className="flex flex-wrap gap-1.5 justify-center mb-8 text-xs">
          {grouped.map(([cat, items]) => {
            const slug = `cat-${slugify(cat)}`;
            return (
              <a
                key={cat}
                href={`#${slug}`}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full border border-stone-200 bg-white text-stone-600 hover:bg-amber-50 hover:text-amber-700 hover:border-amber-300 transition-colors"
              >
                {cat}
                <span className="text-[10px] text-stone-400">{items.length}</span>
              </a>
            );
          })}
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
          No terms match "{query}".
        </p>
      )}

      {data && query && (
        <p className="text-xs text-stone-500 mb-3">
          {totalMatching} {totalMatching === 1 ? 'term' : 'terms'} matching "{query}"
          {grouped.length > 0 && ` across ${grouped.length} ${grouped.length === 1 ? 'category' : 'categories'}`}
        </p>
      )}

      {/* Categorized list */}
      <div className="space-y-10">
        {grouped.map(([cat, items]) => {
          const catSlug = `cat-${slugify(cat)}`;
          return (
            <section key={cat}>
              <h2
                id={catSlug}
                ref={(el) => {
                  catRefs.current[catSlug] = el;
                }}
                className="scroll-mt-20 font-serif text-lg text-ink mb-1 pb-1 border-b border-card-border flex items-baseline gap-2"
              >
                <span>{cat}</span>
                <span className="text-[11px] font-sans font-normal text-ink-muted">
                  {items.length} {items.length === 1 ? 'term' : 'terms'}
                </span>
              </h2>
              <dl className="mt-4 space-y-4">
                {items.map((t) => {
                  const slug = grammarTermSlug(t.term_english);
                  return (
                    <div
                      key={t.term_english}
                      id={slug}
                      ref={(el) => {
                        termRefs.current[slug] = el;
                      }}
                      className="scroll-mt-20 rounded-lg border border-card-border bg-white px-5 py-4 transition-shadow"
                    >
                      <dt className="flex items-baseline flex-wrap gap-x-3 gap-y-1">
                        <span className="font-serif text-base font-semibold text-ink">
                          {t.term_english}
                        </span>
                        {t.term_arabic && (
                          <span className="font-arabic text-lg text-stone-700" dir="rtl" lang="ar">
                            {t.term_arabic}
                          </span>
                        )}
                        <a
                          href={`#${slug}`}
                          className="ml-auto text-[11px] text-stone-400 hover:text-amber-700 transition-colors"
                          aria-label={`Permalink to ${t.term_english}`}
                          title="Copy link to this term"
                          onClick={(e) => {
                            e.preventDefault();
                            const url = `${window.location.origin}/grammar-glossary#${slug}`;
                            try {
                              navigator.clipboard.writeText(url);
                            } catch {
                              /* ignore */
                            }
                            window.history.pushState({}, '', `#${slug}`);
                          }}
                        >
                          #
                        </a>
                      </dt>
                      <dd className="mt-2 text-[14.5px] text-ink-secondary leading-relaxed">
                        {wrapArabicRuns(t.plain_explanation)}
                      </dd>
                      {(t.example_sentence || t.example_translation) && (
                        <dd className="mt-3 pt-3 border-t border-stone-100">
                          {t.example_sentence && (
                            <div className="font-arabic text-base text-stone-700" dir="rtl" lang="ar">
                              {t.example_sentence}
                            </div>
                          )}
                          {t.example_translation && (
                            <div className="mt-1 text-xs italic text-stone-500 leading-relaxed">
                              "{wrapArabicRuns(t.example_translation)}"
                            </div>
                          )}
                        </dd>
                      )}
                    </div>
                  );
                })}
              </dl>
            </section>
          );
        })}
      </div>

      {/* Structured data — per-term DefinedTerm entries with category metadata */}
      {data && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'DefinedTermSet',
              name: 'Arabic Grammar Glossary — al-nuqta',
              url: 'https://al-nuqta.com/grammar-glossary',
              hasDefinedTerm: data.terms.map((t) => ({
                '@type': 'DefinedTerm',
                name: t.term_english,
                alternateName: t.term_arabic || undefined,
                description: t.plain_explanation,
                inDefinedTermSet: t.category || undefined,
                url: `https://al-nuqta.com/grammar-glossary#${grammarTermSlug(t.term_english)}`,
              })),
            }),
          }}
        />
      )}
    </div>
  );
}

/** Slug for a category label — used for the #cat-* anchors. Does NOT
 * need to match any backend routine; it's just a page-local id. */
function slugify(s: string): string {
  return s
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^\w\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-');
}
