import { useEffect, useState } from 'react';
import { useSEO } from '../hooks/useSEO';
import type { DictionaryGuide } from '../content/dictionary-guides/types';
import { loadAllGuides } from '../content/dictionary-guides/loaders';
import { GUIDE_BASE_PATH, guidePath } from '../content/dictionary-guides/registry';
import { HowWePresentNote } from './DictionaryGuidePage';
import { wrapArabicRuns } from '../utils/arabic-runs';
import { renderGuideInline, type CitationIndex } from '../utils/dictionary-guide-markup';

const NO_CITES: CitationIndex = { number: {}, byId: {} };

/** /classical-dictionaries — one card per dictionary shown in the root and
 *  word pages' "Classical Dictionaries" panel, in date order (the panel's own
 *  order), each linking to its reader's guide. Dates order the list; nothing
 *  here ranks the works. */
export default function DictionaryGuidesIndex() {
  const [guides, setGuides] = useState<DictionaryGuide[] | null>(null);
  const [error, setError] = useState(false);

  useSEO({
    title: 'Classical Arabic dictionaries — reader’s guides',
    description:
      'Guides to the classical Arabic dictionaries quoted on al-nuqta’s root and word pages: who wrote each one, how it is organised, what evidence it uses, and how to read its entries when studying the Qur’an.',
    path: GUIDE_BASE_PATH,
  });

  useEffect(() => {
    let cancelled = false;
    loadAllGuides()
      .then((g) => { if (!cancelled) setGuides(g); })
      .catch(() => { if (!cancelled) setError(true); });
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-16 pt-8 sm:pt-10">
      <header className="max-w-[68ch]">
        <p className="text-[11px] font-medium uppercase tracking-[0.09em] text-emerald-700">Reader’s guides</p>
        <h1 className="mt-2 font-serif-translit text-[1.9rem] font-medium leading-tight tracking-tight text-ink sm:text-[2.3rem]">
          The classical dictionaries
        </h1>
        <div className="mt-4 space-y-3 text-[15.5px] leading-[1.75] text-ink-secondary">
          <p>
            Root pages on al-nuqta, and the pages of words built on a root, carry a panel called
            Classical Dictionaries, showing how a series of Arabic dictionaries explain that root (the{' '}
            <a href="/dictionary" className="text-emerald-800 underline decoration-emerald-200 underline-offset-[3px] hover:decoration-emerald-600">
              Qurʾānic Dictionary
            </a>{' '}
            lists every root that has them). The dictionaries were written centuries
            apart, for different readers and for different jobs: some explain the unusual words of the
            Qurʾān, some try to record the language as a whole, some shorten or comment on an earlier
            dictionary, one explains the vocabulary of a law book, and two were written in English in
            the nineteenth century.
          </p>
          <p>
            Knowing which kind of book you are reading changes what an entry can tell you. Each guide
            below explains who made the dictionary, how it is organised, what evidence it relies on, and
            how to read the excerpts you meet on the site — with real entries you can open and check.
            They are listed by date, not by importance.
          </p>
        </div>
      </header>

      {error && (
        <p className="mt-8 rounded-lg border border-stone-200 bg-stone-50 p-5 text-center text-stone-500">
          The guides could not be loaded. Please try again.
        </p>
      )}
      {!guides && !error && (
        <div className="mt-12 flex justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-100 border-t-emerald-600" />
        </div>
      )}

      {guides && (
        <ol className="mt-9 grid gap-3">
          {guides.map((g) => (
            <li key={g.slug}>
              <a
                href={guidePath(g.slug)}
                className="group block rounded-xl border border-stone-200 bg-white px-4 py-4 transition-colors hover:border-emerald-300 hover:bg-emerald-50/30 sm:px-5"
              >
                <span className="block text-[11px] font-medium uppercase tracking-[0.08em] text-emerald-700">{g.kind}</span>
                <span className="mt-1 flex flex-wrap items-baseline gap-x-3 gap-y-0.5">
                  <span className="font-serif-translit text-[1.2rem] font-medium text-ink group-hover:text-emerald-900">
                    {wrapArabicRuns(g.title)}
                  </span>
                  {g.titleAr && (
                    <span dir="rtl" lang="ar" className="font-arabic text-lg text-stone-500">{g.titleAr}</span>
                  )}
                </span>
                <span className="mt-0.5 block text-[13px] text-stone-600">
                  {g.author}
                  <span className="text-stone-300"> · </span>
                  <span className="text-stone-500">{g.period}</span>
                </span>
                <span className="mt-2 block max-w-[68ch] text-[14px] leading-relaxed text-ink-secondary">
                  {renderGuideInline(g.summary, NO_CITES)}
                </span>
                {g.limitedEvidence && (
                  <span className="mt-1.5 block text-[11.5px] text-amber-700">
                    A short account: reliable information about this work is limited.
                  </span>
                )}
              </a>
            </li>
          ))}
        </ol>
      )}

      <div className="mt-10 max-w-[68ch]">
        <HowWePresentNote plural />
      </div>
    </div>
  );
}
