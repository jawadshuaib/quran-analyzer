import type { Word } from '../types';

interface Props {
  selectedWords: { position: number; word: Word; displayText: string }[];
  onDeselect: (position: number) => void;
  onClear: () => void;
  onSearch: () => void;
  loading?: boolean;
}

export default function SelectionFooter({ selectedWords, onDeselect, onClear, onSearch, loading }: Props) {
  return (
    <div className="border-t border-stone-200 bg-stone-50 px-4 py-3 rounded-b-xl -mx-6 -mb-6 mt-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex flex-wrap gap-1.5 min-w-0 flex-1">
          {selectedWords.map(({ position, word, displayText }) => (
            <span
              key={position}
              className="inline-flex items-center gap-1 rounded-full bg-emerald-100 border border-emerald-200 px-2.5 py-1 text-sm"
            >
              <span dir="rtl" lang="ar" className="font-arabic text-emerald-800">
                {displayText}
              </span>
              {word.translation && (
                <span className="text-xs text-emerald-600 max-w-[80px] truncate">
                  {word.translation}
                </span>
              )}
              <button
                onClick={(e) => { e.stopPropagation(); onDeselect(position); }}
                className="ml-0.5 text-emerald-400 hover:text-emerald-700 text-xs font-bold"
                aria-label={`Deselect ${displayText}`}
              >
                &times;
              </button>
            </span>
          ))}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={(e) => { e.stopPropagation(); onClear(); }}
            className="text-xs text-stone-500 hover:text-stone-700 px-2 py-1"
          >
            Clear
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onSearch(); }}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50 transition-colors"
          >
            {loading ? (
              <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
              </svg>
            )}
            Search in Qur'an
          </button>
        </div>
      </div>
    </div>
  );
}
