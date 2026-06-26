import { useEffect, useState } from 'react';
import type { PoemData } from '../types';
import { fetchPoem } from '../api/quran';
import { meterKeyForArabic } from '../utils/meters';
import MeterBeatChip from './MeterBeatChip';

/** /poem/<id> — a full pre-Islamic poem, Arabic + English line by line, with
 *  the lines our comparisons quote highlighted. Translations fill in as the
 *  translation loop runs; untranslated lines simply show the Arabic. */
export default function PoemPage({ poemId }: { poemId: number }) {
  const [poem, setPoem] = useState<PoemData | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setPoem(null); setError('');
    fetchPoem(poemId)
      .then((p) => { if (!cancelled) { setPoem(p); document.title = `${p.poet} — a pre-Islamic poem | al-nuqta`; } })
      .catch(() => { if (!cancelled) setError('Poem not found'); });
    return () => { cancelled = true; };
  }, [poemId]);

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center text-red-700">{error}</div>
      </div>
    );
  }
  if (!poem) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10 flex justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-amber-200 border-t-amber-600" />
      </div>
    );
  }

  const partial = poem.translated_count < poem.line_count;

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10">
      <a href="/poems" className="text-xs text-amber-700 hover:text-amber-900 hover:underline">
        ← All pre-Islamic poems
      </a>

      <header className="mt-3 mb-6">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <h1 dir="rtl" lang="ar" className="font-arabic text-3xl text-stone-800">{poem.poet}</h1>
          {poem.poet_latin && <span className="text-stone-400">{poem.poet_latin}</span>}
        </div>
        {poem.title && (
          <p dir="rtl" lang="ar" className="font-arabic text-lg text-stone-500 mt-1">{poem.title}</p>
        )}
        {poem.title_en && (
          <p className="text-sm text-stone-400 italic mt-0.5">{poem.title_en}</p>
        )}
        <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs">
          {poem.meter && (() => {
            const mk = poem.meter_key || meterKeyForArabic(poem.meter);
            return mk ? (
              <MeterBeatChip label={poem.meter} meterKey={mk} beat={poem.meter_beat} />
            ) : (
              <span className="px-2 py-0.5 rounded-full bg-stone-100 text-stone-500">metre: {poem.meter}</span>
            );
          })()}
          <span className="px-2 py-0.5 rounded-full bg-stone-100 text-stone-500">{poem.line_count} lines</span>
          {partial && (
            <span className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">
              {poem.translated_count} of {poem.line_count} lines translated
            </span>
          )}
        </div>
        <p className="mt-2 text-[11px] text-stone-400 leading-snug">
          A pre-Islamic (Jahilī) poem — <span className="font-medium">not</span> part of the
          Qurʾān. Highlighted lines are the ones quoted in our root and verse notes.
        </p>
      </header>

      <ol className="space-y-1">
        {poem.lines.map((ln) => (
          <li
            id={`line-${ln.line_no}`}
            key={ln.line_no}
            className={`rounded-lg px-3 py-2.5 scroll-mt-24 ${
              ln.quoted ? 'bg-amber-50 border border-amber-200' : 'border border-transparent'
            }`}
          >
            <div className="flex gap-3">
              <span className="text-[11px] text-stone-300 pt-1.5 w-6 shrink-0 text-right tabular-nums">
                {ln.line_no}
              </span>
              <div className="min-w-0 flex-1">
                <p dir="rtl" lang="ar" className="font-arabic text-xl leading-[2.4] text-stone-800">
                  {ln.arabic}
                </p>
                {ln.english ? (
                  <p className="text-sm text-stone-500 italic mt-0.5">{ln.english}</p>
                ) : (
                  <p className="text-xs text-stone-300 mt-0.5">— translation pending —</p>
                )}
              </div>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
