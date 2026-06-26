import { useCallback, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import {
  addHighlight,
  removeHighlight,
  setHighlightColor,
  HIGHLIGHT_COLORS,
  HIGHLIGHT_SWATCH,
  HIGHLIGHT_LABEL,
  type HighlightColor,
} from '../utils/verse-highlights';

/** A highlight just created by the current selection gesture. */
interface ActiveRef {
  verseKey: string;
  id: string;
}

interface PopoverState {
  active: ActiveRef[];
  /** Viewport coords of the selection (for anchoring the popover). */
  rect: { left: number; right: number; top: number; bottom: number };
  /** Shared color of the active highlights, or null when they differ. */
  color: HighlightColor | null;
}

/**
 * Global highlight capture + color/delete popover.
 *
 * On every selection release (mouse or touch) it figures out which Arabic
 * word tokens the selection covers — by intersecting the live Range with the
 * `[data-arabic-region] [data-word-pos]` spans — and creates one highlight
 * per verse touched. Any English (gloss or full translation) caught in the
 * drag is ignored because it carries no `data-word-pos`. A small popover then
 * lets the user recolor or delete the highlight they just made (which doubles
 * as instant undo for an accidental copy-selection).
 *
 * It is DOM-driven (no props): the verse components render the highlights from
 * the same store. Mount it once on any surface that shows highlightable Arabic.
 */
export default function HighlightController() {
  const [popover, setPopover] = useState<PopoverState | null>(null);

  const capture = useCallback(() => {
    // Defer so the browser has finalized the selection after mouseup/touchend.
    window.setTimeout(() => {
      const sel = window.getSelection();
      if (!sel || sel.isCollapsed || sel.rangeCount === 0) return;

      const spans = document.querySelectorAll<HTMLElement>(
        '[data-arabic-region] [data-word-pos]',
      );
      type VerseHit = { min: number; max: number; arabic?: string; translation?: string };
      const byVerse = new Map<string, VerseHit>();
      // Iterate EVERY range — Firefox can hold several (Ctrl-drag) and we don't
      // want to silently drop the disjoint fragments.
      for (let i = 0; i < sel.rangeCount; i++) {
        const range = sel.getRangeAt(i);
        spans.forEach((el) => {
          // intersectsNode is a cheap pre-filter, but it returns true even when
          // the selection only *touches* a token's boundary (0 chars of it
          // selected) — common in these gap-spaced flex rows. Require a real,
          // non-empty overlap so we don't pull in an unintended trailing word.
          if (!range.intersectsNode(el) || !selectionOverlapsToken(range, el)) return;
          const region = el.closest('[data-verse-key]');
          const vk = region?.getAttribute('data-verse-key');
          const pos = parseInt(el.getAttribute('data-word-pos') || '', 10);
          if (!vk || !Number.isFinite(pos)) return;
          const cur = byVerse.get(vk);
          if (!cur) {
            byVerse.set(vk, {
              min: pos,
              max: pos,
              // Carried onto the auto-saved item so the Saved panel can show
              // the verse + its highlights without a fetch.
              arabic: region?.getAttribute('data-verse-text') || undefined,
              translation: region?.getAttribute('data-verse-translation') || undefined,
            });
          } else {
            cur.min = Math.min(cur.min, pos);
            cur.max = Math.max(cur.max, pos);
          }
        });
      }

      if (byVerse.size === 0) return; // selection covered no Arabic tokens

      // Read geometry BEFORE collapsing the selection.
      const r = sel.getRangeAt(0).getBoundingClientRect();
      const rect = { left: r.left, right: r.right, top: r.top, bottom: r.bottom };

      const active: ActiveRef[] = [];
      const colors = new Set<HighlightColor>();
      byVerse.forEach((hit, vk) => {
        const h = addHighlight(vk, hit.min, hit.max, {
          arabic: hit.arabic,
          translation: hit.translation,
        });
        active.push({ verseKey: vk, id: h.id });
        colors.add(h.color);
      });

      // Clear the blue selection so it doesn't sit on top of the new mark.
      sel.removeAllRanges();

      setPopover({ active, rect, color: colors.size === 1 ? [...colors][0] : null });
    }, 0);
  }, []);

  useEffect(() => {
    document.addEventListener('mouseup', capture);
    document.addEventListener('touchend', capture);
    return () => {
      document.removeEventListener('mouseup', capture);
      document.removeEventListener('touchend', capture);
    };
  }, [capture]);

  const close = useCallback(() => setPopover(null), []);

  // Note: these run from the popover's click handlers (a user event), NOT from
  // a render — so mutating the store (which synchronously notifies subscribed
  // verse components) is safe here. Keep the store writes OUTSIDE the setState
  // updater so they never fire mid-render.
  const recolor = (color: HighlightColor) => {
    if (!popover) return;
    popover.active.forEach((a) => setHighlightColor(a.verseKey, a.id, color));
    setPopover({ ...popover, color });
  };

  const deleteActive = () => {
    if (popover) popover.active.forEach((a) => removeHighlight(a.verseKey, a.id));
    setPopover(null);
  };

  if (!popover) return null;

  return createPortal(
    <HighlightPopover
      rect={popover.rect}
      color={popover.color}
      onPick={recolor}
      onDelete={deleteActive}
      onDismiss={close}
    />,
    document.body,
  );
}

// ----- Popover -------------------------------------------------------------

const POPOVER_W = 196;
const POPOVER_H = 40; // single row of swatches — fixed, so we can place without measuring

function HighlightPopover({
  rect,
  color,
  onPick,
  onDelete,
  onDismiss,
}: {
  rect: { left: number; right: number; top: number; bottom: number };
  color: HighlightColor | null;
  onPick: (c: HighlightColor) => void;
  onDelete: () => void;
  onDismiss: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  // Place below the selection; flip above if that would overflow the viewport.
  const below = rect.bottom + 8;
  const top =
    below + POPOVER_H > window.innerHeight - 8 ? Math.max(8, rect.top - POPOVER_H - 8) : below;
  const left = clamp(
    (rect.left + rect.right) / 2 - POPOVER_W / 2,
    8,
    window.innerWidth - POPOVER_W - 8,
  );

  // Dismiss on outside click, Escape, or scroll (highlights are kept).
  useEffect(() => {
    const onDown = (e: MouseEvent | TouchEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onDismiss();
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onDismiss();
    };
    // Defer attaching the outside-click listener so the gesture that opened
    // the popover doesn't immediately close it.
    const t = window.setTimeout(() => {
      document.addEventListener('mousedown', onDown);
      document.addEventListener('touchstart', onDown);
    }, 0);
    document.addEventListener('keydown', onKey);
    window.addEventListener('scroll', onDismiss, true);
    return () => {
      window.clearTimeout(t);
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('touchstart', onDown);
      document.removeEventListener('keydown', onKey);
      window.removeEventListener('scroll', onDismiss, true);
    };
  }, [onDismiss]);

  return (
    // A transient, pointer-anchored color picker — role="toolbar" (not dialog)
    // since it manages no focus trap. The real safeguard against the capture
    // handler treating a swatch click as a new highlight is that the selection
    // was already collapsed (removeAllRanges) when the popover opened, so
    // `capture` early-returns on isCollapsed; no stopPropagation needed (and a
    // synthetic one couldn't stop the native document listener anyway).
    <div
      ref={ref}
      role="toolbar"
      aria-label="Highlight color"
      className="fixed z-50 flex items-center gap-1.5 rounded-full border border-stone-200 bg-white px-2 py-1.5 shadow-lg"
      style={{ left, top, width: POPOVER_W }}
    >
      {HIGHLIGHT_COLORS.map((c) => (
        <button
          key={c}
          type="button"
          aria-label={HIGHLIGHT_LABEL[c]}
          title={HIGHLIGHT_LABEL[c]}
          onClick={() => onPick(c)}
          className={`h-5 w-5 rounded-full ${HIGHLIGHT_SWATCH[c]} transition-transform hover:scale-110 ${
            color === c ? 'ring-2 ring-offset-1 ring-stone-500' : 'ring-1 ring-black/5'
          }`}
        />
      ))}
      <span className="mx-0.5 h-4 w-px bg-stone-200" aria-hidden />
      <button
        type="button"
        aria-label="Remove highlight"
        title="Remove highlight"
        onClick={onDelete}
        className="flex h-5 w-5 items-center justify-center rounded-full text-stone-400 transition-colors hover:bg-rose-50 hover:text-rose-600"
      >
        <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M4 4l8 8M12 4l-8 8" strokeLinecap="round" />
        </svg>
      </button>
    </div>
  );
}

function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v));
}

/**
 * True only when `selection` actually covers some of the token's content —
 * not merely touches its boundary. (Range.intersectsNode returns true even for
 * a zero-width boundary touch, which would pull an unselected adjacent word in.)
 * Overlap ⇔ selection.start < token.end AND token.start < selection.end.
 */
function selectionOverlapsToken(selection: Range, el: Element): boolean {
  const token = el.ownerDocument.createRange();
  token.selectNodeContents(el);
  // compareBoundaryPoints(how, source) returns the position of THIS range's
  // boundary relative to SOURCE's boundary (-1 before / 0 equal / 1 after).
  //   END_TO_START → compares selection.start vs token.end
  //   START_TO_END → compares selection.end   vs token.start
  // Overlap ⇔ selection.start < token.end (−1) AND selection.end > token.start (1).
  const selStartBeforeTokenEnd =
    selection.compareBoundaryPoints(Range.END_TO_START, token) < 0;
  const selEndAfterTokenStart =
    selection.compareBoundaryPoints(Range.START_TO_END, token) > 0;
  return selStartBeforeTokenEnd && selEndAfterTokenStart;
}
