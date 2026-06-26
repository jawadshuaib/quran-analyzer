import { useEffect, useMemo, useState } from 'react';
import type { PoemSummary } from '../types';
import { fetchPoems } from '../api/quran';
import { meterKeyForArabic } from '../utils/meters';

/** /poems — the browsable library of every pre-Islamic poem our comparisons
 *  draw on, grouped by poet. */
export default function PoemsIndex() {
  const [poems, setPoems] = useState<PoemSummary[] | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    document.title = 'Pre-Islamic Poetry — the sources | al-nuqta';
    fetchPoems().then(setPoems).catch(() => setError('Could not load the poems'));
  }, []);

  const byPoet = useMemo(() => {
    const groups = new Map<string, PoemSummary[]>();
    for (const p of poems ?? []) {
      const key = p.poet || 'Unknown';
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key)!.push(p);
    }
    return Array.from(groups.entries());
  }, [poems]);

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
        <h1 className="text-2xl font-semibold text-stone-800">Pre-Islamic Poetry</h1>
        <p className="mt-2 text-sm text-stone-500 leading-relaxed">
          The poems behind the &ldquo;In Pre-Islamic Poetry&rdquo; notes — the most reliably
          transmitted verse of the Jahilī age (the Muʿallaqāt and the major dīwāns). These are
          the words of poets, set beside the Qurʾān only to show how its language reshaped a
          world it spoke into. Each poem is given in full, with translation.
        </p>
      </header>

      {!poems ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-amber-200 border-t-amber-600" />
        </div>
      ) : (
        <div className="space-y-7">
          {byPoet.map(([poet, list]) => (
            <section key={poet}>
              <h2 className="mb-2 flex flex-wrap items-baseline gap-x-2.5">
                <span dir="rtl" lang="ar" className="font-arabic text-xl text-stone-700">{poet}</span>
                {list[0]?.poet_latin && (
                  <span className="text-sm text-stone-400">{list[0].poet_latin}</span>
                )}
              </h2>
              <ul className="space-y-2">
                {list.map((p) => (
                  <li key={p.id}>
                    <a
                      href={`/poem/${p.id}`}
                      className="block rounded-lg border border-stone-200 bg-white hover:border-amber-300 hover:bg-amber-50/40 transition-colors p-3"
                    >
                      <div className="flex items-baseline justify-between gap-3">
                        <span dir="rtl" lang="ar" className="font-arabic text-lg text-stone-800 truncate">
                          {p.title || '—'}
                        </span>
                        <span className="shrink-0 text-[11px] text-stone-400">{p.line_count} lines</span>
                      </div>
                      {p.title_en && (
                        <p className="mt-0.5 text-sm text-stone-500 italic truncate">{p.title_en}</p>
                      )}
                      <div className="mt-1 flex flex-wrap gap-1.5 text-[11px]">
                        {p.meter && (() => {
                          const mk = meterKeyForArabic(p.meter);
                          if (!mk) return <span className="px-1.5 py-0.5 rounded bg-stone-100 text-stone-500">{p.meter}</span>;
                          const go = () => { window.location.href = `/meter/${mk}`; };
                          return (
                            <span
                              role="link"
                              tabIndex={0}
                              onClick={(e) => { e.preventDefault(); e.stopPropagation(); go(); }}
                              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); e.stopPropagation(); go(); } }}
                              className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 hover:bg-amber-200 cursor-pointer"
                            >
                              {p.meter}
                            </span>
                          );
                        })()}
                        {p.translated_count < p.line_count && (
                          <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-700">
                            {p.translated_count}/{p.line_count} translated
                          </span>
                        )}
                      </div>
                    </a>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
