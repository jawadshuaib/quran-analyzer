import { useState } from 'react';
import type { VersePoetryNote, PoetryQuotedLine } from '../types/index.ts';
import NoteMarkdown from './NoteMarkdown.tsx';
import { FRONTEND_BASE } from '../config.ts';

/**
 * Compact pre-Islamic poetry note for the extension popup.
 *
 * Poetic fragments are linked inline within the prose (amber dotted underline,
 * never block-quoted, so a reader can't mistake them for Qurʾān). Because the
 * popup is narrow, hover tooltips are replaced by the GrammarNotesSection
 * pattern: tapping a fragment opens the full line (poet, bayt, translation)
 * in an expandable footer, with a link to the whole poem on the main site.
 */
export default function PoetrySection({ data }: { data: VersePoetryNote }) {
  const [openLrid, setOpenLrid] = useState<number | null>(null);

  const selected: PoetryQuotedLine | null = openLrid !== null
    ? data.quoted_lines.find((q) => q.line_root_id === openLrid) ?? null
    : null;

  return (
    <div className="mt-2 rounded-lg bg-amber-50 border border-amber-200 p-3">
      <div className="text-xs font-medium text-amber-700 mb-1">In Pre-Islamic Poetry</div>
      <NoteMarkdown
        text={data.note_markdown}
        quotes={data.quoted_lines}
        activeQuoteId={openLrid}
        onQuoteClick={(lrid) => setOpenLrid(openLrid === lrid ? null : lrid)}
        className="text-xs text-amber-900/90 leading-relaxed"
      />

      {selected && (
        <div className="mt-3 pt-2 border-t border-amber-200 text-xs">
          <div className="flex items-baseline justify-between">
            <span className="font-semibold uppercase tracking-wide text-amber-800 text-[10px]">
              Pre-Islamic poetry
            </span>
            <button
              onClick={() => setOpenLrid(null)}
              className="text-amber-600 hover:text-amber-800 text-[10px] cursor-pointer"
              title="Close"
            >
              close
            </button>
          </div>
          {selected.poet && (
            <div dir="rtl" lang="ar" className="mt-0.5 font-arabic text-sm text-stone-700">
              {selected.poet}
            </div>
          )}
          {selected.arabic && (
            <div
              dir="rtl"
              lang="ar"
              className="mt-1 font-arabic text-sm leading-loose text-stone-800"
            >
              {selected.arabic}
            </div>
          )}
          {selected.english && (
            <div className="mt-1 italic text-stone-500 leading-relaxed">
              “{selected.english}”
            </div>
          )}
          {selected.poem_id != null && (
            <button
              onClick={() =>
                chrome.tabs.create({
                  url: `${FRONTEND_BASE}/poem/${selected.poem_id}${
                    selected.line_no != null ? `#line-${selected.line_no}` : ''
                  }`,
                })
              }
              className="mt-2 w-full rounded-lg border border-amber-200 bg-white px-3 py-1.5 text-xs font-medium text-amber-700 hover:bg-amber-100 transition-colors cursor-pointer text-center"
            >
              Read the full poem
            </button>
          )}
        </div>
      )}
    </div>
  );
}
