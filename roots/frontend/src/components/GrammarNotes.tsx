import { useState, useEffect, useRef } from 'react';
import type { GrammarNotesData, GrammarTerm } from '../types';
import { fetchGrammarNotes } from '../api/quran';

interface Props {
  surah: number;
  ayah: number;
}

// localStorage key for the user's open/closed preference. Stored globally
// (not per-verse): once the user opens Notes on Grammar, we remember they
// like it open across verses.
const LS_KEY = 'grammarNotesOpen';

function getInitialOpen(): boolean {
  try {
    return localStorage.getItem(LS_KEY) === '1';
  } catch {
    return false;
  }
}

function persistOpen(open: boolean) {
  try {
    localStorage.setItem(LS_KEY, open ? '1' : '0');
  } catch {
    // ignore
  }
}

export default function GrammarNotes({ surah, ayah }: Props) {
  const [expanded, setExpanded] = useState<boolean>(getInitialOpen);
  const [data, setData] = useState<GrammarNotesData | null>(null);
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [notFound, setNotFound] = useState(false);

  // When verse changes, reset data — keep expanded state (user preference)
  useEffect(() => {
    setData(null);
    setLoaded(false);
    setNotFound(false);
  }, [surah, ayah]);

  // If the section is open (from persisted preference), auto-load the notes
  useEffect(() => {
    if (expanded && !loaded && !loading) {
      loadNotes();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [expanded, surah, ayah]);

  async function loadNotes() {
    setLoading(true);
    try {
      const result = await fetchGrammarNotes(surah, ayah);
      setData(result);
      setNotFound(result === null);
    } catch {
      setNotFound(true);
    } finally {
      setLoading(false);
      setLoaded(true);
    }
  }

  function handleToggle() {
    const next = !expanded;
    setExpanded(next);
    persistOpen(next);
    if (next && !loaded && !loading) {
      loadNotes();
    }
  }

  // Don't show the section at all if we already know there are no notes
  // for this verse (404 on the server). Keeps the verse page clean.
  if (loaded && notFound && !loading) return null;

  return (
    <div className="rounded-xl border border-stone-200 bg-white shadow-sm overflow-hidden">
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-stone-50 transition-colors cursor-pointer"
      >
        <span className="text-sm font-semibold text-stone-700">
          Notes on Grammar
        </span>
        <svg
          className={`h-4 w-4 text-stone-400 transition-transform duration-200 ${
            expanded ? 'rotate-180' : ''
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <div className="border-t border-stone-100 px-6 py-4">
          {loading ? (
            <div className="flex justify-center py-4">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-amber-200 border-t-amber-600" />
            </div>
          ) : data ? (
            <div className="prose prose-sm prose-stone max-w-none text-sm text-stone-700 leading-relaxed">
              <NotesBody markdown={data.notes_markdown} terms={data.terms} />
            </div>
          ) : (
            <p className="text-sm text-stone-400 text-center py-2">
              No grammar notes available for this verse yet.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// --------------------------------------------------------------------
// NotesBody — parses [[term]] markers and replaces them with <GrammarChip>.
// Also respects blank lines as paragraph breaks.
// --------------------------------------------------------------------

function NotesBody({ markdown, terms }: { markdown: string; terms: Record<string, GrammarTerm> }) {
  // Split on blank lines into paragraphs
  const paragraphs = markdown.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);
  return (
    <>
      {paragraphs.map((para, i) => (
        <p key={i} className={i > 0 ? 'mt-3' : ''}>
          {renderWithMarkers(para, terms)}
        </p>
      ))}
    </>
  );
}

function renderWithMarkers(text: string, terms: Record<string, GrammarTerm>) {
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
    if (term) {
      nodes.push(<GrammarChip key={key++} term={term} displayText={raw} />);
    } else {
      // Missing definition — render bare text so the note still reads
      nodes.push(<span key={key++}>{raw}</span>);
    }
    lastIdx = regex.lastIndex;
  }
  if (lastIdx < text.length) {
    nodes.push(text.slice(lastIdx));
  }
  return nodes;
}

// --------------------------------------------------------------------
// GrammarChip — inline term with squiggly underline + hover tooltip.
// The tooltip positions itself above or below depending on viewport space,
// and flips horizontally if it would spill off screen.
// --------------------------------------------------------------------

function GrammarChip({ term, displayText }: { term: GrammarTerm; displayText: string }) {
  const [open, setOpen] = useState(false);
  const [placement, setPlacement] = useState<{ above: boolean; shift: number }>({ above: true, shift: 0 });
  const chipRef = useRef<HTMLSpanElement | null>(null);
  const tipRef = useRef<HTMLDivElement | null>(null);
  const closeTimer = useRef<number | null>(null);

  // Compute tooltip position whenever it opens
  useEffect(() => {
    if (!open) return;
    const chip = chipRef.current;
    const tip = tipRef.current;
    if (!chip || !tip) return;

    const chipRect = chip.getBoundingClientRect();
    const tipRect = tip.getBoundingClientRect();
    const viewportW = window.innerWidth;
    const viewportH = window.innerHeight;

    // Above by default; flip below if no room above
    const spaceAbove = chipRect.top;
    const spaceBelow = viewportH - chipRect.bottom;
    const above = spaceAbove >= tipRect.height + 12 || spaceAbove >= spaceBelow;

    // Shift so the tooltip doesn't clip horizontally
    const chipCenter = chipRect.left + chipRect.width / 2;
    const halfTip = tipRect.width / 2;
    let shift = 0;
    if (chipCenter - halfTip < 8) {
      shift = 8 - (chipCenter - halfTip);
    } else if (chipCenter + halfTip > viewportW - 8) {
      shift = (viewportW - 8) - (chipCenter + halfTip);
    }

    setPlacement({ above, shift });
  }, [open]);

  function show() {
    if (closeTimer.current) {
      window.clearTimeout(closeTimer.current);
      closeTimer.current = null;
    }
    setOpen(true);
  }

  function hide() {
    // Small delay so moving from chip -> tooltip doesn't close it
    closeTimer.current = window.setTimeout(() => setOpen(false), 120);
  }

  return (
    <span
      ref={chipRef}
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
      tabIndex={0}
      className="relative inline cursor-help underline decoration-amber-500 decoration-wavy underline-offset-4 decoration-2 outline-none focus-visible:ring-2 focus-visible:ring-amber-400 rounded-sm"
    >
      {displayText}
      {open && (
        <span
          ref={tipRef}
          onMouseEnter={show}
          onMouseLeave={hide}
          style={{ transform: `translate(calc(-50% + ${placement.shift}px), 0)` }}
          className={`absolute left-1/2 z-30 w-72 rounded-xl border border-stone-200 bg-white shadow-xl p-4 text-left pointer-events-auto ${
            placement.above ? 'bottom-full mb-2' : 'top-full mt-2'
          }`}
        >
          <span className="block text-xs font-semibold tracking-wide uppercase text-amber-700">
            {term.term_english}
          </span>
          {term.term_arabic && (
            <span className="block mt-1 text-lg font-serif text-stone-700" dir="rtl" lang="ar">
              {term.term_arabic}
            </span>
          )}
          <span className="block mt-2 text-xs text-stone-600 leading-relaxed font-normal">
            {term.plain_explanation}
          </span>
          {(term.example_sentence || term.example_translation) && (
            <span className="block mt-3 pt-3 border-t border-stone-100">
              {term.example_sentence && (
                <span className="block text-base font-serif text-stone-800" dir="rtl" lang="ar">
                  {term.example_sentence}
                </span>
              )}
              {term.example_translation && (
                <span className="block mt-1 text-xs italic text-stone-500 leading-relaxed font-normal">
                  “{term.example_translation}”
                </span>
              )}
            </span>
          )}
        </span>
      )}
    </span>
  );
}
