import { useState, useEffect, useRef, useCallback } from 'react';
import type { AITranslationData } from '../types';
import { fetchAITranslation } from '../api/quran';
import VerseRefText from './VerseRefText';

interface Props {
  surah: number;
  ayah: number;
}

function MethodologyTooltip() {
  const [show, setShow] = useState(false);
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clear = useCallback(() => {
    if (hideTimer.current) { clearTimeout(hideTimer.current); hideTimer.current = null; }
  }, []);

  useEffect(() => () => clear(), [clear]);

  return (
    <span className="relative inline-block">
      <span
        className="inline-flex items-center justify-center w-4 h-4 rounded-full align-middle
                   text-[10px] font-medium text-violet-300 border border-violet-200
                   cursor-help hover:text-violet-500 hover:border-violet-400 transition-colors -mt-1"
        onMouseEnter={() => { clear(); setShow(true); }}
        onMouseLeave={() => { hideTimer.current = setTimeout(() => setShow(false), 200); }}
        onClick={(e) => e.stopPropagation()}
      >
        ?
      </span>
      {show && (
        <span
          className="absolute left-1/2 -translate-x-1/2 top-full mt-2 z-[100]
                     bg-white rounded-lg shadow-lg border border-violet-200 p-3
                     w-[320px] text-xs text-stone-600 leading-relaxed"
          onMouseEnter={clear}
          onMouseLeave={() => { hideTimer.current = setTimeout(() => setShow(false), 200); }}
          onClick={(e) => e.stopPropagation()}
        >
          <span className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3
                          bg-white border-l border-t border-violet-200 rotate-45" />
          <span className="block font-semibold text-violet-700 mb-1">Methodology</span>
          <span className="block">
            Each verse is translated by an LLM that receives the full morphological
            breakdown (root, lemma, part of speech for every word), cross-references
            to other verses sharing the same roots and lemmas weighted by TF-IDF
            similarity, and Semitic cognate data from Hebrew, Aramaic, and Akkadian.
          </span>
          <span className="block mt-1.5">
            The model is instructed to stay faithful to the Arabic grammar,
            prefer established meanings unless the linguistic evidence suggests
            a departure, and document any differences in the Departure Notes.
          </span>
        </span>
      )}
    </span>
  );
}

export default function AITranslation({ surah, ayah }: Props) {
  const [data, setData] = useState<AITranslationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setData(null);
    setExpanded(true);

    fetchAITranslation(surah, ayah)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch(() => {
        if (!cancelled) setData(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [surah, ayah]);

  // Don't render anything if no translation exists
  if (!loading && !data) return null;

  return (
    <div className="rounded-xl border border-violet-200 bg-white shadow-sm">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-violet-50/50 transition-colors cursor-pointer"
      >
        <span className="inline-flex items-center gap-2">
          <span className="text-sm font-semibold text-violet-700 leading-none">
            AI Translation
          </span>
          <MethodologyTooltip />
        </span>
        <svg
          className={`h-4 w-4 text-violet-400 transition-transform duration-200 ${
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
        <div className="border-t border-violet-100 px-6 py-4">
          {loading ? (
            <div className="flex justify-center py-4">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-violet-200 border-t-violet-600" />
            </div>
          ) : data ? (
            <div className="space-y-3">
              <p className="text-stone-800 leading-relaxed">
                {data.translation}
              </p>

              {data.departure_notes && (
                <div className="rounded-lg bg-violet-50 border border-violet-100 p-3">
                  <p className="text-xs font-medium text-violet-600 mb-1">Departure Notes</p>
                  <p className="text-sm text-violet-800 leading-relaxed">
                    <VerseRefText text={data.departure_notes} />
                  </p>
                </div>
              )}

              <div className="flex items-center gap-3 pt-1">
                <span className="text-[10px] text-stone-400">
                  {new Date(data.created_at + 'Z').toLocaleDateString()}
                </span>
              </div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
