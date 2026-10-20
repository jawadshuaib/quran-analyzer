import { useEffect, useLayoutEffect, useRef } from 'react';
import type { RefObject } from 'react';

/**
 * Swipe between verses on touch screens, drawn as a paper scroll: two rollers
 * appear at the screen edges, the verse card follows the finger, and on
 * release it furls into one roller while the next verse unfurls from the
 * other. Left = next verse, right = previous (the ← / → keys' touch twin).
 *
 * The card unmounts while the next verse loads (App sets data to null), so
 * the rollers live on <body> and the "unfurl" direction is handed to the next
 * mount through `pendingEnter`. Everything moves with transform / opacity
 * only: iOS freezes width animations mid-navigation.
 */

const FLICK_DISTANCE = 60; // px: a quick swipe this long turns the page
const FLICK_MS = 600;
const COMMIT_FRACTION = 0.3; // or a slow drag past this share of the screen
const AXIS_LOCK = 8; // px of travel before we decide horizontal vs vertical
const STRAIGHTNESS = 1.2; // |dx| must beat |dy| by this to count as a swipe
const EDGE_GUARD = 24; // px: the OS uses the screen edges for back/forward
const RUBBER = 0.25; // resistance when there is no verse that way
const FURL_MS = 220;
const UNFURL_MS = 340;

type Dir = 'next' | 'previous';

let rollers: HTMLDivElement | null = null;
let rollersTimer: ReturnType<typeof setTimeout> | null = null;
/** Set when a swipe navigates; the next card to mount unfurls from it. */
let pendingEnter: { dir: Dir; at: number } | null = null;

function reducedMotion() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
}

function showRollers(opacity: number, ms = 0) {
  if (rollersTimer) { clearTimeout(rollersTimer); rollersTimer = null; }
  if (!rollers) {
    rollers = document.createElement('div');
    rollers.setAttribute('aria-hidden', 'true');
    rollers.className = 'scroll-rollers';
    rollers.innerHTML = '<div class="scroll-roller scroll-roller-left"></div>'
      + '<div class="scroll-roller scroll-roller-right"></div>';
    document.body.appendChild(rollers);
  }
  rollers.style.transition = ms ? `opacity ${ms}ms ease` : 'none';
  rollers.style.opacity = String(opacity);
}

function hideRollers(ms = 200) {
  if (!rollers) return;
  showRollers(0, ms);
  rollersTimer = setTimeout(() => {
    rollers?.remove();
    rollers = null;
    document.documentElement.style.overflowX = '';
  }, ms + 20);
}

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

/** Shade the card edge heading into a roller, as paper curving round it. */
function setCurl(curl: HTMLElement | null, side: 'left' | 'right', amount: number, ms = 0) {
  if (!curl) return;
  curl.dataset.side = side;
  curl.style.transition = ms ? `opacity ${ms}ms ease` : 'none';
  curl.style.opacity = String(Math.min(1, Math.max(0, amount)));
}

function moveCard(card: HTMLElement, x: number, ms = 0, easing = 'ease-out') {
  card.style.transition = ms ? `transform ${ms}ms ${easing}` : 'none';
  card.style.transform = x ? `translate3d(${x}px, 0, 0)` : '';
}

