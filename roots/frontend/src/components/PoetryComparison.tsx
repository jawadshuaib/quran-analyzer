import { useEffect, useState } from 'react';
import type { RootPoetryComparison } from '../types';
import { fetchRootPoetry } from '../api/quran';
import FormattedText from './FormattedText';

/** The "In Pre-Islamic Poetry" section on a root page. Lazy-loads the approved
 *  comparison and auto-hides (renders nothing) when a root has none — same
 *  pattern as the AI-translation / exegesis panels. A warm sand palette sets
 *  it apart from the violet AI-meaning panel and the indigo cognates: this one
 *  looks *backward in time* rather than outward across languages.
 *
 *  Poetic lines are NOT listed as standalone blocks (a layperson could mistake
 *  them for Qurʾān); they are linked inline within the prose instead, and lead
 *  to the full poem. No authentication-tier labels are shown to readers. */

export default function PoetryComparison({ rootBw }: { rootBw: string }) {
  const [data, setData] = useState<RootPoetryComparison | null>(null);

  useEffect(() => {
    let cancelled = false;
    setData(null);
    fetchRootPoetry(rootBw)
      .then((d) => { if (!cancelled) setData(d); })
      .catch(() => { if (!cancelled) setData(null); });
    return () => { cancelled = true; };
  }, [rootBw]);

  if (!data) return null;

  const verdict = data.continuity ? 'continuity' : data.shift_type;
  const colloc = data.collocations;

  return (
    <section className="mb-8">
      <h2 className="text-sm font-semibold text-stone-500 uppercase tracking-wide mb-3">
        In Pre-Islamic Poetry
      </h2>
      <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-4 sm:p-5">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <span
            className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
              data.continuity
                ? 'bg-emerald-100 text-emerald-700'
                : 'bg-amber-200/70 text-amber-900'
            }`}
          >
            {verdict}
          </span>
        </div>

        {/* the comparison prose — poetic lines are linked inline (the [[q:…]]
            markers resolve against quoted_lines into hover-tooltip links) */}
        <FormattedText
          text={data.comparison_markdown}
          quotes={data.quoted_lines}
          className="text-sm text-stone-700 leading-relaxed"
        />

        {/* collocational fingerprint — the company the word keeps */}
        {colloc && ((colloc.quran?.length ?? 0) > 0 || (colloc.poetry?.length ?? 0) > 0) && (
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            {colloc.quran?.length ? (
              <div>
                <div className="font-semibold text-stone-500 mb-1">Its company in the Qurʾān</div>
                <div className="flex flex-wrap gap-1">
                  {colloc.quran.map((t) => (
                    <span key={t} className="px-1.5 py-0.5 rounded bg-violet-100/70 text-violet-700">{t}</span>
                  ))}
                </div>
              </div>
            ) : null}
            {colloc.poetry?.length ? (
              <div>
                <div className="font-semibold text-stone-500 mb-1">…and in the poetry</div>
                <div className="flex flex-wrap gap-1">
                  {colloc.poetry.map((t) => (
                    <span key={t} className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-700">{t}</span>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        )}

        <p className="mt-3 text-[11px] text-stone-400 leading-snug">
          Drawn from the most reliably transmitted pre-Islamic poetry (the Muʿallaqāt and major
          dīwāns). Hover a highlighted line for the poet and translation; tap it to read the
          full poem.
        </p>
      </div>
    </section>
  );
}
