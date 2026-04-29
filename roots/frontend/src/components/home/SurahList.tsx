import { useEffect, useState } from 'react';
import { fetchSurahs } from '../../api/quran';
import type { SurahInfo } from '../../types';

/**
 * Homepage Surah list — entry point for reader mode.
 *
 * Renders all 114 surahs as a responsive grid. Clicking a tile takes
 * the user to /read/<surah>. Each tile shows: number, Arabic name,
 * English name, short meaning, verse count.
 *
 * The grid is intentionally compact — ~3 cols on desktop, 2 on mobile —
 * so the full list fits in roughly two screens of scrolling.
 */
export default function SurahList() {
  const [surahs, setSurahs] = useState<SurahInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchSurahs()
      .then((s) => { setSurahs(s); setLoading(false); })
      .catch((e) => { setError(e instanceof Error ? e.message : 'Failed to load'); setLoading(false); });
  }, []);

  if (loading) {
    return (
      <section className="mt-12">
        <div className="flex items-center gap-3 mb-5">
          <h2 className="font-serif text-xl font-medium tracking-tight text-ink">
            Read the Qur&apos;an
          </h2>
        </div>
        <div className="flex justify-center py-8">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-card-border border-t-gold" />
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="mt-12">
        <h2 className="font-serif text-xl font-medium tracking-tight text-ink mb-3">
          Read the Qur&apos;an
        </h2>
        <p className="text-sm text-red-700">{error}</p>
      </section>
    );
  }

  return (
    <section className="mt-12">
      <div className="mb-5">
        <h2 className="font-serif text-xl font-medium tracking-tight text-ink">
          Read the Qur&apos;an
        </h2>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
        {surahs.map((s) => (
          <a
            key={s.number}
            href={`/read/${s.number}`}
            className="group block bg-white border border-card-border rounded-lg px-3 py-3 hover:border-gold/40 hover:bg-gold/5 transition-colors"
          >
            <div className="flex items-baseline gap-2 mb-1.5">
              <span className="font-mono text-[11px] text-ink-muted min-w-[1.5rem]">
                {s.number}
              </span>
              <span className="font-serif text-base text-ink truncate" lang="ar">
                {s.name_arabic || s.name}
              </span>
            </div>
            <div className="flex items-baseline justify-between gap-2 pl-[2rem]">
              <span className="text-[11px] text-ink-secondary group-hover:text-gold-hover truncate">
                {s.name}
                {s.meaning && <span className="text-ink-muted"> · {s.meaning}</span>}
              </span>
              <span className="text-[10px] text-ink-muted flex-shrink-0">
                {s.verse_count}
              </span>
            </div>
          </a>
        ))}
      </div>
    </section>
  );
}
