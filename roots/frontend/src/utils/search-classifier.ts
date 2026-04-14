/**
 * Classify user input into a search intent for the unified search bar.
 */

export type SearchIntent = 'verse_ref' | 'root' | 'semantic' | 'root_and_semantic';

export interface ParsedVerseRef {
  surah: number;
  ayah: number;
  partial: boolean; // true if user typed "2:" (no ayah yet)
}

const VERSE_REF_RE = /^\d{1,3}(?::(\d{0,3}))?$/;
const ARABIC_RE = /[\u0600-\u06FF]/;
// Buckwalter uses ASCII letters plus special chars: $ < > { } * ' ~ &
const SHORT_LATIN_RE = /^[a-zA-Z$<>{}'~&*]{1,4}$/;

/**
 * Try to parse a verse reference from the input.
 * Returns null if not a verse reference pattern.
 */
export function parseVerseRef(input: string): ParsedVerseRef | null {
  const trimmed = input.trim();
  const m = trimmed.match(VERSE_REF_RE);
  if (!m) return null;
  const surah = parseInt(trimmed.split(':')[0], 10);
  if (surah < 1 || surah > 114) return null;
  const ayahStr = m[1];
  if (ayahStr === undefined) {
    // Just a number like "36" — treat as surah:1
    return { surah, ayah: 1, partial: false };
  }
  if (ayahStr === '') {
    // "2:" — partial, waiting for ayah
    return { surah, ayah: 1, partial: true };
  }
  const ayah = parseInt(ayahStr, 10);
  if (ayah < 1) return null;
  return { surah, ayah, partial: false };
}

/**
 * Classify what kind of search the user is performing.
 */
export function classifyInput(input: string): SearchIntent {
  const trimmed = input.trim();
  if (!trimmed) return 'verse_ref'; // empty = no-op

  // 1. Verse reference pattern (digits with optional colon)
  if (parseVerseRef(trimmed)) return 'verse_ref';

  // 2. Arabic characters → root search
  if (ARABIC_RE.test(trimmed)) return 'root';

  // 3. Short Latin/Buckwalter (1-4 chars) → root search
  if (SHORT_LATIN_RE.test(trimmed)) return 'root';

  // 4. Longer English (5+ chars) → both root + semantic
  return 'root_and_semantic';
}
