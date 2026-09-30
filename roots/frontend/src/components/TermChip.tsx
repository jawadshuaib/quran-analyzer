import { useState, useEffect, useRef, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { fetchQuranVocabulary, fetchWordMeanings } from '../api/quran';
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

// Verse key ("2:43") -> the surveyed roots it contains, from the vocabulary's
// per-term verse lists. Lets a translation shown anywhere (search results, a
// verse-reference preview) get the verse page's chips from its reference alone.
let rootsByVerse: Map<string, string[]> | null = null;

function surveyedRootsFor(surah: number, ayah: number): string[] {
  if (!vocabCache) return [];
  if (!rootsByVerse) {
    rootsByVerse = new Map();
    for (const t of vocabCache) {
      for (const v of t.verses ?? []) {
        const list = rootsByVerse.get(v) ?? [];
        list.push(t.root_buckwalter);
        rootsByVerse.set(v, list);
      }
    }
  }
  return rootsByVerse.get(`${surah}:${ayah}`) ?? [];
}

// The verse page hands each chip its word's meaning in that verse. Elsewhere a
// chip loads it on its first hover: one small request per verse, shared by all
// of that verse's chips. Built the way VerseDisplay builds contextByRoot, so
// the Nth chip for a root gets the Nth word carrying it.
const verseContextCache = new Map<string, Promise<Map<string, WordContext[]>>>();

function loadVerseContext(surah: number, ayah: number): Promise<Map<string, WordContext[]>> {
  const key = `${surah}:${ayah}`;
  let p = verseContextCache.get(key);
  if (!p) {
    p = fetchWordMeanings(surah, ayah)
      .then((res) => {
        const map = new Map<string, WordContext[]>();
        if (!res?.roots) return map;
        const positions = Object.keys(res.roots).map(Number).sort((a, b) => a - b);
        for (const pos of positions) {
          const root = res.roots[String(pos)];
          const wm = res.meanings[String(pos)];
          const list = map.get(root) ?? [];
          list.push({
            surah,
            ayah,
            word_pos: pos,
            meaning_short: wm?.preferred_translation || wm?.meaning_short,
            meaning_excerpt: wm?.meaning_excerpt,
            has_detail: wm?.has_detail,
          });
          map.set(root, list);
        }
        return map;
      })
      .catch(() => new Map<string, WordContext[]>());
    verseContextCache.set(key, p);
  }
  return p;
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
  lazy,
}: {
  transliteration: string;
  term: QuranVocabularyTerm;
  wordContext?: WordContext | null;
  /** Where the chip's word sits when no wordContext is passed: its verse and
   *  which occurrence of the root it is. Its meaning is fetched on first hover. */
  lazy?: { surah: number; ayah: number; index: number };
}) {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState<{ left: number; top: number; above: boolean } | null>(null);
  // undefined until the lazily fetched meaning arrives; null when there is none
  const [lazyContext, setLazyContext] = useState<WordContext | null | undefined>(undefined);
  const chipRef = useRef<HTMLSpanElement | null>(null);
  const tipRef = useRef<HTMLDivElement | null>(null);
  const closeTimer = useRef<number | null>(null);
  const requested = useRef(false);
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
    if (!wordContext && lazy && !requested.current) {
      requested.current = true;
      loadVerseContext(lazy.surah, lazy.ayah).then((map) =>
        setLazyContext(map.get(term.root_buckwalter)?.[lazy.index] ?? null),
      );
    }
  }
  function hide() {
    closeTimer.current = window.setTimeout(() => setOpen(false), 120);
  }

  const context = wordContext ?? lazyContext ?? null;
  const loading = !wordContext && !!lazy && lazyContext === undefined;
  const hasContext = !!(context && context.meaning_short);
  const wordHref = context
    ? `/word/${context.surah}:${context.ayah}/${context.word_pos}`
    : null;

  // The tooltip is portaled, but React still bubbles its events up the tree:
  // stop them here so a click on its links never also reaches a card or link
  // the chip sits inside (a search result, a verse preview).
  const tooltip = open && pos ? (
    <div
      ref={tipRef}
      onMouseEnter={show}
      onMouseLeave={hide}
      onClick={(e) => e.stopPropagation()}
      style={{ left: pos.left, top: pos.top, width: TIP_WIDTH }}
      className="fixed z-[1000] rounded-xl border border-stone-200 bg-white shadow-xl p-4 text-left not-italic font-normal pointer-events-auto"
    >
      {/* Primary content: verse-specific context-derived meaning when
          available; otherwise the generic root translation_note. */}
      {loading ? (
        <div className="space-y-2" aria-label="Loading">
          <div className="h-4 w-2/3 animate-pulse rounded bg-stone-100" />
          <div className="h-3 w-full animate-pulse rounded bg-stone-100" />
        </div>
      ) : hasContext ? (
        <>
          <div className="text-[11px] tracking-wide uppercase text-amber-700 mb-1">
            In this verse
          </div>
          <div className="font-serif text-base text-stone-800 leading-snug">
            {wrapArabicRuns(context!.meaning_short || '')}
          </div>
          {context!.meaning_excerpt && (
            <div className="mt-2 text-xs text-stone-600 leading-relaxed line-clamp-5">
              {wrapArabicRuns(context!.meaning_excerpt)}
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
        {wordHref && context?.has_detail && (
          <a href={wordHref} className="text-amber-700 hover:text-amber-800 inline-flex items-center gap-0.5">
            Word details
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </a>
        )}
        <a href={`/root/${encodeURIComponent(term.root_buckwalter)}`} className="text-amber-700 hover:text-amber-800 inline-flex items-center gap-0.5">
          About this root
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
        onClick={(e) => {
          // A tap shows the tooltip; it must not also follow a link or card
          // the translation sits in.
          e.preventDefault();
          e.stopPropagation();
          show();
        }}
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
  /** The verse this is a translation of. Enough on its own for the same chips
   * the verse page shows: the surveyed roots in the verse come from the
   * vocabulary, and each chip fetches its word's meaning on first hover.
   * Pass it wherever a translation appears. */
  verse?: { surah: number; ayah: number };
  /** Optional list of root_buckwalters present in the verse. When
   * provided, only word-family matches for these roots are chipped.
   * Without it (and without `verse`), no word-family chipping happens
   * (italic-only mode). */
  surveyedRootsInVerse?: string[];
  /** Optional map from root_buckwalter to an ordered list of word-level
   * context info (one entry per occurrence of the root in this verse).
   * The Nth chipped match in the translation gets the Nth context entry —
   * which lets the tooltip show the AI-derived meaning for THIS specific
   * word rather than the generic root note. */
  contextByRoot?: Map<string, WordContext[]>;
  /** How plain text between chips is drawn (e.g. search-term highlighting).
   * Defaults to wrapArabicRuns. */
  renderText?: (s: string) => React.ReactNode;
}

/** *term* markers as plain italics: what the text shows until the vocabulary
 *  has loaded, so the asterisks themselves never appear. */
function italicsOnly(text: string, render: (s: string) => React.ReactNode): React.ReactNode[] {
  return text.split(/\*([^\s*][^*]*?[^\s*]|[^\s*])\*/g).map((part, i) =>
    i % 2 === 1 ? <em key={i}>{wrapArabicRuns(part)}</em> : <span key={i}>{render(part)}</span>,
  );
}

export function TranslationWithChips({
  text,
  verse,
  surveyedRootsInVerse,
  contextByRoot,
  renderText,
}: TranslationProps) {
  const lookup = useTermLookup();
  const surah = verse?.surah;
  const ayah = verse?.ayah;

  const nodes = useMemo(() => {
    const render = renderText ?? wrapArabicRuns;
    if (!text) return [] as React.ReactNode[];
    if (!lookup) return italicsOnly(text, render);

    const roots = surveyedRootsInVerse
      ?? (surah !== undefined && ayah !== undefined ? surveyedRootsFor(surah, ayah) : undefined);

    // 1. Find italic markers (transliterations).
    const italicMatches = findItalicMatches(text, lookup);

    // 2. Find whole-word matches in the chip_word_family of each
    //    surveyed root in the verse. Only when the verse's roots are
    //    known — without them, we conservatively skip word matching.
    const vocab: QuranVocabularyTerm[] = [];
    if (vocabCache && roots) {
      vocab.push(...vocabCache);
    }
    const wordMatches = roots
      ? findWordFamilyMatches(text, vocab, roots)
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
        out.push(<span key={key++}>{render(text.slice(last, m.start))}</span>);
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
            lazy={
              !contextByRoot && surah !== undefined && ayah !== undefined
                ? { surah, ayah, index: idx }
                : undefined
            }
          />,
        );
      }
      last = m.end;
    }
    if (last < text.length) {
      out.push(<span key={key++}>{render(text.slice(last))}</span>);
    }
    return out;
  }, [text, lookup, surah, ayah, surveyedRootsInVerse, contextByRoot, renderText]);

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
