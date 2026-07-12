import { Fragment, type ReactNode } from 'react';

/**
 * Split a string into runs and wrap each Arabic-character run in a
 * `font-arabic` span. English/Latin runs render as bare text so they
 * inherit the surrounding font. Ported from the main site
 * (roots/frontend/src/utils/arabic-runs.tsx).
 *
 * Why: the exegesis and poetry notes are English prose with inline pointed
 * Arabic mixed in. The parent paragraph uses the body sans-serif so the
 * English reads correctly, but inline Arabic glyphs INHERIT that sans-serif
 * unless wrapped — and system sans renders Uthmani diacritics poorly (e.g.
 * kasra-under-shadda becomes indistinguishable from fatha-with-shadda).
 */
const ARABIC_CLASS =
  '[\\u0600-\\u06FF\\u0750-\\u077F\\u08A0-\\u08FF\\uFB50-\\uFDFF\\uFE70-\\uFEFF]';

const ARABIC_RE = new RegExp(ARABIC_CLASS);

// Run of Arabic glyphs, optionally bridged by whitespace, common punctuation,
// or Arabic joiners (ZWNJ U+200C / ZWJ U+200D), so a multi-word phrase gets
// one wrapping span rather than several — keeps the kerning natural.
const ARABIC_RUN_RE = new RegExp(
  '(' + ARABIC_CLASS + '+' +
  '(?:[\\s\\u200C\\u200D.,;:!?\'"()\\u060C\\u061B\\u061F-]*' +
  ARABIC_CLASS + '+)*)',
  'g',
);

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
