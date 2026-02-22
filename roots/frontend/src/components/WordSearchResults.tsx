import type { WordSearchResponse, WordSearchResult, ResolvedTerm } from '../types';

interface Props {
  data: WordSearchResponse;
  onNavigate: (surah: number, ayah: number) => void;
  onClose: () => void;
}

const TYPE_STYLES: Record<string, string> = {
  lemma: 'bg-emerald-50 border-emerald-200 text-emerald-700',
  root: 'bg-amber-50 border-amber-200 text-amber-700',
  form: 'bg-stone-100 border-stone-300 text-stone-600',
};

function HighlightedArabicText({ verse }: { verse: WordSearchResult }) {
  const words = verse.text_uthmani.split(/\s+/).filter(Boolean);
  const matchSet = new Set(verse.matched_positions);

  return (
    <p
      dir="rtl"
      lang="ar"
      className="font-arabic text-lg text-stone-800 leading-relaxed mb-1"
    >
      {words.map((word, idx) => {
        const pos = idx + 1;
        const isMatched = matchSet.has(pos);
        return (
          <span key={pos}>
            {idx > 0 && ' '}
            {isMatched ? (
              <span className="bg-yellow-200 rounded px-0.5">{word}</span>
            ) : (
              word
            )}
          </span>
        );
      })}
    </p>
  );
}

function TermPill({ term }: { term: ResolvedTerm }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs ${TYPE_STYLES[term.search_type] ?? TYPE_STYLES.form}`}>
      <span dir="rtl" lang="ar" className="font-arabic text-sm">
        {term.display_arabic}
      </span>
      <span className="opacity-60">{term.search_type}</span>
    </span>
  );
}

export default function WordSearchResults({ data, onNavigate, onClose }: Props) {
  return (
    <div className="rounded-xl border border-stone-200 bg-white shadow-sm overflow-hidden">
      <div className="flex items-center justify-between px-6 py-4 border-b border-stone-100">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-semibold text-stone-700">
            Word Search
          </span>
          {data.terms_used.map((t, i) => (
            <TermPill key={i} term={t} />
          ))}
          <span className="text-xs text-stone-400">
            {data.total_found} verse{data.total_found !== 1 ? 's' : ''} found
          </span>
        </div>
        <button
          onClick={onClose}
          className="text-stone-400 hover:text-stone-600 p-1 cursor-pointer"
          aria-label="Close search results"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>
      </div>

      {data.results.length === 0 ? (
        <div className="px-6 py-8 text-center text-stone-400 text-sm">
          No verses found containing all selected words
        </div>
      ) : (
        <div className="px-6 py-4 space-y-3">
          {data.results.map((v) => (
            <button
              key={`${v.surah}:${v.ayah}`}
              onClick={() => onNavigate(v.surah, v.ayah)}
              className="w-full text-left rounded-lg border border-stone-100 bg-stone-50 p-4 hover:border-emerald-200 hover:bg-emerald-50/30 transition-colors cursor-pointer"
            >
              <div className="flex items-start justify-between gap-3 mb-2">
                <span className="text-xs font-medium text-stone-500">
                  Surah {v.surah}, Ayah {v.ayah}
                </span>
                <span className="shrink-0 text-xs text-stone-400">
                  score {v.score}
                </span>
              </div>

              <HighlightedArabicText verse={v} />

              <p className="text-sm text-stone-500 italic line-clamp-2 mb-2">
                {v.translation}
              </p>

              {v.matched_terms.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {v.matched_terms.map((t, i) => (
                    <TermPill key={i} term={t} />
                  ))}
                </div>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
