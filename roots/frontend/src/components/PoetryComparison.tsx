import { useEffect, useState } from 'react';
import type { RootPoetryComparison } from '../types';
import { fetchRootPoetry } from '../api/quran';
import FormattedText from './FormattedText';

/** The "In Pre-Islamic Poetry" section on a root page. Lazy-loads the approved
 *  comparison and auto-hides (renders nothing) when a root has none — same
 *  pattern as the AI-translation / exegesis panels. A warm sand palette sets
 *  it apart from the violet AI-meaning panel and the indigo cognates: this one
 *  looks *backward in time* rather than outward across languages. */

const TIER_LABEL: Record<string, string> = {
  A: 'Muʿallaqāt',
  B: 'major poets',
  C: 'attributed',
  D: 'disputed',
};

function TierBadge({ tier }: { tier?: string }) {
  if (!tier) return null;
  return (
    <span className="text-[10px] font-medium uppercase tracking-wide px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-700">
      Tier {tier}
      {TIER_LABEL[tier] ? ` · ${TIER_LABEL[tier]}` : ''}
    </span>
  );
}

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
        {/* verdict + tier badges */}
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
          {data.auth_tier_max && <TierBadge tier={data.auth_tier_max} />}
        </div>

        {/* the comparison prose */}
        <FormattedText
          text={data.comparison_markdown}
          className="text-sm text-stone-700 leading-relaxed"
        />

        {/* quoted poetic lines */}
        {data.quoted_lines?.length > 0 && (
          <div className="mt-4 space-y-2.5">
            {data.quoted_lines.map((q) => (
              <div
                key={q.line_root_id}
                className="rounded-lg bg-white/70 border border-amber-100 p-2.5"
              >
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  {q.poet && (
                    <span dir="rtl" lang="ar" className="font-arabic text-sm text-stone-700">
                      {q.poet}
                    </span>
                  )}
                  <TierBadge tier={q.auth_tier} />
                </div>
                {q.arabic && (
                  <p dir="rtl" lang="ar" className="font-arabic text-lg leading-loose text-stone-800">
                    {q.arabic}
                  </p>
                )}
                {q.english && (
                  <p className="text-xs text-stone-500 italic mt-0.5">
                    &ldquo;{q.english}&rdquo;
                    {q.translit ? <span className="not-italic text-stone-400"> — {q.translit}</span> : null}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}

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
          Drawn from authenticated pre-Islamic poetry (the Muʿallaqāt and major dīwāns).
          Tier A/B lines are quotable evidence; Tier C is illustration only.
        </p>
      </div>
    </section>
  );
}
