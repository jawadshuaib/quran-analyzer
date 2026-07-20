import { useRef, useEffect, useState, useCallback, type MutableRefObject } from 'react';
import { useUnifiedSearch, resolveIndex } from '../hooks/useUnifiedSearch';
import SearchDropdown from './unified-search/SearchDropdown';
import SearchEmptyState from './unified-search/SearchEmptyState';
import { getSurahName } from '../utils/surah-names';
import { addRecentSearch, getRecentSearches, subscribeToRecentSearches, removeRecentSearch, clearRecentSearches } from '../utils/recent-searches';
import type { RootSearchResult, SemanticSearchResult } from '../api/quran';
import type { ParsedVerseRef } from '../utils/search-classifier';
import type { SurahMatch } from '../utils/surah-search';

/** Imperative handle to fill text into the search bar from outside */
export interface UnifiedSearchHandle {
  fill: (text: string) => void;
  focus: () => void;
}

interface Props {
  onNavigateVerse: (surah: number, ayah: number) => void;
  onFullSemanticSearch: (query: string) => void;
  loading?: boolean;
  /** Optional ref to expose fill() method to parent */
  handleRef?: MutableRefObject<UnifiedSearchHandle | null>;
  /** Compact variant for use inside the sticky NavBar — smaller padding,
   *  no centering, smaller font. */
  compact?: boolean;
  /** Prefill the bar's text on mount without opening the dropdown or
   *  re-running a search (used by the /search results page). */
  initialQuery?: string;
}

const LISTBOX_ID = 'unified-search-listbox';

