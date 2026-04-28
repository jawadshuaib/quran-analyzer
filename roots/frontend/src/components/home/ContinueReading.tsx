import { useEffect, useState } from 'react';
import { getLastRead, subscribeToLastRead, clearLastRead } from '../../utils/last-read';
import { getSurahName } from '../../utils/surah-names';
import type { LastRead } from '../../utils/last-read';

/**
 * Homepage "Continue reading" card. Renders only when the user has
 * a saved last-read position (set by the reader page as the user
 * scrolls). Click → jump straight back to that verse in the reader.
 */
export default function ContinueReading() {
  const [lastRead, setLastRead] = useState<LastRead | null>(getLastRead());

  useEffect(() => {
    return subscribeToLastRead(() => setLastRead(getLastRead()));
  }, []);

  if (!lastRead) return null;

  const { surah, verse } = lastRead;
  const name = getSurahName(surah);

  function handleDismiss(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    clearLastRead();
  }

  return (
    <a
      href={`/read/${surah}:${verse}`}
      className="group mt-8 mb-10 sm:mb-12 flex items-center justify-between gap-4 rounded-xl border border-gold/30 bg-gold/5 px-4 py-3.5 hover:border-gold hover:bg-gold/10 transition-colors"
    >
      <div className="min-w-0">
        <div className="text-[11px] uppercase tracking-wide text-gold mb-0.5">
          Continue reading
        </div>
        <div className="font-serif text-base text-ink">
          Surah {name} · {surah}:{verse}
        </div>
      </div>
      <div className="flex items-center gap-3 flex-shrink-0">
        <button
          type="button"
          onClick={handleDismiss}
          className="text-[11px] text-ink-muted hover:text-ink-secondary px-2 py-1 cursor-pointer"
          aria-label="Dismiss"
        >
          Dismiss
        </button>
        <span className="text-gold group-hover:translate-x-0.5 transition-transform" aria-hidden="true">
          →
        </span>
      </div>
    </a>
  );
}
