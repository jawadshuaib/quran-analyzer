import { Fragment, type ReactNode } from 'react';
import { ARABIC_FONT } from './shared';

/**
 * Split a string into runs and wrap each Arabic-character run in a
 * span with `fontFamily: ARABIC_FONT`. Latin/English runs render as
 * bare text so they inherit the surrounding SYSTEM_FONT.
 *
 * Why: AI-generated translations, glosses, root meanings, grammar
 * taglines, etc. are mostly English prose with inline Arabic words
 * mixed in ("...the genitive construction بِنِعْمَةِ رَبِّكَ explicitly
 * marks..."). The parent slide uses SYSTEM_FONT for the English so
 * it reads correctly, but inline Arabic glyphs INHERIT that
 * sans-serif. In headless Chromium (which is what Remotion runs in)
 * the system fallback for Arabic is generally a font that drops the
 * kasra-under-shadda combination — verified on the web side where
 * Scheherazade New had the same bug, rendering رَبِّكَ as رَبَّكَ.
 *
 * This is the video-renderer counterpart of
 * roots/frontend/src/utils/arabic-runs.tsx. They can't share code
 * directly because the frontend uses a Tailwind `font-arabic` class
 * while Remotion needs inline `fontFamily` (no Tailwind here).
 *
 * Detected character ranges (typical Arabic + extended + presentation
 * forms):
 *   U+0600–06FF  Basic Arabic
 *   U+0750–077F  Arabic Supplement
 *   U+08A0–08FF  Arabic Extended-A
 *   U+FB50–FDFF  Arabic Presentation Forms-A
 *   U+FE70–FEFF  Arabic Presentation Forms-B
 *   U+200C, U+200D  ZWNJ / ZWJ — bridge characters inside an Arabic run
 *
 * Whitespace and ASCII punctuation between Arabic words stay inside
 * the same run, so a multi-word phrase like "إِيَّاكَ نَعْبُدُ" gets one
 * wrapping span rather than two — keeps the kerning natural.
 */
// Arabic character class as a string fragment, using Unicode escapes
// (avoids literal Arabic in the regex source so linters don't choke).
const ARABIC_CLASS =
  '[\\u0600-\\u06FF\\u0750-\\u077F\\u08A0-\\u08FF\\uFB50-\\uFDFF\\uFE70-\\uFEFF]';

const ARABIC_RE = new RegExp(ARABIC_CLASS);

// Run of Arabic glyphs, optionally bridged by whitespace, common
// punctuation, or Arabic joiners (ZWNJ / ZWJ).
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
 * a span styled with the project's ARABIC_FONT. Idempotent if the
 * text has no Arabic — returns the original string.
 *
 * Callers pass plain strings (e.g. slide.translation,
 * slide.meaning, gloss fields) wherever those would otherwise be
 * rendered inside a SYSTEM_FONT container.
 */
export function wrapArabicRuns(text: string | null | undefined): ReactNode {
  if (!text || !ARABIC_RE.test(text)) return text ?? '';
  ARABIC_RUN_RE.lastIndex = 0;
  const parts: ReactNode[] = [];
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = ARABIC_RUN_RE.exec(text)) !== null) {
    if (m.index > last) {
      parts.push(<Fragment key={`t-${last}`}>{text.slice(last, m.index)}</Fragment>);
    }
    parts.push(
      <span
        key={`a-${m.index}`}
        lang="ar"
        style={{ fontFamily: ARABIC_FONT }}
      >
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
