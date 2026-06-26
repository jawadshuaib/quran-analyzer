import { useEffect, useState } from 'react';
import type { MeterSummary } from '../types';
import { fetchMeters } from '../api/quran';

/** /meters — the metres (buḥūr) of the corpus, most-used first. Each is a
 *  doorway to a beginner-friendly page that lets you hear the rhythm. */
export default function MetersIndex() {
  const [meters, setMeters] = useState<MeterSummary[] | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    document.title = 'The metres of Arabic poetry | al-nuqta';
    fetchMeters().then(setMeters).catch(() => setError('Could not load the metres'));
  }, []);

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center text-red-700">{error}</div>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold text-stone-800">The Metres of Arabic Poetry</h1>
        <p className="mt-2 text-sm text-stone-500 leading-relaxed">
          Every classical Arabic poem keeps time to a <em>baḥr</em> — a metre, a fixed pattern of
          long and short syllables the ear locks onto. These are the metres the pre-Islamic poets
          used, the same music the Qurʾān&rsquo;s first listeners carried in their heads. Pick one to
          hear its beat and read verses written in it.
        </p>
      </header>

      {!meters ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-amber-200 border-t-amber-600" />
        </div>
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2">
          {meters.map((m) => {
            const inner = (
              <>
                <div className="flex items-baseline justify-between gap-2">
                  <span className="text-lg font-semibold text-stone-800">{m.name_en}</span>
                  <span dir="rtl" lang="ar" className="font-arabic text-xl text-stone-500">{m.meter_ar}</span>
                </div>
                <p className="mt-0.5 text-xs text-stone-500">
                  {m.name_meaning && <span className="italic">“{m.name_meaning}”</span>}
                  <span className="text-stone-400"> · {m.poem_count} poems</span>
                </p>
                {!m.has_article && (
                  <p className="mt-1 text-[11px] text-stone-400">write-up coming soon</p>
                )}
              </>
            );
            return (
              <li key={m.key}>
                {m.has_article ? (
                  <a
                    href={`/meter/${m.key}`}
                    className="block rounded-xl border border-stone-200 bg-white p-4 transition-colors hover:border-amber-300 hover:bg-amber-50/40"
                  >
                    {inner}
                  </a>
                ) : (
                  <div className="block rounded-xl border border-stone-200 bg-stone-50/60 p-4 opacity-70">
                    {inner}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
