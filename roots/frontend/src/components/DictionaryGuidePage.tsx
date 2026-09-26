import { useEffect, useMemo, useState } from 'react';
import { useSEO } from '../hooks/useSEO';
import type { DictionaryGuide } from '../content/dictionary-guides/types';
import { GUIDE_LOADERS, loadAllGuides } from '../content/dictionary-guides/loaders';
import { GUIDE_BASE_PATH, guidePath } from '../content/dictionary-guides/registry';
import DictionaryGuideProse from './DictionaryGuideProse';
import { buildCitationIndex, renderGuideInline } from '../utils/dictionary-guide-markup';
import { wrapArabicRuns } from '../utils/arabic-runs';

/** The note every guide carries: what the site's dictionary panel actually
 *  shows, so no essay has to repeat it (FORMAT.md §3 quotes this text). */
export function HowWePresentNote({ plural = false }: { plural?: boolean }) {
  return (
    <section className="rounded-xl border border-stone-200 bg-cream-dark/40 px-4 py-4 sm:px-5">
      <h2 className="text-[11px] font-semibold uppercase tracking-wider text-stone-500">
        How al-nuqta presents {plural ? 'these dictionaries' : 'this dictionary'}
      </h2>
      <p className="mt-2 text-[13.5px] leading-relaxed text-ink-secondary">
        On root and word pages, each entry opens in a readable English version written for
        al-nuqta. It is drafted by AI from the stored original and checked against it in a
        separate AI review. It keeps the entry's distinctions of meaning, grammar and quoted
        evidence but condenses — chains of transmitters, repeated synonyms and digressions are
        dropped, and on some long or multi-root entries it covers only part — so it is not the
        author's own wording. <span className="font-medium">Original Text</span> shows the stored
        original (Arabic, or English for Lane and Salmoné) as published on{' '}
        <a
          href="https://arabiclexicon.hawramani.com/"
          target="_blank"
          rel="noopener noreferrer"
          className="underline decoration-stone-300 underline-offset-2 hover:text-emerald-700"
        >
          arabiclexicon.hawramani.com
        </a>
        , beside a closer English translation (for Lane and Salmoné, a lightly edited copy of the
        English), also prepared for al-nuqta.{' '}
        {plural
          ? 'In the guides, the boxed excerpts come from that stored original; other quotations come from the works listed under each guide’s sources. Translations from Arabic were made for the guides unless another translator is named.'
          : 'On this page, the boxed excerpts come from that stored original; other quotations come from the works listed under Sources. Translations from Arabic were made for this guide unless another translator is named.'}
      </p>
    </section>
  );
}

function Loading() {
  return (
    <div className="mx-auto flex max-w-3xl justify-center px-4 py-16">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-100 border-t-emerald-600" />
    </div>
  );
}

function GuideNav({ slug }: { slug: string }) {
  const [all, setAll] = useState<DictionaryGuide[] | null>(null);
  useEffect(() => {
    let cancelled = false;
    loadAllGuides().then((g) => { if (!cancelled) setAll(g); }).catch(() => {});
    return () => { cancelled = true; };
  }, []);
  if (!all) return null;
  const i = all.findIndex((g) => g.slug === slug);
  const prev = i > 0 ? all[i - 1] : null;
  const next = i >= 0 && i < all.length - 1 ? all[i + 1] : null;
  return (
    <nav className="mt-10 grid gap-3 border-t border-stone-200 pt-6 sm:grid-cols-2" aria-label="Other dictionaries">
      {prev ? (
        <a href={guidePath(prev.slug)} className="rounded-lg border border-stone-200 bg-white px-4 py-3 hover:border-emerald-300">
          <span className="block text-[11px] uppercase tracking-wider text-stone-400">← Earlier</span>
          <span className="font-medium text-stone-800">{prev.title}</span>
          <span className="block text-xs text-stone-500">{prev.author}</span>
        </a>
      ) : <span />}
      {next ? (
        <a href={guidePath(next.slug)} className="rounded-lg border border-stone-200 bg-white px-4 py-3 text-right hover:border-emerald-300">
          <span className="block text-[11px] uppercase tracking-wider text-stone-400">Later →</span>
          <span className="font-medium text-stone-800">{next.title}</span>
          <span className="block text-xs text-stone-500">{next.author}</span>
        </a>
      ) : <span />}
    </nav>
  );
}

