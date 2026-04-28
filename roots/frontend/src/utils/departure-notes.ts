/**
 * Shared utilities for rendering AI translation "departure notes".
 *
 * The text comes back as a paragraph that uses " - " as a bullet
 * separator after a sentence-ending period. We split it into discrete
 * lines so each one renders as its own paragraph (with verse refs +
 * Arabic-root refs auto-linked by VerseRefText).
 */

/** Split departure notes into separate lines at " - " when preceded by
 *  "." within 3 chars. */
export function splitDepartureNotes(text: string): string[] {
  const processed = text.replace(/(\..{0,2}) - /g, '$1\n- ');
  return processed.split('\n');
}
