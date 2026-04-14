import { useState, useRef, useCallback, useEffect } from 'react';
import { searchRoots, semanticSearch, fetchVersePreview } from '../api/quran';
import type { RootSearchResult, SemanticSearchResult, VersePreview } from '../api/quran';
import { classifyInput, parseVerseRef } from '../utils/search-classifier';
import type { SearchIntent, ParsedVerseRef } from '../utils/search-classifier';

export interface UnifiedSearchState {
  query: string;
  intent: SearchIntent;
  verseRef: ParsedVerseRef | null;
  versePreview: VersePreview | null;
  versePreviewLoading: boolean;
  rootResults: RootSearchResult[];
  rootLoading: boolean;
  semanticResults: SemanticSearchResult[];
  semanticLoading: boolean;
  isOpen: boolean;
  activeIndex: number;
}

/** Total number of selectable items in the dropdown. */
export function totalItems(state: UnifiedSearchState): number {
  let count = 0;
  if (state.verseRef && !state.verseRef.partial) count += 1;
  count += state.rootResults.length;
  count += state.semanticResults.length;
  return count;
}

/**
 * Map a flat activeIndex to { category, localIndex }.
 * Order: verse ref (0 or 1) → roots → semantic results.
 * Returns null if index is out of bounds.
 */
export function resolveIndex(state: UnifiedSearchState, idx: number): { category: 'verse' | 'root' | 'semantic'; localIndex: number } | null {
  if (idx < 0 || idx >= totalItems(state)) return null;

  let offset = 0;
  const hasVerseRef = state.verseRef && !state.verseRef.partial;

  if (hasVerseRef) {
    if (idx === 0) return { category: 'verse', localIndex: 0 };
    offset = 1;
  }

  if (idx - offset < state.rootResults.length) {
    return { category: 'root', localIndex: idx - offset };
  }
  offset += state.rootResults.length;

  if (idx - offset < state.semanticResults.length) {
    return { category: 'semantic', localIndex: idx - offset };
  }

  return null;
}

const ROOT_DEBOUNCE = 200;
const SEMANTIC_DEBOUNCE = 400;
const VERSE_PREVIEW_DEBOUNCE = 150;

export function useUnifiedSearch() {
  const [state, setState] = useState<UnifiedSearchState>({
    query: '',
    intent: 'verse_ref',
    verseRef: null,
    versePreview: null,
    versePreviewLoading: false,
    rootResults: [],
    rootLoading: false,
    semanticResults: [],
    semanticLoading: false,
    isOpen: false,
    activeIndex: -1,
  });

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
    const intent = classifyInput(value);
    const verseRef = intent === 'verse_ref' ? parseVerseRef(trimmed) : null;

    // Determine if dropdown should be open
    const hasContent = !!(verseRef && !verseRef.partial) || trimmed.length >= 1;

    setState((prev) => ({
      ...prev,
      query: value,
      intent,
      verseRef,
      activeIndex: -1,
      // Clear ALL categories that don't apply to new intent
      rootResults: intent === 'root' || intent === 'root_and_semantic' ? prev.rootResults : [],
      semanticResults: intent === 'root_and_semantic' ? prev.semanticResults : [],
      versePreview: intent === 'verse_ref' ? prev.versePreview : null,
      versePreviewLoading: false,
      isOpen: hasContent,
    }));

    // Clear old timers
    if (rootTimerRef.current) clearTimeout(rootTimerRef.current);
    if (semanticTimerRef.current) clearTimeout(semanticTimerRef.current);
    if (verseTimerRef.current) clearTimeout(verseTimerRef.current);

    // Fetch verse preview
    if (intent === 'verse_ref' && verseRef && !verseRef.partial) {
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
    if ((intent === 'root' || intent === 'root_and_semantic') && trimmed.length >= 1) {
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

    // Fire semantic search
    if (intent === 'root_and_semantic' && trimmed.length >= 5) {
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
      }, SEMANTIC_DEBOUNCE);
    } else {
      semanticAbortRef.current?.abort();
      setState((p) => ({ ...p, semanticResults: [], semanticLoading: false }));
    }
  }, []);

  const close = useCallback(() => {
    setState((p) => ({ ...p, isOpen: false, activeIndex: -1 }));
  }, []);

  const open = useCallback(() => {
    setState((p) => {
      const hasContent = !!(p.verseRef && !p.verseRef.partial) || p.rootResults.length > 0 || p.semanticResults.length > 0;
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
  }, [state.rootResults.length, state.semanticResults.length, state.verseRef, state.activeIndex]);

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
    close,
    open,
    setActiveIndex,
    moveUp,
    moveDown,
  };
}
