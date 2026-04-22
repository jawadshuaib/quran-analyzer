import { useState } from 'react';
import type { GrammarNotesData, GrammarTerm } from '../types/index.ts';

interface Props {
  data: GrammarNotesData;
}

/**
 * Compact grammar notes card for the Chrome extension popup.
 *
 * Renders notes_markdown prose with [[term]] markers replaced by inline
 * amber-underlined chips. Because the popup is narrow (400-500px), the
 * tooltip strategy is simplified compared to the main site: clicking a
 * chip opens its definition in an expandable footer below the notes
 * (one at a time), rather than floating a positioned tooltip.
 */
export default function GrammarNotesSection({ data }: Props) {
  const [openTerm, setOpenTerm] = useState<string | null>(null);

  const paragraphs = data.notes_markdown
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter(Boolean);

  const selectedTerm: GrammarTerm | null = openTerm ? data.terms[openTerm] ?? null : null;

  return (
    <div className="mt-2 rounded-lg bg-amber-50 border border-amber-100 p-3">
      <div className="text-xs font-medium text-amber-700 mb-1">Notes on Grammar</div>
      <div className="text-xs text-amber-900 leading-relaxed space-y-2">
        {paragraphs.map((para, i) => (
          <p key={i}>
            {renderWithMarkers(para, data.terms, openTerm, setOpenTerm)}
          </p>
        ))}
      </div>

      {selectedTerm && (
        <div className="mt-3 pt-2 border-t border-amber-200 text-xs">
          <div className="flex items-baseline justify-between">
            <span className="font-semibold uppercase tracking-wide text-amber-800 text-[10px]">
              {selectedTerm.term_english}
            </span>
            <button
              onClick={() => setOpenTerm(null)}
              className="text-amber-600 hover:text-amber-800 text-[10px] cursor-pointer"
              title="Close"
            >
              close
            </button>
          </div>
          {selectedTerm.term_arabic && (
            <div
              dir="rtl"
              lang="ar"
              className="mt-0.5 text-sm font-arabic text-stone-800"
            >
              {selectedTerm.term_arabic}
            </div>
          )}
          <div className="mt-1 text-stone-700 leading-relaxed">
            {selectedTerm.plain_explanation}
          </div>
          {(selectedTerm.example_sentence || selectedTerm.example_translation) && (
            <div className="mt-2 pt-2 border-t border-amber-100">
              {selectedTerm.example_sentence && (
                <div
                  dir="rtl"
                  lang="ar"
                  className="font-arabic text-sm text-stone-800"
                >
                  {selectedTerm.example_sentence}
                </div>
              )}
              {selectedTerm.example_translation && (
                <div className="mt-0.5 italic text-stone-500 leading-relaxed">
                  “{selectedTerm.example_translation}”
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function renderWithMarkers(
  text: string,
  terms: Record<string, GrammarTerm>,
  openTerm: string | null,
  setOpenTerm: (t: string | null) => void,
): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  const regex = /\[\[([^\]]+)\]\]/g;
  let lastIdx = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIdx) {
      nodes.push(text.slice(lastIdx, match.index));
    }
    const raw = match[1].trim();
    const lookup = raw.toLowerCase();
    const term = terms[lookup];
    const isOpen = openTerm === lookup;
    if (term) {
      nodes.push(
        <button
          key={key++}
          type="button"
          onClick={() => setOpenTerm(isOpen ? null : lookup)}
          className={`cursor-pointer underline decoration-amber-500 decoration-wavy underline-offset-[3px] decoration-1 ${
            isOpen ? 'text-amber-800 font-medium' : ''
          }`}
          title={term.term_english}
        >
          {raw}
        </button>,
      );
    } else {
      // No definition attached — render the bare text so the note still reads
      nodes.push(<span key={key++}>{raw}</span>);
    }
    lastIdx = regex.lastIndex;
  }
  if (lastIdx < text.length) {
    nodes.push(text.slice(lastIdx));
  }
  return nodes;
}
