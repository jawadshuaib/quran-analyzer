import { useState, useEffect, useRef } from 'react';
import { useSEO } from '../hooks/useSEO';
import { fetchQuranVocabulary, vocabTermSlug } from '../api/quran';
import type { QuranVocabularyTerm } from '../api/quran';

/**
 * /quran-vocabulary — abstract semantic core of 13 Qur'anic roots whose
 * conventional English renderings have narrowed to specific post-Qur'anic
 * institutions (ritual prayer, pilgrimage, alms, fasting, etc.). Derived
 * by surveying every occurrence of each root in the corpus and finding
 * the broader meaning that survives every usage — including the verses
 * the conventional reading cannot accommodate.
 */
export default function QuranVocabularyPage() {
  const [terms, setTerms] = useState<QuranVocabularyTerm[] | null>(null);
  const [error, setError] = useState('');
  const termRefs = useRef<Record<string, HTMLElement | null>>({});

  useSEO({
    title: 'Qur\'an Vocabulary — Abstract meanings of ṣalāh, zakāh, ḥajj, and more',
    description:
      'Some Qur\'anic roots whose meaning is often narrowed when translated are explored in greater detail. For these roots, we trace every occurrence in the corpus and find the broader meaning that survives every usage.',
    path: '/quran-vocabulary',
  });

  useEffect(() => {
    let cancelled = false;
    fetchQuranVocabulary()
      .then((resp) => {
        if (cancelled) return;
        setTerms(resp.terms);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : 'Failed to load');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Scroll to anchor if present in URL
  useEffect(() => {
    if (!terms) return;
    const hash = decodeURIComponent(window.location.hash.replace(/^#/, ''));
    if (!hash) return;
    const el = termRefs.current[hash];
    if (!el) return;
    requestAnimationFrame(() => {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      el.classList.add('ring-2', 'ring-amber-400', 'ring-offset-2');
      setTimeout(() => {
        el.classList.remove('ring-2', 'ring-amber-400', 'ring-offset-2');
      }, 2200);
    });
  }, [terms]);

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10 flex-1">
      <header className="text-center mb-8">
        <p className="text-xs text-ink-muted tracking-[0.08em] uppercase mb-3">Reference</p>
        <h1 className="font-serif text-2xl sm:text-[34px] font-medium tracking-tight leading-tight text-ink mb-3">
          Qur'an Vocabulary
        </h1>
        <p className="text-sm sm:text-[15px] text-ink-secondary max-w-2xl mx-auto leading-relaxed">
          Some Qur'anic roots whose meaning is often narrowed when translated are explored
          in greater detail. For these roots, we trace every occurrence in the corpus and
          find the broader meaning that survives every usage.
        </p>
      </header>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {!terms && !error && (
        <div className="flex justify-center py-16">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-amber-200 border-t-amber-600" />
        </div>
      )}

      {/* Quick jump-pill bar */}
      {terms && (
        <nav aria-label="Jump to term" className="flex flex-wrap gap-1.5 justify-center mb-8 text-xs">
          {terms.map((t) => {
            const slug = vocabTermSlug(t.root_buckwalter);
            return (
              <a
                key={slug}
                href={`#${slug}`}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full border border-stone-200 bg-white text-stone-700 hover:bg-amber-50 hover:text-amber-700 hover:border-amber-300 transition-colors"
              >
                <span className="font-arabic text-sm" lang="ar">{t.root_arabic}</span>
                <span className="text-stone-400">→</span>
                <span className="font-medium">{t.canonical_english}</span>
              </a>
            );
          })}
        </nav>
      )}

      {/* The list */}
      <div className="space-y-8">
        {terms?.map((t) => {
          const slug = vocabTermSlug(t.root_buckwalter);
          return (
            <section
              key={slug}
              id={slug}
              ref={(el) => {
                termRefs.current[slug] = el;
              }}
              className="scroll-mt-20 rounded-xl border border-card-border bg-white p-6 transition-shadow"
            >
              {/* Header */}
              <header className="flex items-baseline flex-wrap gap-x-4 gap-y-1 mb-4 pb-3 border-b border-stone-100">
                <h2 className="font-serif text-2xl text-ink">
                  <span className="text-stone-700" lang="ar">{t.root_arabic}</span>
                </h2>
                <span className="text-stone-300">→</span>
                <span className="font-serif text-xl font-medium text-amber-700">
                  {t.canonical_english}
                </span>
                <span className="ml-auto text-[11px] text-ink-muted tracking-wide">
                  {t.occurrence_count} occurrences
                </span>
                <a
                  href={`#${slug}`}
                  className="text-[11px] text-stone-400 hover:text-amber-700"
                  aria-label={`Permalink to ${t.root_arabic}`}
                  title="Copy link"
                  onClick={(e) => {
                    e.preventDefault();
                    const url = `${window.location.origin}/quran-vocabulary#${slug}`;
                    try { navigator.clipboard.writeText(url); } catch { /* noop */ }
                    window.history.pushState({}, '', `#${slug}`);
                  }}
                >#</a>
              </header>

              {/* Translation note */}
              {t.translation_note && (
                <p className="text-[14.5px] text-ink-secondary leading-relaxed mb-4">
                  {t.translation_note}
                </p>
              )}

              {/* Hard cases */}
              {t.hard_cases.length > 0 && (
                <div className="mt-4 pt-4 border-t border-stone-100">
                  <h3 className="text-[11px] uppercase tracking-[0.1em] text-ink-muted mb-3">
                    Verses where transliteration is preferred ({t.hard_cases.length})
                  </h3>
                  <ul className="space-y-3">
                    {t.hard_cases.map((hc) => (
                      <li key={hc.ref} className="rounded-md border border-amber-100 bg-amber-50/30 px-3 py-2">
                        <div className="flex items-baseline gap-3 flex-wrap">
                          <a
                            href={`/verse/${hc.ref}`}
                            className="font-mono text-xs text-amber-700 hover:underline"
                          >
                            {hc.ref}
                          </a>
                          <span className="font-arabic text-base text-stone-700" lang="ar">
                            {hc.arabic_word}
                          </span>
                          <span className="text-stone-400 text-xs">→</span>
                          <span className="text-sm font-medium italic text-stone-700">
                            {hc.transliteration}
                          </span>
                        </div>
                        <p className="mt-1 text-xs text-stone-600 leading-relaxed">
                          {hc.reason}
                        </p>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* No hard cases — small note */}
              {t.hard_cases.length === 0 && (
                <p className="mt-4 pt-3 border-t border-stone-100 text-[11px] text-stone-400 italic">
                  This canonical works cleanly across all {t.occurrence_count} occurrences —
                  no transliteration overrides needed.
                </p>
              )}
            </section>
          );
        })}
      </div>

      {terms && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'DefinedTermSet',
              name: "Qur'an Vocabulary — al-nuqta",
              url: 'https://al-nuqta.com/quran-vocabulary',
              hasDefinedTerm: terms.map((t) => ({
                '@type': 'DefinedTerm',
                name: t.canonical_english,
                alternateName: t.root_arabic,
                description: t.translation_note || undefined,
                url: `https://al-nuqta.com/quran-vocabulary#${vocabTermSlug(t.root_buckwalter)}`,
              })),
            }),
          }}
        />
      )}
    </div>
  );
}
