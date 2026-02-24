import type { RelatedVerse } from '../types/index.ts';

interface Props {
  verse: RelatedVerse;
  onSelect: (surah: number, ayah: number, textUthmani: string, translation: string) => void;
}

export default function RelatedVerseCard({ verse: v, onSelect }: Props) {
  return (
    <button
      onClick={() => onSelect(v.surah, v.ayah, v.text_uthmani, v.translation)}
      className="w-full text-left rounded-lg border border-stone-100 bg-stone-50 p-3 hover:border-emerald-200 hover:bg-emerald-50/30 transition-colors cursor-pointer"
    >
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <span className="text-xs font-medium text-stone-500">
          {v.surah}:{v.ayah}
        </span>
        <span className="shrink-0 inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700">
          {Math.round(v.similarity_score * 100)}%
        </span>
      </div>

      <p
        dir="rtl"
        lang="ar"
        className="font-arabic text-base text-stone-800 leading-relaxed line-clamp-2 mb-1"
      >
        {v.text_uthmani}
      </p>

      <p className="text-xs text-stone-500 italic line-clamp-2 mb-1.5">
        {v.translation}
      </p>

      {v.shared_roots.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {v.shared_roots.map((root) => (
            <span
              key={root.root_buckwalter}
              className="inline-flex items-center gap-0.5 rounded-full bg-sky-50 border border-sky-200 px-1.5 py-0.5 text-xs text-sky-700"
            >
              <span dir="rtl" lang="ar" className="font-arabic text-xs">
                {root.root_arabic}
              </span>
            </span>
          ))}
        </div>
      )}
    </button>
  );
}
