import { useCallback, useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from 'react';
import HighlightCross from './HighlightCross';
import {
  getNoteHighlights,
  hashNoteSource,
  removeNoteHighlight,
  removeNoteHighlights,
  resolveNoteHighlight,
  subscribeToNoteHighlights,
  type NoteHighlight,
  type NoteKind,
} from '../utils/note-highlights';
import { offsetsToRange, readNoteText } from '../utils/note-highlight-dom';
import {
  isCoarsePointer,
  nextColor,
  HIGHLIGHT_BG,
  HIGHLIGHT_COLORS,
  type HighlightColor,
} from '../utils/verse-highlights';
import { isHighlightingEnabled, subscribeToReaderPrefs } from '../utils/reader-prefs';

// ----- Painting --------------------------------------------------------------
//
// Highlights are painted with the CSS Custom Highlight API (`::highlight(note-hl-<colour>)`
// in index.css) rather than by wrapping the passage in <mark>s. The note is a
// tree of interactive React spans — verse-ref links, grammar chips, citation
// anchors, poetry quotes — and a passage can cut across any of them; painting
// Ranges leaves that tree exactly as React rendered it. Every note on the page
// contributes its Ranges to one shared Highlight per colour.

const registry = new Map<string, { range: Range; color: HighlightColor }[]>();

interface HighlightRegistry {
  set(name: string, h: unknown): void;
  delete(name: string): void;
}

function cssHighlights(): HighlightRegistry | null {
  const reg = (globalThis.CSS as unknown as { highlights?: HighlightRegistry } | undefined)?.highlights;
  const Ctor = (globalThis as { Highlight?: unknown }).Highlight;
  return reg && typeof Ctor === 'function' ? reg : null;
}

/** Browsers without the API get translucent boxes drawn over the passage. */
const canPaintRanges = typeof window !== 'undefined' && !!cssHighlights();

function syncRegistry(): void {
  const reg = cssHighlights();
  if (!reg) return;
  const all = [...registry.values()].flat();
  const Ctor = (globalThis as unknown as { Highlight: new (...r: Range[]) => unknown }).Highlight;
  for (const color of HIGHLIGHT_COLORS) {
    const ranges = all.filter((x) => x.color === color).map((x) => x.range);
    if (ranges.length) reg.set(`note-hl-${color}`, new Ctor(...ranges));
    else reg.delete(`note-hl-${color}`);
  }
}

// ----- Component -------------------------------------------------------------

interface Box {
  color: HighlightColor;
  left: number;
  top: number;
  width: number;
  height: number;
}

interface Layout {
  /** Where each highlight's remove-× sits (its first line's top-left). */
  crosses: { id: string; left: number; top: number }[];
  /** Fallback paint, only filled when ranges can't be painted natively. */
  boxes: Box[];
}

const EMPTY_LAYOUT: Layout = { crosses: [], boxes: [] };

function sameLayout(a: Layout, b: Layout): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

/**
 * Wraps one note under a verse so the reader can highlight passages in it.
 * Selecting text inside highlights and saves it (HighlightController does
 * the capturing, via captureNoteSelection); a highlight is removed with the
 * same "×" verse highlights use — shown on hover, always on touch screens, and
 * reachable by Tab. Colours cycle per note — yellow first, then the next unused.
 *
 * `source` is the note's raw text, used only to tell whether the note has been
 * edited since a highlight was made (see NoteHighlight.srcHash).
 */
export default function NoteHighlightable({
  verseKey,
  note,
  source,
  className,
  children,
}: {
  verseKey: string;
  note: NoteKind;
  source: string;
  className?: string;
  children: React.ReactNode;
}) {
  const instanceId = useId();
  const wrapRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const rangesRef = useRef<{ id: string; range: Range }[]>([]);
  const srcHash = useMemo(() => hashNoteSource(source), [source]);
  const coarse = isCoarsePointer();

  const [all, setAll] = useState<NoteHighlight[]>(() => getNoteHighlights(verseKey));
  useEffect(() => {
    const update = () => setAll(getNoteHighlights(verseKey));
    update();
    return subscribeToNoteHighlights(update);
  }, [verseKey]);
  const highlights = useMemo(() => all.filter((h) => h.note === note), [all, note]);

  const [enabled, setEnabled] = useState(isHighlightingEnabled);
  useEffect(() => subscribeToReaderPrefs(() => setEnabled(isHighlightingEnabled())), []);

  // The colour a selection here shows while it's live. Fixed when the
  // selection starts: the highlight it makes is saved while the passage is
  // still selected, and the selection must keep showing that highlight's colour
  // rather than move on to the one after it.
  const [selColor, setSelColor] = useState<HighlightColor | null>(null);
  useEffect(() => {
    if (!selColor) return;
    const onChange = () => {
      const sel = window.getSelection();
      const content = contentRef.current;
      if (!sel || sel.isCollapsed || !content || !sel.getRangeAt(0).intersectsNode(content)) {
        setSelColor(null);
      }
    };
    document.addEventListener('selectionchange', onChange);
    return () => document.removeEventListener('selectionchange', onChange);
  }, [selColor]);

  const [layout, setLayout] = useState<Layout>(EMPTY_LAYOUT);
  const [hoverId, setHoverId] = useState<string | null>(null);

  /** Find each highlight in the note as rendered now, paint it, and place its ×. */
  const paint = useCallback(() => {
    const wrap = wrapRef.current;
    const content = contentRef.current;
    if (!wrap || !content) return;
    if (!highlights.length) {
      // The common case — most notes carry no highlights — so don't read
      // the text at all. (The reader can mount hundreds of notes at once.)
      rangesRef.current = [];
      if (registry.delete(instanceId)) syncRegistry();
      setLayout(EMPTY_LAYOUT);
      return;
    }
    const model = readNoteText(content);
    const found: { id: string; range: Range; color: HighlightColor }[] = [];
    const stale: string[] = [];
    for (const h of highlights) {
      const at = resolveNoteHighlight(model.text, h);
      const range = at && offsetsToRange(model, at.start, at.end);
      if (range) found.push({ id: h.id, range, color: h.color });
      // The passage is gone and the note has changed since — it was edited
      // away. (Same source but no match is a render in flux; keep it.)
      else if (h.srcHash !== srcHash) stale.push(h.id);
    }
    rangesRef.current = found;
    registry.set(instanceId, found.map(({ range, color }) => ({ range, color })));
    syncRegistry();

    const base = wrap.getBoundingClientRect();
    const next: Layout = { crosses: [], boxes: [] };
    for (const { id, range, color } of found) {
      const rects = [...range.getClientRects()].filter((r) => r.width > 0 && r.height > 0);
      if (!rects.length) continue;
      next.crosses.push({ id, left: rects[0].left - base.left, top: rects[0].top - base.top });
      if (!canPaintRanges) {
        for (const r of rects) {
          next.boxes.push({ color, left: r.left - base.left, top: r.top - base.top, width: r.width, height: r.height });
        }
      }
    }
    setLayout((prev) => (sameLayout(prev, next) ? prev : next));
    if (stale.length) removeNoteHighlights(verseKey, stale);
  }, [highlights, instanceId, srcHash, verseKey]);

  // Repaint when the highlights change, and whenever the note's DOM or size
  // does: glossary chips and poetry quotes swap in after their data loads,
  // tooltips open inline, and a reflow moves every line.
  useLayoutEffect(() => {
    // Measuring the rendered note before paint is this effect's whole job.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    paint();
    const content = contentRef.current;
    const wrap = wrapRef.current;
    if (!content || !wrap || !highlights.length) return;
    let frame = 0;
    const schedule = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(paint);
    };
    const mo = new MutationObserver(schedule);
    mo.observe(content, { childList: true, subtree: true, characterData: true });
    const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(schedule) : null;
    ro?.observe(wrap);
    document.fonts?.ready.then(schedule).catch(() => {});
    return () => {
      cancelAnimationFrame(frame);
      mo.disconnect();
      ro?.disconnect();
    };
  }, [paint, highlights.length]);

  useEffect(
    () => () => {
      registry.delete(instanceId);
      syncRegistry();
    },
    [instanceId],
  );

  // Delegated hover: which highlight is the pointer over? A little slack
  // around each line so the × (which sits on the corner) stays reachable.
  function handleMouseMove(e: React.MouseEvent) {
    if (coarse) return;
    if ((e.target as HTMLElement).closest('[data-nh-ignore]')) return; // on the × itself
    const { clientX: x, clientY: y } = e;
    const PAD = 10;
    let hit: string | null = null;
    for (const { id, range } of rangesRef.current) {
      for (const r of range.getClientRects()) {
        if (x >= r.left - PAD && x <= r.right + PAD && y >= r.top - PAD && y <= r.bottom + PAD) {
          hit = id;
          break;
        }
      }
      if (hit) break;
    }
    if (hit !== hoverId) setHoverId(hit);
  }

  return (
    <div
      ref={wrapRef}
      className={`relative ${className ?? ''}`}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setHoverId(null)}
    >
      <div
        ref={contentRef}
        data-note-hl={note}
        data-note-verse={verseKey}
        data-note-src={srcHash}
        // Selecting in a note is highlighting, so the selection itself shows in
        // the colour the next highlight here will take (index.css) — the passage
        // takes its colour as it's selected and keeps it after, while it can
        // still be copied.
        data-hl-on={enabled ? (selColor ?? nextColor(highlights)) : undefined}
        onPointerDown={() => setSelColor(nextColor(highlights))}
      >
        {children}
      </div>
      {layout.boxes.map(({ color, ...box }, i) => (
        <span
          key={i}
          aria-hidden
          data-nh-ignore
          className={`pointer-events-none absolute rounded-sm mix-blend-multiply ${HIGHLIGHT_BG[color]}`}
          style={box}
        />
      ))}
      {layout.crosses.map((c) => (
        <span key={c.id} data-nh-ignore className="absolute h-0 w-0" style={{ left: c.left, top: c.top }}>
          <HighlightCross
            visible={coarse || hoverId === c.id}
            onRemove={() => {
              // The selection that made the highlight is usually still live
              // (it's kept so it can be copied); drop it, or the next mouseup
              // or touch-selection settle would highlight it all over again.
              const sel = window.getSelection();
              const content = contentRef.current;
              if (sel && content && sel.rangeCount && sel.getRangeAt(0).intersectsNode(content)) {
                sel.removeAllRanges();
              }
              removeNoteHighlight(verseKey, c.id);
              setHoverId(null);
            }}
          />
        </span>
      ))}
    </div>
  );
}
