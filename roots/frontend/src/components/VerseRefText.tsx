import { useState, useRef, useCallback, useEffect } from 'react';
import type { RootDetailData } from '../types';
import { fetchVerse, fetchRoot } from '../api/quran';
import { arabicRootToBuckwalter } from '../utils/buckwalter';
import { verseUrl, ejtaalUrl } from '../utils/urls';

interface Props {
  text: string;
  className?: string;
}

interface CachedVerse {
  surah: number;
  ayah: number;
  text_uthmani: string;
  translation: string;
}

// Matches "56:74" or "96:1–4" / "96:1-4" (en-dash or hyphen range)
const VERSE_REF_RE = /(\d{1,3}:\d{1,3}(?:[–\-]\d{1,3})?)/g;

// Matches spaced Arabic root letters like "ر ح م" or dash-separated like "ع-ب-د"
// (2–5 base Arabic letters separated by spaces or dashes).
// The boundary check in the matching loop ensures these aren't part of full Arabic words.
const ARABIC_ROOT_RE = /([\u0621-\u064A][ \-][\u0621-\u064A](?:[ \-][\u0621-\u064A]){0,3})/g;

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

function VerseRefLink({ verseRef }: { verseRef: string }) {
  const { surah, startAyah, endAyah } = parseRef(verseRef);
  const isRange = endAyah > startAyah;

  const [tooltip, setTooltip] = useState<{
    loading: boolean;
    verses: CachedVerse[];
    error: boolean;
  } | null>(null);

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
      window.open(verseUrl(surah, startAyah), '_blank');
    },
    [surah, startAyah],
  );

  return (
    <span className="relative inline">
      <span
        className="text-violet-600 underline decoration-violet-300 underline-offset-2 cursor-pointer hover:text-violet-800 hover:decoration-violet-500 transition-colors"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
        role="link"
        tabIndex={0}
      >
        {verseRef}
      </span>

      {tooltip && (
        <span
          className="absolute left-1/2 -translate-x-1/2 top-full mt-2 z-50
                     bg-white rounded-lg shadow-lg border border-violet-200 p-3
                     min-w-[220px] max-w-[360px] text-sm text-stone-700"
          style={{ width: isRange ? '340px' : undefined }}
          onMouseEnter={clearHideTimer}
          onMouseLeave={handleMouseLeave}
        >
          {/* Arrow */}
          <span className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3
                          bg-white border-l border-t border-violet-200 rotate-45" />

          {tooltip.loading ? (
            <span className="flex justify-center py-2">
              <span className="h-5 w-5 animate-spin rounded-full border-2 border-violet-200 border-t-violet-600" />
            </span>
          ) : tooltip.error ? (
            <span className="text-xs text-red-500 text-center block">
              Could not load verse
            </span>
          ) : tooltip.verses.length > 0 ? (
            <span className="block space-y-2 max-h-[400px] overflow-y-auto">
              {tooltip.verses.map((v) => (
                <span
                  key={v.ayah}
                  className="block rounded-md hover:bg-violet-50/50 transition-colors px-1 py-0.5 cursor-pointer"
                  onClick={(e) => {
                    e.stopPropagation();
                    window.open(verseUrl(v.surah, v.ayah), '_blank');
                  }}
                >
                  <span className="flex items-center justify-between mb-1">
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
                  </span>
                  <span
                    dir="rtl"
                    lang="ar"
                    className="block font-arabic text-base leading-[2] text-stone-800 text-right"
                  >
                    {v.text_uthmani}
                  </span>
                  <span className="block text-xs text-stone-500 italic leading-relaxed mt-0.5">
                    {v.translation}
                  </span>
                  {/* Divider between verses in a range (not after last) */}
                  {isRange && v.ayah !== endAyah && (
                    <span className="block border-b border-violet-100 mt-2" />
                  )}
                </span>
              ))}
            </span>
          ) : null}
        </span>
      )}
    </span>
  );
}

// Shared cache for root data so repeated hovers don't re-fetch
const rootCache = new Map<string, RootDetailData>();

function RootRefLink({ rootText }: { rootText: string }) {
  const [tooltip, setTooltip] = useState<{
    loading: boolean;
    data: RootDetailData | null;
    error: boolean;
  } | null>(null);
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Convert spaced/dashed Arabic letters to normalized Buckwalter for root lookup
  const letters = rootText.replace(/[ \-]/g, '');
  const bw = arabicRootToBuckwalter(letters);
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
        dir="rtl"
        lang="ar"
        className="font-arabic text-emerald-700 underline decoration-emerald-300 underline-offset-2 cursor-pointer
                   hover:text-emerald-900 hover:decoration-emerald-500 transition-colors"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={(e) => { e.preventDefault(); window.location.href = url; }}
        role="link"
        tabIndex={0}
      >
        {rootText}
      </span>

      {tooltip && (
        <span
          className="absolute left-1/2 -translate-x-1/2 top-full mt-2 z-50
                     bg-white rounded-lg shadow-lg border border-emerald-200 p-3
                     min-w-[200px] max-w-[300px] text-sm text-stone-700"
          onMouseEnter={clearTimer}
          onMouseLeave={handleMouseLeave}
        >
          {/* Arrow */}
          <span className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3
                          bg-white border-l border-t border-emerald-200 rotate-45" />

          {tooltip.loading ? (
            <span className="flex justify-center py-2">
              <span className="h-5 w-5 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-600" />
            </span>
          ) : tooltip.error ? (
            <span className="text-xs text-red-500 text-center block">
              Root not found
            </span>
          ) : tooltip.data ? (
            <span className="block space-y-2">
              {/* Root header */}
              <span className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <span dir="rtl" lang="ar" className="font-arabic text-lg text-stone-800">
                    {tooltip.data.root_arabic}
                  </span>
                  <span className="text-xs text-emerald-600 font-medium">({tooltip.data.root_buckwalter})</span>
                </span>
              </span>
              <span className="block text-xs text-stone-500">
                Mentioned in {tooltip.data.total_occurrences} verse{tooltip.data.total_occurrences !== 1 ? 's' : ''}
              </span>

              {/* Lemmas */}
              {tooltip.data.lemmas.length > 0 && (
                <span className="flex flex-wrap gap-1">
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
                </span>
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
            </span>
          ) : null}
        </span>
      )}
    </span>
  );
}

export default function VerseRefText({ text, className }: Props) {
  if (!text) return null;

  // Collect all matches (verse refs, root refs, quoted text) with their types
  const matches: { index: number; length: number; type: 'ref' | 'root' | 'quoted'; value: string }[] = [];

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

  // If no matches found, just return plain text
  if (matches.length === 0) {
    return <span className={className}>{text}</span>;
  }

  // Build segments
  const parts: { type: 'text' | 'ref' | 'root' | 'quoted'; value: string }[] = [];
  let lastIndex = 0;

  for (const match of matches) {
    if (match.index > lastIndex) {
      parts.push({ type: 'text', value: text.slice(lastIndex, match.index) });
    }
    parts.push({ type: match.type, value: match.value });
    lastIndex = match.index + match.length;
  }

  if (lastIndex < text.length) {
    parts.push({ type: 'text', value: text.slice(lastIndex) });
  }

  return (
    <span className={className}>
      {parts.map((part, i) =>
        part.type === 'ref' ? (
          <VerseRefLink key={i} verseRef={part.value} />
        ) : part.type === 'root' ? (
          <RootRefLink key={i} rootText={part.value} />
        ) : part.type === 'quoted' ? (
          <span key={i} className="italic">{part.value}</span>
        ) : (
          <span key={i}>{part.value}</span>
        ),
      )}
    </span>
  );
}
