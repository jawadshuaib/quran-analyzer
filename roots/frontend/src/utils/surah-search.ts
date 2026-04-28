/**
 * Surah-name matching for the unified search bar.
 *
 * Matches a typed query against every surah's English name, Arabic
 * name, and short English meaning ("The Opening", "The Cow", etc.).
 * Tolerant of:
 *   - case
 *   - leading "Surah " / "Sura " / "سورة "
 *   - leading article prefixes (Al-, Ar-, Ash-, At-, …, ال)
 *   - hyphens / apostrophes / curly quotes / whitespace
 *   - Latin diacritics (Faatiha → fatiha)
 *   - Arabic diacritics on input (الرحمن with or without harakat)
 *   - typos within a small edit-distance budget (Fatiah / Fati'ah →
 *     Al-Fatihah)
 *
 * Returns ranked matches: exact > prefix > substring > fuzzy.
 *
 * The list of surahs is fetched once via /api/surahs and cached for
 * the rest of the session, so matching is synchronous and instant
 * after the first lookup. Results live in the unified search state
 * alongside roots / semantic results.
 */

import type { SurahInfo } from '../types';
import { fetchSurahs } from '../api/quran';

export interface SurahMatch {
  number: number;
  name: string;
  name_arabic: string;
  meaning: string;
  /** Which field produced the match — for showing the user why this
   *  surah came up when they typed the meaning rather than the name. */
  matched_field: 'name' | 'arabic' | 'meaning';
  /** Lower is better. 0 = exact, 1 = prefix, 2 = substring,
   *  3+ = fuzzy (3 + edit distance). */
  score: number;
}

let cached: SurahInfo[] | null = null;
let inflight: Promise<SurahInfo[]> | null = null;

/** Fetch the surah list once and cache. Subsequent calls are instant. */
export function getSurahsForSearch(): Promise<SurahInfo[]> {
  if (cached) return Promise.resolve(cached);
  if (inflight) return inflight;
  inflight = fetchSurahs()
    .then((s) => {
      cached = s;
      return s;
    })
    .catch((e) => {
      inflight = null; // allow retry next time
      throw e;
    });
  return inflight;
}

/** Normalize text for tolerant matching. Same function applied to
 *  both the query and the surah-side fields. */
