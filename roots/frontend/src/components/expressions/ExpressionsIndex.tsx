import { useEffect, useMemo, useState } from 'react';
import type { ExpressionKind, ExpressionKindInfo, ExpressionListItem } from '../../types';
import { fetchExpressions } from '../../api/quran';
import { useSEO } from '../../hooks/useSEO';

// Arabic matching ignores vowel marks, so "فضلنا" finds فَضَّلْنَا.
const TASHKEEL = /[ؐ-ًؚ-ٰٟۖ-ۭـ]/g;
const norm = (s: string) => s.toLowerCase().replace(TASHKEEL, '').replace(/[ٱأإآ]/g, 'ا');

/**
 * /expressions — every published Qur'anic expression, grouped by kind.
 * Entries are written offline from the Qur'an's own verses and checked claim
 * by claim against them (roots/backend/expressions_ai.py). The server renders
 * the same list for crawlers; this is the interactive copy.
 */
export default function ExpressionsIndex() {
  const [kinds, setKinds] = useState<ExpressionKindInfo[]>([]);
  const [items, setItems] = useState<ExpressionListItem[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [kind, setKind] = useState<ExpressionKind | 'all'>('all');

  useSEO({
    title: "Qur'anic Expressions",
    description:
      "Recurring and striking expressions of the Qur'an (mirrored verbs, phrase families, near-twin verses, closing pairs, contrasts and formulas), each explained from the Qur'an's own verses.",
    path: '/expressions',
  });

  useEffect(() => {
    fetchExpressions()
      .then((d) => {
        setKinds(d.kinds);
        setItems(d.items);
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : 'Failed to load expressions'))
      .finally(() => setLoading(false));
  }, []);

  const shown = useMemo(() => {
    const q = norm(query.trim());
    return items.filter(
      (i) =>
        (kind === 'all' || i.kind === kind) &&
        (!q ||
          norm(`${i.title} ${i.expression_ar} ${i.transliteration ?? ''} ${i.gloss ?? ''} ${i.summary ?? ''}`).includes(q)),
    );
  }, [items, query, kind]);

  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    items.forEach((i) => (c[i.kind] = (c[i.kind] ?? 0) + 1));
    return c;
  }, [items]);

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <header className="mb-8">
        <p className="mb-1 text-sm font-semibold uppercase tracking-wide text-stone-500">Qur'anic expressions</p>
        <h1 className="text-3xl font-semibold text-stone-800">Expressions</h1>
        <p className="mt-3 text-stone-600 leading-relaxed">
          Phrases the Qur'an returns to, mirrors, or sets side by side: read together, their verses show what no
          single verse shows alone. Each entry is explained from the Qur'an's own words, and every claim was checked
          against the verses it cites.
        </p>
        {!loading && !error && (
          <p className="mt-2 text-sm text-stone-400">{items.length} expressions in {kinds.length} kinds</p>
        )}
      </header>

      {!loading && !error && (
        <div className="mb-8 space-y-3">
          <label htmlFor="expr-filter" className="sr-only">
            Filter expressions
          </label>
          <input
            id="expr-filter"
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter by word, Arabic, or verse theme…"
            className="w-full rounded-lg border border-stone-200 bg-white px-4 py-2.5 text-stone-800 placeholder:text-stone-400 focus:border-gold focus:outline-none focus:ring-2 focus:ring-gold/20"
          />
          <div className="flex flex-wrap gap-2" role="group" aria-label="Kinds of expression">
            {[{ key: 'all' as const, label: 'All' }, ...kinds].map((k) => {
              const active = kind === k.key;
              const n = k.key === 'all' ? items.length : counts[k.key] ?? 0;
              return (
                <button
                  key={k.key}
                  type="button"
                  onClick={() => setKind(k.key)}
                  aria-pressed={active}
                  className={`rounded-full border px-3 py-1 text-sm transition-colors ${
                    active
                      ? 'border-stone-800 bg-stone-800 text-white'
                      : 'border-stone-200 bg-white text-stone-600 hover:border-stone-400'
                  }`}
                >
                  {k.label} <span className={active ? 'text-stone-300' : 'text-stone-400'}>{n}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {loading && (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
        </div>
      )}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center text-red-700">{error}</div>
      )}

      {!loading && !error && shown.length === 0 && (
        <p className="rounded-xl border border-stone-200 bg-white p-5 text-sm text-stone-500">
          No expression matches “{query}”.
        </p>
      )}

      <div className="space-y-10">
        {kinds.map((k) => {
          const mine = shown.filter((i) => i.kind === k.key);
          if (mine.length === 0) return null;
          return (
            <section key={k.key} aria-labelledby={`kind-${k.key}`}>
              <h2 id={`kind-${k.key}`} className="text-sm font-semibold uppercase tracking-wide text-gold">
                {k.label}
              </h2>
              <p className="mb-4 mt-1 text-sm text-stone-500">{k.description}</p>
              <ul className="grid gap-3">
                {mine.map((i) => (
                  <li key={i.slug}>
                    <a
                      href={`/expressions/${i.slug}`}
                      className="group block rounded-xl border border-stone-200 bg-white p-4 transition-colors hover:border-stone-300"
                    >
                      <p dir="rtl" lang="ar" className="font-arabic text-2xl leading-[1.9] text-stone-800">
                        {i.expression_ar}
                      </p>
                      <p className="mt-1 font-medium text-stone-800 group-hover:text-gold-hover">{i.title}</p>
                      {i.gloss && <p className="text-sm italic text-stone-500">{i.gloss}</p>}
                      {i.summary && <p className="mt-2 line-clamp-2 text-sm text-stone-600">{i.summary}</p>}
                      <p className="mt-2 text-xs text-stone-400">
                        {i.verse_count} {i.verse_count === 1 ? 'verse' : 'verses'}
                      </p>
                    </a>
                  </li>
                ))}
              </ul>
            </section>
          );
        })}
      </div>
    </div>
  );
}