function GuideArticle({ guide }: { guide: DictionaryGuide }) {
  useSEO({
    title: `${guide.title} — how to read this classical dictionary`,
    description: guide.summary,
    path: guidePath(guide.slug),
  });
  const { index, ordered, locators } = useMemo(
    () => buildCitationIndex([guide.lede, guide.body, guide.onOurSite, guide.limitedEvidence ?? ''], guide.sources),
    [guide],
  );
  const sourceLanguage = guide.dictionarySlugs.some((d) => d.startsWith('william-edward-lane') || d.startsWith('habib-anthony-salmone'))
    ? 'en'
    : 'ar';

  return (
    <article className="mx-auto w-full max-w-3xl px-4 pb-16 pt-8 sm:pt-10">
      <a href={GUIDE_BASE_PATH} className="text-xs text-emerald-700 hover:text-emerald-900 hover:underline">
        ← Classical dictionaries
      </a>

      <header className="mt-5">
        <p className="text-[11px] font-medium uppercase tracking-[0.09em] text-emerald-700">{guide.kind}</p>
        <div className="mt-2 flex flex-wrap items-baseline gap-x-4 gap-y-1">
          <h1 className="font-serif-translit text-[1.9rem] font-medium leading-tight tracking-tight text-ink sm:text-[2.3rem] [text-wrap:balance]">
            {wrapArabicRuns(guide.title)}
          </h1>
          {guide.titleAr && (
            <span dir="rtl" lang="ar" className="font-arabic text-[1.7rem] leading-tight text-stone-600">
              {guide.titleAr}
            </span>
          )}
        </div>
        {guide.titleGloss && <p className="mt-1 text-[15px] italic text-stone-500">{guide.titleGloss}</p>}
        <p className="mt-3 flex flex-wrap items-baseline gap-x-2 text-sm text-stone-600">
          <span className="font-medium text-stone-700">{guide.author}</span>
          {guide.authorAr && (
            <span dir="rtl" lang="ar" className="font-arabic text-base text-stone-500">{guide.authorAr}</span>
          )}
          <span className="text-stone-300" aria-hidden>·</span>
          <span className="tabular-nums">{guide.period}</span>
        </p>
      </header>

      <div className="mt-7 max-w-[68ch] text-[17px] leading-[1.75] text-ink">
        <DictionaryGuideProse text={guide.lede} cites={index} sourceLanguage={sourceLanguage} />
      </div>

      <div className="mt-6 max-w-[68ch] text-[15.5px] leading-[1.8] text-ink-secondary">
        <DictionaryGuideProse text={guide.body} cites={index} sourceLanguage={sourceLanguage} />
      </div>

      <div className="mt-12 max-w-[68ch] space-y-5">
        <HowWePresentNote />
        <section>
          <h2 className="font-serif-translit text-lg font-medium text-ink">This dictionary on al-nuqta</h2>
          <div className="mt-2 text-[14.5px] leading-relaxed text-ink-secondary">
            <DictionaryGuideProse text={guide.onOurSite} cites={index} sourceLanguage={sourceLanguage} />
          </div>
        </section>
        {guide.limitedEvidence && (
          <section className="rounded-lg border border-amber-200 bg-amber-50/60 px-4 py-3">
            <h2 className="text-[11px] font-semibold uppercase tracking-wider text-amber-800">
              Why this account is short
            </h2>
            <div className="mt-1 text-[13.5px] leading-relaxed text-stone-700">
              <DictionaryGuideProse text={guide.limitedEvidence} cites={index} sourceLanguage={sourceLanguage} />
            </div>
          </section>
        )}
        <section aria-labelledby="sources-heading">
          <h2 id="sources-heading" className="font-serif-translit text-lg font-medium text-ink">Sources</h2>
          <ol className="mt-3 space-y-2.5 text-[13px] leading-relaxed text-stone-600">
            {ordered.map((s, i) => (
              <li key={s.id} id={`source-${i + 1}`} className="flex scroll-mt-24 gap-2.5">
                <span className="w-5 shrink-0 text-right tabular-nums text-stone-400">{i + 1}.</span>
                <span className="min-w-0 break-words">
                  {renderGuideInline(s.citation, index)}
                  {s.url && (
                    <>
                      {' '}
                      <a
                        href={s.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="break-all text-emerald-700 underline decoration-emerald-200 underline-offset-2 hover:decoration-emerald-600"
                      >
                        {s.url.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '')}
                      </a>
                    </>
                  )}
                  {locators[s.id]?.length ? (
                    <span className="block text-[11.5px] text-stone-400">Cited at: {locators[s.id].join('; ')}</span>
                  ) : null}
                </span>
              </li>
            ))}
          </ol>
        </section>
        {guide.lastVerified && (
          <p className="text-[11.5px] text-stone-400">
            Facts, quotations and examples on this page were independently checked against the
            sources and the stored entries on {guide.lastVerified}.
          </p>
        )}
      </div>

      <GuideNav slug={guide.slug} />
    </article>
  );
}

export default function DictionaryGuidePage({ slug }: { slug: string }) {
  const [guide, setGuide] = useState<DictionaryGuide | null>(null);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = GUIDE_LOADERS[slug];
    if (!load) {
      queueMicrotask(() => { if (!cancelled) setMissing(true); });
      return () => { cancelled = true; };
    }
    load()
      .then((g) => { if (!cancelled) setGuide(g); })
      .catch(() => { if (!cancelled) setMissing(true); });
    return () => { cancelled = true; };
  }, [slug]);

  if (missing) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <a href={GUIDE_BASE_PATH} className="text-xs text-emerald-700 hover:underline">← Classical dictionaries</a>
        <div className="mt-4 rounded-lg border border-stone-200 bg-stone-50 p-6 text-center text-stone-500">
          There is no guide at this address.{' '}
          <a href={GUIDE_BASE_PATH} className="text-emerald-700 underline underline-offset-2">
            See all the classical dictionaries.
          </a>
        </div>
      </div>
    );
  }
  if (!guide) return <Loading />;
  return <GuideArticle guide={guide} />;
}
