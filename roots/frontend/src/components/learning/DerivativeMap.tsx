import type { LearningDerivative } from '../../types/learning';

interface Props {
  rootArabic: string;
  rootBw: string;
  derivatives: LearningDerivative[];
}

export default function DerivativeMap({ rootArabic, rootBw, derivatives }: Props) {
  if (derivatives.length === 0) return null;

  return (
    <div className="rounded-xl border border-stone-200 bg-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-stone-500 uppercase tracking-wide mb-4">
        Word Family from Root{' '}
        <span className="font-arabic text-base text-stone-800" dir="rtl">{rootArabic}</span>
      </h3>

      {/* Root center */}
      <div className="flex flex-col items-center mb-4">
        <div className="rounded-full bg-emerald-100 border-2 border-emerald-400 px-4 py-2">
          <span className="font-arabic text-xl text-emerald-800 font-bold" dir="rtl">
            {rootArabic}
          </span>
        </div>
        <div className="w-px h-4 bg-stone-300" />
      </div>

      {/* Derivatives as branches */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {derivatives.map((d) => (
          <div
            key={d.lemma_buckwalter}
            className="flex items-start gap-3 rounded-lg border border-stone-100 bg-stone-50 p-3 hover:border-emerald-200 hover:bg-emerald-50/30 transition-colors"
          >
            <div className="flex-shrink-0 text-center min-w-[60px]">
              <a
                href={`/root/${encodeURIComponent(rootBw)}`}
                className="font-arabic text-lg text-stone-800 hover:text-emerald-700"
                dir="rtl"
              >
                {d.lemma_arabic}
              </a>
              <div className="text-[10px] text-stone-400 mt-0.5">
                {d.frequency}x
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-stone-700">{d.meaning_gloss}</p>
              {d.verb_form && (
                <span className="inline-block mt-1 text-[10px] px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-600 border border-indigo-100">
                  Form {d.verb_form}
                </span>
              )}
              {d.pos && (
                <span className="inline-block mt-1 ml-1 text-[10px] px-1.5 py-0.5 rounded bg-stone-100 text-stone-500">
                  {d.pos}
                </span>
              )}
              {d.semantic_shift && (
                <p className="text-xs text-stone-400 mt-1 italic">{d.semantic_shift}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
