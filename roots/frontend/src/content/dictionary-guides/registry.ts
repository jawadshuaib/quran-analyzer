/** Which guide explains which dictionary. Kept apart from the guides
 *  themselves so the dictionary panel on root and word pages can link to a
 *  guide without pulling every essay into the main bundle.
 *
 *  Keys are `dictionaries.slug` (the identity used by dictionary_entries and
 *  the /api/root/<bw>/dictionaries payload); values are guide slugs, the route
 *  segment of /classical-dictionaries/<slug>. backend/dictionary_guides_meta.py
 *  mirrors the guide titles for server-rendered SEO — keep the two in step. */

export const GUIDE_BASE_PATH = '/classical-dictionaries';

export const GUIDE_SLUG_BY_DICTIONARY: Record<string, string> = {
  'abdullah-ibn-abbas-gharib-al-quran-fi-shir-al-arab': 'gharib-al-quran-fi-shir-al-arab',
  'al-khalil-b-ahmad-al-farahidi-kitab-al-ain': 'kitab-al-ayn',
  'al-sahib-bin-abbad-al-muhit-fi-l-lugha': 'al-muhit-fi-l-lugha',
  'ismail-bin-hammad-al-jawhari-taj-al-lugha-wa-sihah-al-arabiya': 'al-sihah',
  'ibn-faris-maqayis-al-lugha': 'maqayis-al-lugha',
  'ibn-sida-al-mursi-al-muhkam-wa-l-muhit-al-aazam': 'al-muhkam',
  'al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran': 'al-mufradat',
  'al-zamakhshari-asas-al-balagha': 'asas-al-balagha',
  'zayn-al-din-al-razi-mukhtar-al-sihah': 'mukhtar-al-sihah',
  'ibn-manzur-lisan-al-arab': 'lisan-al-arab',
  'abu-hayyan-al-gharnati-tuhfat-al-arib-bi-ma-fi-l-quran-min-al-gharib': 'tuhfat-al-arib',
  'al-fayyumi-al-misbah-al-munir-fi-gharib-al-sharh-al-kabir': 'al-misbah-al-munir',
  'firuzabadi-al-qamus-al-muhit': 'al-qamus-al-muhit',
  'murtada-al-zabidi-taj-al-arus-fi-jawahir-al-qamus': 'taj-al-arus',
  'william-edward-lane-arabic-english-lexicon': 'lane-lexicon',
  'habib-anthony-salmone-an-advanced-learners-arabic-english-dictionary': 'salmone-dictionary',
};

/** Names as the dictionary panel shows them — for link titles and excerpt
 *  captions, where loading the other guide just for its title isn't worth it. */
export const DICTIONARY_LABELS: Record<string, string> = {
  'abdullah-ibn-abbas-gharib-al-quran-fi-shir-al-arab': 'Gharīb al-Qurʾān fī Shiʿr al-ʿArab',
  'al-khalil-b-ahmad-al-farahidi-kitab-al-ain': 'Kitāb al-ʿAyn',
  'al-sahib-bin-abbad-al-muhit-fi-l-lugha': 'al-Muḥīṭ fī l-Lugha',
  'ismail-bin-hammad-al-jawhari-taj-al-lugha-wa-sihah-al-arabiya': 'al-Ṣiḥāḥ',
  'ibn-faris-maqayis-al-lugha': 'Maqāyīs al-Lugha',
  'ibn-sida-al-mursi-al-muhkam-wa-l-muhit-al-aazam': 'al-Muḥkam',
  'al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran': 'al-Mufradāt',
  'al-zamakhshari-asas-al-balagha': 'Asās al-Balāgha',
  'zayn-al-din-al-razi-mukhtar-al-sihah': 'Mukhtār al-Ṣiḥāḥ',
  'ibn-manzur-lisan-al-arab': 'Lisān al-ʿArab',
  'abu-hayyan-al-gharnati-tuhfat-al-arib-bi-ma-fi-l-quran-min-al-gharib': 'Tuḥfat al-Arīb',
  'al-fayyumi-al-misbah-al-munir-fi-gharib-al-sharh-al-kabir': 'al-Miṣbāḥ al-Munīr',
  'firuzabadi-al-qamus-al-muhit': 'al-Qāmūs al-Muḥīṭ',
  'murtada-al-zabidi-taj-al-arus-fi-jawahir-al-qamus': 'Tāj al-ʿArūs',
  'william-edward-lane-arabic-english-lexicon': "Lane's Lexicon",
  'habib-anthony-salmone-an-advanced-learners-arabic-english-dictionary': "Salmoné's dictionary",
};

export const GUIDE_SLUGS: string[] = Array.from(new Set(Object.values(GUIDE_SLUG_BY_DICTIONARY)));

/** Guide slug → the dictionary it explains (first one, when a guide covers several). */
export const DICTIONARY_BY_GUIDE: Record<string, string> = Object.fromEntries(
  Object.entries(GUIDE_SLUG_BY_DICTIONARY).map(([d, g]) => [g, d]).reverse(),
);

export function guidePath(guideSlug: string): string {
  return `${GUIDE_BASE_PATH}/${guideSlug}`;
}

export function guidePathForDictionary(dictionarySlug: string): string | null {
  const g = GUIDE_SLUG_BY_DICTIONARY[dictionarySlug];
  return g ? guidePath(g) : null;
}

/** Hash on a root page that opens one dictionary's entry and scrolls to it. */
export function dictionaryEntryHash(dictionarySlug: string): string {
  return `dict-${dictionarySlug}`;
}

/** /root/<bw>#dict-<slug> — relative, so it works on any host. */
export function rootDictionaryEntryUrl(rootBw: string, dictionarySlug: string): string {
  return `/root/${encodeURIComponent(rootBw)}#${dictionaryEntryHash(dictionarySlug)}`;
}
