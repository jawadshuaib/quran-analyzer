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

/** Convert Arabic Unicode characters to Buckwalter transliteration. */
export function arabicToBuckwalter(arabic: string): string {
  return Array.from(arabic)
    .map((ch) => ARABIC_TO_BUCKWALTER[ch] ?? ch)
    .join('');
}
