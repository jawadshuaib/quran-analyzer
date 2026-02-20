import { useState } from 'react';
import type { Word, CognateData } from '../types';

interface Props {
  word: Word;
  cognate?: CognateData | null;
}

export default function WordTooltip({ word, cognate }: Props) {
  const [expanded, setExpanded] = useState(false);
  const mainRoot = word.segments.find((s) => s.root_arabic)?.root_arabic;
  const mainLemma = word.segments.find((s) => s.lemma_arabic)?.lemma_arabic;
  const posLabels = word.segments
    .map((s) => s.pos)
    .filter((p) => p && p !== 'Prefix' && p !== 'Suffix');

  return (
    <div
      dir="ltr"
      className="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-50
                 bg-white rounded-lg shadow-lg border border-stone-200 p-3
                 min-w-[150px] max-w-[260px] text-sm text-stone-700"
      onClick={(e) => e.stopPropagation()}
    >
      {/* Arrow */}
      <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3
                      bg-white border-l border-t border-stone-200 rotate-45" />

      {word.translation && (
        <div className="font-semibold text-stone-900 mb-1.5 text-center">
          {word.translation}
        </div>
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
              className="font-arabic text-sm text-stone-700"
            >
              {mainRoot}
            </span>
          </div>
        )}
        {mainLemma && (
          <div className="flex justify-between gap-3">
            <span>Lemma</span>
            <span
              dir="rtl"
              lang="ar"
              className="font-arabic text-sm text-stone-700"
            >
              {mainLemma}
            </span>
          </div>
        )}
      </div>

      {cognate && (
        <div className="mt-2 pt-2 border-t border-stone-100">
          <div className="text-xs text-indigo-600 font-medium mb-0.5">
            Semitic Root: {cognate.concept}
          </div>
          {cognate.derivatives.length > 0 && (
            <div className="space-y-0.5">
              {(expanded ? cognate.derivatives : cognate.derivatives.slice(0, 4)).map((d, i) => (
                <div key={i} className="text-xs text-stone-500 flex justify-between gap-2">
                  <span className="text-stone-400 shrink-0">{d.language}</span>
                  <span className="text-stone-700 truncate text-right">{d.meaning || d.concept}</span>
                </div>
              ))}
              {cognate.derivatives.length > 4 && (
                <button
                  className="text-xs text-indigo-500 hover:text-indigo-700 text-center w-full mt-0.5"
                  onClick={() => setExpanded(!expanded)}
                >
                  {expanded ? 'Show less' : `+${cognate.derivatives.length - 4} more`}
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
