import type { LearningDerivative } from '../../types/learning';
import { wrapArabicRuns } from '../../utils/arabic-runs';

interface Props {
  rootArabic: string;
  rootBw: string;
  derivatives: LearningDerivative[];
}

export default function DerivativeMap({ rootArabic, rootBw, derivatives }: Props) {
  if (derivatives.length === 0) return null;

  return (
    <div className="rounded-2xl border border-stone-200 bg-white p-6 sm:p-8 shadow-sm">
      <h3 className="text-sm font-semibold text-stone-500 uppercase tracking-wider mb-6">
        Word Family from Root{' '}
        <span className="font-arabic text-lg text-stone-800" dir="rtl">{rootArabic}</span>
      </h3>

      {/* Root center */}
      <div className="flex flex-col items-center mb-6">
        <div className="rounded-full bg-emerald-100 border-2 border-emerald-400 px-6 py-3">
          <span className="font-arabic text-2xl text-emerald-800 font-bold" dir="rtl">
            {rootArabic}
          </span>
        </div>
        <div className="w-px h-5 bg-stone-300" />
      </div>

      {/* Derivatives as branches */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {derivatives.map((d) => (
          <div
            key={d.lemma_buckwalter}
            className="flex items-start gap-4 rounded-xl border border-stone-100 bg-stone-50 p-4 hover:border-emerald-200 hover:bg-emerald-50/30 transition-all"
          >
            <div className="flex-shrink-0 text-center min-w-[70px]">
              <a
                href={`/root/${encodeURIComponent(rootBw)}`}
                className="font-arabic text-xl text-stone-800 hover:text-emerald-700"
                dir="rtl"
              >
                {d.lemma_arabic}
              </a>
              <div className="text-xs text-stone-400 mt-1">
                {d.frequency}x
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-base text-stone-700">{wrapArabicRuns(d.meaning_gloss || '')}</p>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {d.verb_form && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-600 border border-indigo-100 font-medium">
                    Form {d.verb_form}
                  </span>
                )}
                {d.pos && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-stone-100 text-stone-500">
                    {d.pos}
                  </span>
                )}
              </div>
              {d.semantic_shift && (
                <p className="text-sm text-stone-400 mt-2 italic">{wrapArabicRuns(d.semantic_shift)}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
