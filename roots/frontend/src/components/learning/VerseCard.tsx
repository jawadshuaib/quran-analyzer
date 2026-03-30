import { useState, useEffect } from 'react';
import type { LearningVerseData } from '../../types/learning';

interface Props {
  verse: LearningVerseData;
  teachingNote?: string;
  showExploreLink?: boolean;
  onFlip?: (flipped: boolean) => void;
  flipTrigger?: number;
}

export default function VerseCard({ verse, teachingNote, showExploreLink = true, onFlip, flipTrigger }: Props) {
  const [flipped, setFlipped] = useState(false);

  // External flip trigger — toggle flip when trigger changes
  useEffect(() => {
    if (flipTrigger !== undefined && flipTrigger > 0) {
      setFlipped((prev) => { const next = !prev; onFlip?.(next); return next; });
    }
  }, [flipTrigger]); // eslint-disable-line react-hooks/exhaustive-deps

  const targetWords = verse.words.filter((w) => w.is_target);

  return (
    <div className="perspective-1000">
      <div
        className={`relative w-full transition-transform duration-500 transform-style-preserve-3d cursor-pointer ${
          flipped ? 'rotate-y-180' : ''
        }`}
        onClick={() => { const next = !flipped; setFlipped(next); onFlip?.(next); }}
        style={{ minHeight: '220px' }}
      >
        {/* Front: Arabic verse */}
        <div className="absolute inset-0 backface-hidden rounded-2xl border border-stone-200 bg-white p-6 sm:p-8 shadow-sm flex flex-col items-center justify-center">
          <p className="text-sm text-stone-400 mb-4">
            {verse.surah_name} {verse.chapter}:{verse.verse}
          </p>
          <p className="font-arabic text-2xl sm:text-3xl md:text-4xl leading-[2.2] text-stone-800 text-center" dir="rtl" lang="ar">
            {verse.words.map((w, i) => (
              <span key={i}>
                {i > 0 && ' '}
                <span
                  className={
                    w.is_target
                      ? 'text-emerald-700 font-bold underline decoration-emerald-300 decoration-2 underline-offset-8'
                      : ''
                  }
                >
                  {w.arabic}
                </span>
              </span>
            ))}
          </p>
          <p className="text-sm text-stone-400 mt-5 flex items-center gap-1.5">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
            </svg>
            Tap to reveal meaning
          </p>
        </div>

        {/* Back: Translation + word breakdown */}
        <div className="absolute inset-0 backface-hidden rotate-y-180 rounded-2xl border border-emerald-200 bg-emerald-50 p-6 sm:p-8 shadow-sm overflow-y-auto">
          <p className="text-sm text-stone-400 mb-3">
            {verse.surah_name} {verse.chapter}:{verse.verse}
          </p>

          {/* Word-by-word (compact) — shown first */}
          <div className="mb-4">
            <p className="text-xs font-semibold text-stone-500 uppercase tracking-wider mb-3">
              Word by Word
            </p>
            <div className="flex flex-wrap gap-x-5 gap-y-2" dir="rtl">
              {verse.words.map((w) => (
                <div key={w.pos} className="text-center">
                  <p className={`font-arabic text-base ${w.is_target ? 'text-emerald-700 font-bold' : 'text-stone-700'}`}>
                    {w.arabic}
                  </p>
                  <p className="text-xs text-stone-400 mt-0.5" dir="ltr">
                    {w.ai_meaning?.preferred_translation
                      || w.ai_meaning?.meaning_short
                      || w.gloss
                      || ''}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Full translation */}
          <div className="border-t border-emerald-200 pt-4 mb-4">
            <p className="text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">
              Translation
            </p>
            <p className="text-stone-700 text-base leading-relaxed">
              {verse.translation}
            </p>
          </div>

          {/* Target word(s) highlighted */}
          {targetWords.length > 0 && (
            <div className="border-t border-emerald-200 pt-4">
              <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wider mb-3">
                Target Word{targetWords.length > 1 ? 's' : ''}
              </p>
              {targetWords.map((tw) => (
                <div key={tw.pos} className="mb-3 flex items-baseline gap-2 flex-wrap">
                  <span className="font-arabic text-xl text-emerald-800 font-bold" dir="rtl">
                    {tw.arabic}
                  </span>
                  <span className="text-stone-400">—</span>
                  <span className="text-stone-700 text-base font-medium">
                    {tw.ai_meaning?.preferred_translation
                      || tw.ai_meaning?.meaning_short
                      || tw.gloss
                      || '(no translation)'}
                  </span>
                  {tw.part_of_speech && (
                    <span className="text-xs text-stone-400 bg-white/60 px-2 py-0.5 rounded-full">
                      {tw.part_of_speech}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}

          {teachingNote && (
            <p className="text-sm text-emerald-600 italic mt-4 border-t border-emerald-200 pt-3">
              {teachingNote}
            </p>
          )}

          {showExploreLink && (
            <div className="mt-4 text-right">
              <a
                href={`/verse/${verse.chapter}:${verse.verse}`}
                className="text-sm text-emerald-600 hover:text-emerald-800 underline font-medium"
                onClick={(e) => e.stopPropagation()}
              >
                Explore this verse &rarr;
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
