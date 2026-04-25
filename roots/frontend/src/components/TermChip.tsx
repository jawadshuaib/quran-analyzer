import { useState, useEffect, useRef, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { fetchQuranVocabulary, vocabTermSlug } from '../api/quran';
import type { QuranVocabularyTerm } from '../api/quran';

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

function TermChip({
  transliteration,
  term,
}: {
  transliteration: string;
  term: QuranVocabularyTerm;
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
      const vw = window.innerWidth;
      const vh = window.innerHeight;
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

  const tooltip = open && pos ? (
    <div
      ref={tipRef}
      onMouseEnter={show}
      onMouseLeave={hide}
      style={{ left: pos.left, top: pos.top, width: TIP_WIDTH }}
      className="fixed z-[1000] rounded-xl border border-stone-200 bg-white shadow-xl p-4 text-left pointer-events-auto"
    >
      <div className="flex items-baseline gap-2 mb-1">
        <span className="font-serif text-lg text-stone-800" lang="ar">
          {term.root_arabic}
        </span>
        <span className="text-stone-300">→</span>
        <span className="text-sm font-semibold text-amber-700">
          {term.canonical_english}
        </span>
      </div>
      <div className="text-[11px] text-ink-muted tracking-wide mb-2">
        Transliterated as <em className="not-italic font-medium text-stone-600">{transliteration}</em>
        {' '}· {term.occurrence_count} occurrences in the Qur'an
      </div>
      {term.translation_note && (
        <div className="mt-2 text-xs text-stone-600 leading-relaxed line-clamp-6">
          {term.translation_note}
        </div>
      )}
      <div className="mt-3 pt-3 border-t border-stone-100">
        <a
          href={`/quran-vocabulary#${slug}`}
          className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-700 hover:text-amber-800"
        >
          View in vocabulary
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

// ---------- Public renderer: parse *...* and emit chips inline ----------

export function TranslationWithChips({ text }: { text: string }) {
  const lookup = useTermLookup();

  const nodes = useMemo(() => {
    if (!text) return [] as React.ReactNode[];
    const out: React.ReactNode[] = [];
    // Match *xxx* — non-greedy, no whitespace at start/end, allow Unicode letters
    // and the common transliteration diacritics ā ī ū ḥ ṣ ṭ ẓ ḍ ʿ ʾ etc.
    const regex = /\*([^\s*][^*]*?[^\s*]|[^\s*])\*/g;
    let last = 0;
    let m: RegExpExecArray | null;
    let key = 0;
    while ((m = regex.exec(text)) !== null) {
      if (m.index > last) {
        out.push(text.slice(last, m.index));
      }
      const inner = m[1];
      const norm = normalize(inner);
      const entry = lookup?.get(norm);
      if (entry) {
        out.push(
          <TermChip key={key++} transliteration={inner} term={entry.term} />
        );
      } else {
        // Italic but not a known term — render as plain emphasis.
        out.push(<em key={key++}>{inner}</em>);
      }
      last = regex.lastIndex;
    }
    if (last < text.length) {
      out.push(text.slice(last));
    }
    return out;
  }, [text, lookup]);

  return <>{nodes}</>;
}
