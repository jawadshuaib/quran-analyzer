import { useState, useEffect } from 'react';
import type { AITranslationData } from '../types';
import { fetchAITranslation } from '../api/quran';

interface Props {
  surah: number;
  ayah: number;
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
    <div className="rounded-xl border border-violet-200 bg-white shadow-sm overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-violet-50/50 transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-violet-700">
            AI Translation
          </span>
          <span className="text-[10px] font-medium text-violet-400 bg-violet-50 px-1.5 py-0.5 rounded">
            experimental
          </span>
        </div>
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
                    {data.departure_notes}
                  </p>
                </div>
              )}

              <div className="flex items-center gap-3 pt-1">
                <span className="text-[10px] font-medium text-violet-500 bg-violet-50 px-2 py-0.5 rounded-full">
                  {data.model_name}
                </span>
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
