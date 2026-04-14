import { useState, useEffect, useMemo } from 'react';
import type { VerseData } from '../../types';
import { fetchVerse } from '../../api/quran';

// Pool of well-known verses to pick from
const VERSE_POOL: [number, number][] = [
  [1, 1], [2, 255], [24, 35], [36, 1], [55, 13],
  [59, 22], [67, 1], [96, 1], [112, 1], [13, 28],
  [94, 5], [49, 13], [21, 107], [3, 139], [56, 77],
  [39, 53], [31, 18], [17, 1], [18, 10], [2, 152],
];

/** Pick a deterministic "daily" verse based on day-of-year */
function pickDailyVerse(): [number, number] {
  const now = new Date();
  const start = new Date(now.getFullYear(), 0, 0);
  const dayOfYear = Math.floor((now.getTime() - start.getTime()) / 86_400_000);
  return VERSE_POOL[dayOfYear % VERSE_POOL.length];
}

interface Props {
  onNavigate: (surah: number, ayah: number) => void;
}

export default function VerseOfTheDay({ onNavigate }: Props) {
  const [surah, ayah] = useMemo(pickDailyVerse, []);
  const [data, setData] = useState<VerseData | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchVerse(surah, ayah)
      .then((v) => { if (!cancelled) setData(v); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [surah, ayah]);

  if (!data) return null;

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
        className="font-serif text-[28px] leading-[1.9] text-ink text-right mb-3.5 tracking-wide font-arabic"
      >
        {data.text_uthmani}
      </p>

      {/* Translation */}
      <p className="font-serif text-base leading-relaxed text-ink-secondary italic mb-4">
        {data.translation}
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
                  &middot; {r.cognate.concept}
                </span>
              )}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
