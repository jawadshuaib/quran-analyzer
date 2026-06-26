import { useEffect, useState } from 'react';
import type { MeterData, MeterShowcaseLine } from '../types';
import { fetchMeter } from '../api/quran';
import FormattedText from './FormattedText';
import MeterRhythmPlayer from './MeterRhythmPlayer';

/** /meter/<key> — a beginner-friendly teaching page for one Arabic meter
 *  (baḥr): what it is, how it sounds, its history and character, and real
 *  pre-Islamic verses in it with read-aloud transliteration. */
export default function MeterPage({ meterKey }: { meterKey: string }) {
  const [data, setData] = useState<MeterData | null>(null);
  const [state, setState] = useState<'loading' | 'error' | 'empty' | 'ok'>('loading');

  useEffect(() => {
    let cancelled = false;
    setState('loading'); setData(null);
    fetchMeter(meterKey)
      .then((d) => {
        if (cancelled) return;
        if (!d) { setState('empty'); return; }
        setData(d);
        setState('ok');
        document.title = `${d.name_en} — an Arabic poetic metre | al-nuqta`;
      })
      .catch(() => { if (!cancelled) setState('error'); });
    return () => { cancelled = true; };
  }, [meterKey]);

  if (state === 'loading') {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10 flex justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-amber-200 border-t-amber-600" />
      </div>
    );
  }
  if (state === 'error' || (state === 'empty' && !data)) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <a href="/meters" className="text-xs text-amber-700 hover:underline">← All metres</a>
        <div className="mt-3 rounded-lg border border-stone-200 bg-stone-50 p-5 text-center text-stone-500">
          {state === 'error' ? 'Could not load this metre.' : 'No write-up for this metre yet.'}
        </div>
      </div>
    );
  }
  if (!data) return null;

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10">
      <a href="/meters" className="text-xs text-amber-700 hover:text-amber-900 hover:underline">
        ← All metres
      </a>

      <header className="mt-3 mb-6">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <h1 className="text-3xl font-semibold text-stone-800">{data.name_en}</h1>
          <span dir="rtl" lang="ar" className="font-arabic text-2xl text-stone-500">{data.meter_ar}</span>
        </div>
        <p className="mt-1 text-sm text-stone-500">
          {data.name_meaning && <span className="italic">{data.name_meaning}</span>}
          {data.name_meaning && ' · '}
          {data.poem_count} poem{data.poem_count === 1 ? '' : 's'} in this metre in our corpus
        </p>
      </header>

      {/* Hear it */}
      <section className="mb-6">
        <MeterRhythmPlayer pattern={data.syllable_pattern} mnemonic={data.mnemonic_en} />
      </section>

      {/* The pattern (tafāʿīl) */}
      {(data.tafil_ar || data.tafil_latin) && (
        <section className="mb-6 rounded-xl border border-stone-200 bg-white p-4">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-stone-400">The pattern</h2>
          {data.tafil_ar && (
            <p dir="rtl" lang="ar" className="font-arabic text-2xl leading-loose text-stone-800 mt-1">
              {data.tafil_ar}
            </p>
          )}
          {data.tafil_latin && (
            <p className="text-sm italic text-stone-500">{data.tafil_latin}</p>
          )}
          <p className="mt-1 text-[11px] text-stone-400">
            The repeating &ldquo;feet&rdquo; the ear keeps time to — one bar of the rhythm above.
          </p>
        </section>
      )}

      {/* The write-up */}
      {data.article_markdown && (
        <section className="mb-8">
          <FormattedText
            text={data.article_markdown}
            className="text-[15px] leading-relaxed text-stone-700"
          />
        </section>
      )}

      {/* See it in action */}
      {data.showcase.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 text-lg font-semibold text-stone-800">See it in action</h2>
          <ul className="space-y-4">
            {data.showcase.map((s) => <ShowcaseVerse key={s.line_id} s={s} />)}
          </ul>
        </section>
      )}

      {/* Variants */}
      {data.variants.length > 0 && (
        <section className="mb-8 rounded-xl border border-stone-200 bg-stone-50/60 p-4">
          <h2 className="text-sm font-semibold text-stone-700">Shortened forms in this corpus</h2>
          <p className="mt-1 text-[13px] leading-relaxed text-stone-500">
            Poets often clip a metre — dropping a foot (<span dir="rtl" lang="ar" className="font-arabic">مجزوء</span>,
            &ldquo;halved&rdquo;) or trimming an ending. These poems still beat to {data.name_en}; they just run a
            little shorter:
          </p>
          <ul className="mt-2 flex flex-wrap gap-2">
            {data.variants.map((v) => (
              <li key={v.meter_ar} className="rounded-full bg-white border border-stone-200 px-2.5 py-1 text-xs text-stone-600">
                <span dir="rtl" lang="ar" className="font-arabic">{v.meter_ar}</span>
                <span className="text-stone-400"> · {v.poem_count}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Poems in this metre */}
      {data.poems.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold text-stone-800">Poems in this metre</h2>
          <ul className="grid gap-2 sm:grid-cols-2">
            {data.poems.map((p) => (
              <li key={p.id}>
                <a
                  href={`/poem/${p.id}`}
                  className="block rounded-lg border border-stone-200 bg-white p-3 transition-colors hover:border-amber-300 hover:bg-amber-50/40"
                >
                  <div className="flex items-baseline justify-between gap-2">
                    <span dir="rtl" lang="ar" className="font-arabic text-base text-stone-800 truncate">
                      {p.title || '—'}
                    </span>
                    <span className="shrink-0 text-[11px] text-stone-400">{p.line_count} lines</span>
                  </div>
                  {(p.poet_latin || p.poet) && (
                    <p className="mt-0.5 truncate text-xs text-stone-500">{p.poet_latin || p.poet}</p>
                  )}
                </a>
              </li>
            ))}
          </ul>
        </section>
      )}

      <p className="mt-8 text-[11px] text-stone-400 leading-snug">
        These are pre-Islamic (Jahilī) poems — <span className="font-medium">not</span> part of the
        Qurʾān — shown so an English reader can hear the music the Qurʾān&rsquo;s first audience knew.
      </p>
    </div>
  );
}

/** Convert a stored scansion string ("u - - …") to display marks ("∪ – – …"). */
function scansionMarks(raw?: string | null): string {
  if (!raw) return '';
  return raw
    .split(/\s+/)
    .map((t) => (/[u∪v.]/i.test(t) ? '∪' : /[-–—ox]/i.test(t) ? '–' : t))
    .join(' ');
}

function ShowcaseVerse({ s }: { s: MeterShowcaseLine }) {
  const marks = scansionMarks(s.scansion);
  return (
    <li className="rounded-xl border border-stone-200 bg-white p-4">
      {marks && (
        <p className="font-mono text-xs tracking-widest text-amber-600/90">{marks}</p>
      )}
      <p dir="rtl" lang="ar" className="font-arabic text-xl leading-[2.2] text-stone-800 mt-0.5">
        {s.arabic}
      </p>
      {s.transliteration && (
        <p className="mt-1 text-sm italic text-stone-600">{s.transliteration}</p>
      )}
      {s.translation && (
        <p className="mt-1 text-sm text-stone-500">{s.translation}</p>
      )}
      <div className="mt-1.5 flex items-center gap-2 text-[11px] text-stone-400">
        {(s.poet_latin || s.poet) && <span>{s.poet_latin || s.poet}</span>}
        <a href={`/poem/${s.poem_id}#line-${s.line_no}`} className="text-amber-700 hover:underline">
          read the poem →
        </a>
      </div>
    </li>
  );
}
