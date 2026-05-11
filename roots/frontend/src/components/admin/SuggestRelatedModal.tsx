import { useState, useEffect } from 'react';
import { suggestRelatedVerses } from '../../api/admin';
import type { RelatedVerse } from '../../api/admin';

interface Props {
  seedChapter: number;
  seedAyah: number;
  onSelect: (chapter: number, ayah: number) => void;
  onClose: () => void;
}

export default function SuggestRelatedModal({ seedChapter, seedAyah, onSelect, onClose }: Props) {
  const [results, setResults] = useState<RelatedVerse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');
    suggestRelatedVerses(seedChapter, seedAyah)
      .then((data) => {
        if (!cancelled) setResults(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to fetch suggestions');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [seedChapter, seedAyah]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[80vh] flex flex-col mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-stone-200">
          <div>
            <h3 className="font-semibold text-stone-800">Suggest Related Verses</h3>
            <p className="text-xs text-stone-500 mt-0.5">
              Based on {seedChapter}:{seedAyah} — shared root analysis
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-stone-400 hover:text-stone-600 text-xl leading-none cursor-pointer"
          >
            &times;
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
          {loading && (
            <div className="flex justify-center py-8">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-stone-300 border-t-stone-600" />
            </div>
          )}

          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
              {error}
            </div>
          )}

          {!loading && !error && results.length === 0 && (
            <p className="text-sm text-stone-500 text-center py-6">No related verses found.</p>
          )}

          {results.map((v) => (
            <div
              key={`${v.chapter}:${v.ayah}`}
              className="border border-stone-200 rounded-lg p-3 hover:border-stone-300 transition-colors"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-stone-800">{v.ref}</span>
                    <span className="text-xs text-stone-400">
                      {(v.similarity_score * 100).toFixed(0)}% match
                    </span>
                  </div>
                  <p className="text-sm text-stone-600 line-clamp-2">{v.translation}</p>
                  {v.shared_roots.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {v.shared_roots.map((r) => (
                        <span
                          key={r.root_buckwalter}
                          dir="rtl"
                          lang="ar"
                          className="inline-block font-arabic text-xs bg-stone-100 text-stone-600 px-1.5 py-0.5 rounded"
                        >
                          {r.root_arabic}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <button
                  onClick={() => onSelect(v.chapter, v.ayah)}
                  className="shrink-0 text-xs font-medium bg-stone-800 text-white px-3 py-1.5 rounded-md hover:bg-stone-700 transition-colors cursor-pointer"
                >
                  Add
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-stone-200">
          <button
            onClick={onClose}
            className="text-sm text-stone-500 hover:text-stone-700 cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
