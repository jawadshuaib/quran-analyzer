import type { Word } from '../types/index.ts';
import { FRONTEND_BASE } from '../config.ts';

interface Props {
  word: Word;
  aiMeaning?: string;
  preferredTranslation?: string;
  preferredSource?: 'conventional' | 'ai' | 'judge';
}

export default function WordTooltip({ word, aiMeaning, preferredTranslation }: Props) {
  const mainRootSeg = word.segments.find((s) => s.root_arabic);
  const mainRoot = mainRootSeg?.root_arabic;
  const mainLemma = word.segments.find((s) => s.lemma_arabic)?.lemma_arabic;
  const posLabels = word.segments
    .map((s) => s.pos)
    .filter((p) => p && p !== 'Prefix' && p !== 'Suffix');

  return (
    <div
      dir="ltr"
      className="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-50
                 bg-white rounded-lg shadow-lg border border-stone-200 p-3
                 min-w-[140px] max-w-[240px] text-sm text-stone-700"
      onClick={(e) => e.stopPropagation()}
    >
      {/* Arrow */}
      <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3
                      bg-white border-l border-t border-stone-200 rotate-45" />

      {preferredTranslation ? (
        <div className="mb-1.5 text-center">
          <span className="font-semibold text-stone-900">{preferredTranslation}</span>
        </div>
      ) : (
        <>
          {word.translation && (
            <div className="font-semibold text-stone-900 mb-1.5 text-center">
              {word.translation}
            </div>
          )}
          {aiMeaning && (
            <div className="mb-1.5 text-center">
              <div className="inline-flex items-center gap-1">
                {word.translation && (
                  <span className="text-[10px] font-bold bg-violet-100 text-violet-600 rounded px-1 py-px uppercase">
                    AI
                  </span>
                )}
                <span className="text-xs font-medium text-violet-700">{aiMeaning}</span>
              </div>
            </div>
          )}
        </>
      )}

      {posLabels.length > 0 && (
        <div className="flex flex-wrap justify-center gap-1 mb-1.5">
          {posLabels.map((pos, i) => (
            <span
              key={i}
              className="text-xs bg-stone-100 text-stone-600 rounded-full px-2 py-0.5"
            >
              {pos}
            </span>
          ))}
        </div>
      )}

      <div className="space-y-0.5 text-xs text-stone-500">
        {mainRoot && (
          <div className="flex justify-between gap-3">
            <span>Root</span>
            <span
              dir="rtl"
              lang="ar"
              className="font-arabic text-sm text-emerald-700 underline decoration-emerald-300 underline-offset-2 cursor-pointer hover:text-emerald-900 transition-colors"
              onClick={() =>
                chrome.tabs.create({
                  url: `${FRONTEND_BASE}/root/${encodeURIComponent(mainRootSeg!.root_buckwalter)}`,
                })
              }
            >
              {mainRoot}
            </span>
          </div>
        )}
        {mainLemma && (
          <div className="flex justify-between gap-3">
            <span>Lemma</span>
            <span dir="rtl" lang="ar" className="font-arabic text-sm text-stone-700">
              {mainLemma}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
