/** Arabic Unicode → Buckwalter transliteration mapping (base letters only). */
const ARABIC_TO_BUCKWALTER: Record<string, string> = {
  '\u0621': "'", // hamza
  '\u0622': '|', // alef with madda
  '\u0623': '>', // alef with hamza above
  '\u0624': '&', // waw with hamza
  '\u0625': '<', // alef with hamza below
  '\u0626': '}', // ya with hamza
  '\u0627': 'A', // alef
  '\u0628': 'b', // ba
  '\u0629': 'p', // ta marbuta
  '\u062A': 't', // ta
  '\u062B': 'v', // tha
  '\u062C': 'j', // jeem
  '\u062D': 'H', // ha
  '\u062E': 'x', // kha
  '\u062F': 'd', // dal
  '\u0630': '*', // thal
  '\u0631': 'r', // ra
  '\u0632': 'z', // zay
  '\u0633': 's', // seen
  '\u0634': '$', // sheen
  '\u0635': 'S', // sad
  '\u0636': 'D', // dad
  '\u0637': 'T', // ta (emphatic)
  '\u0638': 'Z', // za (emphatic)
  '\u0639': 'E', // ain
  '\u063A': 'g', // ghain
  '\u0641': 'f', // fa
  '\u0642': 'q', // qaf
  '\u0643': 'k', // kaf
  '\u0644': 'l', // lam
  '\u0645': 'm', // meem
  '\u0646': 'n', // noon
  '\u0647': 'h', // ha
  '\u0648': 'w', // waw
  '\u0649': 'Y', // alef maksura
  '\u064A': 'y', // ya
  '\u0671': '{', // alef wasla
};

/** Buckwalter transliteration → Arabic Unicode mapping (letters + common vowel/mark symbols). */
const BUCKWALTER_TO_ARABIC: Record<string, string> = {
  "'": '\u0621', // hamza
  '|': '\u0622', // alef with madda
  '>': '\u0623', // alef with hamza above
  '&': '\u0624', // waw with hamza
  '<': '\u0625', // alef with hamza below
  '}': '\u0626', // ya with hamza
  'A': '\u0627', // alef
  'b': '\u0628', // ba
  'p': '\u0629', // ta marbuta
  't': '\u062A', // ta
  'v': '\u062B', // tha
  'j': '\u062C', // jeem
  'H': '\u062D', // ha
  'x': '\u062E', // kha
  'd': '\u062F', // dal
  '*': '\u0630', // thal
  'r': '\u0631', // ra
  'z': '\u0632', // zay
  's': '\u0633', // seen
  '$': '\u0634', // sheen
  'S': '\u0635', // sad
  'D': '\u0636', // dad
  'T': '\u0637', // ta (emphatic)
  'Z': '\u0638', // za (emphatic)
  'E': '\u0639', // ain
  'g': '\u063A', // ghain
  'f': '\u0641', // fa
  'q': '\u0642', // qaf
  'k': '\u0643', // kaf
  'l': '\u0644', // lam
  'm': '\u0645', // meem
  'n': '\u0646', // noon
  'h': '\u0647', // ha
  'w': '\u0648', // waw
  'Y': '\u0649', // alef maksura
  'y': '\u064A', // ya
  '{': '\u0671', // alef wasla
  'a': '\u064E', // fatha
  'u': '\u064F', // damma
  'i': '\u0650', // kasra
  'o': '\u0652', // sukun
  '~': '\u0651', // shadda
  '`': '\u0670', // superscript alef
  'F': '\u064B', // fathatan
  'N': '\u064C', // dammatan
  'K': '\u064D', // kasratan
  '^': '\u0654', // hamza above
};

/** Convert Arabic Unicode characters to Buckwalter transliteration. */
export function arabicToBuckwalter(arabic: string): string {
  return Array.from(arabic)
    .map((ch) => ARABIC_TO_BUCKWALTER[ch] ?? ch)
    .join('');
}

/**
 * Normalize hamza variants to base consonants for root lookup.
 * Quranic roots are stored with plain forms (A, w, y) not hamza carriers (>, <, |, &, }, ').
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
  const raw = arabicToBuckwalter(arabic);
  return Array.from(raw)
    .map((ch) => ROOT_NORMALIZE[ch] ?? ch)
    .join('');
}

/** Convert Buckwalter transliteration to Arabic script (best-effort, unknown chars preserved). */
export function buckwalterToArabic(bw: string): string {
  return Array.from(bw || '')
    .map((ch) => BUCKWALTER_TO_ARABIC[ch] ?? ch)
    .join('');
}

/** Convert Buckwalter root to spaced Arabic root letters for root-tooltip detection (e.g. "Aty" -> "ا ت ي"). */
export function buckwalterRootToArabicSpaced(rootBw: string): string {
  const normalized = Array.from(rootBw || '')
    .map((ch) => ROOT_NORMALIZE[ch] ?? ch)
    .join('');
  const lettersOnly = normalized.replace(/[^A-Za-z<>\|&}'\{\$]/g, '');
  const arabic = buckwalterToArabic(lettersOnly);
  return Array.from(arabic).join(' ');
}
