import { useState, useRef, useCallback, useEffect } from 'react';
import { createPortal } from 'react-dom';
import type { RootDetailData, Word } from '../types';
import { fetchVerse, fetchRoot } from '../api/quran';
import { arabicRootToBuckwalter } from '../utils/buckwalter';
import { verseUrl, ejtaalUrl } from '../utils/urls';
import { wrapArabicRuns } from '../utils/arabic-runs';
import { viewportSize } from '../utils/viewport';

/** Shared viewport-clamped placement for these hover tooltips — fixed
 *  positioning (escapes any overflow-hidden ancestor) below the trigger,
 *  flipped above if there's no room, and clamped so it can never sit off
 *  either edge. Was `absolute` + `-translate-x-1/2` centered on the trigger
 *  with no clamping at all, which ran a verse-range tooltip off the right
 *  edge next to a ref near the end of a line. Recomputes on scroll/resize so
 *  it tracks the trigger, and again whenever the tooltip's own content
 *  changes size (e.g. a loading spinner resolving to a multi-verse list). */
function useTooltipPosition(
  open: boolean,
  triggerRef: React.RefObject<HTMLElement | null>,
  tipRef: React.RefObject<HTMLElement | null>,
  width: number,
  contentKey: unknown,
) {
  const [pos, setPos] = useState<{ left: number; top: number } | null>(null);
  const GAP = 8;

  useEffect(() => {
    if (!open) {
      setPos(null);
      return;
    }
    function place() {
      const trigger = triggerRef.current;
      if (!trigger) return;
      const rect = trigger.getBoundingClientRect();
      const tipH = tipRef.current?.getBoundingClientRect().height ?? 160;
      const { width: viewportW, height: viewportH } = viewportSize();

      const below = rect.bottom + GAP;
      const top =
        below + tipH > viewportH - GAP ? Math.max(GAP, rect.top - tipH - GAP) : below;
      const center = rect.left + rect.width / 2;
      const left = Math.max(GAP, Math.min(center - width / 2, viewportW - width - GAP));
      setPos({ left, top });
    }
    place();
    window.addEventListener('scroll', place, true);
    window.addEventListener('resize', place);
    return () => {
      window.removeEventListener('scroll', place, true);
      window.removeEventListener('resize', place);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, contentKey]);

  return pos;
}

interface Props {
  text: string;
  className?: string;
  disableVerseNavigation?: boolean;
  /** Buckwalter root/lemma this text is "about" (a root page's own root, a
   *  word page's own lemma). When a verse-ref tooltip opens, the word in that
   *  verse carrying this root/lemma is highlighted — the point of pausing on
   *  "2:73" is usually to see the matching word, and long verses make that
   *  hard to spot unaided. Either or both may be given; a word matches on
   *  lemma OR root. */
  highlightRootBw?: string;
  highlightLemmaBw?: string;
}

interface CachedVerse {
  surah: number;
  ayah: number;
  text_uthmani: string;
  translation: string;
  words: Word[];
}

/** Word positions (1-indexed) in `words` whose lemma or root matches. Lemma
 *  and root are checked independently (either counts) since a caller may only
 *  have one — a root page knows its root but not which lemma is cited, a word
 *  page knows both its own lemma and root. */
function matchedWordPositions(words: Word[], rootBw?: string, lemmaBw?: string): Set<number> {
  const positions = new Set<number>();
  if (!rootBw && !lemmaBw) return positions;
  for (const w of words) {
    const hit = w.segments.some(
      (s) => (lemmaBw && s.lemma_buckwalter === lemmaBw) || (rootBw && s.root_buckwalter === rootBw),
    );
    if (hit) positions.add(w.position);
  }
  return positions;
}

// Matches "56:74" or "96:1–4" / "96:1-4" (en-dash or hyphen range)
const VERSE_REF_RE = /(\d{1,3}:\d{1,3}(?:[–\-]\d{1,3})?)/g;

// Matches spaced Arabic root letters like "ر ح م" or dash-separated like "ع-ب-د"
// (2–5 base Arabic letters separated by spaces or dashes).
// The boundary check in the matching loop ensures these aren't part of full Arabic words.
const ARABIC_ROOT_RE = /([\u0621-\u064A][ \-][\u0621-\u064A](?:[ \-][\u0621-\u064A]){0,3})/g;

// Latin/transliterated triliteral roots written hyphenated, e.g. "f-l-q",
// "kh-sh-\u02BF", "\u02BE-m-n", "\u1E6D-gh-y". The exegesis notes name roots this way, whereas
// the grammar/translation notes use spaced Arabic letters (ARABIC_ROOT_RE).
// Each unit is a consonant (or alif "a" / hamza "\u02BE"); 3\u20134 units joined by "-".
// Requiring every unit to be a consonant cleanly excludes the vowel-bearing
// Arabic fragments the notes also hyphenate ("wa-m\u0101", "bi-l", "fa-l\u0101", "a-fa").
const TRANSLIT_UNIT = '(?:th|kh|dh|sh|gh|\u1E25|\u1E63|\u1E0D|\u1E6D|\u1E93|\u02BF|\u02BE|a|[btjdrzsfqklmnhwy])';
const LATIN_ROOT_RE = new RegExp(`${TRANSLIT_UNIT}(?:-${TRANSLIT_UNIT}){2,3}`, 'g');
// A char that, adjacent to a candidate, marks it as part of a larger Latin word
// (so not an isolated root): Latin letters incl. macrons/dots, the hamza/\u02BFayn
// modifier letters, and the hyphen.
const TRANSLIT_BOUNDARY_RE = /[A-Za-z\u00C0-\u024F\u1E00-\u1EFF\u02BE\u02BF-]/;
// Transliteration unit \u2192 normalized Buckwalter. Mirrors arabicRootToBuckwalter:
// hamza "\u02BE" and alif "a" both normalize to "A"; \u02BFayn \u2192 E; emphatics \u2192 caps;
// digraphs th/kh/dh/sh/gh \u2192 v/x/*/$/g.
const TRANSLIT_TO_BW: Record<string, string> = {
  th: 'v', kh: 'x', dh: '*', sh: '$', gh: 'g',
  '\u1E25': 'H', '\u1E63': 'S', '\u1E0D': 'D', '\u1E6D': 'T', '\u1E93': 'Z', '\u02BF': 'E', '\u02BE': 'A', a: 'A',
  b: 'b', t: 't', j: 'j', d: 'd', r: 'r', z: 'z', s: 's',
  f: 'f', q: 'q', k: 'k', l: 'l', m: 'm', n: 'n', h: 'h', w: 'w', y: 'y',
};

/** Map a hyphenated transliterated root ("f-l-q") to normalized Buckwalter
 * ("flq"), or null if any unit isn't a known consonant (so it isn't a root). */
function translitRootToBuckwalter(token: string): string | null {
  let bw = '';
  for (const unit of token.split('-')) {
    const c = TRANSLIT_TO_BW[unit];
    if (c === undefined) return null;
    bw += c;
  }
  return bw;
}

// Matches quoted strings: "..." or \u201C...\u201D (curly quotes)
const QUOTED_RE = /["\u201C][^"\u201D]+["\u201D]/g;

// Arabic base letters (\u0621-\u064A) and diacritics (\u064B-\u0652, \u0670 superscript alef, \u0671 alef wasla)
const ARABIC_CHAR_RE = /[\u0621-\u0652\u0670\u0671]/;

function parseRef(ref: string): { surah: number; startAyah: number; endAyah: number } {
  const [surah, rest] = ref.split(':');
  const parts = rest.split(/[–\-]/);
  const startAyah = Number(parts[0]);
  const endAyah = parts.length > 1 ? Number(parts[1]) : startAyah;
  return { surah: Number(surah), startAyah, endAyah };
}

// Shared cross-instance cache so repeated hovers don't re-fetch
const verseCache = new Map<string, CachedVerse>();

const VERSE_TIP_W_SINGLE = 300; // within the old min-w-220/max-w-360 range
const VERSE_TIP_W_RANGE = 340; // matches the old fixed range width

function VerseRefLink({
  verseRef,
  disableNavigation,
  highlightRootBw,
  highlightLemmaBw,
}: {
  verseRef: string;
  disableNavigation?: boolean;
  highlightRootBw?: string;
  highlightLemmaBw?: string;
}) {
  const { surah, startAyah, endAyah } = parseRef(verseRef);
  const isRange = endAyah > startAyah;
  const tipWidth = isRange ? VERSE_TIP_W_RANGE : VERSE_TIP_W_SINGLE;

  const [tooltip, setTooltip] = useState<{
    loading: boolean;
    verses: CachedVerse[];
    error: boolean;
  } | null>(null);

  const triggerRef = useRef<HTMLSpanElement>(null);
  const tipRef = useRef<HTMLDivElement>(null);
  const pos = useTooltipPosition(!!tooltip, triggerRef, tipRef, tipWidth, tooltip);

  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearHideTimer = useCallback(() => {
    if (hideTimer.current) {
      clearTimeout(hideTimer.current);
      hideTimer.current = null;
    }
  }, []);

  const handleMouseEnter = useCallback(async () => {
    clearHideTimer();

    // Check if all verses in range are already cached
    const allCached: CachedVerse[] = [];
    let allHit = true;
    for (let a = startAyah; a <= endAyah; a++) {
      const key = `${surah}:${a}`;
      if (verseCache.has(key)) {
        allCached.push(verseCache.get(key)!);
      } else {
        allHit = false;
        break;
      }
    }

    if (allHit) {
      setTooltip({ loading: false, verses: allCached, error: false });
      return;
    }

    setTooltip({ loading: true, verses: [], error: false });
    try {
      const promises: Promise<CachedVerse>[] = [];
      for (let a = startAyah; a <= endAyah; a++) {
        const key = `${surah}:${a}`;
        if (verseCache.has(key)) {
          promises.push(Promise.resolve(verseCache.get(key)!));
        } else {
          promises.push(
            fetchVerse(surah, a).then((data) => {
              const cached: CachedVerse = {
                surah,
                ayah: a,
                text_uthmani: data.text_uthmani,
                translation: data.translation,
                words: data.words,
              };
              verseCache.set(key, cached);
              return cached;
            }),
          );
        }
      }
      const verses = await Promise.all(promises);
      setTooltip({ loading: false, verses, error: false });
    } catch {
      setTooltip({ loading: false, verses: [], error: true });
    }
  }, [surah, startAyah, endAyah, clearHideTimer]);

  const handleMouseLeave = useCallback(() => {
    hideTimer.current = setTimeout(() => setTooltip(null), 200);
  }, []);

  useEffect(() => {
    return () => clearHideTimer();
  }, [clearHideTimer]);

  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      if (disableNavigation) return;
      window.open(verseUrl(surah, startAyah), '_blank');
    },
    [disableNavigation, surah, startAyah],
  );

  return (
    <span className="relative inline">
      <span
        ref={triggerRef}
        className="text-violet-600 underline decoration-violet-300 underline-offset-2 cursor-pointer hover:text-violet-800 hover:decoration-violet-500 transition-colors"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
        role="link"
        tabIndex={0}
      >
        {verseRef}
      </span>

      {tooltip &&
        pos &&
        createPortal(
          <div
            ref={tipRef}
            className="fixed z-50 bg-white rounded-lg shadow-lg border border-violet-200 p-3
                       text-sm text-stone-700"
            style={{ left: pos.left, top: pos.top, width: tipWidth }}
            onMouseEnter={clearHideTimer}
            onMouseLeave={handleMouseLeave}
          >
            {tooltip.loading ? (
              <div className="flex justify-center py-2">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-violet-200 border-t-violet-600" />
              </div>
            ) : tooltip.error ? (
              <div className="text-xs text-red-500 text-center">
                Could not load verse
              </div>
            ) : tooltip.verses.length > 0 ? (
              <div className="space-y-2 max-h-[400px] overflow-y-auto">
                {tooltip.verses.map((v) => {
                  const uthmaniWords = v.text_uthmani.split(/\s+/).filter(Boolean);
                  const matched = matchedWordPositions(v.words, highlightRootBw, highlightLemmaBw);
                  return (
                  <div
                    key={v.ayah}
                    className="rounded-md hover:bg-violet-50/50 transition-colors px-1 py-0.5 cursor-pointer"
                    onClick={(e) => {
                      e.stopPropagation();
                      window.open(verseUrl(v.surah, v.ayah), '_blank');
                    }}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-violet-600">
                        {v.surah}:{v.ayah}
                      </span>
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-3 w-3 text-violet-400"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                        <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
                      </svg>
                    </div>
                    <div
                      dir="rtl"
                      lang="ar"
                      className="font-arabic text-base leading-[2] text-stone-800 text-right"
                    >
                      {matched.size > 0
                        ? uthmaniWords.map((w, i) => (
                            <span
                              key={i}
                              className={
                                matched.has(i + 1)
                                  ? 'rounded bg-violet-100 px-0.5 text-violet-900'
                                  : undefined
                              }
                            >
                              {w}
                              {i < uthmaniWords.length - 1 ? ' ' : ''}
                            </span>
                          ))
                        : v.text_uthmani}
                    </div>
                    <div className="text-xs text-stone-500 italic leading-relaxed mt-0.5">
                      {v.translation}
                    </div>
                    {/* Divider between verses in a range (not after last) */}
                    {isRange && v.ayah !== endAyah && (
                      <div className="border-b border-violet-100 mt-2" />
                    )}
                  </div>
                  );
                })}
              </div>
            ) : null}
          </div>,
          document.body,
        )}
    </span>
  );
}

