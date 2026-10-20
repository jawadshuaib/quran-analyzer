import { useState } from 'react';
import type { AltTranslationData } from '../types';
import { FormattedInline } from './FormattedText';

/**
 * "See translation by X" under our root-based translation.
 *
 * The tier comes from two LLM judges (alt_translations_ai.py) grading how
 * much the most Qur'an-faithful public-domain translation adds to ours:
 *   3  shown expanded: it conveys something ours leaves out
 *   2  dark gray wavy link: a reading worth weighing
 *   1  light gray wavy link: a smaller nuance
 * Tier 0 never reaches the client.
 */
export default function AltTranslation({
  alt,
  verseKey,
}: {
  alt?: AltTranslationData | null;
  verseKey: string;
}) {
  const [open, setOpen] = useState(alt?.tier === 3);
  if (!alt || alt.tier < 1) return null;

  const linkTone =
    alt.tier >= 2
      ? 'text-ink-secondary decoration-ink-secondary/80 hover:text-ink'
      : 'text-stone-400 decoration-stone-400 hover:text-ink-secondary';

  return (
    <div className="mt-2">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className={`text-xs sm:text-[13px] underline decoration-wavy decoration-1 underline-offset-4
                    transition-colors cursor-pointer ${linkTone}`}
      >
        See translation by {alt.translator}
      </button>
      {open && (
        <div className="mt-2 border-l-2 border-stone-200 pl-3">
          <p className="text-[14px] sm:text-[15px] leading-relaxed text-ink-secondary">{alt.text}</p>
          {alt.note && (
            <p className="mt-1.5 text-xs leading-relaxed text-ink-muted">
              {/* Same renderer as the translation notes: *transliterations*
                  that quote this verse highlight their Arabic words on hover. */}
              <FormattedInline
                text={alt.note}
                anchors={alt.anchors?.length ? { verseKey, list: alt.anchors } : undefined}
              />
            </p>
          )}
        </div>
      )}
    </div>
  );
}
