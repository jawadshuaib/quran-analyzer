import { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import type { GrammarNotesData, GrammarTerm } from '../types';
import { fetchGrammarNotes, grammarTermSlug } from '../api/quran';
import { wrapArabicRuns } from '../utils/arabic-runs';

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

  // When verse changes, reset data — keep expanded state (user preference)
  useEffect(() => {
    setData(null);
    setLoaded(false);
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
    } catch {
      setData(null);
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
//
// Exported so the reader (ReaderVerse's combined-notes panel) can render
// grammar notes the same way the research view does, without copy-paste.
// --------------------------------------------------------------------

export function NotesBody({ markdown, terms }: { markdown: string; terms: Record<string, GrammarTerm> }) {
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
      nodes.push(<span key={key++}>{wrapArabicRuns(text.slice(lastIdx, match.index))}</span>);
    }
    const raw = match[1].trim();
    const lookup = raw.toLowerCase();
    const term = terms[lookup];
    if (term) {
      nodes.push(<GrammarChip key={key++} term={term} displayText={raw} />);
    } else {
      // Missing definition — render bare text so the note still reads
      nodes.push(<span key={key++}>{wrapArabicRuns(raw)}</span>);
    }
    lastIdx = regex.lastIndex;
  }
  if (lastIdx < text.length) {
    nodes.push(<span key={key++}>{wrapArabicRuns(text.slice(lastIdx))}</span>);
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
  // Viewport coordinates of where the tooltip should render.
  // Uses position: fixed so it escapes any overflow-hidden ancestor.
  const [pos, setPos] = useState<{ left: number; top: number; above: boolean } | null>(null);
  const chipRef = useRef<HTMLSpanElement | null>(null);
  const tipRef = useRef<HTMLDivElement | null>(null);
  const closeTimer = useRef<number | null>(null);
  const TIP_WIDTH = 288; // keep in sync with w-72 (288px)
  const GAP = 8;

  // Compute tooltip position relative to the viewport whenever it opens.
  // Re-runs on scroll / resize so the tooltip follows the chip if the page
  // moves while open.
  useEffect(() => {
    if (!open) return;

    function place() {
      const chip = chipRef.current;
      if (!chip) return;
      const chipRect = chip.getBoundingClientRect();
      const tipH = tipRef.current?.getBoundingClientRect().height ?? 200;
      const viewportW = window.innerWidth;
      const viewportH = window.innerHeight;

      // Prefer above; flip below if no room
      const spaceAbove = chipRect.top;
      const spaceBelow = viewportH - chipRect.bottom;
      const above = spaceAbove >= tipH + GAP || spaceAbove >= spaceBelow;

      const chipCenter = chipRect.left + chipRect.width / 2;
      let left = chipCenter - TIP_WIDTH / 2;
      left = Math.max(GAP, Math.min(left, viewportW - TIP_WIDTH - GAP));

      const top = above ? chipRect.top - tipH - GAP : chipRect.bottom + GAP;
      setPos({ left, top, above });
    }

    place();
    window.addEventListener('scroll', place, true);
    window.addEventListener('resize', place);
    return () => {
      window.removeEventListener('scroll', place, true);
      window.removeEventListener('resize', place);
    };
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

  const tooltip = open && pos ? (
    <div
      ref={tipRef}
      onMouseEnter={show}
      onMouseLeave={hide}
      style={{ left: pos.left, top: pos.top, width: TIP_WIDTH }}
      className="fixed z-[1000] rounded-xl border border-stone-200 bg-white shadow-xl p-4 text-left pointer-events-auto"
    >
      <div className="text-xs font-semibold tracking-wide uppercase text-amber-700">
        {term.term_english}
      </div>
      {term.term_arabic && (
        <div className="mt-1 text-lg font-arabic text-stone-700" dir="rtl" lang="ar">
          {term.term_arabic}
        </div>
      )}
      <div className="mt-2 text-xs text-stone-600 leading-relaxed">
        {wrapArabicRuns(term.plain_explanation)}
      </div>
      {(term.example_sentence || term.example_translation) && (
        <div className="mt-3 pt-3 border-t border-stone-100">
          {term.example_sentence && (
            <div className="text-base font-arabic text-stone-800" dir="rtl" lang="ar">
              {term.example_sentence}
            </div>
          )}
          {term.example_translation && (
            <div className="mt-1 text-xs italic text-stone-500 leading-relaxed">
              “{wrapArabicRuns(term.example_translation)}”
            </div>
          )}
        </div>
      )}
      {/* Glossary deep-link — scrolls directly to this term's row in the
          full grammar glossary page. */}
      <div className="mt-3 pt-3 border-t border-stone-100">
        <a
          href={`/grammar-glossary#${grammarTermSlug(term.term_english)}`}
          className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-700 hover:text-amber-800"
        >
          View in glossary
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </a>
      </div>
    </div>
  ) : null;

  return (
    <>
      <span
        ref={chipRef}
        onMouseEnter={show}
        onMouseLeave={hide}
        onFocus={show}
        onBlur={hide}
        tabIndex={0}
        className="cursor-help underline decoration-amber-500 decoration-wavy underline-offset-[3px] decoration-1 outline-none focus-visible:ring-2 focus-visible:ring-amber-400 rounded-sm"
      >
        {displayText}
      </span>
      {tooltip && createPortal(tooltip, document.body)}
    </>
  );
}