// Shared cache for root data so repeated hovers don't re-fetch
const rootCache = new Map<string, RootDetailData>();

const ROOT_TIP_W = 280; // within the old min-w-200/max-w-300 range

function RootRefLink({ rootText, buckwalter, latin = false }: { rootText: string; buckwalter?: string; latin?: boolean }) {
  const [tooltip, setTooltip] = useState<{
    loading: boolean;
    data: RootDetailData | null;
    error: boolean;
  } | null>(null);
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const triggerRef = useRef<HTMLSpanElement>(null);
  const tipRef = useRef<HTMLDivElement>(null);
  const pos = useTooltipPosition(!!tooltip, triggerRef, tipRef, ROOT_TIP_W, tooltip);

  // Arabic roots: convert spaced/dashed letters to normalized Buckwalter.
  // Transliterated roots (e.g. "f-l-q") arrive with their Buckwalter precomputed.
  const letters = rootText.replace(/[ \-]/g, '');
  const bw = buckwalter ?? arabicRootToBuckwalter(letters);
  const url = `/root/${encodeURIComponent(bw)}`;

  const clearTimer = useCallback(() => {
    if (hideTimer.current) {
      clearTimeout(hideTimer.current);
      hideTimer.current = null;
    }
  }, []);

  const handleMouseEnter = useCallback(async () => {
    clearTimer();

    if (rootCache.has(bw)) {
      setTooltip({ loading: false, data: rootCache.get(bw)!, error: false });
      return;
    }

    setTooltip({ loading: true, data: null, error: false });
    try {
      const result = await fetchRoot(bw);
      rootCache.set(bw, result);
      setTooltip({ loading: false, data: result, error: false });
    } catch {
      setTooltip({ loading: false, data: null, error: true });
    }
  }, [bw, clearTimer]);

  const handleMouseLeave = useCallback(() => {
    hideTimer.current = setTimeout(() => setTooltip(null), 200);
  }, []);

  useEffect(() => {
    return () => clearTimer();
  }, [clearTimer]);

  return (
    <span className="relative inline">
      <span
        ref={triggerRef}
        {...(latin ? {} : { dir: 'rtl', lang: 'ar' })}
        className={`${latin ? '' : 'font-arabic '}text-emerald-700 underline decoration-emerald-300 underline-offset-2 cursor-pointer hover:text-emerald-900 hover:decoration-emerald-500 transition-colors`}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={(e) => { e.preventDefault(); window.location.href = url; }}
        role="link"
        tabIndex={0}
      >
        {rootText}
      </span>

      {tooltip &&
        pos &&
        createPortal(
          <div
            ref={tipRef}
            className="fixed z-50 bg-white rounded-lg shadow-lg border border-emerald-200 p-3
                       text-sm text-stone-700"
            style={{ left: pos.left, top: pos.top, width: ROOT_TIP_W }}
            onMouseEnter={clearTimer}
            onMouseLeave={handleMouseLeave}
          >
            {tooltip.loading ? (
              <div className="flex justify-center py-2">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-600" />
              </div>
            ) : tooltip.error ? (
              <div className="text-xs text-red-500 text-center">
                Root not found
              </div>
            ) : tooltip.data ? (
              <div className="space-y-2">
                {/* Root header */}
                <div className="flex items-center gap-2">
                  <span dir="rtl" lang="ar" className="font-arabic text-lg text-stone-800">
                    {tooltip.data.root_arabic}
                  </span>
                  <span className="text-xs text-emerald-600 font-medium">({tooltip.data.root_buckwalter})</span>
                </div>
                <div className="text-xs text-stone-500">
                  Mentioned in {tooltip.data.total_occurrences} verse{tooltip.data.total_occurrences !== 1 ? 's' : ''}
                </div>

                {/* Lemmas */}
                {tooltip.data.lemmas.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {tooltip.data.lemmas.slice(0, 6).map((l) => (
                      <span
                        key={l.lemma_buckwalter}
                        dir="rtl"
                        lang="ar"
                        className="inline-block font-arabic text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full px-2 py-0.5"
                      >
                        {l.lemma_arabic}
                      </span>
                    ))}
                    {tooltip.data.lemmas.length > 6 && (
                      <span className="text-xs text-stone-400">+{tooltip.data.lemmas.length - 6} more</span>
                    )}
                  </div>
                )}

                {/* Link to root page */}
                <a
                  href={url}
                  className="flex items-center justify-center gap-1.5 w-full px-2 py-1.5 rounded-md
                             bg-emerald-50 text-emerald-600 hover:bg-emerald-100 hover:text-emerald-700
                             text-xs font-medium transition-colors"
                  onClick={(e) => e.stopPropagation()}
                >
                  View root page
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                    <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
                  </svg>
                </a>
                {/* Link to Arabic dictionary */}
                <a
                  href={ejtaalUrl(bw)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-1.5 w-full px-2 py-1.5 rounded-md
                             bg-amber-50 text-amber-600 hover:bg-amber-100 hover:text-amber-700
                             text-xs font-medium transition-colors mt-1.5"
                  onClick={(e) => e.stopPropagation()}
                >
                  Arabic Dictionary
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
                  </svg>
                </a>
              </div>
            ) : null}
          </div>,
          document.body,
        )}
    </span>
  );
}

