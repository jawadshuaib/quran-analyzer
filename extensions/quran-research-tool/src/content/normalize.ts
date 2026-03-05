/**
 * Arabic text normalization — must produce identical output to the Python
 * build_trigram_index.py normalize_arabic() function.
 */

/** Strip all Unicode combining marks (category Mn). */
function stripCombiningMarks(text: string): string {
  // \p{Mn} matches all nonspacing combining marks (diacritics, small signs, etc.)
  return text.replace(/\p{Mn}/gu, '');
}

/** Normalize Arabic text to a canonical consonantal skeleton. */
export function normalizeArabic(text: string): string {
  let t = text;
  // Alef variants → bare alef
  t = t.replace(/\u0671/g, '\u0627'); // alef wasla
  t = t.replace(/\u0623/g, '\u0627'); // alef + hamza above
  t = t.replace(/\u0625/g, '\u0627'); // alef + hamza below
  t = t.replace(/\u0622/g, '\u0627'); // alef + madda
  // Alef maqsura → ya
  t = t.replace(/\u0649/g, '\u064A');
  // Remove tatweel
  t = t.replace(/\u0640/g, '');
  // Strip all combining marks (diacritics, Quranic small signs, etc.)
  t = stripCombiningMarks(t);
  return t;
}

/** Check if a character is an Arabic letter (base range). */
export function isArabicChar(ch: string): boolean {
  const code = ch.charCodeAt(0);
  return (code >= 0x0621 && code <= 0x064A) || code === 0x0671;
}

/** Check if a string contains any Arabic characters. */
export function hasArabic(text: string): boolean {
  return /[\u0621-\u064A\u0671]/.test(text);
}

/**
 * Tokenize Arabic text into words.
 * Splits on whitespace + common punctuation, returns non-empty tokens.
 */
export function tokenizeArabic(text: string): string[] {
  return text.split(/[\s\u00A0\u200B-\u200F\u2028\u2029]+/).filter(Boolean);
}
