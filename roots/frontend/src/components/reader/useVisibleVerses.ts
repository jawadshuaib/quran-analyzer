import { useEffect, useRef, useState } from 'react';

export interface VisibleVerseState {
  /** The single verse the user is most likely "on" right now — used as
   *  the anchor for last-read marker, Ask-the-Quran storage, etc.
   *  -1 when no verse is meaningfully visible. */
  anchor: number;
  /** Inclusive [first, last] range of verses with appreciable on-screen
   *  presence. Null when no verses meet the visibility threshold. The
   *  range is verse numbers (not array indices) and is always contiguous
   *  in the ascending direction; gaps in visibility (rare) collapse to
   *  [min..max]. */
  window: [number, number] | null;
}

/**
 * Track which verses are visible inside a scrolling reader pane.
 *
 * Wraps a single IntersectionObserver across all the verse elements
 * registered via the returned `setRef` callback. Updates state at most
 * once per requestAnimationFrame so a fast scroll doesn't churn React.
 *
 * Design notes:
 * - The "anchor" is the verse with the highest intersection ratio. Ties
 *   get broken by which one is closer to the viewport center, but the
 *   ratio dominates in practice because the verses are stacked.
 * - The "window" includes any verse whose visibility ratio crossed the
 *   `windowThreshold` (default 0.4). On a phone this typically yields
 *   1–3 verses; on desktop 4–8.
 * - State only updates when the anchor or window endpoints actually
 *   change, so consumers can use it in `useEffect` deps without firing
 *   on every scroll tick.
 *
 * Usage:
 *
 *   const { anchor, window: range, setRef } = useVisibleVerses({
 *     enabled: !!data,
 *     windowThreshold: 0.4,
 *   });
 *   ...
 *   <div ref={(el) => setRef(verse, el)} data-verse={verse}>...</div>
 *
 * The component must set `data-verse="<n>"` on each observed element
 * (the existing ReaderVerse already does this).
 */
export function useVisibleVerses(opts: {
  enabled: boolean;
  /** Min intersection ratio for a verse to count as "in the window". */
  windowThreshold?: number;
  /** rootMargin passed to IntersectionObserver — defaults match the
   *  existing last-read tracker so the hook is a drop-in replacement. */
  rootMargin?: string;
}) {
  const { enabled, windowThreshold = 0.4, rootMargin = '-80px 0px -50% 0px' } = opts;

  const refs = useRef<Map<number, HTMLElement>>(new Map());
  const ratiosRef = useRef<Map<number, number>>(new Map());
  const rafRef = useRef<number | null>(null);

  const [state, setState] = useState<VisibleVerseState>({
    anchor: -1,
    window: null,
  });

  // Derive {anchor, window} from the current ratios map. Pulled out so
  // we can call it from rAF without re-creating it on every render.
  const recompute = () => {
    const ratios = ratiosRef.current;
    let anchor = -1;
    let bestRatio = 0;
    let lo = Number.POSITIVE_INFINITY;
    let hi = Number.NEGATIVE_INFINITY;

    for (const [verse, ratio] of ratios) {
      if (ratio > bestRatio) {
        bestRatio = ratio;
        anchor = verse;
      }
      if (ratio >= windowThreshold) {
        if (verse < lo) lo = verse;
        if (verse > hi) hi = verse;
      }
    }

    const nextWindow: [number, number] | null =
      lo === Number.POSITIVE_INFINITY ? null : [lo, hi];

    setState((prev) => {
      if (
        prev.anchor === anchor &&
        ((prev.window === null && nextWindow === null) ||
          (prev.window !== null &&
            nextWindow !== null &&
            prev.window[0] === nextWindow[0] &&
            prev.window[1] === nextWindow[1]))
      ) {
        return prev;
      }
      return { anchor, window: nextWindow };
    });
  };

  useEffect(() => {
    if (!enabled) return;
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const v = parseInt(
            entry.target.getAttribute('data-verse') || '0',
            10,
          );
          if (!v) continue;
          if (entry.isIntersecting) {
            ratiosRef.current.set(v, entry.intersectionRatio);
          } else {
            ratiosRef.current.delete(v);
          }
        }
        // Coalesce updates — multiple verses cross thresholds in a
        // single scroll tick, no point in re-rendering for each.
        if (rafRef.current === null) {
          rafRef.current = requestAnimationFrame(() => {
            rafRef.current = null;
            recompute();
          });
        }
      },
      {
        rootMargin,
        threshold: [0, 0.1, 0.25, 0.4, 0.5, 0.75, 1],
      },
    );

    refs.current.forEach((el) => observer.observe(el));
    return () => {
      observer.disconnect();
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    };
    // recompute is intentionally a stable closure (no deps) — it reads
    // refs, not state, so it never goes stale.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, rootMargin, windowThreshold]);

  function setRef(verse: number, el: HTMLElement | null) {
    if (el) {
      refs.current.set(verse, el);
    } else {
      refs.current.delete(verse);
      ratiosRef.current.delete(verse);
    }
  }

  return { anchor: state.anchor, window: state.window, setRef };
}
