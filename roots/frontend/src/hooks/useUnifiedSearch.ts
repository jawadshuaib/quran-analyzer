import { useState, useRef, useCallback, useEffect } from 'react';
import { searchRoots, semanticSearch, fetchVersePreview } from '../api/quran';
import type { RootSearchResult, SemanticSearchResult, VersePreview } from '../api/quran';
import { classifyInput } from '../utils/search-classifier';
import type { SearchPlan, ParsedVerseRef } from '../utils/search-classifier';
import { getSurahsForSearch, matchSurahs } from '../utils/surah-search';
import type { SurahMatch } from '../utils/surah-search';
import type { SurahInfo } from '../types';

export interface UnifiedSearchState {
  query: string;
  plan: SearchPlan;
  verseRef: ParsedVerseRef | null;
  versePreview: VersePreview | null;
  versePreviewLoading: boolean;
  rootResults: RootSearchResult[];
  rootLoading: boolean;
  semanticResults: SemanticSearchResult[];
  semanticLoading: boolean;
  /** Surah-name matches — runs alongside root + semantic, not gated by
   *  intent because surah names overlap with prophet names / common
   *  words and we want them surfaced regardless. Limited to 6 results. */
  surahMatches: SurahMatch[];
  isOpen: boolean;
  activeIndex: number;
}

/** Total number of selectable items in the dropdown. */
export function totalItems(state: UnifiedSearchState): number {
  let count = 0;
  if (state.verseRef && !state.verseRef.partial) count += 1;
  count += state.surahMatches.length;
  count += state.rootResults.length;
  count += state.semanticResults.length;
  return count;
}

/**
 * Map a flat activeIndex to { category, localIndex }.
 * Order: verse ref → surah matches → then root/semantic in `plan.lead` order
 * (concept queries lead with "verse matches", root queries lead with roots).
 * Verse-ref + surah come first because typing a reference or a surah name is
 * unambiguous navigation. Returns null if index is out of bounds. The dropdown
 * renders sections in this exact order so keyboard/flat indices stay in sync.
 */
export function resolveIndex(state: UnifiedSearchState, idx: number): { category: 'verse' | 'surah' | 'root' | 'semantic'; localIndex: number } | null {
  if (idx < 0 || idx >= totalItems(state)) return null;

  let offset = 0;
  const hasVerseRef = state.verseRef && !state.verseRef.partial;

  if (hasVerseRef) {
    if (idx === 0) return { category: 'verse', localIndex: 0 };
    offset = 1;
  }

  if (idx - offset < state.surahMatches.length) {
    return { category: 'surah', localIndex: idx - offset };
  }
  offset += state.surahMatches.length;

  const semanticFirst = state.plan.lead === 'semantic';
  const first = semanticFirst
    ? { cat: 'semantic' as const, arr: state.semanticResults }
    : { cat: 'root' as const, arr: state.rootResults };
  const second = semanticFirst
    ? { cat: 'root' as const, arr: state.rootResults }
    : { cat: 'semantic' as const, arr: state.semanticResults };

  if (idx - offset < first.arr.length) return { category: first.cat, localIndex: idx - offset };
  offset += first.arr.length;
  if (idx - offset < second.arr.length) return { category: second.cat, localIndex: idx - offset };

  return null;
}

const ROOT_DEBOUNCE = 200;
const VERSE_PREVIEW_DEBOUNCE = 150;
const SEMANTIC_MIN_LEN = 3;

// Semantic (by-meaning) search fires whenever the classifier's plan says so
// (`plan.fire.semantic`) — which now includes single-word English concepts
// like "mercy" — as long as the query is ≥3 chars and isn't already answered
// by a settled verse-ref or an EXACT surah-name match. The classifier owns the
// what/when; the two suppressors below only stop redundant embeds. The
// dropdown's "Search all verses for X" footer (Enter) is always the manual
// escape hatch. Debounce comes from the plan (longer for likely-transliteration).

