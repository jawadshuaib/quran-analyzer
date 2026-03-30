import { useState, useEffect, useMemo } from 'react';
import type { LearningUnit } from '../types/learning';
import { fetchCurriculum } from '../api/learning';

/**
 * A visually compelling section promoting the /learning feature.
 * Shows a collage of mnemonic images overlaid with a floating word cloud
 * of Arabic root words.
 */
export default function LearningPromo() {
  const [units, setUnits] = useState<LearningUnit[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchCurriculum()
      .then((data) => {
        if (!cancelled) setUnits(data.units);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoaded(true);
      });
    return () => { cancelled = true; };
  }, []);

  // Collect roots with mnemonic images + all roots for word cloud
  const allRoots = useMemo(
    () => units.flatMap((u) => u.roots),
    [units],
  );

  const mnemonicRoots = useMemo(
    () => allRoots.filter((r) => r.mnemonic_image_url),
    [allRoots],
  );

  // Shuffle images for variety on each load
  const shuffledImages = useMemo(
    () => [...mnemonicRoots].sort(() => Math.random() - 0.5).slice(0, 12),
    [mnemonicRoots],
  );

  // Word cloud items — shuffled roots for the overlay grid
  const wordCloudItems = useMemo(() => {
    const shuffled = [...allRoots].sort(() => Math.random() - 0.5);
    return shuffled.slice(0, 20);
  }, [allRoots]);

  if (!loaded || allRoots.length === 0) return null;

  return (
    <div className="mx-auto max-w-2xl rounded-xl border border-stone-200 bg-white shadow-sm overflow-hidden text-left">
      {/* Image collage + word cloud overlay */}
      <div className="relative">
        {/* Image grid background */}
        {shuffledImages.length > 0 ? (
          <div className="grid grid-cols-4 sm:grid-cols-6">
            {shuffledImages.map((root) => (
              <div key={root.root_buckwalter} className="aspect-square overflow-hidden">
                <img
                  src={root.mnemonic_image_url!}
                  alt=""
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
              </div>
            ))}
          </div>
        ) : (
          <div className="h-40 bg-gradient-to-br from-emerald-50 to-teal-50" />
        )}

        {/* Gradient overlay with root word grid — clickable */}
        <a
          href="/learning"
          className="absolute inset-0 bg-gradient-to-t from-emerald-900/90 via-emerald-900/60 to-emerald-900/40 flex items-center justify-center p-4 sm:p-6 cursor-pointer hover:from-emerald-900/85 hover:via-emerald-900/50 hover:to-emerald-900/30 transition-all"
        >
          <div className="grid grid-cols-5 sm:grid-cols-5 gap-x-4 gap-y-3 max-w-md" dir="rtl">
            {wordCloudItems.map((root, i) => (
              <div key={i} className="text-center">
                <span
                  className="font-arabic text-xl sm:text-2xl font-semibold select-none"
                  style={{ color: `rgba(255,255,255,${i < 5 ? 0.95 : i < 12 ? 0.7 : 0.5})` }}
                >
                  {root.root_arabic}
                </span>
                <div
                  className="mx-auto mt-1 rounded-full"
                  style={{
                    width: '60%',
                    height: '1px',
                    background: `rgba(255,255,255,${i < 5 ? 0.35 : i < 12 ? 0.2 : 0.12})`,
                  }}
                />
              </div>
            ))}
          </div>
        </a>
      </div>

      {/* Text content */}
      <div className="p-5">
        <p className="text-xs font-semibold tracking-wide text-emerald-700 uppercase">
          Interactive Learning
        </p>
        <a href="/learning" className="group block mt-1">
          <h2 className="text-lg font-semibold text-stone-800 group-hover:text-emerald-700 transition-colors">
            Learn Quranic Arabic Through Root Words &rarr;
          </h2>
        </a>
        <p className="text-sm text-stone-500 mt-1.5 leading-relaxed">
          Master {allRoots.length} essential roots through visual mnemonics,
          spaced repetition, and verse-by-verse discovery.
          Each root unlocks a family of words used across the Quran.
        </p>
        <p className="text-xs text-stone-400 mt-2">
          {units.length} units &middot; {allRoots.length} roots &middot; Free
        </p>
      </div>
    </div>
  );
}
