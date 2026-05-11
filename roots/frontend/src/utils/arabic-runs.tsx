import { Fragment, type ReactNode } from 'react';

/**
 * Split a string into runs and wrap each Arabic-character run in a
 * `font-arabic` span. English/Latin runs render as bare text so they
 * inherit the surrounding font.
 *
 * Why: AI-generated content (ai_word_meanings.meaning_detailed,
 * cross_ref_notes, cognate_notes, …) is mostly English prose with
 * inline Arabic words mixed in ("...the genitive construction
 * بِنِعْمَةِ رَبِّكَ explicitly marks..."). The parent paragraph
 * uses the body sans-serif so the English reads correctly, but the
 * inline Arabic glyphs INHERIT that sans-serif unless we wrap them.
 * System sans-serif renders Uthmani diacritics poorly — most
 * notably, kasra-under-shadda became visually indistinguishable from
 * fatha-with-shadda. Wrapping the Arabic runs in font-arabic
 * (Amiri-first) restores correct rendering.
 *
 * Detected character ranges (typical Arabic + extended + presentation
 * forms + ZWNJ/ZWJ/Arabic mark):
 *   U+0600–06FF  Basic Arabic
 *   U+0750–077F  Arabic Supplement
 *   U+08A0–08FF  Arabic Extended-A
 *   U+FB50–FDFF  Arabic Presentation Forms-A
 *   U+FE70–FEFF  Arabic Presentation Forms-B
 *   U+200C, U+200D  ZWNJ / ZWJ (often used between letters; treat
 *                   as part of an Arabic run when adjacent to one)
 *
 * Whitespace and ASCII punctuation between Arabic words stay inside
 * the same run, so a multi-word phrase like "إِيَّاكَ نَعْبُدُ" gets one
 * wrapping span rather than two — keeps the kerning natural.
 */
// Arabic character class as a string fragment, written with Unicode
// escapes so the linter doesn't see "irregular whitespace" from the
// embedded codepoints.
const ARABIC_CLASS =
  '[\\u0600-\\u06FF\\u0750-\\u077F\\u08A0-\\u08FF\\uFB50-\\uFDFF\\uFE70-\\uFEFF]';

const ARABIC_RE = new RegExp(ARABIC_CLASS);

// Run of Arabic glyphs, optionally bridged by whitespace, common
// punctuation, or Arabic joiners (ZWNJ U+200C / ZWJ U+200D — these
// are LEGITIMATELY part of Arabic runs; the linter's
// no-misleading-character-class warning is about combining-marks
// confusion, which doesn't apply here since we're using them as
// bridge characters, not as letter modifiers).
/* eslint-disable no-misleading-character-class */
const ARABIC_RUN_RE = new RegExp(
  '(' + ARABIC_CLASS + '+' +
  '(?:[\\s\\u200C\\u200D.,;:!?\'"()\\u060C\\u061B\\u061F-]*' +
  ARABIC_CLASS + '+)*)',
  'g',
);
/* eslint-enable no-misleading-character-class */

/** True when the text contains at least one Arabic character. */
export function hasArabic(text: string): boolean {
  return ARABIC_RE.test(text);
}

/**
 * Render a string as React children with each Arabic run wrapped in
 * <span lang="ar" className="font-arabic">. Idempotent if the text
 * has no Arabic — just returns the original string.
 */
export function wrapArabicRuns(text: string): ReactNode {
  if (!text || !ARABIC_RE.test(text)) return text;
  // Reset lastIndex since this is a /g RegExp shared across calls.
  ARABIC_RUN_RE.lastIndex = 0;
  const parts: ReactNode[] = [];
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = ARABIC_RUN_RE.exec(text)) !== null) {
    if (m.index > last) {
      parts.push(<Fragment key={`t-${last}`}>{text.slice(last, m.index)}</Fragment>);
    }
    parts.push(
      <span key={`a-${m.index}`} lang="ar" className="font-arabic">
        {m[0]}
      </span>,
    );
    last = m.index + m[0].length;
  }
  if (last < text.length) {
    parts.push(<Fragment key={`t-${last}`}>{text.slice(last)}</Fragment>);
  }
  return parts;
}
