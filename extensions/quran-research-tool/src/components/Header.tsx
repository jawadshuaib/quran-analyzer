import type { ParsedVerse } from '../utils/parseQuranUrl.ts';

interface Props {
  parsed: ParsedVerse | null;
  onBack?: () => void;
  detailVerse?: { surah: number; ayah: number } | null;
}

export default function Header({ parsed, onBack, detailVerse }: Props) {
  const verseLabel = parsed
    ? parsed.ayahs.length === 1
      ? `${parsed.surah}:${parsed.ayahs[0]}`
      : `${parsed.surah}:${parsed.ayahs[0]}-${parsed.ayahs[parsed.ayahs.length - 1]}`
    : null;

  return (
    <div className="px-5 py-3 border-b border-stone-200 bg-white">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {onBack && (
            <button
              onClick={onBack}
              className="text-stone-400 hover:text-stone-600 transition-colors cursor-pointer"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
          )}
          <h1 className="text-base font-bold text-stone-800">Quran Research Tool</h1>
        </div>
        {verseLabel && (
          <span className="inline-flex items-center rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-700">
            {verseLabel}
          </span>
        )}
      </div>
      {parsed && !detailVerse && (
        <p className="text-sm text-stone-500 mt-1">
          Verses similar to {verseLabel}
        </p>
      )}
      {detailVerse && (
        <p className="text-sm text-stone-500 mt-1">
          Surrounding context for {detailVerse.surah}:{detailVerse.ayah}
        </p>
      )}
    </div>
  );
}
