import { useEffect, useRef } from 'react';

/** How far, how straight and how fast a swipe must be to count, so that a
 *  slow drag, a diagonal scroll or a long-press text selection never turns
 *  the page. */
const MIN_DISTANCE = 60; // px
const MAX_DURATION = 600; // ms
const STRAIGHTNESS = 1.5; // |dx| must exceed |dy| by this factor
/** iOS / Android use the screen edges for browser back/forward. */
const EDGE_GUARD = 24; // px

function startsInBlockedArea(target: EventTarget | null): boolean {
  let el = target instanceof Element ? target : null;
  while (el && el !== document.body) {
    if (el instanceof HTMLElement) {
      if (el.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName)) return true;
      if (el.getAttribute('aria-modal') === 'true' || el.getAttribute('role') === 'dialog') return true;
      // Anything that scrolls sideways owns horizontal drags.
      const ox = getComputedStyle(el).overflowX;
      if ((ox === 'auto' || ox === 'scroll') && el.scrollWidth > el.clientWidth) return true;
    }
    el = el.parentElement;
  }
  return false;
}

/**
 * Swipe left / right on touch screens to call `onNext` / `onPrevious`, the
 * touch counterpart of the ← / → keys. Either callback may be omitted (first
 * or last verse); `enabled: false` detaches the listeners.
 */
export function useSwipeNavigation({
  onPrevious,
  onNext,
  enabled = true,
}: {
  onPrevious?: () => void;
  onNext?: () => void;
  enabled?: boolean;
}) {
  // Read the latest callbacks without re-binding listeners on every render.
  const handlers = useRef({ onPrevious, onNext });
  handlers.current = { onPrevious, onNext };

  useEffect(() => {
    if (!enabled) return;
    let start: { x: number; y: number; t: number } | null = null;

    const onStart = (e: TouchEvent) => {
      start = null;
      if (e.touches.length !== 1) return;
      const p = e.touches[0];
      if (p.clientX < EDGE_GUARD || p.clientX > window.innerWidth - EDGE_GUARD) return;
      if (startsInBlockedArea(e.target)) return;
      if (document.querySelector('[aria-modal="true"]')) return;
      start = { x: p.clientX, y: p.clientY, t: Date.now() };
    };

    const onEnd = (e: TouchEvent) => {
      const s = start;
      start = null;
      if (!s || e.changedTouches.length !== 1) return;
      const p = e.changedTouches[0];
      const dx = p.clientX - s.x;
      const dy = p.clientY - s.y;
      if (Date.now() - s.t > MAX_DURATION) return;
      if (Math.abs(dx) < MIN_DISTANCE || Math.abs(dx) < Math.abs(dy) * STRAIGHTNESS) return;
      // A drag that selected text is a selection, not a page turn.
      if ((window.getSelection()?.toString() ?? '').trim()) return;
      const go = dx < 0 ? handlers.current.onNext : handlers.current.onPrevious;
      go?.();
    };

    const onCancel = () => { start = null; };

    window.addEventListener('touchstart', onStart, { passive: true });
    window.addEventListener('touchend', onEnd, { passive: true });
    window.addEventListener('touchcancel', onCancel, { passive: true });
    return () => {
      window.removeEventListener('touchstart', onStart);
      window.removeEventListener('touchend', onEnd);
      window.removeEventListener('touchcancel', onCancel);
    };
  }, [enabled]);
}
