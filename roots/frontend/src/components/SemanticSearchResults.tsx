import type { SemanticSearchResponse } from '../api/quran';

interface Props {
  data: SemanticSearchResponse;
  onNavigate: (surah: number, ayah: number) => void;
  onClose: () => void;
}

export default function SemanticSearchResults({ data, onNavigate, onClose }: Props) {
  if (!data.results.length) {
    return (
      <div className="rounded-xl border border-stone-200 bg-white p-6 text-center">
        <p className="text-stone-500">No matching verses found for &ldquo;{data.query}&rdquo;</p>
        <button
          onClick={onClose}
          className="mt-3 text-sm text-stone-400 hover:text-stone-600 cursor-pointer"
        >
          Dismiss
        </button>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-stone-200 bg-white shadow-sm overflow-hidden">
      <div className="flex items-center justify-between border-b border-stone-100 px-5 py-3 bg-violet-50/50">
        <div>
          <h3 className="text-sm font-semibold text-violet-800">
            Semantic Search Results
          </h3>
          <p className="text-xs text-stone-500 mt-0.5">
            {data.total} verse{data.total !== 1 ? 's' : ''} matching &ldquo;{data.query}&rdquo;
          </p>
        </div>
        <button
          onClick={onClose}
          className="rounded-md p-1 text-stone-400 hover:bg-stone-100 hover:text-stone-600
                     focus:ring-2 focus:ring-violet-400 transition-colors cursor-pointer"
          aria-label="Close semantic search results"
          title="Close"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <ul className="divide-y divide-stone-100">
        {data.results.map((r) => (
          <li key={`${r.surah}:${r.ayah}`}>
            <button
              className="w-full px-5 py-4 text-left hover:bg-stone-50 transition-colors cursor-pointer"
              onClick={() => onNavigate(r.surah, r.ayah)}
              aria-label={`View ${r.surah_name} ${r.surah}:${r.ayah}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <span className="text-xs font-medium text-violet-600">
                    {r.surah_name} {r.surah}:{r.ayah}
                  </span>
                  <p
                    className="mt-1.5 text-right text-lg leading-loose text-stone-800 font-['Scheherazade_New',serif]"
                    dir="rtl"
                  >
                    {r.text_uthmani}
                  </p>
                  {r.translation && (
                    <p className="mt-1 text-sm text-stone-600 leading-relaxed line-clamp-2">
                      {r.translation}
                    </p>
                  )}
                </div>
                <span className="shrink-0 mt-0.5 rounded-full bg-violet-100 px-2 py-0.5 text-[10px] font-medium text-violet-700">
                  {Math.round(r.score * 100)}%
                </span>
              </div>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
