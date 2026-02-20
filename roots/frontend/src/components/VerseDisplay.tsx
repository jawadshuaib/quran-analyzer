import { useState, useRef, useEffect } from 'react';
import type { VerseData, Word } from '../types';
import WordTooltip from './WordTooltip';

interface Props {
  data: VerseData;
}

export default function VerseDisplay({ data }: Props) {
  const [hoveredPos, setHoveredPos] = useState<number | null>(null);
  const [pinnedPos, setPinnedPos] = useState<number | null>(null);
  const [hoveredRoot, setHoveredRoot] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const uthmaniWords = data.text_uthmani.split(/\s+/).filter(Boolean);

  // Build position -> Word lookup (positions are 1-indexed)
  const wordMap = new Map<number, Word>();
  data.words.forEach((w) => wordMap.set(w.position, w));

  // Build root_buckwalter -> set of word positions
  const rootToPositions = new Map<string, Set<number>>();
  data.words.forEach((w) => {
    w.segments.forEach((seg) => {
      if (seg.root_buckwalter) {
        if (!rootToPositions.has(seg.root_buckwalter)) {
          rootToPositions.set(seg.root_buckwalter, new Set());
        }
        rootToPositions.get(seg.root_buckwalter)!.add(w.position);
      }
    });
  });

  // Reset state when verse changes
  useEffect(() => {
    setPinnedPos(null);
    setHoveredRoot(null);
  }, [data]);

  // Click outside the card to dismiss pinned tooltip
  useEffect(() => {
    if (pinnedPos === null) return;
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setPinnedPos(null);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [pinnedPos]);

  const activePos = pinnedPos ?? hoveredPos;
  const highlightedByRoot = hoveredRoot ? rootToPositions.get(hoveredRoot) : null;

  return (
    <div
      ref={containerRef}
      className="rounded-xl border border-stone-200 bg-white p-6 shadow-sm"
      onClick={() => setPinnedPos(null)}
    >
      <div className="mb-1 text-sm font-medium text-stone-500">
        Surah {data.surah}, Ayah {data.ayah}
      </div>

      <div
        dir="rtl"
        lang="ar"
        className="mb-4 text-3xl leading-[2.8] font-arabic text-stone-800 flex flex-wrap gap-x-2"
      >
        {uthmaniWords.map((word, idx) => {
          const pos = idx + 1;
          const wordData = wordMap.get(pos);
          const isActive = activePos === pos;
          const isRootHighlighted = highlightedByRoot?.has(pos) ?? false;

          return (
            <span
              key={pos}
              className={`relative inline-block cursor-pointer rounded-md px-1 transition-colors duration-150 ${
                isActive
                  ? 'bg-emerald-100 text-emerald-900'
                  : isRootHighlighted
                    ? 'bg-amber-100 text-amber-900'
                    : 'hover:bg-stone-100'
              }`}
              onMouseEnter={() => {
                if (pinnedPos === null) setHoveredPos(pos);
              }}
              onMouseLeave={() => {
                if (pinnedPos === null) setHoveredPos(null);
              }}
              onClick={(e) => {
                e.stopPropagation();
                setPinnedPos(pinnedPos === pos ? null : pos);
              }}
            >
              {word}
              {isActive && wordData && <WordTooltip word={wordData} />}
            </span>
          );
        })}
      </div>

      <p className="text-stone-600 italic">{data.translation}</p>

      {data.roots_summary.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {data.roots_summary.map((r) => (
            <span
              key={r.root_buckwalter}
              className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1
                         text-sm font-medium border cursor-pointer transition-colors duration-150 ${
                hoveredRoot === r.root_buckwalter
                  ? 'bg-amber-100 text-amber-800 border-amber-300'
                  : 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
              }`}
              onMouseEnter={() => setHoveredRoot(r.root_buckwalter)}
              onMouseLeave={() => setHoveredRoot(null)}
            >
              <span dir="rtl" lang="ar" className="font-arabic text-base">
                {r.root_arabic}
              </span>
              <span
                className={`text-xs ${
                  hoveredRoot === r.root_buckwalter
                    ? 'text-amber-600'
                    : 'text-emerald-500'
                }`}
              >
                ({r.root_buckwalter})
              </span>
              {r.occurrences > 1 && (
                <span
                  className={`text-xs ${
                    hoveredRoot === r.root_buckwalter
                      ? 'text-amber-500'
                      : 'text-emerald-400'
                  }`}
                >
                  &times;{r.occurrences}
                </span>
              )}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
