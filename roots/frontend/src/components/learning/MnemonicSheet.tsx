import { useState, useEffect } from 'react';
import type { LearningUnit } from '../../types/learning';
import { fetchCurriculum } from '../../api/learning';

interface Props {
  onBack: () => void;
  onSelectRoot: (rootBw: string) => void;
}

export default function MnemonicSheet({ onBack, onSelectRoot }: Props) {
  const [units, setUnits] = useState<LearningUnit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

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
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center text-red-700">
        {error}
      </div>
    );
  }

  const allRoots = units.flatMap((u) =>
    u.roots
      .filter((r) => r.mnemonic_image_url && r.mnemonic_caption)
      .map((r) => ({ ...r, unit_number: u.unit_number, unit_theme: u.unit_theme }))
  );

  return (
    <div className="space-y-8">
      {/* Header — hidden when printing */}
      <div className="print:hidden">
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={onBack}
            className="text-sm text-stone-500 hover:text-stone-700 flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Dashboard
          </button>
          <button
            onClick={() => window.print()}
            className="px-5 py-2 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            Print Sheet
          </button>
        </div>
      </div>

      {/* Title — visible in print */}
      <div className="text-center">
        <h1 className="text-2xl sm:text-3xl font-bold text-stone-800 mb-1">
          Quranic Root Mnemonic Sheet
        </h1>
        <p className="text-sm text-stone-500">
          {allRoots.length} roots — study the images, then practice at{' '}
          <span className="text-emerald-600 font-medium print:text-stone-600">al-nuqta.com/learning</span>
        </p>
      </div>

      {/* Cards grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 print:grid-cols-4 print:gap-3">
        {allRoots.map((root) => (
          <button
            key={root.root_buckwalter}
            onClick={() => onSelectRoot(root.root_buckwalter)}
            className="rounded-xl border border-stone-200 bg-white overflow-hidden print:break-inside-avoid print:border-stone-300 text-left transition-all hover:border-emerald-300 hover:shadow-md cursor-pointer"
          >
            <img
              src={root.mnemonic_image_url!}
              alt={`Mnemonic for ${root.root_arabic}`}
              className="w-full aspect-square object-cover"
            />
            <div className="p-2.5 space-y-1">
              <div className="flex items-baseline justify-between">
                <span className="font-arabic text-xl font-bold text-stone-800" dir="rtl">
                  {root.root_arabic}
                </span>
                <span className="text-[10px] text-stone-400 print:text-stone-500">
                  Unit {root.unit_number}
                </span>
              </div>
              <p className="text-xs text-stone-600 leading-snug print:text-[10px] print:leading-tight">
                {root.mnemonic_caption}
              </p>
              {root.top_derivatives && root.top_derivatives.length > 0 && (
                <div className="pt-1 border-t border-stone-100 space-y-0.5">
                  {root.top_derivatives.map((d, i) => (
                    <p key={i} className="text-[11px] text-stone-500 leading-snug print:text-[9px]">
                      <span className="font-arabic text-stone-700 font-medium" dir="rtl">{d.lemma_arabic}</span>
                      {' '}
                      <span className="text-stone-400">— {d.meaning_gloss}</span>
                    </p>
                  ))}
                </div>
              )}
            </div>
          </button>
        ))}
      </div>

      {/* Print footer */}
      <div className="hidden print:block text-center text-xs text-stone-400 pt-4 border-t border-stone-200">
        Generated from al-nuqta.com — Quranic Root Word Analyzer
      </div>
    </div>
  );
}
