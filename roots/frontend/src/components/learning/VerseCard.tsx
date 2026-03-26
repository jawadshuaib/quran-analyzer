import { useState } from 'react';
import type { LearningVerseData } from '../../types/learning';

interface Props {
  verse: LearningVerseData;
  teachingNote?: string;
  showExploreLink?: boolean;
}

export default function VerseCard({ verse, teachingNote, showExploreLink = true }: Props) {
  const [flipped, setFlipped] = useState(false);

  const targetWords = verse.words.filter((w) => w.is_target);

  return (
    <div className="perspective-1000">
      <div
        className={`relative w-full transition-transform duration-500 transform-style-preserve-3d cursor-pointer ${
          flipped ? 'rotate-y-180' : ''
        }`}
        onClick={() => setFlipped(!flipped)}
        style={{ minHeight: '180px' }}
      >
        {/* Front: Arabic verse */}
        <div className="absolute inset-0 backface-hidden rounded-xl border border-stone-200 bg-white p-6 shadow-sm flex flex-col items-center justify-center">
          <p className="text-xs text-stone-400 mb-3">
            {verse.surah_name} {verse.chapter}:{verse.verse}
          </p>
          <p className="font-arabic text-2xl sm:text-3xl leading-loose text-stone-800 text-center" dir="rtl" lang="ar">
            {verse.words.map((w, i) => (
              <span key={i}>
                {i > 0 && ' '}
                <span
                  className={
                    w.is_target
                      ? 'text-emerald-700 font-bold underline decoration-emerald-300 decoration-2 underline-offset-4'
                      : ''
                  }
                >
                  {w.arabic}
                </span>
              </span>
            ))}
          </p>
          <p className="text-xs text-stone-400 mt-4">
            Tap to reveal meaning
          </p>
        </div>

        {/* Back: Translation + word breakdown */}
        <div className="absolute inset-0 backface-hidden rotate-y-180 rounded-xl border border-emerald-200 bg-emerald-50 p-6 shadow-sm overflow-y-auto">
          <p className="text-xs text-stone-400 mb-2">
            {verse.surah_name} {verse.chapter}:{verse.verse}
          </p>

          {/* Full translation */}
          <p className="text-stone-700 text-sm leading-relaxed mb-4">
            {verse.translation}
          </p>

          {/* Target word(s) highlighted */}
          {targetWords.length > 0 && (
            <div className="border-t border-emerald-200 pt-3">
              <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wide mb-2">
                Target Word{targetWords.length > 1 ? 's' : ''}
              </p>
              {targetWords.map((tw) => (
                <div key={tw.pos} className="mb-2">
                  <span className="font-arabic text-lg text-emerald-800" dir="rtl">
                    {tw.arabic}
                  </span>
                  <span className="text-stone-500 mx-2">—</span>
                  <span className="text-stone-700 text-sm">
                    {tw.ai_meaning?.preferred_translation
                      || tw.ai_meaning?.meaning_short
                      || tw.gloss
                      || '(no translation)'}
                  </span>
                  {tw.part_of_speech && (
                    <span className="ml-2 text-xs text-stone-400">
                      ({tw.part_of_speech})
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Word-by-word (compact) */}
          <div className="border-t border-emerald-200 pt-3 mt-2">
            <p className="text-xs font-semibold text-stone-500 uppercase tracking-wide mb-2">
              Word by Word
            </p>
            <div className="flex flex-wrap gap-x-4 gap-y-1" dir="rtl">
              {verse.words.map((w) => (
                <div key={w.pos} className="text-center">
                  <p className={`font-arabic text-sm ${w.is_target ? 'text-emerald-700 font-bold' : 'text-stone-700'}`}>
                    {w.arabic}
                  </p>
                  <p className="text-[10px] text-stone-400" dir="ltr">
                    {w.ai_meaning?.preferred_translation
                      || w.ai_meaning?.meaning_short
                      || w.gloss
                      || ''}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {teachingNote && (
            <p className="text-xs text-emerald-600 italic mt-3 border-t border-emerald-200 pt-2">
              {teachingNote}
            </p>
          )}

          {showExploreLink && (
            <div className="mt-3 text-right">
              <a
                href={`/verse/${verse.chapter}:${verse.verse}`}
                className="text-xs text-emerald-600 hover:text-emerald-800 underline"
                onClick={(e) => e.stopPropagation()}
              >
                Explore this verse
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
