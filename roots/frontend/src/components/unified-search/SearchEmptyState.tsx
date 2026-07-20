import { SUGGESTED_QUERIES } from '../../utils/recent-searches';

interface Props {
  recents: string[];
  onPick: (query: string) => void;
  onRemove: (query: string) => void;
  onClear: () => void;
}

/**
 * The empty-input dropdown: recent searches (with per-row remove + Clear) and a
 * few curated suggestions. Shown when the search bar is focused but empty and
 * the user has search history. Purely local — no query text leaves the browser.
 */
export default function SearchEmptyState({ recents, onPick, onRemove, onClear }: Props) {
  // A couple of suggestions the user hasn't recently searched.
  const lower = new Set(recents.map((r) => r.toLowerCase()));
  const suggestions = SUGGESTED_QUERIES.filter((s) => !lower.has(s.toLowerCase())).slice(0, 4);

  return (
    <div className="absolute z-50 mt-2 w-full rounded-2xl border border-stone-200 bg-white shadow-xl overflow-hidden">
      <div className="flex items-center justify-between px-4 pt-3 pb-1">
        <span className="text-[10px] font-semibold text-stone-400 uppercase tracking-wider">
          Recent
        </span>
        <button
          type="button"
          onClick={onClear}
          className="text-[10px] text-stone-400 hover:text-stone-600 cursor-pointer"
        >
          Clear
        </button>
      </div>
      <ul>
        {recents.map((q) => (
          <li
            key={q}
            onClick={() => onPick(q)}
            className="group flex items-center gap-2.5 px-4 py-2 cursor-pointer hover:bg-stone-50 transition-colors"
          >
            <svg viewBox="0 0 20 20" className="h-3.5 w-3.5 shrink-0 text-stone-300" fill="none" stroke="currentColor" strokeWidth={1.5}>
              <circle cx="10" cy="10" r="7.25" />
              <path d="M10 6.5V10l2.5 1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span className="flex-1 min-w-0 truncate text-sm text-stone-700">{q}</span>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onRemove(q);
              }}
              aria-label={`Remove "${q}" from recent searches`}
              className="shrink-0 rounded p-0.5 text-stone-300 opacity-0 group-hover:opacity-100 hover:text-stone-500 transition-opacity cursor-pointer"
            >
              <svg viewBox="0 0 20 20" className="h-3.5 w-3.5" fill="currentColor">
                <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
              </svg>
            </button>
          </li>
        ))}
      </ul>

      {suggestions.length > 0 && (
        <div className="border-t border-stone-100 px-4 py-3">
          <span className="text-[10px] font-semibold text-stone-400 uppercase tracking-wider">
            Try
          </span>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {suggestions.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => onPick(s)}
                className="rounded-full border border-stone-200 bg-stone-50 px-2.5 py-1 text-xs text-stone-600 hover:border-violet-300 hover:text-violet-700 transition-colors cursor-pointer"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
