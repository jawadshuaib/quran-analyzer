import { useEffect, useState, useRef } from 'react';
import { fetchSurah, fetchDefaultReciter } from '../../api/quran';
import type { SurahData } from '../../types';
import type { DefaultReciter } from '../../api/quran';
import { setLastRead } from '../../utils/last-read';
import {
  isWordByWordEnabled,
  subscribeToReaderPrefs,
} from '../../utils/reader-prefs';
import ReaderVerse from './ReaderVerse';
import { useVisibleVerses } from './useVisibleVerses';
import ReaderAsk from './ReaderAsk';

interface Props {
  surah: number;
  /** Optional verse to scroll to and highlight on load (deep link
   *  /read/<surah>:<verse>). The user can land directly on a verse
   *  via the homepage "Continue reading" card. */
  initialVerse?: number;
  /** When set together with initialVerse, the reader shows ONLY verses
   *  initialVerse..endVerse of the surah (e.g. /read/36:32-34). Used
   *  for sharing a passage rather than a whole surah. */
  endVerse?: number;
}

/**
 * Per-surah reader. Fetches every verse in one bulk request via
 * /api/surah/<n>. The fetch always asks for `surveyed_roots` so the
 * chip-tooltip layer can highlight surveyed words in translations,
 * and conditionally asks for `words` (per-word arabic + gloss) when
 * the user has the word-by-word setting enabled.
 *
 * As the user scrolls, an IntersectionObserver tracks which verse is
 * currently in view and writes a debounced last-read marker to
 * localStorage so the homepage's "Continue reading" card can take
 * them back where they left off.
 */
