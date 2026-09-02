import { memo } from 'react';
import type { ParsedVerseRef } from '../../utils/search-classifier';
import type { VersePreview } from '../../api/quran';

interface Props {
  verseRef: ParsedVerseRef;
  surahName: string;
  preview: VersePreview | null;
  previewLoading: boolean;
  active: boolean;
  onSelect: () => void;
  onHover: () => void;
  id: string;
}

export default memo(function VerseRefSuggestion({
  verseRef, surahName, preview, previewLoading, active, onSelect, onHover, id,
}: Props) {
  const displayName = preview?.surah_name || surahName;

  return (
    <li
      id={id}
      role="option"
      aria-selected={active}
      className={`group px-4 py-3 cursor-pointer transition-colors ${
        active ? 'bg-emerald-50/80' : 'hover:bg-stone-50'
      }`}
      onClick={onSelect}
      onMouseEnter={onHover}
    >
      <div className="flex items-start gap-3">
        {/* Verse ref circle */}
        <div className="shrink-0 w-10 h-10 rounded-full bg-emerald-100 border border-emerald-200/60 flex items-center justify-center">
          <span className={`font-semibold text-emerald-700 tabular-nums ${
            verseRef.endAyah ? 'text-[10px] leading-tight text-center' : 'text-xs'
          }`}>
            {verseRef.surah}:{verseRef.ayah}
            {verseRef.endAyah ? `-${verseRef.endAyah}` : ''}
          </span>
        </div>

        <div className="flex-1 min-w-0">
          {/* Surah name + ref */}
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-stone-800">
              {displayName}
            </span>
            {/* A range opens the reader, not the verse page — say so, so the
                destination isn't a surprise. */}
            {verseRef.endAyah && (
              <span className="rounded-full bg-emerald-100 px-1.5 py-0.5 text-[10px] font-medium text-emerald-700">
                {verseRef.endAyah - verseRef.ayah + 1} verses · read
              </span>
            )}
            {previewLoading && (
              <div className="h-3 w-3 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-600" />
            )}
          </div>

          {/* Arabic text preview */}
          {preview?.text_uthmani && (
            <p
              dir="rtl"
              lang="ar"
              className="mt-1 font-arabic text-base leading-[2.2] text-stone-600 truncate"
            >
              {preview.text_uthmani}
            </p>
          )}

          {/* Translation preview */}
          {preview?.translation && (
            <p className="mt-0.5 text-xs text-stone-500 truncate">
              {preview.translation}
            </p>
          )}
        </div>

        {/* Arrow */}
        <svg className={`w-4 h-4 shrink-0 mt-1 transition-colors ${active ? 'text-emerald-500' : 'text-stone-300'}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </li>
  );
});
