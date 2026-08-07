import { useState, useEffect, useRef, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { fetchQuranVocabulary, vocabTermSlug } from '../api/quran';
import type { QuranVocabularyTerm } from '../api/quran';
import { wrapArabicRuns } from '../utils/arabic-runs';
import { viewportSize } from '../utils/viewport';

/**
 * Parses translation text containing markdown italic markers (*term*)
 * and renders matching transliterations as TermChip — a hoverable
 * inline element that shows the root, canonical, and a "view in
 * vocabulary" link.
 *
 * Markers that don't match a known transliteration render as plain
 * <em>italic</em> text. This keeps the component safe to apply to any
 * translation string without risk of breaking unrelated emphasis.
 */

// ---------- Module-level cache for the vocabulary lookup ----------
// One fetch per page-load; chips share the result.

interface TransliterationEntry {
  term: QuranVocabularyTerm;
  // The exact transliteration as stored in hard_cases (for tooltip text)
  transliteration: string;
}

let vocabCache: QuranVocabularyTerm[] | null = null;
let vocabPromise: Promise<QuranVocabularyTerm[]> | null = null;

function loadVocabulary(): Promise<QuranVocabularyTerm[]> {
  if (vocabCache) return Promise.resolve(vocabCache);
  if (vocabPromise) return vocabPromise;
  vocabPromise = fetchQuranVocabulary()
    .then((r) => {
      vocabCache = r.terms;
      return r.terms;
    })
    .catch(() => {
      vocabCache = [];
      return [];
    });
  return vocabPromise;
}

/**
 * Build a lookup map from a transliteration token → its root info.
 * Strips diacritics for fuzzy matching (so "yuṣallūna" matches even
 * if the marker has slightly different unicode normalization).
 */
function buildLookup(terms: QuranVocabularyTerm[]): Map<string, TransliterationEntry> {
  const map = new Map<string, TransliterationEntry>();
  for (const t of terms) {
    for (const hc of t.hard_cases) {
      const trans = hc.transliteration || '';
      if (!trans) continue;
      const key = normalize(trans);
      map.set(key, { term: t, transliteration: trans });
    }
  }
  return map;
}

function normalize(s: string): string {
  return s
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-zA-Z]/g, '')
    .toLowerCase();
}

// ---------- Hook ----------

export function useTermLookup() {
  const [lookup, setLookup] = useState<Map<string, TransliterationEntry> | null>(
    vocabCache ? buildLookup(vocabCache) : null,
  );
  useEffect(() => {
    if (lookup) return;
    let cancelled = false;
    loadVocabulary().then((terms) => {
      if (!cancelled) setLookup(buildLookup(terms));
    });
    return () => {
      cancelled = true;
    };
  }, [lookup]);
  return lookup;
}

// ---------- The chip ----------

/** Context for a specific occurrence of a surveyed root in a verse —
 * the AI-derived word-level meaning. When provided, the chip's tooltip
 * leads with this verse-specific gloss instead of the generic root note. */
export interface WordContext {
  surah: number;
  ayah: number;
  word_pos: number;
  meaning_short?: string;
  meaning_excerpt?: string | null;
  has_detail?: boolean;
}

