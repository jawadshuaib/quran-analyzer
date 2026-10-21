import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import {
  getHighlights,
  getHighlightAt,
  subscribeToHighlights,
  HIGHLIGHT_BG,
  type HighlightColor,
} from '../../utils/verse-highlights';
import { getCopyContext, subscribeCopyContext } from '../../utils/copy-context';
import { isHighlightingEnabled } from '../../utils/reader-prefs';
import { relatedPhraseUrl } from '../../utils/urls';

/** The server's cap on runs in one selection (related_phrases.MAX_RUNS). */
const MAX_TOGETHER = 8;

interface Props {
  /** The verse page's own verse: offered as soon as it has highlights. */
  defaultVerseKey?: string;
  defaultVerseText?: string;
}

/** The verse the bar is about, and the words the reader just selected in it. */
interface Active {
  verseKey: string;
  text: string;
  focus?: { start: number; end: number };
}

interface Run {
  start: number;
  end: number;
  color?: HighlightColor;
}

/**
 * The "See verses related to …" bar at the bottom of the screen.
 *
 * It follows the verse the reader last selected words in (via the copy
 * context the highlight controller sets) or tapped a highlight of, and offers
 * the related-verses page for each highlighted run in that verse — and for all
 * of them together when there are several. With highlighting turned off, the
 * selection itself is the phrase. On the verse page it also shows for that
 * verse's existing highlights. Mount it next to HighlightController.
 */
export default function RelatedPhraseBar({ defaultVerseKey, defaultVerseText }: Props) {
  const [active, setActive] = useState<Active | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const [, setVersion] = useState(0);

  // A new selection in a verse makes it the bar's verse.
  useEffect(
    () =>
      subscribeCopyContext(() => {
        const ctx = getCopyContext();
        if (!ctx) return; // deselecting keeps the bar; × dismisses it
        setActive({
          verseKey: ctx.verseKey,
          text: ctx.arabic,
          focus: { start: ctx.startPos, end: ctx.endPos },
        });
        setDismissed(false);
      }),
    [],
  );

  // Tapping an existing highlight does too (the reader has many verses).
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      const word = (e.target as Element | null)?.closest?.('[data-arabic-region] [data-word-pos]');
      const region = word?.closest('[data-verse-key]');
      const vk = region?.getAttribute('data-verse-key');
      const pos = parseInt(word?.getAttribute('data-word-pos') || '', 10);
      if (!vk || !Number.isFinite(pos) || !getHighlightAt(vk, pos)) return;
      setActive({ verseKey: vk, text: region?.getAttribute('data-verse-text') || '' });
      setDismissed(false);
    };
    document.addEventListener('click', onClick);
    return () => document.removeEventListener('click', onClick);
  }, []);

  // Re-render on any highlight change (added, recoloured, removed).
  useEffect(() => subscribeToHighlights(() => setVersion((v) => v + 1)), []);

  // A different verse page starts fresh.
  useEffect(() => {
    setActive(null);
    setDismissed(false);
  }, [defaultVerseKey]);

  const current: Active | null =
    active ?? (defaultVerseKey && defaultVerseText ? { verseKey: defaultVerseKey, text: defaultVerseText } : null);
  if (!current || dismissed) return null;

  const runs: Run[] = getHighlights(current.verseKey).map((h) => ({
    start: h.startPos,
    end: h.endPos,
    color: h.color,
  }));
  // With highlighting off nothing was stored: the selection is the phrase.
  if (current.focus && !isHighlightingEnabled()) {
    const f = current.focus;
    if (!runs.some((r) => r.start <= f.start && r.end >= f.end)) runs.push({ ...f });
    runs.sort((a, b) => a.start - b.start);
  }
  if (runs.length === 0) return null;

  const [s, a] = current.verseKey.split(':').map(Number);
  const words = current.text.split(/\s+/).filter(Boolean);
  if (!s || !a || words.length === 0) return null;

  return createPortal(
    <div
      data-related-bar
      role="region"
      aria-label="Related verses"
      className="fixed inset-x-0 bottom-20 z-40 flex justify-center px-3 pointer-events-none"
    >
      <div className="pointer-events-auto w-full max-w-xl animate-chip-pop rounded-2xl border border-stone-200 bg-white px-3 py-2.5 shadow-lg">
        {runs.length === 1 ? (
          <div className="flex items-center gap-2">
            <a
              href={relatedPhraseUrl(s, a, runs)}
              className="group flex min-w-0 flex-1 items-center gap-2 text-sm text-stone-600"
            >
              <span className="shrink-0">See verses related to</span>
              <PhraseLabel words={words} run={runs[0]} />
              <Arrow />
            </a>
            <DismissButton onClick={() => setDismissed(true)} />
          </div>
        ) : (
          <>
            <div className="mb-1.5 flex items-center gap-2">
              <span className="min-w-0 flex-1 text-sm text-stone-600">
                See verses related to <span className="text-stone-400">· {current.verseKey}</span>
              </span>
              {runs.length <= MAX_TOGETHER && (
                <a
                  href={relatedPhraseUrl(s, a, runs)}
                  className="shrink-0 rounded-full bg-emerald-600 px-3 py-1 text-xs font-semibold text-white hover:bg-emerald-700"
                >
                  All {runs.length} together
                </a>
              )}
              <DismissButton onClick={() => setDismissed(true)} />
            </div>
            {/* In reading order (right to left), wrapping rather than scrolling
                sideways so every highlight is in view. */}
            <div dir="rtl" className="flex max-h-28 flex-wrap gap-1.5 overflow-y-auto">
              {runs.map((r) => (
                <a key={r.start} href={relatedPhraseUrl(s, a, [r])} className="min-w-0 max-w-full">
                  <PhraseLabel words={words} run={r} chip />
                </a>
              ))}
            </div>
          </>
        )}
      </div>
    </div>,
    document.body,
  );
}

/** The run's Arabic, shortened to its first and last words when long. */
function PhraseLabel({ words, run, chip }: { words: string[]; run: Run; chip?: boolean }) {
  const slice = words.slice(run.start - 1, run.end);
  const text = slice.length > 6 ? `${slice.slice(0, 3).join(' ')} … ${slice.slice(-2).join(' ')}` : slice.join(' ');
  return (
    <span
      dir="rtl"
      lang="ar"
      className={`min-w-0 truncate rounded-md px-1.5 font-arabic leading-[1.9] text-stone-800 ${
        run.color ? HIGHLIGHT_BG[run.color] : 'bg-stone-100'
      } ${chip ? 'block max-w-full text-base sm:text-lg hover:ring-1 hover:ring-stone-400' : 'text-lg sm:text-xl group-hover:underline'}`}
    >
      {text}
    </span>
  );
}

function Arrow() {
  return (
    <svg viewBox="0 0 16 16" className="h-4 w-4 shrink-0 text-emerald-600" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M3 8h10M9 4l4 4-4 4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function DismissButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      aria-label="Close"
      title="Close"
      onClick={onClick}
      className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-stone-400 transition-colors hover:bg-stone-100 hover:text-stone-600"
    >
      <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M4 4l8 8M12 4l-8 8" strokeLinecap="round" />
      </svg>
    </button>
  );
}