export function useScrollSwipe({
  cardRef,
  curlRef,
  verseKey,
  onPrevious,
  onNext,
  enabled = true,
}: {
  cardRef: RefObject<HTMLElement | null>;
  curlRef: RefObject<HTMLElement | null>;
  /** Changes on every verse, so a re-render with new data also unfurls. */
  verseKey: string;
  onPrevious?: () => void;
  onNext?: () => void;
  enabled?: boolean;
}) {
  const handlers = useRef({ onPrevious, onNext });
  handlers.current = { onPrevious, onNext };

  // Unfurl: the verse a swipe navigated to rolls out of the opposite roller.
  useLayoutEffect(() => {
    const card = cardRef.current;
    const p = pendingEnter;
    pendingEnter = null;
    if (!card || !p || Date.now() - p.at > 6000 || reducedMotion()) {
      if (rollers) hideRollers();
      return;
    }
    const rect = card.getBoundingClientRect();
    const from = p.dir === 'next' ? window.innerWidth - rect.left : -rect.right;
    moveCard(card, from);
    setCurl(curlRef.current, p.dir === 'next' ? 'right' : 'left', 1);
    void card.offsetWidth; // commit the start position before animating
    moveCard(card, 0, UNFURL_MS, 'cubic-bezier(0.2, 0.8, 0.2, 1)');
    setCurl(curlRef.current, p.dir === 'next' ? 'right' : 'left', 0, UNFURL_MS);
    const t = setTimeout(() => {
      card.style.transition = '';
      hideRollers(220);
    }, UNFURL_MS);
    return () => clearTimeout(t);
  }, [verseKey, cardRef, curlRef]);

  useEffect(() => {
    const card = cardRef.current;
    if (!enabled || !card) return;
    let g: { x: number; y: number; t: number; axis: 'x' | 'y' | null; dx: number } | null = null;

    const onStart = (e: TouchEvent) => {
      g = null;
      if (e.touches.length !== 1) return;
      if ((window.visualViewport?.scale ?? 1) > 1.01) return; // pinch-zoomed: pan, don't page
      const p = e.touches[0];
      if (p.clientX < EDGE_GUARD || p.clientX > window.innerWidth - EDGE_GUARD) return;
      if (startsInBlockedArea(e.target)) return;
      if (document.querySelector('[aria-modal="true"]')) return;
      // Text already selected: this touch is adjusting the selection.
      if ((window.getSelection()?.toString() ?? '').trim()) return;
      g = { x: p.clientX, y: p.clientY, t: Date.now(), axis: null, dx: 0 };
    };

    const onMove = (e: TouchEvent) => {
      if (!g || e.touches.length !== 1) return;
      const p = e.touches[0];
      const dx = p.clientX - g.x;
      const dy = p.clientY - g.y;
      if (!g.axis) {
        if (Math.abs(dx) < AXIS_LOCK && Math.abs(dy) < AXIS_LOCK) return;
        g.axis = Math.abs(dx) > Math.abs(dy) * STRAIGHTNESS ? 'x' : 'y';
        if (g.axis === 'y') { g = null; return; } // a scroll, not a swipe
      }
      e.preventDefault(); // horizontal: keep the page from drifting vertically
      if (reducedMotion()) { g.dx = dx; return; }
      const has = dx < 0 ? !!handlers.current.onNext : !!handlers.current.onPrevious;
      g.dx = has ? dx : dx * RUBBER;
      document.documentElement.style.overflowX = 'hidden';
      showRollers(Math.min(1, Math.abs(g.dx) / 40));
      moveCard(card, g.dx);
      setCurl(curlRef.current, g.dx < 0 ? 'left' : 'right', Math.abs(g.dx) / (window.innerWidth * 0.5));
    };

    const springBack = () => {
      moveCard(card, 0, 200);
      setCurl(curlRef.current, curlRef.current?.dataset.side === 'right' ? 'right' : 'left', 0, 200);
      hideRollers(200);
      setTimeout(() => { card.style.transition = ''; }, 220);
    };

    const onEnd = (e: TouchEvent) => {
      const s = g;
      g = null;
      if (!s || s.axis !== 'x') return;
      const p = e.changedTouches[0];
      const dx = p ? p.clientX - s.x : s.dx;
      const quick = Date.now() - s.t <= FLICK_MS && Math.abs(dx) >= FLICK_DISTANCE;
      const far = Math.abs(dx) >= window.innerWidth * COMMIT_FRACTION;
      const dir: Dir = dx < 0 ? 'next' : 'previous';
      const go = dir === 'next' ? handlers.current.onNext : handlers.current.onPrevious;
      // A drag that selected text is a selection, not a page turn.
      const selecting = !!(window.getSelection()?.toString() ?? '').trim();
      if (!go || selecting || !(quick || far)) { springBack(); return; }
      if (reducedMotion()) { go(); return; }

      // Furl: roll the card the rest of the way into the roller, then go.
      const rect = card.getBoundingClientRect();
      const offX = s.dx + (dir === 'next' ? -rect.right : window.innerWidth - rect.left);
      showRollers(1, 120);
      moveCard(card, offX, FURL_MS, 'cubic-bezier(0.4, 0, 1, 1)');
      setCurl(curlRef.current, dir === 'next' ? 'left' : 'right', 1, FURL_MS);
      setTimeout(() => {
        pendingEnter = { dir, at: Date.now() };
        go();
        // If no card mounts (load error), don't leave the rollers up.
        rollersTimer = setTimeout(() => {
          if (pendingEnter) { pendingEnter = null; moveCard(card, 0); hideRollers(); }
        }, 6000);
      }, FURL_MS);
    };

    const onCancel = () => { if (g?.axis === 'x') springBack(); g = null; };

    card.addEventListener('touchstart', onStart, { passive: true });
    card.addEventListener('touchmove', onMove, { passive: false });
    card.addEventListener('touchend', onEnd, { passive: true });
    card.addEventListener('touchcancel', onCancel, { passive: true });
    return () => {
      card.removeEventListener('touchstart', onStart);
      card.removeEventListener('touchmove', onMove);
      card.removeEventListener('touchend', onEnd);
      card.removeEventListener('touchcancel', onCancel);
    };
  }, [enabled, cardRef, curlRef]);
}