export default function ReaderPage({ surah, initialVerse, endVerse }: Props) {
  const isRange = endVerse !== undefined && initialVerse !== undefined && endVerse > initialVerse;
  const [data, setData] = useState<SurahData | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [wordByWord, setWordByWord] = useState(() => isWordByWordEnabled());
  const [reciter, setReciter] = useState<DefaultReciter | null>(null);

  useEffect(() => {
    fetchDefaultReciter().then(setReciter).catch(() => { /* play button silently disabled */ });
  }, []);

  const lastWrittenRef = useRef<number>(0);

  // Visibility tracker — drives both the last-read marker and the
  // floating "Ask about <verse>" launcher. The hook also computes a
  // [first, last] window; we don't use it today (the Ask flow is
  // single-verse-anchored) but it's cheap and handy for future
  // surrounding-context features.
  const {
    anchor: visibleAnchor,
    setRef: setVerseRef,
  } = useVisibleVerses({ enabled: !!data });

  // Debounced last-read writer — keyed off the visibility hook, no need
  // for a separate observer. Throttles writes to once per 2s so a fast
  // scroll doesn't hammer localStorage.
  useEffect(() => {
    if (visibleAnchor <= 0) return;
    const now = Date.now();
    if (now - lastWrittenRef.current > 2000) {
      lastWrittenRef.current = now;
      setLastRead(surah, visibleAnchor);
    }
  }, [visibleAnchor, surah]);

  // Pick up live changes to the word-by-word setting (e.g. user toggles
  // it from Settings in another tab) and re-render. The fetch effect
  // below re-runs whenever wordByWord flips, so the page reloads with
  // the new include set.
  useEffect(() => {
    return subscribeToReaderPrefs(() => setWordByWord(isWordByWordEnabled()));
  }, []);

  useEffect(() => {
    setLoading(true);
    fetchSurah(surah, {
      includeWords: wordByWord,
      includeSurveyedRoots: true,
    })
      .then((d) => {
        setData(d);
        setLoading(false);
        document.title = `Read Surah ${d.name} (${d.name_arabic}) | al-nuqta`;
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : 'Failed to load surah');
        setLoading(false);
      });
  }, [surah, wordByWord]);

  // Scroll the deep-linked verse into view once the data + DOM are ready.
  // The visibility hook holds the actual element refs internally, so we
  // wait one frame after data lands to give it a chance to register.
  useEffect(() => {
    if (!data || !initialVerse) return;
    const t = setTimeout(() => {
      const el = document.querySelector(
        `[data-verse="${initialVerse}"]`,
      ) as HTMLElement | null;
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 80);
    return () => clearTimeout(t);
  }, [data, initialVerse]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-card-border border-t-gold" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-10">
        <p className="text-sm text-red-700">{error || 'Surah not found.'}</p>
        <a href="/" className="mt-3 inline-block text-sm text-gold hover:underline">
          ← Back to home
        </a>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 pb-16">
      {/* Surah header (static — scrolls away with the rest of the page) */}
      <header className="pt-6 pb-8 text-center border-b border-card-border mb-8">
        <p className="text-[11px] tracking-[0.08em] uppercase text-ink-muted mb-2">
          Surah {data.surah} of 114
        </p>
        <h1 className="font-serif text-4xl sm:text-5xl text-ink mb-2" lang="ar">
          {data.name_arabic}
        </h1>
        <p className="font-serif text-lg text-ink-secondary">
          {data.name}
          {data.meaning && (
            <span className="text-ink-muted"> · {data.meaning}</span>
          )}
        </p>
        <p className="text-xs text-ink-muted mt-2">
          {data.verse_count} {data.verse_count === 1 ? 'verse' : 'verses'}
        </p>
        <SurahNav surah={data.surah} />
      </header>

      {isRange && (
        <div className="mb-6 rounded-lg border border-card-border bg-cream/50 px-4 py-3 text-sm text-ink-secondary flex items-center justify-between gap-3">
          <span>
            Showing verses <strong>{initialVerse}–{endVerse}</strong> of Surah {data.name}.
          </span>
          <a href={`/read/${data.surah}`} className="text-gold hover:underline whitespace-nowrap">
            Read full surah →
          </a>
        </div>
      )}

      {/* Verses */}
      <div className="space-y-1">
        {data.verses
          .filter((v) =>
            !isRange ? true : (v.verse >= (initialVerse as number) && v.verse <= (endVerse as number)),
          )
          .map((v) => (
            <ReaderVerse
              key={v.verse}
              ref={(el) => setVerseRef(v.verse, el)}
              surah={data.surah}
              verse={v}
              wordByWord={wordByWord}
              reciter={reciter}
              highlighted={initialVerse === v.verse}
            />
          ))}
      </div>

      {/* Footer nav: previous / next surah */}
      <div className="mt-12 flex items-center justify-between text-sm">
        <SurahNavLink direction="prev" current={data.surah} />
        <a href="/" className="text-ink-muted hover:text-ink-secondary">
          Surah list
        </a>
        <SurahNavLink direction="next" current={data.surah} />
      </div>

      {/* Floating "Ask about <verse>" launcher. Lives outside the page
          flow (fixed positioning) so it doesn't affect layout. The
          label tracks the most-visible verse until the user clicks;
          the click freezes that verse and mounts the assistant. */}
      <ReaderAsk surah={data.surah} anchor={visibleAnchor} />
    </div>
  );
}

function SurahNav({ surah }: { surah: number }) {
  return (
    <div className="mt-4 flex items-center justify-center gap-3 text-[11px] text-ink-muted">
      {surah > 1 && (
        <a href={`/read/${surah - 1}`} className="hover:text-gold">
          ← Previous
        </a>
      )}
      <span>·</span>
      <a href="/" className="hover:text-gold">
        All surahs
      </a>
      {surah < 114 && (
        <>
          <span>·</span>
          <a href={`/read/${surah + 1}`} className="hover:text-gold">
            Next →
          </a>
        </>
      )}
    </div>
  );
}

function SurahNavLink({ direction, current }: { direction: 'prev' | 'next'; current: number }) {
  const target = direction === 'prev' ? current - 1 : current + 1;
  if (target < 1 || target > 114) return <span />;
  return (
    <a
      href={`/read/${target}`}
      className="text-ink-secondary hover:text-gold transition-colors"
    >
      {direction === 'prev' ? '← Surah ' : 'Surah '}
      {target}
      {direction === 'next' ? ' →' : ''}
    </a>
  );
}
