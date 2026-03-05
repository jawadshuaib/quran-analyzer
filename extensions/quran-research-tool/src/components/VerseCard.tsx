import { useState, useEffect, useRef } from 'react';
import type { VerseData, AITranslationData, Word, WordMeaningBrief } from '../types/index.ts';
import WordTooltip from './WordTooltip.tsx';

interface Props {
  verse: VerseData;
  aiTranslation: AITranslationData | null;
  wordMeanings: Record<string, WordMeaningBrief>;
}

const FRONTEND_BASE = 'http://localhost:4000';

// Matches "56:74" or "96:1-4"
const VERSE_REF_RE = /(\d{1,3}:\d{1,3}(?:[–\-]\d{1,3})?)/g;
// Matches spaced Arabic root letters like "ر ح م"
const ARABIC_ROOT_RE = /([\u0621-\u064A][ \-][\u0621-\u064A](?:[ \-][\u0621-\u064A]){0,3})/g;
const ARABIC_CHAR_RE = /[\u0621-\u0652\u0670\u0671]/;
// Matches quoted strings
const QUOTED_RE = /["\u201C][^"\u201D]+["\u201D]/g;

/** Split departure notes into separate lines at " - " when preceded by "." within 3 chars. */
function splitDepartureNotes(text: string): string[] {
  const processed = text.replace(/(\..{0,2}) - /g, '$1\n- ');
  return processed.split('\n');
}

/** Render text with verse refs as links and Arabic roots as links, quoted text as italic. */
function NoteText({ text }: { text: string }) {
  type Part = { type: 'text' | 'ref' | 'root' | 'quoted'; value: string };
  const matches: { index: number; length: number; type: 'ref' | 'root' | 'quoted'; value: string }[] = [];

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

  matches.sort((a, b) => a.index - b.index);
  if (matches.length === 0) return <span>{text}</span>;

  const parts: Part[] = [];
  let lastIndex = 0;
  for (const match of matches) {
    if (match.index > lastIndex) parts.push({ type: 'text', value: text.slice(lastIndex, match.index) });
    parts.push({ type: match.type, value: match.value });
    lastIndex = match.index + match.length;
  }
  if (lastIndex < text.length) parts.push({ type: 'text', value: text.slice(lastIndex) });

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
        ) : part.type === 'root' ? (
          <span
            key={i}
            dir="rtl"
            lang="ar"
            className="font-arabic text-emerald-700 underline decoration-emerald-300 underline-offset-2 cursor-pointer hover:text-emerald-900 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              const letters = part.value.replace(/[ \-]/g, '');
              chrome.tabs.create({ url: `${FRONTEND_BASE}/root/${encodeURIComponent(letters)}` });
            }}
          >
            {part.value}
          </span>
        ) : part.type === 'quoted' ? (
          <span key={i} className="italic">{part.value}</span>
        ) : (
          <span key={i}>{part.value}</span>
        ),
      )}
    </span>
  );
}

export default function VerseCard({ verse, aiTranslation, wordMeanings }: Props) {
  const [activePos, setActivePos] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const uthmaniWords = verse.text_uthmani.split(/\s+/).filter(Boolean);
  const wordMap = new Map<number, Word>();
  verse.words.forEach((w) => wordMap.set(w.position, w));

  // Click outside to dismiss tooltip
  useEffect(() => {
    if (activePos === null) return;
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setActivePos(null);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [activePos]);

  return (
    <div ref={containerRef} className="px-5 py-4 border-b border-stone-200">
      {/* Surah name */}
      <div className="text-xs font-medium text-stone-400 mb-2">
        Surah {verse.surah_name} ({verse.surah}:{verse.ayah})
      </div>

      {/* Arabic text with interactive words */}
      <div
        dir="rtl"
        lang="ar"
        className="mb-3 text-xl leading-[2.4] font-arabic text-stone-800 flex flex-wrap gap-x-1.5"
        onClick={() => setActivePos(null)}
      >
        {uthmaniWords.map((word, idx) => {
          const pos = idx + 1;
          const wordData = wordMap.get(pos);
          const isActive = activePos === pos;

          return (
            <span
              key={pos}
              className={`relative inline-block cursor-pointer rounded-md px-0.5 transition-colors duration-150 ${
                isActive
                  ? 'bg-emerald-100 text-emerald-900'
                  : 'hover:bg-stone-100'
              }`}
              onClick={(e) => {
                e.stopPropagation();
                setActivePos(isActive ? null : pos);
              }}
            >
              {word}
              {isActive && wordData && (
                <WordTooltip
                  word={wordData}
                  aiMeaning={wordMeanings[String(pos)]?.meaning_short}
                  preferredTranslation={wordMeanings[String(pos)]?.preferred_translation}
                  preferredSource={wordMeanings[String(pos)]?.preferred_source}
                />
              )}
            </span>
          );
        })}
      </div>

      {/* Translation — prefer AI translation when available */}
      <p className="text-sm text-stone-600 italic">
        {aiTranslation ? aiTranslation.translation : verse.translation}
      </p>

      {/* Translation notes */}
      {aiTranslation?.departure_notes && (
        <div className="mt-2 rounded-lg bg-violet-50 border border-violet-100 p-3">
          <div className="text-xs font-medium text-violet-600 mb-1">Translation Notes</div>
          <div className="text-xs text-violet-800 leading-relaxed">
            {splitDepartureNotes(aiTranslation.departure_notes).map((line, i) => (
              <p key={i} className={i > 0 ? 'mt-1.5' : ''}>
                <NoteText text={line} />
              </p>
            ))}
          </div>
        </div>
      )}

      {/* Root pills */}
      {verse.roots_summary.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {verse.roots_summary.map((r) => (
            <span
              key={r.root_buckwalter}
              className="inline-flex items-center gap-1 rounded-full bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-xs text-emerald-700 cursor-pointer hover:bg-emerald-100 transition-colors"
              onClick={() =>
                chrome.tabs.create({
                  url: `${FRONTEND_BASE}/root/${encodeURIComponent(r.root_buckwalter)}`,
                })
              }
            >
              <span dir="rtl" lang="ar" className="font-arabic text-sm">
                {r.root_arabic}
              </span>
              {r.occurrences > 1 && (
                <span className="text-emerald-400">&times;{r.occurrences}</span>
              )}
            </span>
          ))}
        </div>
      )}

      {/* Open in Explorer */}
      <button
        onClick={() =>
          chrome.tabs.create({
            url: `${FRONTEND_BASE}/verse/${verse.surah}:${verse.ayah}`,
          })
        }
        className="mt-3 w-full rounded-lg border border-stone-200 bg-white px-3 py-1.5 text-xs font-medium text-emerald-700 hover:bg-emerald-50 transition-colors cursor-pointer text-center"
      >
        Explore More
      </button>
    </div>
  );
}
