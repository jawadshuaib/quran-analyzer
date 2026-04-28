import { useEffect, useState, useRef } from 'react';
import { fetchSurah } from '../../api/quran';
import type { SurahData } from '../../types';
import { setLastRead } from '../../utils/last-read';
import ReaderVerse from './ReaderVerse';

interface Props {
  surah: number;
  /** Optional verse to scroll to and highlight on load (deep link
   *  /read/<surah>:<verse>). The user can land directly on a verse
   *  via the homepage "Continue reading" card. */
  initialVerse?: number;
}

/**
 * Per-surah reader. Fetches every verse in one request via /api/surah/<n>,
 * renders them as a clean column with a left "gutter" of subtle
 * affordance icons per verse (notes, grammar, related, save, research).
 *
 * As the user scrolls, an IntersectionObserver tracks which verse is
 * currently in view and writes a debounced last-read marker to
 * localStorage so the homepage's "Continue reading" card can take them
 * back where they left off.
 */
export default function ReaderPage({ surah, initialVerse }: Props) {
  const [data, setData] = useState<SurahData | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  // Compact-header mode kicks in once the user has scrolled past the
  // initial full hero. The hero is sticky throughout — it just shrinks
  // so it doesn't eat half the viewport while reading.
  const [compactHeader, setCompactHeader] = useState(false);

  // For the IntersectionObserver — we need refs to each verse block.
  // A keyed-by-verse-number map keeps it simple.
  const verseRefs = useRef<Map<number, HTMLElement>>(new Map());
  const lastWrittenRef = useRef<number>(0);

  useEffect(() => {
    fetchSurah(surah)
      .then((d) => {
        setData(d);
        setLoading(false);
        document.title = `Read Surah ${d.name} (${d.name_arabic}) | al-nuqta`;
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : 'Failed to load surah');
        setLoading(false);
      });
  }, [surah]);

  // Scroll the deep-linked verse into view once the data + DOM are ready.
  useEffect(() => {
    if (!data || !initialVerse) return;
    const el = verseRefs.current.get(initialVerse);
    if (el) {
      // Slight delay to let the page settle (sticky nav, etc.)
      setTimeout(() => {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 50);
    }
  }, [data, initialVerse]);

  // Toggle compact header once the user has scrolled past the initial
  // full-size hero (~200 pixels). Cheap scroll listener.
  useEffect(() => {
    function check() {
      setCompactHeader(window.scrollY > 200);
    }
    check();
    window.addEventListener('scroll', check, { passive: true });
    return () => window.removeEventListener('scroll', check);
  }, []);

  // Track which verse is most-visible, write last-read marker (debounced).
  useEffect(() => {
    if (!data) return;
    const observer = new IntersectionObserver(
      (entries) => {
        // Pick the entry with greatest intersection ratio that's actually
        // visible. Prefer ones near the top of the viewport.
        let bestVerse = -1;
        let bestRatio = 0;
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          if (entry.intersectionRatio > bestRatio) {
            bestRatio = entry.intersectionRatio;
            const v = parseInt(entry.target.getAttribute('data-verse') || '0', 10);
            if (v) bestVerse = v;
          }
        }
        if (bestVerse > 0) {
          // Debounce writes — at most one per 2 seconds
          const now = Date.now();
          if (now - lastWrittenRef.current > 2000) {
            lastWrittenRef.current = now;
            setLastRead(surah, bestVerse);
          }
        }
      },
      {
        // Watch for verses entering the upper half of the viewport
        rootMargin: '-80px 0px -50% 0px',
        threshold: [0, 0.25, 0.5, 0.75, 1],
      },
    );
    verseRefs.current.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, [data, surah]);

  function setVerseRef(verse: number, el: HTMLElement | null) {
    if (el) verseRefs.current.set(verse, el);
    else verseRefs.current.delete(verse);
  }

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
    <>
      {/* Sticky surah header — full-width strip below the top nav. Starts
          full-size and shrinks once the user scrolls past it, so the
          surah info stays visible without eating the viewport while
          reading. */}
      <header
        className={`sticky top-[56px] sm:top-[64px] z-20 w-full border-b border-card-border bg-cream/95 backdrop-blur-sm transition-all duration-200 ${
          compactHeader ? 'py-2.5 sm:py-3' : 'pt-6 pb-8'
        }`}
      >
        <div className="max-w-3xl mx-auto px-4 text-center">
          {compactHeader ? (
            // Compact form — single line, optimized for "I just need
            // to know which surah I'm in"
            <div className="flex items-center justify-center gap-3 flex-wrap text-sm">
              <span className="font-mono text-[11px] text-ink-muted">
                {data.surah}
              </span>
              <h1 className="font-serif text-xl sm:text-2xl text-ink leading-none" lang="ar">
                {data.name_arabic}
              </h1>
              <span className="text-ink-muted">·</span>
              <span className="font-serif text-ink-secondary">
                {data.name}
              </span>
              <span className="hidden sm:inline text-ink-muted text-xs">
                · {data.verse_count} verses
              </span>
            </div>
          ) : (
            // Full hero — only on initial scroll position
            <>
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
            </>
          )}
        </div>
      </header>

      <div className="max-w-3xl mx-auto px-4 pb-16">
        {/* Verses */}
        <div className="space-y-1 mt-6">
          {data.verses.map((v) => (
            <ReaderVerse
              key={v.verse}
              ref={(el) => setVerseRef(v.verse, el)}
              surah={data.surah}
              verse={v}
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
      </div>
    </>
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
