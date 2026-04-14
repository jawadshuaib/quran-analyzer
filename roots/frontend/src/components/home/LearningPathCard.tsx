import { useState, useEffect } from 'react';
import type { LearningUnit } from '../../types/learning';
import { fetchCurriculum } from '../../api/learning';

export default function LearningPathCard() {
  const [units, setUnits] = useState<LearningUnit[]>([]);
  const [totalRoots, setTotalRoots] = useState(0);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchCurriculum()
      .then((data) => {
        if (cancelled) return;
        setUnits(data.units);
        setTotalRoots(data.units.reduce((sum, u) => sum + u.roots.length, 0));
      })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoaded(true); });
    return () => { cancelled = true; };
  }, []);

  if (!loaded || units.length === 0) return null;

  // Progress bars: filled (gold), partial (gold-light), empty (cream-dark)
  // This is decorative — showing unit count as bars
  const totalBars = 9;
  const filledBars = Math.min(Math.round((units.length / 18) * totalBars), totalBars);

  return (
    <a
      href="/learning"
      className="block bg-white border border-card-border rounded-xl p-6 mb-4 hover:border-gold/30 transition-colors"
    >
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 sm:gap-7">
        <div className="flex-1 min-w-0">
          <p className="text-[11px] text-ink-muted tracking-wider uppercase mb-1.5">
            learning path
          </p>
          <p className="font-serif text-base sm:text-lg font-medium text-ink mb-2">
            Learn Quranic Arabic through its roots
          </p>
          <p className="text-xs sm:text-[13.5px] text-ink-secondary leading-relaxed max-w-[56ch]">
            Most words in Classical Arabic are derived from root letters. In the
            Quran, these roots form a thematic backbone that, once understood, can
            make the entire revelation more accessible. Use this tool to learn them
            quickly.
          </p>
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0 pt-1">
          {/* Progress bars */}
          <div className="flex gap-[3px]">
            {Array.from({ length: totalBars }).map((_, i) => (
              <span
                key={i}
                className="w-2.5 h-6 rounded-sm"
                style={{
                  background:
                    i < filledBars
                      ? 'var(--color-gold)'
                      : i < filledBars + 2
                        ? 'var(--color-gold-light)'
                        : 'var(--color-cream-dark)',
                }}
              />
            ))}
          </div>
          <span className="text-[11px] text-ink-muted">
            {totalRoots} roots &middot; {units.length} units
          </span>
        </div>
      </div>
    </a>
  );
}