function normalize(s: string): string {
  if (!s) return '';
  return s
    .toLowerCase()
    // Strip Latin diacritics: NFD then remove combining marks
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    // Strip Arabic diacritics (harakat) + superscript alef + alef wasla
    .replace(/[ً-ْٰٱ]/g, '')
    // Strip leading "Surah " / "Sura " / Arabic سورة
    .replace(/^(surah?|سورة|سوره)[\s_-]+/, '')
    // Strip leading article prefixes — both Latin and Arabic.
    // We do this BEFORE removing whitespace/hyphens so we can match
    // word-boundaries cleanly.
    .replace(/^(al|ar|as|at|an|ash|ath|az|adh|ad)[-\s]/, '')
    .replace(/^ال/, '')
    // Strip everything that's just punctuation/space — apostrophes and
    // ʿ / ʾ (ayn / hamza marks in transliteration), hyphens, en/em
    // dashes, smart quotes, regular and non-breaking spaces.
    .replace(/[\s \-‐-―'‘’ʻ-ʿʿʾ]/g, '')
    .trim();
}

/** Phonetic-class substitutions for common Arabic-to-Latin
 *  transliteration variation. Each rule maps a digraph (or short
 *  cluster) to a set of alternatives a non-specialist transliterator
 *  might pick. Real-world examples we want to catch:
 *
 *    Al-Kawthar / Al-Kawsar / Al-Kausar / Al-Kowsar / Al-Kawser
 *    Adh-Dhariyat / Adh-Zariyat / Az-Zariyat
 *    Al-Khidr / Al-Kidr / Al-Hidr
 *    Al-Ghashiyah / Al-Gashiyah
 *    Quraysh / Kuraysh / Kuraish
 *    Yusuf / Yousuf / Yousef / Joseph
 *
 *  Each rule independently fans out the variant set; combinatorial
 *  growth is bounded because most names contain at most one digraph.
 *  We cap at MAX_VARIANTS per name to avoid pathological blowup on
 *  hypothetical names with many overlapping clusters. */
const DIGRAPH_RULES: Array<{ from: string; alts: string[] }> = [
  // ث: thaa — Indo-Pak transliterations often write 's' or 't'
  { from: 'th', alts: ['th', 's', 't', 'z'] },
  // ذ: dhaal
  { from: 'dh', alts: ['dh', 'd', 'z', 'j'] },
  // خ: khaa
  { from: 'kh', alts: ['kh', 'k', 'h', 'ch'] },
  // غ: ghain
  { from: 'gh', alts: ['gh', 'g', 'q'] },
  // ش: shiin — usually consistent, but Persian/Pashto sometimes ch
  { from: 'sh', alts: ['sh', 's', 'ch'] },
  // English Anglicizations
  { from: 'ph', alts: ['ph', 'f'] },
  { from: 'ck', alts: ['ck', 'k'] },
];

/** Single-letter phonetic equivalents that don't form digraphs.
 *  Applied AFTER digraph expansion so we don't accidentally split
 *  digraphs like 'th' by re-mapping its 't'. */
const SINGLE_LETTER_RULES: Array<{ from: string; alts: string[] }> = [
  // ق: qaaf — very commonly written as 'k' by non-specialists
  { from: 'q', alts: ['q', 'k', 'g'] },
];

const MAX_VARIANTS = 32;

function applyRules(
  variants: Set<string>,
  rules: Array<{ from: string; alts: string[] }>,
): Set<string> {
  for (const rule of rules) {
    if (variants.size >= MAX_VARIANTS) break;
    if (rule.alts.length <= 1) continue;
    const next = new Set<string>();
    for (const v of variants) {
      if (!v.includes(rule.from)) {
        next.add(v);
        continue;
      }
      for (const alt of rule.alts) {
        next.add(v.split(rule.from).join(alt));
        if (next.size >= MAX_VARIANTS) break;
      }
      if (next.size >= MAX_VARIANTS) break;
    }
    variants = next;
  }
  return variants;
}

/** Generate phonetic-variant set for a normalized name.
 *  Always includes the original; variants are bounded. */
function phoneticVariants(normalized: string): string[] {
  if (!normalized) return [];
  let set: Set<string> = new Set([normalized]);
  set = applyRules(set, DIGRAPH_RULES);
  set = applyRules(set, SINGLE_LETTER_RULES);
  return Array.from(set);
}

// Module-level cache of pre-computed variants per surah number.
// Computed once on first matchSurahs call after the list is loaded.
const variantCache = new Map<number, string[]>();

/** Levenshtein edit distance between two strings, capped to maxOk+1
 *  for early exit. Returns +Infinity if it would exceed the cap.
 *
 *  Plain dynamic programming, O(n*m) — fine for short surah names
 *  (≤ 25 chars) and 114 surahs (~3000 cells worst case). Inlined
 *  rather than pulled in as a dep. */
function editDistance(a: string, b: string, maxOk: number): number {
  if (a === b) return 0;
  if (Math.abs(a.length - b.length) > maxOk) return Infinity;
  const m = a.length, n = b.length;
  if (m === 0) return n <= maxOk ? n : Infinity;
  if (n === 0) return m <= maxOk ? m : Infinity;
  let prev = new Array(n + 1);
  let curr = new Array(n + 1);
  for (let j = 0; j <= n; j++) prev[j] = j;
  for (let i = 1; i <= m; i++) {
    curr[0] = i;
    let rowMin = curr[0];
    for (let j = 1; j <= n; j++) {
      const cost = a.charCodeAt(i - 1) === b.charCodeAt(j - 1) ? 0 : 1;
      curr[j] = Math.min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost);
      if (curr[j] < rowMin) rowMin = curr[j];
    }
    if (rowMin > maxOk) return Infinity;
    [prev, curr] = [curr, prev];
  }
  return prev[n];
}

/** Match a query against the surah list. Returns up to `limit` matches
 *  ordered best-first. Caller passes the cached list explicitly so the
 *  hook can avoid awaiting on every keystroke. */
export function matchSurahs(
  rawQuery: string,
  surahs: SurahInfo[] | null,
  limit = 6,
): SurahMatch[] {
  if (!surahs || surahs.length === 0) return [];
  const q = normalize(rawQuery);
  // 2 chars min — anything shorter ("a", "i") matches everything.
  if (q.length < 2) return [];

  type Candidate = SurahMatch;
  const candidates: Candidate[] = [];

  // Edit-distance budget scales with query length. ~1 typo per 3
  // characters (capped at 3 total). At length 6 — typical for short
  // surah names — this allows 2 edits, which is what catches double
  // phonetic variations like "yousef" → "yusuf" (insert + substitute)
  // without exploding the false-positive rate on shorter queries.
  const editBudget = Math.max(1, Math.min(3, Math.floor(q.length / 3)));

  for (const s of surahs) {
    // Get-or-build phonetic variants for the English name. The Arabic
    // name and meaning don't get phonetic expansion — those match
    // directly because Latin-letter variation doesn't apply to them.
    let nameVariants = variantCache.get(s.number);
    if (!nameVariants) {
      nameVariants = phoneticVariants(normalize(s.name));
      variantCache.set(s.number, nameVariants);
    }

    let best: { score: number; field: 'name' | 'arabic' | 'meaning' } | null = null;

    // Score against each phonetic variant of the English name + the
    // Arabic name + the meaning.
    type Candidate = { text: string; field: 'name' | 'arabic' | 'meaning' };
    const fields: Candidate[] = [
      ...nameVariants.map((v): Candidate => ({ text: v, field: 'name' })),
      { text: normalize(s.name_arabic || ''), field: 'arabic' },
      { text: normalize(s.meaning || ''), field: 'meaning' },
    ];

    for (const { text: t, field } of fields) {
      if (!t) continue;
      let score: number | null = null;
      if (t === q) score = 0;
      else if (t.startsWith(q)) score = 1;
      else if (t.includes(q)) score = 2;
      else {
        const ed = editDistance(q, t, editBudget);
        if (ed <= editBudget) score = 3 + ed;
      }
      if (score !== null && (best === null || score < best.score)) {
        best = { score, field };
      }
    }
    if (best !== null) {
      candidates.push({
        number: s.number,
        name: s.name,
        name_arabic: s.name_arabic || '',
        meaning: s.meaning || '',
        matched_field: best.field,
        score: best.score,
      });
    }
  }

  candidates.sort((a, b) => a.score - b.score || a.number - b.number);
  return candidates.slice(0, limit);
}
