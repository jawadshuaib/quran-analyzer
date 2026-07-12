import { FRONTEND_BASE } from '../config.ts';
import {
  arabicRootToBuckwalter,
  LATIN_ROOT_RE,
  TRANSLIT_BOUNDARY_RE,
  translitRootToBuckwalter,
} from '../utils/buckwalter.ts';
import { wrapArabicRuns } from '../utils/arabic-runs.tsx';

// Matches "56:74" or "96:1-4"
const VERSE_REF_RE = /(\d{1,3}:\d{1,3}(?:[–\-]\d{1,3})?)/g;
// Matches spaced Arabic root letters like "ر ح م"
const ARABIC_ROOT_RE = /([\u0621-\u064A][ \-][\u0621-\u064A](?:[ \-][\u0621-\u064A]){0,3})/g;
const ARABIC_CHAR_RE = /[\u0621-\u0652\u0670\u0671]/;
// Matches quoted strings
const QUOTED_RE = /["“][^"”]+["”]/g;

/** Render text with verse refs and roots (spaced Arabic like "ر ح م" or
 * transliterated like "ṭ-r-q") as links, quoted text as italic, and every
 * inline Arabic run wrapped in the Arabic font. */
export default function NoteText({ text }: { text: string }) {
  type Part = { type: 'text' | 'ref' | 'root' | 'quoted'; value: string; bw?: string; latin?: boolean };
  const matches: { index: number; length: number; type: 'ref' | 'root' | 'quoted'; value: string; bw?: string; latin?: boolean }[] = [];

  VERSE_REF_RE.lastIndex = 0;
  let m: RegExpExecArray | null;
  while ((m = VERSE_REF_RE.exec(text)) !== null) {
    matches.push({ index: m.index, length: m[0].length, type: 'ref', value: m[1] });
  }

  ARABIC_ROOT_RE.lastIndex = 0;
  while ((m = ARABIC_ROOT_RE.exec(text)) !== null) {
    const charBefore = m.index > 0 ? text[m.index - 1] : '';
    const charAfter = text[m.index + m[0].length] ?? '';
    if (ARABIC_CHAR_RE.test(charBefore) || ARABIC_CHAR_RE.test(charAfter)) continue;
    const overlaps = matches.some(
      (prev) => m!.index < prev.index + prev.length && m!.index + m![0].length > prev.index,
    );
    if (!overlaps) {
      const bw = arabicRootToBuckwalter(m[1].replace(/[ \-]/g, ''));
      matches.push({ index: m.index, length: m[0].length, type: 'root', value: m[1], bw });
    }
  }

  // Transliterated roots (e.g. "f-l-q") — the exegesis notes name roots this
  // way, whereas the grammar/translation notes use spaced Arabic letters.
  LATIN_ROOT_RE.lastIndex = 0;
  while ((m = LATIN_ROOT_RE.exec(text)) !== null) {
    // Boundary check: skip if adjacent to other Latin letters/hyphens, so we
    // only catch isolated root tokens (not pieces of a longer word).
    const charBefore = m.index > 0 ? text[m.index - 1] : '';
    const charAfter = text[m.index + m[0].length] ?? '';
    if (TRANSLIT_BOUNDARY_RE.test(charBefore) || TRANSLIT_BOUNDARY_RE.test(charAfter)) continue;
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

  matches.sort((a, b) => a.index - b.index);
  if (matches.length === 0) return <span>{wrapArabicRuns(text)}</span>;

  const parts: Part[] = [];
  let lastIndex = 0;
  for (const match of matches) {
    if (match.index > lastIndex) parts.push({ type: 'text', value: text.slice(lastIndex, match.index) });
    parts.push({ type: match.type, value: match.value, bw: match.bw, latin: match.latin });
    lastIndex = match.index + match.length;
  }
  if (lastIndex < text.length) parts.push({ type: 'text', value: text.slice(lastIndex) });

  const openRoot = (bw: string) => {
    chrome.tabs.create({ url: `${FRONTEND_BASE}/root/${encodeURIComponent(bw)}` });
  };

  return (
    <span>
      {parts.map((part, i) =>
        part.type === 'ref' ? (
          <span
            key={i}
            className="text-violet-600 underline decoration-violet-300 underline-offset-2 cursor-pointer hover:text-violet-800 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              const [surah, rest] = part.value.split(':');
              const ayah = rest.split(/[–\-]/)[0];
              chrome.tabs.create({ url: `${FRONTEND_BASE}/verse/${surah}:${ayah}` });
            }}
          >
            {part.value}
          </span>
        ) : part.type === 'root' && part.latin ? (
          <span
            key={i}
            className="text-emerald-700 underline decoration-emerald-300 underline-offset-2 cursor-pointer hover:text-emerald-900 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              openRoot(part.bw!);
            }}
          >
            {part.value}
          </span>
        ) : part.type === 'root' ? (
          <span
            key={i}
            dir="rtl"
            lang="ar"
            className="font-arabic text-emerald-700 underline decoration-emerald-300 underline-offset-2 cursor-pointer hover:text-emerald-900 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              openRoot(part.bw!);
            }}
          >
            {part.value}
          </span>
        ) : part.type === 'quoted' ? (
          <span key={i} className="italic">{wrapArabicRuns(part.value)}</span>
        ) : (
          <span key={i}>{wrapArabicRuns(part.value)}</span>
        ),
      )}
    </span>
  );
}