export default function VerseRefText({
  text,
  className,
  disableVerseNavigation = false,
  highlightRootBw,
  highlightLemmaBw,
}: Props) {
  if (!text) return null;

  // Collect all matches (verse refs, root refs, quoted text) with their types
  const matches: { index: number; length: number; type: 'ref' | 'root' | 'quoted'; value: string; bw?: string; latin?: boolean }[] = [];

  VERSE_REF_RE.lastIndex = 0;
  let m: RegExpExecArray | null;
  while ((m = VERSE_REF_RE.exec(text)) !== null) {
    matches.push({ index: m.index, length: m[0].length, type: 'ref', value: m[1] });
  }

  ARABIC_ROOT_RE.lastIndex = 0;
  while ((m = ARABIC_ROOT_RE.exec(text)) !== null) {
    // Boundary check: skip if adjacent to other Arabic chars (diacritics or letters).
    // This filters out regular Arabic words like "لَا إِلَٰهَ" that happen to have
    // base letters separated by spaces — real root notation like "ر ح م" is isolated.
    const charBefore = m.index > 0 ? text[m.index - 1] : '';
    const charAfter = text[m.index + m[0].length] ?? '';
    if (ARABIC_CHAR_RE.test(charBefore) || ARABIC_CHAR_RE.test(charAfter)) {
      continue;
    }

    // Avoid overlapping with verse refs
    const overlaps = matches.some(
      (prev) => m!.index < prev.index + prev.length && m!.index + m![0].length > prev.index,
    );
    if (!overlaps) {
      matches.push({ index: m.index, length: m[0].length, type: 'root', value: m[1] });
    }
  }

  // Transliterated roots (e.g. "f-l-q") — link to the root page with a tooltip,
  // just like the spaced-Arabic roots above. These appear in the exegesis notes.
  LATIN_ROOT_RE.lastIndex = 0;
  while ((m = LATIN_ROOT_RE.exec(text)) !== null) {
    // Boundary check: skip if adjacent to other Latin letters/hyphens, so we
    // only catch isolated root tokens (not pieces of a longer word).
    const charBefore = m.index > 0 ? text[m.index - 1] : '';
    const charAfter = text[m.index + m[0].length] ?? '';
    if (TRANSLIT_BOUNDARY_RE.test(charBefore) || TRANSLIT_BOUNDARY_RE.test(charAfter)) {
      continue;
    }
    const bw = translitRootToBuckwalter(m[0]);
    if (!bw) continue;
    const overlaps = matches.some(
      (prev) => m!.index < prev.index + prev.length && m!.index + m![0].length > prev.index,
    );
    if (!overlaps) {
      matches.push({ index: m.index, length: m[0].length, type: 'root', value: m[0], bw, latin: true });
    }
  }

  QUOTED_RE.lastIndex = 0;
  while ((m = QUOTED_RE.exec(text)) !== null) {
    const overlaps = matches.some(
      (prev) => m!.index < prev.index + prev.length && m!.index + m![0].length > prev.index,
    );
    if (!overlaps) {
      matches.push({ index: m.index, length: m[0].length, type: 'quoted', value: m[0] });
    }
  }

  // Sort by position
  matches.sort((a, b) => a.index - b.index);

  // If no matches found, just return plain text (with inline Arabic
  // glyph runs wrapped in font-arabic — otherwise body sans-serif
  // bleeds onto Uthmani diacritics).
  if (matches.length === 0) {
    return <span className={className}>{wrapArabicRuns(text)}</span>;
  }

  // Build segments
  const parts: { type: 'text' | 'ref' | 'root' | 'quoted'; value: string; bw?: string; latin?: boolean }[] = [];
  let lastIndex = 0;

  for (const match of matches) {
    if (match.index > lastIndex) {
      parts.push({ type: 'text', value: text.slice(lastIndex, match.index) });
    }
    parts.push({ type: match.type, value: match.value, bw: match.bw, latin: match.latin });
    lastIndex = match.index + match.length;
  }

  if (lastIndex < text.length) {
    parts.push({ type: 'text', value: text.slice(lastIndex) });
  }

  return (
    <span className={className}>
      {parts.map((part, i) =>
        part.type === 'ref' ? (
          <VerseRefLink
            key={i}
            verseRef={part.value}
            disableNavigation={disableVerseNavigation}
            highlightRootBw={highlightRootBw}
            highlightLemmaBw={highlightLemmaBw}
          />
        ) : part.type === 'root' ? (
          <RootRefLink key={i} rootText={part.value} buckwalter={part.bw} latin={part.latin} />
        ) : part.type === 'quoted' ? (
          // Quoted strings can themselves contain inline Arabic (the
          // AI sometimes embeds Arabic words inside a quoted English
          // phrase). Wrap the Arabic runs so diacritics render with
          // Amiri.
          <span key={i} className="italic">{wrapArabicRuns(part.value)}</span>
        ) : (
          // Plain prose between matches. Same treatment — any Arabic
          // glyph runs (e.g. "the form is رَبِّكَ here") get the
          // font-arabic span so the kasra-under-shadda renders.
          <span key={i}>{wrapArabicRuns(part.value)}</span>
        ),
      )}
    </span>
  );
}
