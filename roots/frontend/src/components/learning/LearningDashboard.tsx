import { useState, useEffect } from 'react';
import type { LearningUnit } from '../../types/learning';
import { fetchCurriculum } from '../../api/learning';
import { loadProgress, getUnitMastery } from '../../utils/learning-storage';
import { isDue } from '../../utils/spaced-repetition';
import { loadDismissed } from '../../utils/mnemonic-dismissed';

interface Props {
  onSelectRoot: (rootBw: string) => void;
  onStartReview: () => void;
}

export default function LearningDashboard({ onSelectRoot, onStartReview }: Props) {
  const [units, setUnits] = useState<LearningUnit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const progress = loadProgress();
  const dismissed = loadDismissed();
  const dueCount = progress.reviewQueue.filter((r) => isDue(r) && !dismissed.has(r.rootBw)).length;

  useEffect(() => {
    let cancelled = false;
    fetchCurriculum()
      .then((data) => { if (!cancelled) setUnits(data.units); })
      .catch((e) => { if (!cancelled) setError(e.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center text-red-700 text-base">
        {error}
      </div>
    );
  }

  if (units.length === 0) {
    return (
      <div className="rounded-xl border border-stone-200 bg-white p-10 text-center">
        <p className="text-stone-500 text-base">No curriculum data yet. Run the curriculum generation script first.</p>
      </div>
    );
  }

  // Find next unlearned root (skip dismissed roots — user already knows them)
  const nextRoot = (() => {
    for (const unit of units) {
      for (const root of unit.roots) {
        if (dismissed.has(root.root_buckwalter)) continue;
        const rp = progress.rootProgress[root.root_buckwalter];
        if (!rp || rp.status === 'unseen') return root;
      }
    }
    return null;
  })();

  // Count dismissed roots as "learned" (avoid double-counting roots that were both studied and dismissed)
  const dismissedOnly = Array.from(dismissed).filter((bw) => {
    const rp = progress.rootProgress[bw];
    return !rp || rp.status === 'unseen';
  }).length;
  const totalLearned = progress.stats.totalRootsLearned + dismissedOnly;
  const totalRoots = units.reduce((acc, u) => acc + u.roots.length, 0);
  const progressPct = totalRoots > 0 ? Math.round((totalLearned / totalRoots) * 100) : 0;

  // Collect mnemonic images for collage
  const mnemonicRoots = units
    .flatMap((u) => u.roots)
    .filter((r) => r.mnemonic_image_url);

  function navigateToMnemonicSheet() {
    window.history.pushState(null, '', '/learning/mnemonic-sheet');
    window.dispatchEvent(new PopStateEvent('popstate'));
  }

  return (
    <div className="space-y-8">
      {/* Hero stats card */}
      <div className="rounded-2xl border border-stone-200 bg-white p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="flex items-center gap-8 sm:gap-10">
            <div className="text-center">
              <p className="text-4xl font-bold text-emerald-600">{totalLearned}</p>
              <p className="text-sm text-stone-400 mt-1">Roots Learned</p>
            </div>
            <div className="w-px h-10 bg-stone-200 hidden sm:block" />
            <div className="text-center">
              <p className="text-4xl font-bold text-stone-700">{progress.stats.currentStreak}</p>
              <p className="text-sm text-stone-400 mt-1">Day Streak</p>
            </div>
            <div className="w-px h-10 bg-stone-200 hidden sm:block" />
            <div className="text-center">
              <p className="text-4xl font-bold text-stone-400">{totalRoots}</p>
              <p className="text-sm text-stone-400 mt-1">Total Roots</p>
            </div>
          </div>
          <div className="flex gap-3 w-full sm:w-auto flex-wrap">
            {dueCount > 0 && (
              <button
                onClick={onStartReview}
                className="relative flex-1 sm:flex-none px-6 py-3 rounded-xl bg-amber-500 text-white text-base font-semibold hover:bg-amber-600 transition-colors shadow-sm"
              >
                Review Due
                <span className="absolute -top-2 -right-2 flex h-6 w-6 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white shadow">
                  {dueCount}
                </span>
              </button>
            )}
            {nextRoot && (
              <button
                onClick={() => onSelectRoot(nextRoot.root_buckwalter)}
                className="flex-1 sm:flex-none px-6 py-3 rounded-xl bg-emerald-600 text-white text-base font-semibold hover:bg-emerald-700 transition-colors shadow-sm"
              >
                Continue Learning
              </button>
            )}
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-stone-500">Overall progress</span>
            <span className="text-sm font-medium text-stone-600">{progressPct}%</span>
          </div>
          <div className="rounded-full bg-stone-100 h-3 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-emerald-400 to-emerald-600 rounded-full transition-all duration-700"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Mnemonic collage section */}
      {mnemonicRoots.length > 0 && (
        <div className="rounded-2xl border border-stone-200 bg-white overflow-hidden shadow-sm">
          <div className="relative">
            {/* Image collage grid */}
            <div className="grid grid-cols-6 sm:grid-cols-8 md:grid-cols-10">
              {mnemonicRoots.slice(0, 20).map((root) => (
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
            {/* Gradient overlay with text */}
            <div
              className="absolute inset-0 bg-gradient-to-t from-stone-900/80 via-stone-900/30 to-transparent flex flex-col items-center justify-end p-5 sm:p-6 cursor-pointer"
              onClick={navigateToMnemonicSheet}
            >
              <h3 className="text-white text-lg sm:text-xl font-bold mb-1 drop-shadow-lg">
                Visual Mnemonic Sheet
              </h3>
              <p className="text-white/80 text-xs sm:text-sm text-center max-w-md mb-3 drop-shadow">
                {mnemonicRoots.length} root illustrations — study, print, and memorize
              </p>
              <button
                onClick={navigateToMnemonicSheet}
                className="px-5 py-2.5 rounded-xl bg-white/95 text-stone-800 text-sm font-semibold hover:bg-white transition-colors shadow-lg flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                View Full Sheet
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Unit grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        {units.map((unit) => {
          const rootBws = unit.roots.map((r) => r.root_buckwalter);
          const mastery = getUnitMastery(progress, rootBws);

          return (
            <div
              key={unit.unit_number}
              className="rounded-2xl border border-stone-200 bg-white p-5 sm:p-6 shadow-sm transition-all hover:border-emerald-300 hover:shadow-md"
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider">
                    Unit {unit.unit_number}
                  </span>
                  <h3 className="text-lg font-semibold text-stone-800 mt-0.5">
                    {unit.unit_theme}
                  </h3>
                </div>
                <div className="text-right">
                  <span className="text-lg font-bold text-stone-600">{mastery}%</span>
                </div>
              </div>

              {/* Mastery bar */}
              <div className="rounded-full bg-stone-100 h-2 mb-4 overflow-hidden">
                <div
                  className="h-full bg-emerald-400 rounded-full transition-all duration-500"
                  style={{ width: `${mastery}%` }}
                />
              </div>

              {/* Root cards */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                {unit.roots.map((root) => {
                  const rp = progress.rootProgress[root.root_buckwalter];
                  const status = rp?.status || 'unseen';
                  const isDismissed = dismissed.has(root.root_buckwalter);

                  return (
                    <button
                      key={root.root_buckwalter}
                      onClick={() => onSelectRoot(root.root_buckwalter)}
                      className={`group flex flex-col items-center rounded-xl border overflow-hidden transition-all hover:shadow-md ${
                        isDismissed
                          ? 'border-stone-100 bg-stone-50 opacity-40 grayscale hover:opacity-70 hover:grayscale-0'
                          : status === 'mastered'
                            ? 'border-emerald-300 bg-emerald-50'
                            : status === 'reviewing'
                              ? 'border-emerald-200 bg-emerald-50/50'
                              : status === 'learning'
                                ? 'border-amber-200 bg-amber-50/50'
                                : 'border-stone-200 bg-white hover:border-emerald-300'
                      }`}
                      title={`${root.root_arabic} (${root.root_buckwalter})${isDismissed ? ' — marked as known' : ''}`}
                    >
                      {root.mnemonic_image_url ? (
                        <img
                          src={root.mnemonic_image_url}
                          alt=""
                          className="w-full aspect-[4/3] object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                      ) : (
                        <div className="w-full aspect-[4/3] bg-stone-100 flex items-center justify-center">
                          <span className="font-arabic text-3xl text-stone-300" dir="rtl">{root.root_arabic}</span>
                        </div>
                      )}
                      <div className="flex items-center gap-1.5 px-2 py-2">
                        <span className="font-arabic text-lg font-medium text-stone-800" dir="rtl">{root.root_arabic}</span>
                        {status === 'mastered' && !isDismissed && (
                          <svg className="w-4 h-4 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