export function useUnifiedSearch() {
  const [state, setState] = useState<UnifiedSearchState>({
    query: '',
    plan: classifyInput(''),
    verseRef: null,
    versePreview: null,
    versePreviewLoading: false,
    rootResults: [],
    rootLoading: false,
    semanticResults: [],
    semanticLoading: false,
    surahMatches: [],
    isOpen: false,
    activeIndex: -1,
  });

  // Surah list lazy-loads once on first non-empty query and is cached
  // by surah-search.ts for the rest of the session. Local ref so the
  // matcher can run synchronously without re-fetching.
  const surahListRef = useRef<SurahInfo[] | null>(null);

  const rootTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const semanticTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const verseTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const rootAbortRef = useRef<AbortController | null>(null);
  const semanticAbortRef = useRef<AbortController | null>(null);
  const verseAbortRef = useRef<AbortController | null>(null);
  // Track the query each request was issued for to discard stale responses
  const rootQueryRef = useRef('');
  const semanticQueryRef = useRef('');
  const verseRefRef = useRef('');

  const setQuery = useCallback((value: string) => {
    const trimmed = value.trim();
    const plan = classifyInput(value);
    const verseRef = plan.verseRef;

    // Determine if dropdown should be open
    const hasContent = !!(verseRef && !verseRef.partial) || trimmed.length >= 1;

    // Surah matching is synchronous + cheap, runs every keystroke. Empty
    // query → no matches. We use the cached list if available; otherwise
    // we fire the (one-time) fetch and the matches will arrive a moment
    // later via the .then below.
    const initialSurahMatches = trimmed.length >= 2
      ? matchSurahs(trimmed, surahListRef.current)
      : [];

    setState((prev) => ({
      ...prev,
      query: value,
      plan,
      verseRef,
      activeIndex: -1,
      // Clear categories the new plan doesn't fire
      rootResults: plan.fire.root ? prev.rootResults : [],
      semanticResults: plan.fire.semantic ? prev.semanticResults : [],
      surahMatches: initialSurahMatches,
      versePreview: verseRef ? prev.versePreview : null,
      versePreviewLoading: false,
      isOpen: hasContent,
    }));

    // Lazy-load the surah list on first non-trivial query and re-run
    // the match once it lands.
    if (trimmed.length >= 2 && !surahListRef.current) {
      getSurahsForSearch()
        .then((list) => {
          surahListRef.current = list;
          // Re-run match with the same trimmed query (set may have moved)
          setState((p) => {
            if (!p.query.trim() || p.query.trim() !== trimmed) return p;
            return { ...p, surahMatches: matchSurahs(trimmed, list) };
          });
        })
        .catch(() => {
          /* silent — surah search just stays empty */
        });
    }

    // Clear old timers
    if (rootTimerRef.current) clearTimeout(rootTimerRef.current);
    if (semanticTimerRef.current) clearTimeout(semanticTimerRef.current);
    if (verseTimerRef.current) clearTimeout(verseTimerRef.current);

    // Fetch verse preview
    if (verseRef && !verseRef.partial) {
      const refKey = `${verseRef.surah}:${verseRef.ayah}`;
      setState((p) => ({ ...p, versePreviewLoading: true }));
      verseTimerRef.current = setTimeout(() => {
        verseAbortRef.current?.abort();
        const controller = new AbortController();
        verseAbortRef.current = controller;
        verseRefRef.current = refKey;
        fetchVersePreview(verseRef.surah, verseRef.ayah, controller.signal)
          .then((data) => {
            if (verseRefRef.current === refKey) {
              setState((p) => ({
                ...p,
                versePreview: data,
                versePreviewLoading: false,
              }));
            }
          })
          .catch((err) => {
            if (err instanceof DOMException && err.name === 'AbortError') return;
            if (verseRefRef.current === refKey) {
              setState((p) => ({ ...p, versePreview: null, versePreviewLoading: false }));
            }
          });
      }, VERSE_PREVIEW_DEBOUNCE);
    } else {
      verseAbortRef.current?.abort();
      setState((p) => ({ ...p, versePreview: null, versePreviewLoading: false }));
    }

    // Fire root search
    if (plan.fire.root && trimmed.length >= 1) {
      setState((p) => ({ ...p, rootLoading: true }));
      rootTimerRef.current = setTimeout(() => {
        rootAbortRef.current?.abort();
        const controller = new AbortController();
        rootAbortRef.current = controller;
        rootQueryRef.current = trimmed;
        searchRoots(trimmed, 5, controller.signal)
          .then((data) => {
            if (rootQueryRef.current === trimmed) {
              setState((p) => ({
                ...p,
                rootResults: data,
                rootLoading: false,
                isOpen: true,
              }));
            }
          })
          .catch((err) => {
            if (err instanceof DOMException && err.name === 'AbortError') return;
            if (rootQueryRef.current === trimmed) {
              setState((p) => ({ ...p, rootResults: [], rootLoading: false }));
            }
          });
      }, ROOT_DEBOUNCE);
    } else {
      rootAbortRef.current?.abort();
      setState((p) => ({ ...p, rootResults: [], rootLoading: false }));
    }

    // Semantic search — fire whenever the plan says so, unless a settled
    // verse-ref or an EXACT surah-name match already answers the query.
    const hasExactSurahMatch =
      initialSurahMatches.length > 0 && initialSurahMatches[0].score === 0;
    const verseRefSettled = !!verseRef && !verseRef.partial;
    const semanticAutoFire =
      plan.fire.semantic &&
      trimmed.length >= SEMANTIC_MIN_LEN &&
      !verseRefSettled &&
      !hasExactSurahMatch;

    if (semanticAutoFire) {
      setState((p) => ({ ...p, semanticLoading: true }));
      semanticTimerRef.current = setTimeout(() => {
        semanticAbortRef.current?.abort();
        const controller = new AbortController();
        semanticAbortRef.current = controller;
        semanticQueryRef.current = trimmed;
        semanticSearch(trimmed, 4, controller.signal)
          .then((data) => {
            if (semanticQueryRef.current === trimmed) {
              setState((p) => ({
                ...p,
                semanticResults: data.results,
                semanticLoading: false,
                isOpen: true,
              }));
            }
          })
          .catch((err) => {
            if (err instanceof DOMException && err.name === 'AbortError') return;
            if (semanticQueryRef.current === trimmed) {
              setState((p) => ({ ...p, semanticResults: [], semanticLoading: false }));
            }
          });
      }, plan.semanticDebounce);
    } else {
      semanticAbortRef.current?.abort();
      setState((p) => ({ ...p, semanticResults: [], semanticLoading: false }));
    }
  }, []);

  /** Set only the visible input text — no classify, no fetch, no dropdown.
   *  Used to prefill the bar on the /search page without re-searching. */
  const setQueryText = useCallback((text: string) => {
    setState((p) => ({ ...p, query: text }));
  }, []);

  const close = useCallback(() => {
    setState((p) => ({ ...p, isOpen: false, activeIndex: -1 }));
  }, []);

  const open = useCallback(() => {
    setState((p) => {
      const hasContent = !!(p.verseRef && !p.verseRef.partial)
        || p.rootResults.length > 0
        || p.semanticResults.length > 0
        || p.surahMatches.length > 0;
      return { ...p, isOpen: hasContent };
    });
  }, []);

  const setActiveIndex = useCallback((idx: number) => {
    setState((p) => ({ ...p, activeIndex: idx }));
  }, []);

  const moveUp = useCallback(() => {
    setState((p) => ({
      ...p,
      activeIndex: Math.max(p.activeIndex - 1, -1),
    }));
  }, []);

  const moveDown = useCallback(() => {
    setState((p) => ({
      ...p,
      activeIndex: Math.min(p.activeIndex + 1, totalItems(p) - 1),
    }));
  }, []);

  // Clamp activeIndex when items disappear due to async results changing
  useEffect(() => {
    const max = totalItems(state) - 1;
    if (state.activeIndex > max) {
      setState((p) => ({ ...p, activeIndex: Math.max(max, -1) }));
    }
  }, [state.rootResults.length, state.semanticResults.length, state.surahMatches.length, state.verseRef, state.activeIndex]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (rootTimerRef.current) clearTimeout(rootTimerRef.current);
      if (semanticTimerRef.current) clearTimeout(semanticTimerRef.current);
      if (verseTimerRef.current) clearTimeout(verseTimerRef.current);
      rootAbortRef.current?.abort();
      semanticAbortRef.current?.abort();
      verseAbortRef.current?.abort();
    };
  }, []);

  return {
    state,
    setQuery,
    setQueryText,
    close,
    open,
    setActiveIndex,
    moveUp,
    moveDown,
  };
}
