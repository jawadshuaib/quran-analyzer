import { useState, useEffect } from 'react';
import type { ContextVerse, VerseSurahContext } from '../types';
import { fetchContext, fetchSurahContext } from '../api/quran';
import VerseRefText from './VerseRefText';

interface Props {
  surah: number;
  ayah: number;
  onNavigate: (surah: number, ayah: number) => void;
}

export default function SurroundingContext({ surah, ayah, onNavigate }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [verses, setVerses] = useState<ContextVerse[]>([]);
  const [loading, setLoading] = useState(false);
  const [surahContext, setSurahContext] = useState<VerseSurahContext | null>(null);
  const [surahContextLoading, setSurahContextLoading] = useState(false);

  useEffect(() => {
    setExpanded(false);
    setVerses([]);
    setSurahContext(null);
  }, [surah, ayah]);

  async function handleToggle() {
    if (expanded) {
      setExpanded(false);
      return;
    }
    // Lazy-load on first expand
    if (verses.length === 0) {
      setLoading(true);
      try {
        const data = await fetchContext(surah, ayah);
        setVerses(data.context);
      } catch {
        // silently fail
      } finally {
        setLoading(false);
      }
    }
    if (!surahContext && !surahContextLoading) {
      setSurahContextLoading(true);
      try {
        const data = await fetchSurahContext(surah, ayah);
        setSurahContext(data?.surah_context ?? null);
      } catch {
        // silently fail
      } finally {
        setSurahContextLoading(false);
      }
    }
    setExpanded(true);
  }

  return (
    <div className="rounded-xl border border-stone-200 bg-white shadow-sm overflow-hidden">
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-stone-50 transition-colors cursor-pointer"
      >
        <span className="text-sm font-semibold text-stone-700">
          Surrounding Context
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
          {(surahContextLoading || !!surahContext?.summary_so_far) && (
            <div className="rounded-lg border border-indigo-100 bg-indigo-50/40 p-4 mb-4">
              {surahContextLoading ? (
                <div className="flex justify-center py-2">
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600" />
                </div>
              ) : (
              <div className="space-y-3">
                <p className="text-xs font-semibold text-indigo-700">What Has Happened So Far</p>
                  <VerseRefText
                    text={surahContext?.summary_so_far ?? ''}
                    className="text-sm text-stone-700"
                    disableVerseNavigation
                  />
              </div>
              )}
            </div>
          )}

          {loading ? (
            <div className="flex justify-center py-4">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-600" />
            </div>
          ) : verses.length === 0 ? (
            <p className="text-sm text-stone-400 text-center py-2">
              No surrounding verses available
            </p>
          ) : (
            <div className="space-y-3">
              {verses.map((v) => {
                const isCurrent = v.surah === surah && v.ayah === ayah;
                return (
                  <button
                    key={`${v.surah}:${v.ayah}`}
                    onClick={() => !isCurrent && onNavigate(v.surah, v.ayah)}
                    disabled={isCurrent}
                    className={`w-full text-left rounded-lg border p-4 transition-colors ${
                      isCurrent
                        ? 'border-emerald-300 bg-emerald-50/50 cursor-default'
                        : 'border-stone-100 bg-stone-50 hover:border-emerald-200 hover:bg-emerald-50/30 cursor-pointer'
                    }`}
                  >
                    <span className="text-xs font-medium text-stone-500">
                      {v.surah}:{v.ayah}
                    </span>
                    <p
                      dir="rtl"
                      lang="ar"
                      className="font-arabic text-lg text-stone-800 leading-relaxed mt-1 mb-1"
                    >
                      {v.text_uthmani}
                    </p>
                    <p className="text-sm text-stone-500 italic">
                      {v.translation}
                    </p>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
