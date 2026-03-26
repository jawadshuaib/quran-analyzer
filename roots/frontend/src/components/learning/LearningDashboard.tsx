import { useState, useEffect } from 'react';
import type { LearningUnit } from '../../types/learning';
import { fetchCurriculum } from '../../api/learning';
import { loadProgress, getUnitMastery } from '../../utils/learning-storage';
import { getDueCount } from '../../utils/spaced-repetition';

interface Props {
  onSelectRoot: (rootBw: string) => void;
  onStartReview: () => void;
}

export default function LearningDashboard({ onSelectRoot, onStartReview }: Props) {
  const [units, setUnits] = useState<LearningUnit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const progress = loadProgress();
  const dueCount = getDueCount(progress.reviewQueue);

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
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center text-red-700">
        {error}
      </div>
    );
  }

  if (units.length === 0) {
    return (
      <div className="rounded-lg border border-stone-200 bg-white p-8 text-center">
        <p className="text-stone-500">No curriculum data yet. Run the curriculum generation script first.</p>
      </div>
    );
  }

  // Find next unlearned root
  const nextRoot = (() => {
    for (const unit of units) {
      for (const root of unit.roots) {
        const rp = progress.rootProgress[root.root_buckwalter];
        if (!rp || rp.status === 'unseen') return root;
      }
    }
    return null;
  })();

  const totalLearned = progress.stats.totalRootsLearned;
  const totalRoots = units.reduce((acc, u) => acc + u.roots.length, 0);

  return (
    <div className="space-y-6">
      {/* Stats bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
        <div className="flex items-center gap-6">
          <div>
            <p className="text-2xl font-bold text-emerald-700">{totalLearned}</p>
            <p className="text-xs text-stone-400">Roots Learned</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-stone-700">{progress.stats.currentStreak}</p>
            <p className="text-xs text-stone-400">Day Streak</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-stone-700">{totalRoots}</p>
            <p className="text-xs text-stone-400">Total Roots</p>
          </div>
        </div>
        <div className="flex gap-3">
          {dueCount > 0 && (
            <button
              onClick={onStartReview}
              className="relative px-5 py-2.5 rounded-lg bg-amber-500 text-white text-sm font-medium hover:bg-amber-600 transition-colors"
            >
              Review Due
              <span className="absolute -top-2 -right-2 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
                {dueCount}
              </span>
            </button>
          )}
          {nextRoot && (
            <button
              onClick={() => onSelectRoot(nextRoot.root_buckwalter)}
              className="px-5 py-2.5 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 transition-colors"
            >
              Continue Learning
            </button>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="rounded-full bg-stone-200 h-2 overflow-hidden">
        <div
          className="h-full bg-emerald-500 transition-all duration-500"
          style={{ width: `${totalRoots > 0 ? (totalLearned / totalRoots) * 100 : 0}%` }}
        />
      </div>

      {/* Unit grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {units.map((unit) => {
          const rootBws = unit.roots.map((r) => r.root_buckwalter);
          const mastery = getUnitMastery(progress, rootBws);

          return (
            <div
              key={unit.unit_number}
              className="rounded-xl border border-stone-200 bg-white p-4 shadow-sm transition-colors hover:border-emerald-200"
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-stone-700">
                  <span className="text-xs text-stone-400 mr-1">Unit {unit.unit_number}</span>
                  {unit.unit_theme}
                </h3>
                <span className="text-xs text-stone-400">{mastery}%</span>
              </div>

              {/* Mastery bar */}
              <div className="rounded-full bg-stone-100 h-1.5 mb-3 overflow-hidden">
                <div
                  className="h-full bg-emerald-400 transition-all duration-300"
                  style={{ width: `${mastery}%` }}
                />
              </div>

              {/* Root pills */}
              <div className="flex flex-wrap gap-1.5">
                {unit.roots.map((root) => {
                  const rp = progress.rootProgress[root.root_buckwalter];
                  const status = rp?.status || 'unseen';

                  return (
                    <button
                      key={root.root_buckwalter}
                      onClick={() => onSelectRoot(root.root_buckwalter)}
                      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-sm border transition-colors ${
                        status === 'mastered'
                          ? 'border-emerald-300 bg-emerald-100 text-emerald-800'
                          : status === 'reviewing'
                            ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                            : status === 'learning'
                              ? 'border-amber-200 bg-amber-50 text-amber-700'
                              : 'border-stone-200 bg-white text-stone-600 hover:border-emerald-300 hover:bg-emerald-50'
                      }`}
                      title={`${root.root_arabic} (${root.root_buckwalter}) — ${root.frequency_rank}th most common`}
                    >
                      <span className="font-arabic text-xs" dir="rtl">{root.root_arabic}</span>
                      {status === 'mastered' && (
                        <svg className="w-3 h-3 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
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