export default function UnifiedSearch({ onNavigateVerse, onFullSemanticSearch, loading, handleRef, compact, initialQuery }: Props) {
  const { state, setQuery, setQueryText, close, open, setActiveIndex, moveUp, moveDown } = useUnifiedSearch();
  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [focused, setFocused] = useState(false);
  const [recents, setRecents] = useState<string[]>(getRecentSearches);

  // Keep the recent-searches list fresh (also across tabs).
  useEffect(() => subscribeToRecentSearches(() => setRecents(getRecentSearches())), []);

  // Keep the bar's text in sync with the page's query prop — prefill on
  // mount plus the updates the /search page drives from suggestion clicks
  // and browser back/forward. setQueryText only sets the text (no search,
  // no dropdown); typing doesn't refire this because the prop only changes
  // on submit/popstate, not on every keystroke.
  useEffect(() => {
    if (initialQuery !== undefined) setQueryText(initialQuery);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuery]);

  // Expose fill() to parent via handleRef
  useEffect(() => {
    if (handleRef) {
      handleRef.current = {
        fill(text: string) {
          setQuery(text);
          inputRef.current?.focus();
        },
        focus() {
          inputRef.current?.focus();
        },
      };
    }
  }, [handleRef, setQuery]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        close();
        setFocused(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [close]);

  // Scroll active item into view on keyboard navigation
  useEffect(() => {
    if (state.activeIndex >= 0) {
      const el = document.getElementById(`search-item-${state.activeIndex}`);
      el?.scrollIntoView({ block: 'nearest' });
    }
  }, [state.activeIndex]);

  const handleSelectVerse = useCallback((ref: ParsedVerseRef) => {
    close();
    setFocused(false);
    setQuery('');
    onNavigateVerse(ref.surah, ref.ayah);
  }, [close, setQuery, onNavigateVerse]);

  const handleSelectRoot = useCallback((root: RootSearchResult) => {
    close();
    setFocused(false);
    setQuery('');
    window.location.href = `/root/${encodeURIComponent(root.root_buckwalter)}`;
  }, [close, setQuery]);

  const handleSelectSemantic = useCallback((result: SemanticSearchResult) => {
    addRecentSearch(state.query);
    close();
    setFocused(false);
    setQuery('');
    onNavigateVerse(result.surah, result.ayah);
  }, [state.query, close, setQuery, onNavigateVerse]);

  const handleSelectSurah = useCallback((surah: SurahMatch) => {
    close();
    setFocused(false);
    setQuery('');
    // Surah → reader mode (not the verse-research view). Hard-navigate so
    // the page mounts fresh under /read/<n>.
    window.location.href = `/read/${surah.number}`;
  }, [close, setQuery]);

  const handleFullSearch = useCallback(() => {
    const trimmed = state.query.trim();
    if (!trimmed) return;
    addRecentSearch(trimmed);
    close();
    onFullSemanticSearch(trimmed);
  }, [state.query, close, onFullSemanticSearch]);

  /** Run a search from a picked recent/suggestion chip in the empty state. */
  const handlePickQuery = useCallback((q: string) => {
    const trimmed = q.trim();
    if (!trimmed) return;
    addRecentSearch(trimmed);
    setFocused(false);
    close();
    onFullSemanticSearch(trimmed);
  }, [close, onFullSemanticSearch]);

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (!state.isOpen) { open(); return; }
      moveDown();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      moveUp();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const trimmed = state.query.trim();
      if (!trimmed) return;

      if (state.activeIndex >= 0 && state.isOpen) {
        // Select the active item
        const resolved = resolveIndex(state, state.activeIndex);
        if (!resolved) return;
        const { category, localIndex } = resolved;
        if (category === 'verse' && state.verseRef) {
          handleSelectVerse(state.verseRef);
        } else if (category === 'surah' && state.surahMatches[localIndex]) {
          handleSelectSurah(state.surahMatches[localIndex]);
        } else if (category === 'root' && state.rootResults[localIndex]) {
          handleSelectRoot(state.rootResults[localIndex]);
        } else if (category === 'semantic' && state.semanticResults[localIndex]) {
          handleSelectSemantic(state.semanticResults[localIndex]);
        }
      } else {
        // No selection — Enter submits: navigate a settled verse-ref; else
        // run the full "by meaning" search when semantic is in play. For
        // Arabic (semantic held for Phase B) fall back to the top root match
        // rather than sending Arabic to the English-only semantic index.
        // (A partial "2:" ref does neither.)
        if (state.verseRef && !state.verseRef.partial) {
          handleSelectVerse(state.verseRef);
        } else if (!state.verseRef) {
          if (state.plan.fire.semantic) {
            handleFullSearch();
          } else if (state.rootResults[0]) {
            handleSelectRoot(state.rootResults[0]);
          }
        }
      }
    } else if (e.key === 'Escape') {
      close();
      setFocused(false);
    }
  }

  const surahName = state.verseRef ? getSurahName(state.verseRef.surah) : '';
  const anyLoading = loading || state.rootLoading || state.semanticLoading;

  // Determine active descendant for aria
  const activeDescendant = state.activeIndex >= 0 ? `search-item-${state.activeIndex}` : undefined;

  return (
    <div
      ref={wrapperRef}
      className={compact ? "relative w-full" : "relative w-full max-w-lg mx-auto"}
    >
      <div className="relative">
        <svg
          className={`absolute top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none ${
            compact ? 'left-3 w-4 h-4' : 'left-4 w-5 h-5'
          }`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          ref={inputRef}
          type="text"
          value={state.query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => { setFocused(true); if (state.query.trim()) open(); }}
          placeholder='Search by verse, root, or phrase'
          role="combobox"
          aria-expanded={state.isOpen}
          aria-controls={LISTBOX_ID}
          aria-activedescendant={activeDescendant}
          aria-autocomplete="list"
          autoComplete="off"
          spellCheck={false}
          className={
            compact
              ? "w-full rounded-lg border border-black/15 bg-white pl-9 pr-9 py-1.5 text-[13px] placeholder:text-ink-muted focus:border-gold focus:ring-[3px] focus:ring-gold/10 focus:outline-none"
              : "w-full rounded-xl sm:rounded-[14px] border border-black/15 bg-white pl-10 pr-10 py-2.5 sm:py-3.5 text-sm sm:text-[17px] placeholder:text-ink-muted focus:border-gold focus:ring-[6px] focus:ring-gold/10 focus:outline-none shadow-[0_1px_2px_rgba(0,0,0,0.03),0_0_0_6px_rgba(186,117,23,0.06)]"
          }
        />
        {anyLoading && (
          <div className={`absolute top-1/2 -translate-y-1/2 ${compact ? 'right-2.5' : 'right-3.5'}`}>
            <div className={`animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-600 ${compact ? 'h-3 w-3' : 'h-4 w-4'}`} />
          </div>
        )}
      </div>

      {focused && !state.query.trim() && recents.length > 0 ? (
        <SearchEmptyState
          recents={recents}
          onPick={handlePickQuery}
          onRemove={removeRecentSearch}
          onClear={clearRecentSearches}
        />
      ) : state.isOpen ? (
        <SearchDropdown
          state={state}
          surahName={surahName}
          onSelectVerse={handleSelectVerse}
          onSelectRoot={handleSelectRoot}
          onSelectSemantic={handleSelectSemantic}
          onSelectSurah={handleSelectSurah}
          onFullSearch={handleFullSearch}
          onHoverIndex={setActiveIndex}
          listboxId={LISTBOX_ID}
        />
      ) : null}
    </div>
  );
}
