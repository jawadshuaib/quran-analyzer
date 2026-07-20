import type { ReactNode } from 'react';
import type { UnifiedSearchState } from '../../hooks/useUnifiedSearch';
import type { RootSearchResult, SemanticSearchResult } from '../../api/quran';
import type { ParsedVerseRef } from '../../utils/search-classifier';
import type { SurahMatch } from '../../utils/surah-search';
import VerseRefSuggestion from './VerseRefSuggestion';
import RootResultItem from './RootResultItem';
import SemanticResultItem from './SemanticResultItem';

interface Props {
  state: UnifiedSearchState;
  surahName: string;
  onSelectVerse: (verseRef: ParsedVerseRef) => void;
  onSelectRoot: (root: RootSearchResult) => void;
  onSelectSemantic: (result: SemanticSearchResult) => void;
  onSelectSurah: (surah: SurahMatch) => void;
  onFullSearch: () => void;
  onHoverIndex: (index: number) => void;
  listboxId: string;
}

export default function SearchDropdown({
  state,
  surahName,
  onSelectVerse,
  onSelectRoot,
  onSelectSemantic,
  onSelectSurah,
  onFullSearch,
  onHoverIndex,
  listboxId,
}: Props) {
  const { verseRef, rootResults, rootLoading, semanticResults, semanticLoading, surahMatches, activeIndex, plan } = state;
  const showVerseRef = verseRef && !verseRef.partial;
  const hasSurahs = surahMatches.length > 0;
  const hasRoots = rootResults.length > 0;
  const hasSemantic = semanticResults.length > 0;
  // Only offer the "search all verses by meaning" escape hatch when semantic
  // actually fires — never for Arabic (held for Phase B; the English index
  // would return noise). Arabic queries just show their root matches.
  const showFullSearchFooter = !showVerseRef && plan.fire.semantic && state.query.trim().length >= 3;
  const hasAnything = showVerseRef || hasSurahs || hasRoots || hasSemantic || rootLoading || semanticLoading || showFullSearchFooter;

  if (!hasAnything) return null;

  // Flat indices in the SAME order resolveIndex() walks: verse-ref → surahs →
  // then root/semantic in plan.lead order. Keeping these in sync is what makes
  // keyboard navigation land on the visible row.
  const semanticFirst = plan.lead === 'semantic';
  let nextIdx = 0;
  const verseIdx = showVerseRef ? nextIdx++ : -1;
  const surahIndices = surahMatches.map(() => nextIdx++);
  let rootIndices: number[];
  let semanticIndices: number[];
  if (semanticFirst) {
    semanticIndices = semanticResults.map(() => nextIdx++);
    rootIndices = rootResults.map(() => nextIdx++);
  } else {
    rootIndices = rootResults.map(() => nextIdx++);
    semanticIndices = semanticResults.map(() => nextIdx++);
  }

  const rootBlock: ReactNode = (hasRoots || rootLoading) ? (
    <>
      <li className="px-4 pt-3 pb-1 border-t border-stone-100" role="presentation">
        <span className="border-l-2 border-emerald-300 pl-2 text-[10px] font-semibold text-stone-400 uppercase tracking-wider">
          Root matches
        </span>
      </li>
      {rootResults.map((root, i) => (
        <RootResultItem
          key={root.root_buckwalter}
          root={root}
          active={activeIndex === rootIndices[i]}
          onSelect={() => onSelectRoot(root)}
          onHover={() => onHoverIndex(rootIndices[i])}
          id={`search-item-${rootIndices[i]}`}
        />
      ))}
      {rootLoading && !hasRoots && (
        <li className="px-4 py-3 flex items-center gap-2" role="presentation">
          <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-600" />
          <span className="text-xs text-stone-400">Searching roots...</span>
        </li>
      )}
    </>
  ) : null;

  const semanticBlock: ReactNode = (hasSemantic || semanticLoading) ? (
    <>
      <li className="px-4 pt-3 pb-1 border-t border-stone-100" role="presentation">
        <span className="border-l-2 border-violet-300 pl-2 text-[10px] font-semibold text-stone-400 uppercase tracking-wider">
          Verse matches &middot; by meaning
        </span>
      </li>
      {semanticResults.map((result, i) => (
        <SemanticResultItem
          key={`${result.surah}:${result.ayah}`}
          result={result}
          query={state.query}
          active={activeIndex === semanticIndices[i]}
          onSelect={() => onSelectSemantic(result)}
          onHover={() => onHoverIndex(semanticIndices[i])}
          id={`search-item-${semanticIndices[i]}`}
        />
      ))}
      {semanticLoading && !hasSemantic && (
        <li className="px-4 py-3 flex items-center gap-2" role="presentation">
          <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-violet-200 border-t-violet-600" />
          <span className="text-xs text-stone-400">Searching by meaning...</span>
        </li>
      )}
    </>
  ) : null;

  return (
    <ul
      id={listboxId}
      role="listbox"
      className="absolute z-50 mt-2 w-full rounded-2xl border border-stone-200 bg-white shadow-xl overflow-hidden max-h-[420px] overflow-y-auto"
    >
      {/* Verse reference suggestion */}
      {showVerseRef && (
        <VerseRefSuggestion
          verseRef={verseRef}
          surahName={surahName}
          preview={state.versePreview}
          previewLoading={state.versePreviewLoading}
          active={activeIndex === verseIdx}
          onSelect={() => onSelectVerse(verseRef)}
          onHover={() => onHoverIndex(verseIdx)}
          id={`search-item-${verseIdx}`}
        />
      )}

      {/* Surah-name matches — pinned right after the verse-ref preview because
          typing a surah name is unambiguous navigation. */}
      {hasSurahs && (
        <>
          <li className="px-4 pt-3 pb-1 border-t border-stone-100" role="presentation">
            <span className="text-[10px] font-semibold text-stone-400 uppercase tracking-wider">
              Surahs
            </span>
          </li>
          {surahMatches.map((surah, i) => (
            <li
              key={surah.number}
              id={`search-item-${surahIndices[i]}`}
              role="option"
              aria-selected={activeIndex === surahIndices[i]}
              onClick={() => onSelectSurah(surah)}
              onMouseMove={() => onHoverIndex(surahIndices[i])}
              className={`px-4 py-2.5 cursor-pointer transition-colors flex items-center gap-3 ${
                activeIndex === surahIndices[i] ? 'bg-stone-100' : 'hover:bg-stone-50'
              }`}
            >
              <span className="font-mono text-[11px] text-stone-400 min-w-[1.75rem]">
                {surah.number}
              </span>
              {surah.name_arabic && (
                <span className="font-arabic text-base text-stone-800 min-w-[5.5rem]" lang="ar" dir="rtl">
                  {surah.name_arabic}
                </span>
              )}
              <span className="text-sm text-stone-700">{surah.name}</span>
              {surah.meaning && (
                <span className="text-xs text-stone-400 truncate">· {surah.meaning}</span>
              )}
              <span className="ml-auto text-[11px] text-stone-300">Read →</span>
            </li>
          ))}
        </>
      )}

      {/* Root + semantic in plan.lead order */}
      {semanticFirst ? <>{semanticBlock}{rootBlock}</> : <>{rootBlock}{semanticBlock}</>}

      {/* Full search footer */}
      {showFullSearchFooter && (
        <li
          className="border-t border-stone-100 px-4 py-2.5 cursor-pointer hover:bg-stone-50 transition-colors"
          role="presentation"
          onClick={onFullSearch}
        >
          <div className="flex items-center gap-2 text-xs text-stone-500">
            <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <span>
              Search all verses for <span className="font-medium text-stone-700">&ldquo;{state.query.trim()}&rdquo;</span>
            </span>
            <kbd className="hidden sm:inline ml-auto text-[10px] text-stone-400 bg-stone-100 rounded px-1.5 py-0.5">
              Enter
            </kbd>
          </div>
        </li>
      )}
    </ul>
  );
}
