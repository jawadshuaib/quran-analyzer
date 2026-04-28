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

  // Edit-distance budget scales with query length so a 4-letter query
  // tolerates 1 typo, a 12-letter query tolerates up to 3.
  const editBudget = Math.max(1, Math.min(3, Math.floor(q.length / 4)));

  for (const s of surahs) {
    const fields: Array<[string, 'name' | 'arabic' | 'meaning']> = [
      [s.name, 'name'],
      [s.name_arabic || '', 'arabic'],
      [s.meaning || '', 'meaning'],
    ];
    let best: { score: number; field: 'name' | 'arabic' | 'meaning' } | null = null;
    for (const [text, field] of fields) {
      const t = normalize(text);
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
