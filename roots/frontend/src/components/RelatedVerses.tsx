import { useState, useEffect } from 'react';
import type { RelatedVerse } from '../types';
import { fetchRelatedVerses } from '../api/quran';

interface Props {
  surah: number;
  ayah: number;
  onNavigate: (surah: number, ayah: number) => void;
  forceCollapse?: boolean;
}

export default function RelatedVerses({ surah, ayah, onNavigate, forceCollapse }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [verses, setVerses] = useState<RelatedVerse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch automatically when verse changes, auto-expand if results found
  useEffect(() => {
    setExpanded(false);
    setVerses([]);
    setError('');
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const data = await fetchRelatedVerses(surah, ayah);
        if (cancelled) return;
        setVerses(data.related);
        if (data.related.length > 0) setExpanded(true);
      } catch {
        if (!cancelled) setError('Failed to load related verses');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [surah, ayah]);

  // Collapse when parent requests it (e.g. word search results are showing)
  useEffect(() => {
    if (forceCollapse) setExpanded(false);
  }, [forceCollapse]);

  // Don't render anything if no results and done loading
  if (!loading && !error && verses.length === 0) return null;

  return (
    <div className="rounded-xl border border-stone-200 bg-white shadow-sm overflow-hidden">
      {loading && (
        <div className="flex justify-center px-6 py-6">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-600" />
        </div>
      )}

      {error && (
        <p className="text-sm text-red-600 text-center px-6 py-4">{error}</p>
      )}

      {verses.length > 0 && (
        <>
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-stone-50 transition-colors cursor-pointer"
          >
            <span className="text-sm font-semibold text-stone-700">
              Related Verses
            </span>
            <svg
              className={`h-4 w-4 text-stone-400 transition-transform duration-200 ${
                expanded ? 'rotate-180' : ''
              }`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {expanded && (
            <div className="border-t border-stone-100 px-6 py-4">
            <div className="space-y-3">
              {verses.map((v) => (
                <button
                  key={`${v.surah}:${v.ayah}`}
                  onClick={() => onNavigate(v.surah, v.ayah)}
                  className="w-full text-left rounded-lg border border-stone-100 bg-stone-50 p-4 hover:border-emerald-200 hover:bg-emerald-50/30 transition-colors cursor-pointer"
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <span className="text-xs font-medium text-stone-500">
                      Surah {v.surah}, Ayah {v.ayah}
                    </span>
                    <span className="shrink-0 inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700">
                      {Math.round(v.similarity_score * 100)}% match
                    </span>
                  </div>

                  <p
                    dir="rtl"
                    lang="ar"
                    className="font-arabic text-lg text-stone-800 leading-relaxed line-clamp-2 mb-1"
                  >
                    {v.text_uthmani}
                  </p>

                  <p className="text-sm text-stone-500 italic line-clamp-2 mb-2">
                    {v.translation}
                  </p>

                  {v.shared_roots.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {v.shared_roots.map((root) => (
                        <span
                          key={root.root_buckwalter}
                          className="inline-flex items-center gap-1 rounded-full bg-sky-50 border border-sky-200 px-2 py-0.5 text-xs text-sky-700"
                        >
                          <span dir="rtl" lang="ar" className="font-arabic text-sm">
                            {root.root_arabic}
                          </span>
                          <span className="text-sky-500">
                            ({root.root_buckwalter})
                          </span>
                        </span>
                      ))}
                    </div>
                  )}
                </button>
              ))}
            </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