function TermChip({
  transliteration,
  term,
  wordContext,
}: {
  transliteration: string;
  term: QuranVocabularyTerm;
  wordContext?: WordContext | null;
}) {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState<{ left: number; top: number; above: boolean } | null>(null);
  const chipRef = useRef<HTMLSpanElement | null>(null);
  const tipRef = useRef<HTMLDivElement | null>(null);
  const closeTimer = useRef<number | null>(null);
  const TIP_WIDTH = 320;
  const GAP = 8;

  useEffect(() => {
    if (!open) return;
    function place() {
      const chip = chipRef.current;
      if (!chip) return;
      const rect = chip.getBoundingClientRect();
      const tipH = tipRef.current?.getBoundingClientRect().height ?? 200;
      const { width: vw, height: vh } = viewportSize();
      const above = rect.top >= tipH + GAP || rect.top >= vh - rect.bottom;
      const center = rect.left + rect.width / 2;
      let left = center - TIP_WIDTH / 2;
      left = Math.max(GAP, Math.min(left, vw - TIP_WIDTH - GAP));
      const top = above ? rect.top - tipH - GAP : rect.bottom + GAP;
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
    closeTimer.current = window.setTimeout(() => setOpen(false), 120);
  }

  const slug = vocabTermSlug(term.root_buckwalter);

  const hasContext = !!(wordContext && wordContext.meaning_short);
  const wordHref = wordContext
    ? `/word/${wordContext.surah}:${wordContext.ayah}/${wordContext.word_pos}`
    : null;

  const tooltip = open && pos ? (
    <div
      ref={tipRef}
      onMouseEnter={show}
      onMouseLeave={hide}
      style={{ left: pos.left, top: pos.top, width: TIP_WIDTH }}
      className="fixed z-[1000] rounded-xl border border-stone-200 bg-white shadow-xl p-4 text-left pointer-events-auto"
    >
      {/* Primary content: verse-specific context-derived meaning when
          available; otherwise the generic root translation_note. */}
      {hasContext ? (
        <>
          <div className="text-[11px] tracking-wide uppercase text-amber-700 mb-1">
            In this verse
          </div>
          <div className="font-serif text-base text-stone-800 leading-snug">
            {wrapArabicRuns(wordContext!.meaning_short || '')}
          </div>
          {wordContext!.meaning_excerpt && (
            <div className="mt-2 text-xs text-stone-600 leading-relaxed line-clamp-5">
              {wrapArabicRuns(wordContext!.meaning_excerpt)}
            </div>
          )}
        </>
      ) : (
        term.translation_note ? (
          <div className="text-xs text-stone-700 leading-relaxed line-clamp-6">
            {wrapArabicRuns(term.translation_note)}
          </div>
        ) : (
          <div className="text-xs text-stone-500 italic">
            (No translation note available.)
          </div>
        )
      )}

      {/* Secondary: small root-info strip */}
      <div className="mt-3 pt-3 border-t border-stone-100 text-[11px] text-ink-muted">
        Root <span className="font-arabic text-sm text-stone-700 mx-0.5" lang="ar">{term.root_arabic}</span>
        <span className="mx-1">→</span>
        <span className="font-medium text-stone-700">{term.canonical_english}</span>
        {' '}· transliterated <em className="not-italic text-stone-700">{transliteration}</em>
      </div>

      {/* Drill-in links */}
      <div className="mt-2 flex items-center gap-3 text-[11px] font-medium">
        {wordHref && wordContext?.has_detail && (
          <a href={wordHref} className="text-amber-700 hover:text-amber-800 inline-flex items-center gap-0.5">
            Word details
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </a>
        )}
        <a href={`/quran-vocabulary#${slug}`} className="text-amber-700 hover:text-amber-800 inline-flex items-center gap-0.5">
          {hasContext ? 'About this root' : 'View in vocabulary'}
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </a>
      </div>
    </div>
  ) : null;

  return (
    <>
      <em
        ref={chipRef}
        onMouseEnter={show}
        onMouseLeave={hide}
        onFocus={show}
        onBlur={hide}
        tabIndex={0}
        className="cursor-help underline decoration-amber-500 decoration-wavy underline-offset-[3px] decoration-1 outline-none focus-visible:ring-2 focus-visible:ring-amber-400 rounded-sm font-medium"
      >
        {transliteration}
      </em>
      {tooltip && createPortal(tooltip, document.body)}
    </>
  );
}

// ---------- Word-family chip layer ----------
// In addition to the *xxx* italic transliteration markers above, we also
// chip plain English words ("prayer", "alms", "prostrate", …) when:
//   (a) the verse contains the matching surveyed root, AND
//   (b) the word appears in that root's chip_word_family.
// This scoping by verse-roots keeps false positives at zero — "prayer"
// in a non-Slw verse is left alone.

interface ChipMatch {
  start: number;
  end: number;
  matchedText: string;
  term: QuranVocabularyTerm;
  /** "italic" for *xxx* markers; "word" for word-family matches. */
  kind: 'italic' | 'word';
}

function findWordFamilyMatches(
  text: string,
  vocab: QuranVocabularyTerm[],
  surveyedRootsInVerse: string[] | undefined,
): ChipMatch[] {
  if (!text) return [];
  // If the caller knows which surveyed roots appear in the verse, use
  // only those. Otherwise consider all (looser).
  const allowedRoots = surveyedRootsInVerse
    ? new Set(surveyedRootsInVerse)
    : null;
  const eligibleTerms = allowedRoots
    ? vocab.filter((t) => allowedRoots.has(t.root_buckwalter))
    : vocab;
  if (!eligibleTerms.length) return [];

  // Build a single regex from all candidate words, longest-first to
  // prefer "remembrance" over "remember" when both could match.
  const wordsByTerm: Array<{ word: string; term: QuranVocabularyTerm }> = [];
  for (const term of eligibleTerms) {
    for (const w of term.chip_word_family || []) {
      wordsByTerm.push({ word: w, term });
    }
  }
  if (!wordsByTerm.length) return [];
  wordsByTerm.sort((a, b) => b.word.length - a.word.length);

  // Escape regex metas
  const escape = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const alternation = wordsByTerm.map((w) => escape(w.word)).join('|');
  // Whole-word, case-insensitive
  const re = new RegExp(`\\b(${alternation})\\b`, 'gi');

  const matches: ChipMatch[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    const matched = m[1];
    // Find the term this match belongs to (case-insensitive)
    const lower = matched.toLowerCase();
    const entry = wordsByTerm.find((w) => w.word.toLowerCase() === lower);
    if (!entry) continue;
    matches.push({
      start: m.index,
      end: m.index + matched.length,
      matchedText: matched,
      term: entry.term,
      kind: 'word',
    });
  }
  return matches;
}

function findItalicMatches(
  text: string,
  lookup: Map<string, TransliterationEntry>,
): ChipMatch[] {
  const out: ChipMatch[] = [];
  const regex = /\*([^\s*][^*]*?[^\s*]|[^\s*])\*/g;
  let m: RegExpExecArray | null;
  while ((m = regex.exec(text)) !== null) {
    const inner = m[1];
    const norm = normalize(inner);
    const entry = lookup.get(norm);
    if (entry) {
      out.push({
        start: m.index,
        end: m.index + m[0].length,
        matchedText: inner,
        term: entry.term,
        kind: 'italic',
      });
    } else {
      // Mark as plain italic — handled by leftover-text rendering
      out.push({
        start: m.index,
        end: m.index + m[0].length,
        matchedText: inner,
        // dummy term, filtered out before render
        term: null as unknown as QuranVocabularyTerm,
        kind: 'italic',
      });
    }
  }
  return out;
}

// ---------- Public renderer ----------

interface TranslationProps {
  text: string;
  /** Optional list of root_buckwalters present in the verse. When
   * provided, only word-family matches for these roots are chipped.
   * Without it, no word-family chipping happens (italic-only mode). */
  surveyedRootsInVerse?: string[];
  /** Optional map from root_buckwalter to an ordered list of word-level
   * context info (one entry per occurrence of the root in this verse).
   * The Nth chipped match in the translation gets the Nth context entry —
   * which lets the tooltip show the AI-derived meaning for THIS specific
   * word rather than the generic root note. */
  contextByRoot?: Map<string, WordContext[]>;
}

export function TranslationWithChips({
  text,
  surveyedRootsInVerse,
  contextByRoot,
}: TranslationProps) {
  const lookup = useTermLookup();

  const nodes = useMemo(() => {
    if (!text) return [] as React.ReactNode[];
    if (!lookup) return [text];

    // 1. Find italic markers (transliterations).
    const italicMatches = findItalicMatches(text, lookup);

    // 2. Find whole-word matches in the chip_word_family of each
    //    surveyed root in the verse. Only when surveyedRootsInVerse is
    //    given — without it, we conservatively skip word matching.
    const vocab: QuranVocabularyTerm[] = [];
    if (vocabCache && surveyedRootsInVerse) {
      vocab.push(...vocabCache);
    }
    const wordMatches = surveyedRootsInVerse
      ? findWordFamilyMatches(text, vocab, surveyedRootsInVerse)
      : [];

    // 3. Combine matches, sorted by start index, dropping word matches
    //    that fall inside an italic match (italic wins).
    const all: ChipMatch[] = [...italicMatches, ...wordMatches]
      .sort((a, b) => a.start - b.start);

    const filtered: ChipMatch[] = [];
    let cursor = 0;
    for (const m of all) {
      if (m.start < cursor) continue; // overlap, skip
      filtered.push(m);
      cursor = m.end;
    }

    // 4. Render — interleave plain text and chips. Track per-root
    //    occurrence counter so the Nth chip for root R gets the Nth
    //    word_pos's context.
    const out: React.ReactNode[] = [];
    let last = 0;
    let key = 0;
    const perRootCounter = new Map<string, number>();

    for (const m of filtered) {
      if (m.start > last) {
        out.push(<span key={key++}>{wrapArabicRuns(text.slice(last, m.start))}</span>);
      }
      if (m.kind === 'italic' && !m.term) {
        out.push(<em key={key++}>{wrapArabicRuns(m.matchedText)}</em>);
      } else {
        const root = m.term.root_buckwalter;
        const idx = perRootCounter.get(root) ?? 0;
        perRootCounter.set(root, idx + 1);
        const context = contextByRoot?.get(root)?.[idx] ?? null;
        out.push(
          <TermChip
            key={key++}
            transliteration={m.matchedText}
            term={m.term}
            wordContext={context}
          />,
        );
      }
      last = m.end;
    }
    if (last < text.length) {
      out.push(<span key={key++}>{wrapArabicRuns(text.slice(last))}</span>);
    }
    return out;
  }, [text, lookup, surveyedRootsInVerse, contextByRoot]);

  return <>{nodes}</>;
}

// Legacy single-pass (kept for any callers that want italic-only)
export function TranslationWithItalicChips({ text }: { text: string }) {
  const lookup = useTermLookup();

  const nodes = useMemo(() => {
    if (!text) return [] as React.ReactNode[];
    const out: React.ReactNode[] = [];
    const regex = /\*([^\s*][^*]*?[^\s*]|[^\s*])\*/g;
    let last = 0;
    let m: RegExpExecArray | null;
    let key = 0;
    while ((m = regex.exec(text)) !== null) {
      if (m.index > last) {
        out.push(<span key={key++}>{wrapArabicRuns(text.slice(last, m.index))}</span>);
      }
      const inner = m[1];
      const norm = normalize(inner);
      const entry = lookup?.get(norm);
      if (entry) {
        out.push(
          <TermChip key={key++} transliteration={inner} term={entry.term} />
        );
      } else {
        out.push(<em key={key++}>{wrapArabicRuns(inner)}</em>);
      }
      last = regex.lastIndex;
    }
    if (last < text.length) {
      out.push(<span key={key++}>{wrapArabicRuns(text.slice(last))}</span>);
    }
    return out;
  }, [text, lookup]);

  return <>{nodes}</>;
}
