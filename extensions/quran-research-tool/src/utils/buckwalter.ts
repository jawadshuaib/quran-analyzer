/**
 * Root-name → Buckwalter conversion, ported from the main site
 * (roots/frontend/src/utils/buckwalter.ts + VerseRefText.tsx). The site's
 * /root/<key> route and /api/root/<key> endpoint are keyed by normalized
 * Buckwalter, so any root link the popup opens must convert first.
 */

/** Arabic Unicode → Buckwalter transliteration mapping (base letters only). */
const ARABIC_TO_BUCKWALTER: Record<string, string> = {
  'ء': "'", // hamza
  'آ': '|', // alef with madda
  'أ': '>', // alef with hamza above
  'ؤ': '&', // waw with hamza
  'إ': '<', // alef with hamza below
  'ئ': '}', // ya with hamza
  'ا': 'A', // alef
  'ب': 'b', // ba
  'ة': 'p', // ta marbuta
  'ت': 't', // ta
  'ث': 'v', // tha
  'ج': 'j', // jeem
  'ح': 'H', // ha
  'خ': 'x', // kha
  'د': 'd', // dal
  'ذ': '*', // thal
  'ر': 'r', // ra
  'ز': 'z', // zay
  'س': 's', // seen
  'ش': '$', // sheen
  'ص': 'S', // sad
  'ض': 'D', // dad
  'ط': 'T', // ta (emphatic)
  'ظ': 'Z', // za (emphatic)
  'ع': 'E', // ain
  'غ': 'g', // ghain
  'ف': 'f', // fa
  'ق': 'q', // qaf
  'ك': 'k', // kaf
  'ل': 'l', // lam
  'م': 'm', // meem
  'ن': 'n', // noon
  'ه': 'h', // ha
  'و': 'w', // waw
  'ى': 'Y', // alef maksura
  'ي': 'y', // ya
  'ٱ': '{', // alef wasla
};

/**
 * Normalize hamza variants to base consonants for root lookup.
 * Quranic roots are stored with plain forms (A, w, y) not hamza carriers.
 */
const ROOT_NORMALIZE: Record<string, string> = {
  '>': 'A', // alef with hamza above → plain alef
  '<': 'A', // alef with hamza below → plain alef
  '|': 'A', // alef with madda → plain alef
  '{': 'A', // alef wasla → plain alef
  "'": 'A', // standalone hamza → plain alef
  '&': 'w', // waw with hamza → plain waw
  '}': 'y', // ya with hamza → plain ya
};

/** Convert Arabic root letters to normalized Buckwalter suitable for DB lookup. */
export function arabicRootToBuckwalter(arabic: string): string {
  return Array.from(arabic)
    .map((ch) => ARABIC_TO_BUCKWALTER[ch] ?? ch)
    .map((ch) => ROOT_NORMALIZE[ch] ?? ch)
    .join('');
}

// Latin/transliterated triliteral roots written hyphenated, e.g. "f-l-q",
// "kh-sh-ʿ", "ʾ-m-n", "ṭ-gh-y". The exegesis notes name roots this way,
// whereas the grammar/translation notes use spaced Arabic letters.
// Each unit is a consonant (or alif "a" / hamza "ʾ"); 3–4 units joined by "-".
const TRANSLIT_UNIT = '(?:th|kh|dh|sh|gh|ḥ|ṣ|ḍ|ṭ|ẓ|ʿ|ʾ|a|[btjdrzsfqklmnhwy])';
export const LATIN_ROOT_RE = new RegExp(`${TRANSLIT_UNIT}(?:-${TRANSLIT_UNIT}){2,3}`, 'g');
// A char that, adjacent to a candidate, marks it as part of a larger Latin word
// (so not an isolated root): Latin letters incl. macrons/dots, the hamza/ʿayn
// modifier letters, and the hyphen.
export const TRANSLIT_BOUNDARY_RE = /[A-Za-zÀ-ɏḀ-ỿʾʿ-]/;
// Transliteration unit → normalized Buckwalter. Mirrors arabicRootToBuckwalter:
// hamza "ʾ" and alif "a" both normalize to "A"; ʿayn → E; emphatics → caps;
// digraphs th/kh/dh/sh/gh → v/x/*/$/g.
const TRANSLIT_TO_BW: Record<string, string> = {
  th: 'v', kh: 'x', dh: '*', sh: '$', gh: 'g',
  'ḥ': 'H', 'ṣ': 'S', 'ḍ': 'D', 'ṭ': 'T', 'ẓ': 'Z', 'ʿ': 'E', 'ʾ': 'A', a: 'A',
  b: 'b', t: 't', j: 'j', d: 'd', r: 'r', z: 'z', s: 's',
  f: 'f', q: 'q', k: 'k', l: 'l', m: 'm', n: 'n', h: 'h', w: 'w', y: 'y',
};

/** Map a hyphenated transliterated root ("f-l-q") to normalized Buckwalter
 * ("flq"), or null if any unit isn't a known consonant (so it isn't a root). */
export function translitRootToBuckwalter(token: string): string | null {
  let bw = '';
  for (const unit of token.split('-')) {
    const c = TRANSLIT_TO_BW[unit];
    if (c === undefined) return null;
    bw += c;
  }
  return bw;
}
