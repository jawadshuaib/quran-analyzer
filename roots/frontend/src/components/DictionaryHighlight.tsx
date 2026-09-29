import { useEffect, useRef, useState, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import type { DictionaryHighlight } from '../types';
import { viewportSize } from '../utils/viewport';

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

const TIP_W = 260;

function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v));
}

/** One highlighted phrase. Its note (why it is marked) shows on hover, on
 *  keyboard focus, and on tap — a fixed, viewport-clamped bubble, portaled to
 *  body so a phrase at a screen edge on a phone never pushes it off-screen. */
export function HighlightMark({
  kind,
  note,
  children,
}: {
  kind: DictionaryHighlight['kind'];
  note?: string;
  children: ReactNode;
}) {
  const ref = useRef<HTMLElement>(null);
  const [tip, setTip] = useState<{ left: number; top: number; above: boolean } | null>(null);
  const label = HIGHLIGHT_LABEL[kind];
  const text = note ? `${label}: ${note}` : label;

  function show() {
    const r = ref.current?.getBoundingClientRect();
    if (!r) return;
    const { width, height } = viewportSize();
    const left = clamp(r.left, 8, Math.max(8, width - TIP_W - 8));
    const above = r.bottom + 64 > height;
    setTip({ left, top: above ? r.top - 6 : r.bottom + 6, above });
  }
  const hide = () => setTip(null);

  // The bubble does not follow the phrase; dismiss rather than drift.
  useEffect(() => {
    if (!tip) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && hide();
    window.addEventListener('scroll', hide, true);
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('scroll', hide, true);
      window.removeEventListener('keydown', onKey);
    };
  }, [tip]);

  return (
    <mark
      ref={ref}
      tabIndex={0}
      aria-label={text}
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
      className={`rounded-[3px] px-px text-inherit [box-decoration-break:clone] cursor-help focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-emerald-400 ${MARK_CLASS[kind]}`}
    >
      {children}
      {tip &&
        createPortal(
          <span
            role="tooltip"
            style={{
              position: 'fixed',
              left: tip.left,
              top: tip.top,
              width: 'max-content',
              maxWidth: TIP_W,
              transform: tip.above ? 'translateY(-100%)' : undefined,
            }}
            className="pointer-events-none z-50 rounded-md bg-stone-800 px-2.5 py-1.5 text-xs leading-snug text-stone-50 shadow-lg"
          >
            {text}
          </span>,
          document.body,
        )}
    </mark>
  );
}

/** The key above a highlighted entry: only the kinds this entry uses, and a
 *  switch that hides or shows the marks on every entry (remembered). */
export function HighlightLegend({
  kinds,
  on,
  onToggle,
}: {
  kinds: DictionaryHighlight['kind'][];
  on: boolean;
  onToggle: () => void;
}) {
  const order: DictionaryHighlight['kind'][] = ['core', 'quran', 'early', 'later'];
  return (
    <div className="mb-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-stone-500">
      {on &&
        order
          .filter((k) => kinds.includes(k))
          .map((k) => (
            <span key={k} className="inline-flex items-center gap-1.5">
              {k === 'later' ? (
                <span aria-hidden className="inline-block w-5 border-b-2 border-dotted border-hl-later" />
              ) : (
                <span aria-hidden className={`inline-block h-2.5 w-4 rounded-sm ${MARK_CLASS[k]}`} />
              )}
              {HIGHLIGHT_LABEL[k]}
            </span>
          ))}
      <button
        type="button"
        onClick={onToggle}
        aria-pressed={on}
        className="font-medium text-emerald-700 underline decoration-emerald-200 underline-offset-2 hover:text-emerald-900"
      >
        {on ? 'Hide highlights' : 'Show highlights'}
      </button>
    </div>
  );
}

const PREF_KEY = 'nuqta.dictHighlights';

/** Whether reader highlights show, remembered across visits (on by default). */
export function useHighlightsOn(): [boolean, () => void] {
  const [on, setOn] = useState(() => {
    try {
      return localStorage.getItem(PREF_KEY) !== 'off';
    } catch {
      return true;
    }
  });
  const toggle = () =>
    setOn((v) => {
      try {
        localStorage.setItem(PREF_KEY, v ? 'off' : 'on');
      } catch {
        /* private mode: the choice lasts for this page only */
      }
      return !v;
    });
  return [on, toggle];
}
