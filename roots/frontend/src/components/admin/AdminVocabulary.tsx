import { useState, useEffect, useRef } from 'react';
import { searchAdminRoots } from '../../api/admin';
import type { RootSearchHit } from '../../api/admin';

/**
 * Admin: Vocabulary landing.
 *
 * - Search box: query roots by Buckwalter, Arabic form, transliteration,
 *   or English meaning. Reuses the same /api/roots/search endpoint the
 *   homepage uses. Results clickable → opens the studio.
 * - "Already studied" list: roots that have a term_surveys row.
 *   Sorted by most-recently-surveyed.
 *
 * Hitting Enter / clicking a row navigates to /admin/vocabulary/<bw>.
 */
export default function AdminVocabulary() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<RootSearchHit[]>([]);
  const [searching, setSearching] = useState(false);
  const [studied, setStudied] = useState<Array<{
    root_buckwalter: string;
    root_arabic: string;
    canonical_english: string | null;
    occurrence_count: number;
    surveyor_run_at: string | null;
  }>>([]);
  const debounceRef = useRef<number | null>(null);

  // Live search with debounce
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    if (debounceRef.current) window.clearTimeout(debounceRef.current);
    debounceRef.current = window.setTimeout(() => {
      setSearching(true);
      searchAdminRoots(query.trim())
        .then((hits) => setResults(hits))
        .catch(() => setResults([]))
        .finally(() => setSearching(false));
    }, 220);
  }, [query]);

  // Already-studied list (uses public /api/quran-vocabulary)
  useEffect(() => {
    fetch('/api/quran-vocabulary')
      .then((r) => r.json())
      .then((d: { terms: Array<{
        root_buckwalter: string;
        root_arabic: string;
        canonical_english: string | null;
        occurrence_count: number;
      }> }) => {
        setStudied(
          d.terms.map((t) => ({
            ...t,
            surveyor_run_at: null,
          })),
        );
      })
      .catch(() => setStudied([]));
  }, []);

  const studiedSet = new Set(studied.map((s) => s.root_buckwalter));

  function go(rootBw: string) {
    window.location.href = `/admin/vocabulary/${encodeURIComponent(rootBw)}`;
  }

  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between">
        <h1 className="text-xl font-semibold text-stone-800">Vocabulary Studio</h1>
        <span className="text-xs text-stone-400">{studied.length} root{studied.length === 1 ? '' : 's'} surveyed</span>
      </div>
      <p className="text-sm text-stone-500 mb-6">
        Survey a Qur'anic root for its abstract semantic core, then bulk-apply
        canonical revisions across verse translations, grammar notes, and
        word meanings. Each revision is reversible per row.
      </p>

      {/* Search */}
      <div className="mb-8">
        <label className="block text-sm font-medium text-stone-700 mb-2">
          Search a root
        </label>
        <div className="relative">
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && results[0]) {
                go(results[0].root_buckwalter);
              }
            }}
            placeholder="Buckwalter (e.g. Slw), Arabic (e.g. ص-ل-و), transliteration, or English meaning…"
            className="w-full px-4 py-2.5 pr-10 rounded-lg border border-stone-300 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent font-mono"
            autoFocus
          />
          {searching && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin rounded-full border-2 border-stone-200 border-t-stone-500" />
          )}
        </div>

        {/* Search results */}
        {results.length > 0 && (
          <div className="mt-3 rounded-lg border border-stone-200 bg-white divide-y divide-stone-100 overflow-hidden">
            {results.map((r) => (
              <button
                key={r.root_buckwalter}
                onClick={() => go(r.root_buckwalter)}
                className="w-full px-4 py-3 text-left hover:bg-amber-50 cursor-pointer flex items-center gap-3"
              >
                <span className="font-serif text-lg text-stone-800 min-w-[5rem]" lang="ar">
                  {r.root_arabic}
                </span>
                <span className="font-mono text-xs text-stone-500 min-w-[3rem]">
                  {r.root_buckwalter}
                </span>
                {typeof r.occurrences === 'number' && (
                  <span className="text-[11px] text-stone-400">
                    {r.occurrences} occurrence{r.occurrences === 1 ? '' : 's'}
                  </span>
                )}
                {r.meaning && (
                  <span className="text-xs text-stone-600 truncate">{r.meaning}</span>
                )}
                {studiedSet.has(r.root_buckwalter) && (
                  <span className="ml-auto px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-100 text-emerald-700 border border-emerald-200">
                    surveyed
                  </span>
                )}
              </button>
            ))}
          </div>
        )}

        {query.trim() && !searching && results.length === 0 && (
          <p className="mt-3 text-xs text-stone-400">No roots match "{query}".</p>
        )}
      </div>

      {/* Already studied */}
      <div>
        <h2 className="text-sm font-semibold text-stone-700 mb-3">Already surveyed</h2>
        {studied.length === 0 ? (
          <p className="text-xs text-stone-400">No roots surveyed yet.</p>
        ) : (
          <div className="rounded-lg border border-stone-200 bg-white divide-y divide-stone-100 overflow-hidden">
            {studied.map((s) => (
              <button
                key={s.root_buckwalter}
                onClick={() => go(s.root_buckwalter)}
                className="w-full px-4 py-3 text-left hover:bg-amber-50 cursor-pointer flex items-center gap-3"
              >
                <span className="font-serif text-lg text-stone-800 min-w-[5rem]" lang="ar">
                  {s.root_arabic}
                </span>
                <span className="font-mono text-xs text-stone-500 min-w-[3rem]">
                  {s.root_buckwalter}
                </span>
                <span className="text-stone-300">→</span>
                <span className="text-sm font-medium text-amber-700">
                  {s.canonical_english ?? '(no canonical yet)'}
                </span>
                <span className="ml-auto text-[11px] text-stone-400">
                  {s.occurrence_count} occurrences
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
