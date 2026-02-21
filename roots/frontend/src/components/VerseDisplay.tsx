import { useState, useRef, useEffect } from 'react';
import type { VerseData, Word, CognateData, RootSummary, SearchTerm } from '../types';
import { searchWordsCount } from '../api/quran';
import WordTooltip from './WordTooltip';
import CognatePanel from './CognatePanel';
import SelectionHeader from './SelectionHeader';

interface Props {
  data: VerseData;
  onWordSearch?: (terms: SearchTerm[], queryVerse: { surah: number; ayah: number }) => void;
  wordSearchLoading?: boolean;
}

/** Return the primary content segment of a word, skipping prefixes/suffixes/pronouns. */
function getContentSegment(word: Word) {
  return (
    word.segments.find(
      (s) =>
        (s.lemma_buckwalter || s.root_buckwalter) &&
        s.pos !== 'Prefix' && s.pos !== 'Suffix' && s.pos !== 'Pronoun'
    ) ??
    word.segments.find(
      (s) =>
        s.form_buckwalter &&
        s.pos !== 'Prefix' && s.pos !== 'Suffix' && s.pos !== 'Pronoun'
    )
  );
}

export default function VerseDisplay({ data, onWordSearch, wordSearchLoading }: Props) {
  const [hoveredPos, setHoveredPos] = useState<number | null>(null);
  const [selectedPositions, setSelectedPositions] = useState<Set<number>>(new Set());
  const [selectedRoots, setSelectedRoots] = useState<Set<string>>(new Set());
  const [hoveredRoot, setHoveredRoot] = useState<string | null>(null);
  const [expandedRoot, setExpandedRoot] = useState<string | null>(null);
  const [resultCount, setResultCount] = useState<number | null>(null);
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

  // Build root_buckwalter -> cognate data lookup
  const rootCognateMap = new Map<string, CognateData>();
  data.roots_summary.forEach((r) => {
    if (r.cognate) {
      rootCognateMap.set(r.root_buckwalter, r.cognate);
    }
  });

  // Get cognate for a word (from its first root-bearing segment)
  function getCognateForWord(word: Word): CognateData | undefined {
    const rootBw = word.segments.find((s) => s.root_buckwalter)?.root_buckwalter;
    return rootBw ? rootCognateMap.get(rootBw) : undefined;
  }

  // Reset state when verse changes
  useEffect(() => {
    setSelectedPositions(new Set());
    setSelectedRoots(new Set());
    setHoveredRoot(null);
    setExpandedRoot(null);
    setResultCount(null);
  }, [data]);

  const hasSelection = selectedPositions.size > 0 || selectedRoots.size > 0;

  // Click outside the card to dismiss all selections
  useEffect(() => {
    if (!hasSelection) return;
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setSelectedPositions(new Set());
        setSelectedRoots(new Set());
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [hasSelection]);

  // Build search terms from selected positions AND selected roots
  function buildAllSearchTerms(): SearchTerm[] {
    const terms: SearchTerm[] = [];

    // Word-based terms
    for (const pos of selectedPositions) {
      const word = wordMap.get(pos);
      if (!word) continue;
      const seg = getContentSegment(word);
      if (!seg) continue;
      const displayText = uthmaniWords[pos - 1] ?? seg.form_arabic;
      terms.push({
        lemma_bw: seg.lemma_buckwalter || null,
        root_bw: seg.root_buckwalter || null,
        form_bw: seg.form_buckwalter || null,
        display_arabic: displayText,
      });
    }

    // Root-based terms
    for (const rbw of selectedRoots) {
      // Skip if a selected word already covers this root
      const alreadyCovered = terms.some((t) => t.root_bw === rbw);
      if (alreadyCovered) continue;

      const rootInfo = data.roots_summary.find((r) => r.root_buckwalter === rbw);
      terms.push({
        lemma_bw: null,
        root_bw: rbw,
        form_bw: null,
        display_arabic: rootInfo?.root_arabic ?? rbw,
      });
    }

    return terms;
  }

  // Stable key for combined selection
  const wordKey = Array.from(selectedPositions).sort((a, b) => a - b).join(',');
  const rootKey = Array.from(selectedRoots).sort().join(',');
  const selectionKey = `${wordKey}|${rootKey}`;

  // Auto-count results when selection changes
  useEffect(() => {
    if (!hasSelection) {
      setResultCount(null);
      return;
    }
    const terms = buildAllSearchTerms();
    if (terms.length === 0) {
      setResultCount(0);
      return;
    }
    let cancelled = false;
    setResultCount(null); // loading
    const timer = setTimeout(() => {
      searchWordsCount(terms, { surah: data.surah, ayah: data.ayah }).then(
        (count) => { if (!cancelled) setResultCount(count); },
        () => { if (!cancelled) setResultCount(0); },
      );
    }, 200);
    return () => { cancelled = true; clearTimeout(timer); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectionKey, data.surah, data.ayah]);

  const highlightedByRoot = hoveredRoot ? rootToPositions.get(hoveredRoot) : null;

  // Find the root summary for the expanded root
  const expandedRootData: RootSummary | undefined = expandedRoot
    ? data.roots_summary.find((r) => r.root_buckwalter === expandedRoot)
    : undefined;

  // Build selected word info for header
  const selectedWordItems = Array.from(selectedPositions)
    .sort((a, b) => a - b)
    .map((pos) => ({
      position: pos,
      word: wordMap.get(pos)!,
      displayText: uthmaniWords[pos - 1] ?? '',
    }))
    .filter((sw) => sw.word);

  // Build selected root info for header
  const selectedRootItems = Array.from(selectedRoots)
    .map((rbw) => {
      const info = data.roots_summary.find((r) => r.root_buckwalter === rbw);
      return { root_buckwalter: rbw, root_arabic: info?.root_arabic ?? rbw };
    });

  function handleSearch() {
    if (!onWordSearch) return;
    const terms = buildAllSearchTerms();
    if (terms.length === 0) return;
    onWordSearch(terms, { surah: data.surah, ayah: data.ayah });
  }

  function clearAll() {
    setSelectedPositions(new Set());
    setSelectedRoots(new Set());
  }

  return (
    <div
      ref={containerRef}
      className="rounded-xl border border-stone-200 bg-white p-6 shadow-sm"
      onClick={clearAll}
    >
      {hasSelection && (
        <SelectionHeader
          selectedWords={selectedWordItems}
          selectedRoots={selectedRootItems}
          onDeselectWord={(pos) => {
            setSelectedPositions((prev) => {
              const next = new Set(prev);
              next.delete(pos);
              return next;
            });
          }}
          onDeselectRoot={(rbw) => {
            setSelectedRoots((prev) => {
              const next = new Set(prev);
              next.delete(rbw);
              return next;
            });
          }}
          onClear={clearAll}
          onSearch={handleSearch}
          loading={wordSearchLoading}
          resultCount={resultCount}
        />
      )}

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
          const isSelected = selectedPositions.has(pos);
          const isHovered = !hasSelection && hoveredPos === pos;
          const isActive = isSelected || isHovered;
          const isRootHighlighted = highlightedByRoot?.has(pos) ?? false;

          return (
            <span
              key={pos}
              className={`relative inline-block cursor-pointer rounded-md px-1 transition-colors duration-150 ${
                isSelected
                  ? 'bg-emerald-100 text-emerald-900 ring-1 ring-emerald-400'
                  : isHovered
                    ? 'bg-emerald-100 text-emerald-900'
                    : isRootHighlighted
                      ? 'bg-amber-100 text-amber-900'
                      : 'hover:bg-stone-100'
              }`}
              onMouseEnter={() => {
                if (!hasSelection) setHoveredPos(pos);
              }}
              onMouseLeave={() => {
                if (!hasSelection) setHoveredPos(null);
              }}
              onClick={(e) => {
                e.stopPropagation();
                setSelectedPositions((prev) => {
                  const next = new Set(prev);
                  if (next.has(pos)) {
                    next.delete(pos);
                  } else {
                    next.add(pos);
                  }
                  return next;
                });
              }}
            >
              {word}
              {isActive && wordData && (
                <WordTooltip
                  word={wordData}
                  cognate={getCognateForWord(wordData)}
                />
              )}
            </span>
          );
        })}
      </div>

      <p className="text-stone-600 italic">{data.translation}</p>

      {data.roots_summary.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {data.roots_summary.map((r) => {
            const isRootSelected = selectedRoots.has(r.root_buckwalter);
            return (
              <span
                key={r.root_buckwalter}
                className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1
                           text-sm font-medium border cursor-pointer transition-colors duration-150 ${
                  isRootSelected
                    ? 'bg-sky-100 text-sky-800 border-sky-300 ring-1 ring-sky-400'
                    : hoveredRoot === r.root_buckwalter
                      ? 'bg-amber-100 text-amber-800 border-amber-300'
                      : 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
                }`}
                onMouseEnter={() => setHoveredRoot(r.root_buckwalter)}
                onMouseLeave={() => setHoveredRoot(null)}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedRoots((prev) => {
                    const next = new Set(prev);
                    if (next.has(r.root_buckwalter)) {
                      next.delete(r.root_buckwalter);
                    } else {
                      next.add(r.root_buckwalter);
                    }
                    return next;
                  });
                }}
              >
                <span dir="rtl" lang="ar" className="font-arabic text-base">
                  {r.root_arabic}
                </span>
                <span
                  className={`text-xs ${
                    isRootSelected
                      ? 'text-sky-500'
                      : hoveredRoot === r.root_buckwalter
                        ? 'text-amber-600'
                        : 'text-emerald-500'
                  }`}
                >
                  ({r.root_buckwalter})
                </span>
                {r.occurrences > 1 && (
                  <span
                    className={`text-xs ${
                      isRootSelected
                        ? 'text-sky-400'
                        : hoveredRoot === r.root_buckwalter
                          ? 'text-amber-500'
                          : 'text-emerald-400'
                    }`}
                  >
                    &times;{r.occurrences}
                  </span>
                )}
                {r.cognate && (
                  <span
                    className={`text-xs italic ${
                      isRootSelected
                        ? 'text-sky-500'
                        : hoveredRoot === r.root_buckwalter
                          ? 'text-amber-600'
                          : 'text-emerald-500'
                    }`}
                  >
                    &middot; {r.cognate.concept}
                  </span>
                )}
              </span>
            );
          })}
        </div>
      )}

      {expandedRootData?.cognate && (
        <CognatePanel
          rootArabic={expandedRootData.root_arabic}
          rootBuckwalter={expandedRootData.root_buckwalter}
          cognate={expandedRootData.cognate}
          onClose={() => setExpandedRoot(null)}
        />
      )}
    </div>
  );
}
