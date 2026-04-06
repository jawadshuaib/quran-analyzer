import { useState, useRef, useEffect, useCallback } from 'react';
import { searchRoots } from '../api/quran';
import type { RootSearchResult } from '../api/quran';

export default function RootSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<RootSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [selectedIdx, setSelectedIdx] = useState(-1);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const doSearch = useCallback(async (q: string) => {
    if (!q.trim() || q.trim().length < 1) {
      setResults([]);
      setOpen(false);
      return;
    }
    setLoading(true);
    try {
      const data = await searchRoots(q, 8);
      setResults(data);
      setOpen(data.length > 0);
      setSelectedIdx(-1);
    } catch {
      setResults([]);
      setOpen(false);
    } finally {
      setLoading(false);
    }
  }, []);

  function handleChange(value: string) {
    setQuery(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(value), 250);
  }

  function navigate(root: RootSearchResult) {
    setOpen(false);
    setQuery('');
    if (root.in_curriculum) {
      window.location.href = `/learning/root/${root.root_buckwalter}`;
    } else {
      window.location.href = `/root/${encodeURIComponent(root.root_buckwalter)}`;
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!open || results.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIdx((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter' && selectedIdx >= 0) {
      e.preventDefault();
      navigate(results[selectedIdx]);
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  return (
    <div ref={wrapperRef} className="relative w-full max-w-md mx-auto">
      <div className="relative">
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-400 pointer-events-none"
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => handleChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => { if (results.length > 0) setOpen(true); }}
          placeholder="Search roots — e.g. xlq, خلق, khalaq, create"
          className="w-full rounded-xl border border-stone-300 bg-white pl-10 pr-4 py-2.5 text-sm
                     placeholder:text-stone-400 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 focus:outline-none"
          autoComplete="off"
          spellCheck={false}
        />
        {loading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-600" />
          </div>
        )}
      </div>

      {open && results.length > 0 && (
        <ul className="absolute z-50 mt-2 w-full rounded-2xl border border-stone-200 bg-white shadow-xl overflow-hidden max-h-[480px] overflow-y-auto">
          {results.map((r, i) => (
            <li
              key={r.root_buckwalter}
              className={`group px-4 py-4 cursor-pointer transition-all duration-150 ${
                i === selectedIdx ? 'bg-emerald-50/80 shadow-sm' : 'hover:bg-stone-50/60'
              } ${i > 0 ? 'border-t border-stone-100' : ''}`}
              onMouseEnter={() => setSelectedIdx(i)}
              onClick={() => navigate(r)}
            >
              <div className="flex items-start gap-4">
                {/* Arabic root — prominent circle */}
                <div className="shrink-0 w-14 h-14 rounded-full bg-gradient-to-br from-emerald-50 to-emerald-100 border border-emerald-200/60 flex items-center justify-center group-hover:from-emerald-100 group-hover:to-emerald-200 group-hover:border-emerald-300 group-hover:shadow-md transition-all duration-150">
                  <span className="font-arabic text-lg text-emerald-800 font-bold group-hover:text-emerald-900 transition-colors" dir="rtl">
                    {r.root_arabic}
                  </span>
                </div>

                <div className="flex-1 min-w-0 pt-0.5">
                  {/* Top row: Buckwalter + badges */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-base font-mono text-emerald-700 font-semibold">
                      {r.root_buckwalter}
                    </span>
                    <span className="text-xs text-stone-400 tabular-nums">
                      {r.frequency.toLocaleString()} verse{r.frequency !== 1 ? 's' : ''}
                    </span>
                    {r.in_curriculum && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-semibold tracking-wide uppercase">
                        Learn
                      </span>
                    )}
                  </div>

                  {/* Meaning */}
                  {r.meaning && (
                    <p className="text-sm text-stone-600 mt-0.5 truncate">
                      {r.meaning}
                    </p>
                  )}

                  {/* Sample verse — Arabic with highlighted root words */}
                  {r.sample_verse && (
                    <div className="mt-2">
                      <div className="flex items-start gap-1.5">
                        <svg className="w-3 h-3 shrink-0 text-stone-300 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                        <span className="text-[11px] text-stone-400 font-medium shrink-0">{r.sample_verse.ref}</span>
                      </div>
                      <p className="font-arabic text-sm leading-[1.8] text-stone-400 mt-1 group-hover:text-stone-500 transition-colors" dir="rtl" lang="ar">
                        {r.sample_verse.starts_truncated && <span>... </span>}
                        {r.sample_verse.words.map((word, wi) => {
                          const isMatch = r.sample_verse!.matched_positions.includes(wi + 1);
                          return (
                            <span key={wi}>
                              {wi > 0 && ' '}
                              <span className={isMatch
                                ? 'text-emerald-700 font-bold bg-emerald-100/80 px-1 py-0.5 rounded group-hover:bg-emerald-200 group-hover:text-emerald-900 group-hover:shadow-sm transition-all'
                                : ''
                              }>
                                {word}
                              </span>
                            </span>
                          );
                        })}
                        {r.sample_verse.ends_truncated && <span> ...</span>}
                      </p>
                    </div>
                  )}
                </div>

                {/* Arrow indicator */}
                <svg className={`w-4 h-4 shrink-0 mt-1.5 transition-colors ${i === selectedIdx ? 'text-emerald-500' : 'text-stone-300'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
