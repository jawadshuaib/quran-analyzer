/** A reader's guide to one classical dictionary shown in the site's
 *  "Classical Dictionaries" panel (/classical-dictionaries/<slug>).
 *
 *  The prose fields (`lede`, `body`, `onOurSite`) use the small markup set out
 *  in docs/research/dictionary-guides/FORMAT.md and rendered by
 *  components/DictionaryGuideProse.tsx. `npm run validate:guides` checks every
 *  guide against the live dictionaries API: root links, quoted excerpts,
 *  citations. */

export interface GuideSource {
  /** Cited in the prose as [^id] or [^id|locator]. */
  id: string;
  /** Full reference as the reader sees it in the source list. May use *italic*. */
  citation: string;
  /** A working link that was actually opened while writing or verifying. */
  url?: string;
  kind: 'primary' | 'edition' | 'scholarship' | 'reference' | 'site';
}

export interface DictionaryGuide {
  /** Route segment: /classical-dictionaries/<slug>. Matches the file name. */
  slug: string;
  /** The `dictionaries.slug` value(s) this page explains (usually one). */
  dictionarySlugs: string[];
  /** Recognisable transliterated title, e.g. "Maqāyīs al-Lugha". */
  title: string;
  /** Arabic title — only when verified. */
  titleAr?: string;
  /** English rendering of the title, when it means something ("The Standards of Language"). */
  titleGloss?: string;
  /** Display author line, e.g. "Ibn Fāris" or "Attributed to ʿAbdullāh ibn ʿAbbās". */
  author: string;
  authorFull?: string;
  authorAr?: string;
  /** Concise date or period, e.g. "d. 395 AH / 1004–5 CE" or "compiled c. 10th century". */
  period: string;
  /** Approximate CE year used only to order the overview page. */
  sortYear: number;
  /** Short descriptor shown above the title, e.g. "Root-meaning dictionary". */
  kind: string;
  /** Overview-card description (≤ 45 words). Says what the work is useful for; never ranks it. */
  summary: string;
  /** Opening paragraph: what is distinctive about the work. */
  lede: string;
  /** The essay. */
  body: string;
  /** What al-nuqta actually displays for this work, and from which text. */
  onOurSite: string;
  sources: GuideSource[];
  /** Present when the account is deliberately short because reliable information is limited. */
  limitedEvidence?: string;
  /** Date of the last completed independent verification (YYYY-MM-DD). */
  lastVerified?: string;
}
