import { useState, useEffect } from 'react';
import type { VerseData } from '../../types';
import { fetchVerse, getDailyVerse } from '../../api/quran';
import { wrapArabicRuns } from '../../utils/arabic-runs';

// Fallback used only when /api/verse-of-the-day is unreachable
// (e.g. backend is down on a NotFound or BadGateway page). The
// pool itself lives in the backend and is admin-curated via
// /admin/verse-of-the-day; on a healthy site the API response
// always wins.
const FALLBACK: [number, number] = [2, 255];

interface Props {
  onNavigate: (surah: number, ayah: number) => void;
}

export default function VerseOfTheDay({ onNavigate }: Props) {
  const [pick, setPick] = useState<[number, number] | null>(null);
  const [data, setData] = useState<VerseData | null>(null);

  // Two-step fetch: first ask the backend which verse is "today's"
  // (cheap, just a chapter:verse pair), then fetch the full verse
  // payload via the existing endpoint. Both fail closed — if the
  // pool API errors we use a known-good fallback ref, and if the
  // verse fetch errors we render nothing.
  useEffect(() => {
    let cancelled = false;
    getDailyVerse()
      .then((p) => {
        if (cancelled) return;
        setPick([p.chapter, p.verse]);
      })
      .catch(() => {
        if (cancelled) return;
        setPick(FALLBACK);
      });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!pick) return;
    let cancelled = false;
    fetchVerse(pick[0], pick[1])
      .then((v) => { if (!cancelled) setData(v); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [pick]);

  if (!pick || !data) return null;
  const [surah, ayah] = pick;

  // Get up to 4 meaningful roots (skip those without root_arabic)
  const roots = data.roots_summary
    .filter((r) => r.root_arabic)
    .slice(0, 4);

  return (
    <div
      className="bg-white border border-card-border rounded-xl p-6 mb-8 cursor-pointer hover:border-gold/30 transition-colors"
      onClick={() => onNavigate(surah, ayah)}
    >
      {/* Header */}
      <div className="flex items-baseline justify-between mb-3.5">
        <span className="text-[11px] text-ink-muted tracking-wider uppercase">
          verse of the day &middot; {surah}:{ayah}
        </span>
        <span className="text-xs text-ink-secondary">
          {data.surah_name} &rarr;
        </span>
      </div>

      {/* Arabic text */}
      <p
        dir="rtl"
        lang="ar"
        className="font-arabic text-[28px] leading-[1.9] text-ink text-right mb-3.5 tracking-wide"
      >
        {data.text_uthmani}
      </p>

      {/* Translation */}
      <p className="font-serif text-base leading-relaxed text-ink-secondary italic mb-4">
        {wrapArabicRuns(data.translation)}
      </p>

      {/* Root pills — matching verse page style */}
      {roots.length > 0 && (
        <div className="border-t border-card-border pt-3 flex flex-wrap gap-2">
          {roots.map((r) => (
            <span
              key={r.root_buckwalter}
              className="inline-flex items-center gap-1.5 rounded-full px-3 py-1
                         text-sm font-medium border bg-emerald-50 text-emerald-700 border-emerald-200"
            >
              <span dir="rtl" lang="ar" className="font-arabic text-base">
                {r.root_arabic}
              </span>
              <span className="text-xs text-emerald-500">
                ({r.root_buckwalter})
              </span>
              {r.cognate && (
                <span className="hidden sm:inline text-xs italic text-emerald-500">
                  &middot; {wrapArabicRuns(r.cognate.concept)}
                </span>
              )}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
