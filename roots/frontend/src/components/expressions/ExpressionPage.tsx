import { useEffect, useState } from 'react';
import type { ExpressionDetail } from '../../types';
import { fetchExpression } from '../../api/quran';
import { useSEO } from '../../hooks/useSEO';
import FormattedText from '../FormattedText';

const TASHKEEL = /[ؐ-ًؚ-ٰٟۖ-ۭـ]/g;
const bare = (s: string) => s.replace(TASHKEEL, '').replace(/[ٱأإآ]/g, 'ا').replace(/[^ء-ي]/g, '');

// Particles that would light up all over a verse if marked wherever they occur.
const PARTICLES = new Set(['على', 'علي', 'من', 'في', 'فى', 'ما', 'لا', 'ان', 'او', 'ثم', 'الى', 'الي', 'عن', 'لم', 'لن', 'قد', 'هو', 'هم', 'الا', 'ولا', 'وما', 'به', 'له', 'لهم']);

/** A verse's words, with those of the expression marked (vowel marks ignored). */
function MarkedVerse({ text, expression }: { text: string; expression: string }) {
  const wanted = new Set(
    expression.split(/\s+/).map(bare).filter((w) => w.length > 1 && !PARTICLES.has(w)),
  );
  return (
    <p dir="rtl" lang="ar" className="font-arabic text-2xl leading-[2.1] text-stone-800">
      {text.split(/\s+/).map((w, i) => (
        <span key={i}>
          {i > 0 && ' '}
          {wanted.has(bare(w)) ? <mark className="rounded bg-gold-light px-0.5 text-inherit">{w}</mark> : w}
        </span>
      ))}
    </p>
  );
}

/**
 * /expressions/<slug> — one Qur'anic expression: what reading its verses
 * together shows, each verse in full with the expression marked, and what
 * changes between occurrences. The server renders the same text for crawlers.
 */
export default function ExpressionPage({ slug }: { slug: string }) {
  const [data, setData] = useState<ExpressionDetail | null>(null);
  const [error, setError] = useState('');

  useSEO({
    title: data ? `${data.title} — ${data.expression_ar} | Qur'anic Expressions` : "Qur'anic Expressions",
    description: data?.summary ?? "A Qur'anic expression explained from the Qur'an's own verses.",
    path: `/expressions/${slug}`,
  });

  useEffect(() => {
    let cancelled = false;
    fetchExpression(slug)
      .then((d) => !cancelled && setData(d))
      .catch((e: unknown) => !cancelled && setError(e instanceof Error ? e.message : 'Failed to load'));
    return () => {
      cancelled = true;
    };
  }, [slug]);

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center text-red-700">{error}</div>
        <p className="mt-4 text-center text-sm">
          <a href="/expressions" className="text-gold-hover hover:underline">All expressions</a>
        </p>
      </div>
    );
  }
  if (!data) {
    return (
      <div className="flex justify-center py-16">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
      </div>
    );
  }

  const roles = new Map(data.occurrences.map((o) => [o.ref, o.role]));

  return (
    <article className="mx-auto max-w-3xl px-4 py-10">
      <nav className="mb-6 text-sm text-stone-500" aria-label="Breadcrumb">
        <a href="/expressions" className="hover:text-stone-800">Expressions</a>
        <span className="mx-1.5 text-stone-300">/</span>
        <span>{data.kind_label}</span>
      </nav>

      <header className="mb-8">
        <p className="mb-1 text-sm font-semibold uppercase tracking-wide text-gold">{data.kind_label}</p>
        <h1 className="text-2xl font-semibold text-stone-800 sm:text-3xl">{data.title}</h1>
        <p dir="rtl" lang="ar" className="mt-4 font-arabic text-3xl leading-[2] text-stone-800 sm:text-4xl">
          {data.expression_ar}
        </p>
        <p className="mt-1 text-stone-500">
          {data.transliteration && <i>{data.transliteration}</i>}
          {data.transliteration && data.gloss && ' · '}
          {data.gloss}
        </p>
      </header>

      {data.summary && <p className="mb-6 text-lg leading-relaxed text-stone-700">{data.summary}</p>}
      {data.explanation && (
        <FormattedText text={data.explanation} className="mb-10 leading-relaxed text-stone-700" />
      )}

      <section className="mb-10" aria-labelledby="where">
        <h2 id="where" className="mb-3 text-sm font-semibold uppercase tracking-wide text-stone-500">
          Where it occurs <span className="font-normal normal-case tracking-normal text-stone-400">({data.verses.length})</span>
        </h2>
        <ol className="space-y-3">
          {data.verses.map((v) => (
            <li key={v.ref} className="rounded-xl border border-stone-200 bg-white p-4 sm:p-5">
              <a href={`/verse/${v.ref}`} className="text-sm font-medium text-gold-hover hover:underline">
                {v.surah_name} {v.ref}
              </a>
              <MarkedVerse text={v.arabic} expression={data.expression_ar} />
              <p className="mt-1 text-sm italic leading-relaxed text-stone-500">{v.translation}</p>
              {roles.get(v.ref) && (
                <p className="mt-2 border-t border-stone-100 pt-2 text-sm leading-relaxed text-stone-700">
                  {roles.get(v.ref)}
                </p>
              )}
            </li>
          ))}
        </ol>
      </section>

      {data.variation && (
        <section className="mb-10" aria-labelledby="changes">
          <h2 id="changes" className="mb-2 text-sm font-semibold uppercase tracking-wide text-stone-500">What changes</h2>
          <FormattedText text={data.variation} className="leading-relaxed text-stone-700" />
        </section>
      )}

      {data.for_researchers.length > 0 && (
        <section className="mb-10" aria-labelledby="research">
          <h2 id="research" className="mb-2 text-sm font-semibold uppercase tracking-wide text-stone-500">For researchers</h2>
          <ul className="list-disc space-y-2 pl-5 text-stone-700">
            {data.for_researchers.map((r, i) => (
              <li key={i}>
                <FormattedText text={r} className="leading-relaxed" />
              </li>
            ))}
          </ul>
        </section>
      )}

      {data.see_also.length > 0 && (
        <section className="mb-10" aria-labelledby="see-also">
          <h2 id="see-also" className="mb-3 text-sm font-semibold uppercase tracking-wide text-stone-500">Sharing these verses</h2>
          <ul className="grid gap-2 sm:grid-cols-2">
            {data.see_also.map((s) => (
              <li key={s.slug}>
                <a href={`/expressions/${s.slug}`} className="block rounded-lg border border-stone-200 bg-white p-3 hover:border-stone-300">
                  <span dir="rtl" lang="ar" className="block font-arabic text-lg text-stone-800">{s.expression_ar}</span>
                  <span className="text-sm text-stone-600">{s.title}</span>
                </a>
              </li>
            ))}
          </ul>
        </section>
      )}

    </article>
  );
}
