import { useEffect, useRef, useState, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import type { DictionaryHighlight } from '../types';
import { viewportSize } from '../utils/viewport';
import VerseRefText from './VerseRefText';

/**
 * Reader highlights on a dictionary entry's readable version (made by the
 * highlights job; stored in dictionary_highlights). Four kinds, matching the
 * evidence the site weighs when it chooses which entry opens first:
 *
 *   core   yellow  what the root's words share, as the entry states it
 *   quran  orange  the entry's sense of a word the Qur'an uses, or its reading
 *                  of a verse through ordinary Arabic
 *   early  blue    a witness from the Qur'an's own time: an early poet, a
 *                  proverb, Bedouin speech
 *   later  dotted  a sense drawn from hadith, exegesis, law or theology — a
 *                  quiet underline that says "weigh this", not a highlight
 */
export const HIGHLIGHT_LABEL: Record<DictionaryHighlight['kind'], string> = {
  core: 'Core meaning',
  quran: "The Qur'an's words",
  early: 'Early usage',
  later: 'Later interpretation',
};

const MARK_CLASS: Record<DictionaryHighlight['kind'], string> = {
  core: 'bg-hl-core',
  quran: 'bg-hl-quran',
  early: 'bg-hl-early',
  later: 'bg-transparent underline decoration-dotted decoration-2 decoration-hl-later underline-offset-[3px]',
};

const TIP_W = 300;
const HIDE_DELAY = 220;

const LABEL_CLASS: Record<DictionaryHighlight['kind'], string> = {
  core: 'bg-hl-core',
  quran: 'bg-hl-quran',
  early: 'bg-hl-early',
  later: 'border-b-2 border-dotted border-hl-later',
};

function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v));
}

/** One highlighted phrase. Its note shows on hover, keyboard focus and tap, in
 *  a fixed, viewport-clamped card portaled to body (a phrase at a screen edge
 *  on a phone can't push it off-screen). The card stays open while the pointer
 *  is on it, so the verse references in a note (rendered by VerseRefText) can
 *  be previewed and followed. */
export function HighlightMark({
  kind,
  note,
  detail,
  children,
}: {
  kind: DictionaryHighlight['kind'];
  note?: string;
  /** The fuller note, written from the site's own data (_highlight_notes.py). */
  detail?: string;
  children: ReactNode;
}) {
  const ref = useRef<HTMLElement>(null);
  const cardRef = useRef<HTMLSpanElement>(null);
  const hideTimer = useRef<number | null>(null);
  const usingCard = useRef(false);
  const [tip, setTip] = useState<{ left: number; top: number; above: boolean } | null>(null);
  const label = HIGHLIGHT_LABEL[kind];
  const body = detail || note || '';

  const cancelHide = () => {
    if (hideTimer.current) {
      window.clearTimeout(hideTimer.current);
      hideTimer.current = null;
    }
  };
  const hide = () => {
    cancelHide();
    setTip(null);
  };
  const hideSoon = () => {
    cancelHide();
    hideTimer.current = window.setTimeout(() => setTip(null), HIDE_DELAY);
  };

  function show() {
    cancelHide();
    const r = ref.current?.getBoundingClientRect();
    if (!r) return;
    const { width, height } = viewportSize();
    const left = clamp(r.left, 8, Math.max(8, width - TIP_W - 8));
    const above = r.bottom + 140 > height;
    setTip({ left, top: above ? r.top - 6 : r.bottom + 6, above });
  }

  // The card does not follow the phrase; dismiss rather than drift. A press
  // anywhere outside the phrase and the card closes it.
  useEffect(() => {
    if (!tip) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && hide();
    const onDown = (e: PointerEvent) => {
      const t = e.target as Node;
      if (!ref.current?.contains(t) && !cardRef.current?.contains(t)) hide();
    };
    window.addEventListener('scroll', hide, true);
    window.addEventListener('keydown', onKey);
    document.addEventListener('pointerdown', onDown, true);
    return () => {
      window.removeEventListener('scroll', hide, true);
      window.removeEventListener('keydown', onKey);
      document.removeEventListener('pointerdown', onDown, true);
    };
  }, [tip]);

  useEffect(() => cancelHide, []);

  return (
    <mark
      ref={ref}
      tabIndex={0}
      aria-label={body ? `${label}: ${body}` : label}
      onMouseEnter={show}
      onMouseLeave={hideSoon}
      onFocus={show}
      onBlur={(e) => {
        // Focus moving into the card (a verse link) keeps it open.
        if (usingCard.current || cardRef.current?.contains(e.relatedTarget as Node)) return;
        hideSoon();
      }}
      className={`rounded-[3px] px-px text-inherit [box-decoration-break:clone] cursor-help focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-emerald-400 ${MARK_CLASS[kind]}`}
    >
      {children}
      {tip &&
        createPortal(
          <span
            ref={cardRef}
            role="tooltip"
            onMouseEnter={cancelHide}
            onMouseLeave={hideSoon}
            onPointerDown={() => {
              cancelHide();
              usingCard.current = true;
              window.setTimeout(() => (usingCard.current = false), 600);
            }}
            style={{
              position: 'fixed',
              left: tip.left,
              top: tip.top,
              width: 'max-content',
              maxWidth: TIP_W,
              transform: tip.above ? 'translateY(-100%)' : undefined,
            }}
            className="z-50 block rounded-lg border border-stone-200 bg-white px-3 py-2 text-left text-[13px] font-normal not-italic leading-snug text-stone-700 shadow-lg"
          >
            <span className="mb-1 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wide text-stone-500">
              <span aria-hidden className={`inline-block h-2 w-3.5 rounded-sm ${LABEL_CLASS[kind]}`} />
              {label}
            </span>
            {body && (
              <span className="block">
                <VerseRefText text={body} />
              </span>
            )}
          </span>,
          document.body,
        )}
    </mark>
  );
}
