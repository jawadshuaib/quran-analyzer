import FitText from '../FitText';

// The round badge that leads a search result. One size for all of them, sized
// with its longest labels in mind: "10:109", and roots such as "ف ض ض".
const CIRCLE = 'shrink-0 w-11 h-11 rounded-full flex items-center justify-center';

/** A root's letters in a badge, a thin space apart: Amiri's full space made
 *  "ص م ع" wrap onto two lines, and a hair space runs them into what reads as
 *  a word. A wide root ("ف ض ض") shrinks just enough to fit. */
export function RootBadge({ rootArabic }: { rootArabic: string }) {
  return (
    <span className={`${CIRCLE} bg-gradient-to-br from-emerald-50 to-emerald-100 border border-emerald-200/60`}>
      <FitText max={36} dir="rtl" lang="ar" className="font-arabic text-[13px] font-bold text-emerald-800">
        {[...rootArabic.replace(/\s+/g, '')].join(' ')}
      </FitText>
    </span>
  );
}

interface VerseRefBadgeProps {
  surah: number;
  ayah: number;
  /** Last verse of a range: shown as a second line, "–239". */
  endAyah?: number;
  /** Background, border and text colour. */
  className: string;
}

/** A verse reference in a badge. A six-character reference ("10:109") takes
 *  the smaller size to fit; a range goes on two lines. */
export function VerseRefBadge({ surah, ayah, endAyah, className }: VerseRefBadgeProps) {
  const ref = `${surah}:${ayah}`;
  return (
    <span className={`${CIRCLE} ${className}`}>
      {endAyah ? (
        <span className="text-[10px] font-semibold leading-tight text-center tabular-nums">
          {ref}
          <br />
          &ndash;{endAyah}
        </span>
      ) : (
        <span className={`font-semibold tabular-nums ${ref.length > 5 ? 'text-[10px]' : 'text-xs'}`}>
          {ref}
        </span>
      )}
    </span>
  );
}
