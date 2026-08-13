import { useState, useRef, useEffect, useMemo } from 'react';
import type { VerseData, Word, CognateData, RootSummary, SearchTerm, WordMeaningBrief, AITranslationData, VerseExegesisData, VersePoetryNote, VerseRootLexicon } from '../types';
import { searchWordsCount, fetchWordMeanings, fetchAITranslation, fetchVerseExegesis, fetchVersePoetry, fetchVerseRootLexicon } from '../api/quran';
import RootLexiconPanel from './RootLexiconPanel';
import FormattedText, { FormattedInline, linkifyTranslationNotesRefs } from './FormattedText';
import { linkifyGrammarTermRefs } from '../utils/grammar-term-refs';
import { useGrammarTermsIfMentioned } from '../hooks/useGrammarTerms';
import { TranslationWithChips, type WordContext } from './TermChip';
import WordTooltip from './WordTooltip';
import CognatePanel from './CognatePanel';
import SelectionHeader from './SelectionHeader';
import MethodologyTooltip from './MethodologyTooltip';
import SaveButton from './SaveButton';
import NoteButton from './NoteButton';
import VersePlayButton from './VersePlayButton';
import HighlightCross from './HighlightCross';
import { splitDepartureNotes } from '../utils/departure-notes';
import { wrapArabicRuns } from '../utils/arabic-runs';
import { useVerseHighlights } from '../hooks/useVerseHighlights';
import { HIGHLIGHT_BG, removeHighlight, isCoarsePointer } from '../utils/verse-highlights';
import { getWordHover, subscribeWordHover, isWordHovered } from '../utils/word-hover';
import { getCopyContext, openCopyModal, subscribeCopyContext } from '../utils/copy-context';

const WORD_TO_WORD_KEY = 'quranExplorer.wordToWordEnabled';

interface Props {
  data: VerseData;
  onWordSearch?: (terms: SearchTerm[], queryVerse: { surah: number; ayah: number }) => void;
  wordSearchLoading?: boolean;
  onNavigate?: (surah: number, ayah: number) => void;
}

/** Return the primary content segment of a word, skipping prefixes/suffixes/pronouns. */
function getContentSegment(word: Word) {
  return (
    word.segments.find(
      (s) =>
        (s.lemma_buckwalter || s.root_buckwalter) &&
        s.pos !== 'Prefix' && s.pos !== 'Suffix' && s.pos !== 'Pronoun'
    ) ??
    word.segments.find(
      (s) =>
        s.form_buckwalter &&
        s.pos !== 'Prefix' && s.pos !== 'Suffix' && s.pos !== 'Pronoun'
    )
  );
}

export default function VerseDisplay({ data, onWordSearch, wordSearchLoading, onNavigate }: Props) {
  const [hoveredPos, setHoveredPos] = useState<number | null>(null);
  const [selectedPositions, setSelectedPositions] = useState<Set<number>>(new Set());
  const [expandedRoot, setExpandedRoot] = useState<string | null>(null);
  const [resultCount, setResultCount] = useState<number | null>(null);
  const [wordMeanings, setWordMeanings] = useState<Record<string, WordMeaningBrief>>({});
  const [aiTranslation, setAiTranslation] = useState<AITranslationData | null>(null);
  const [exegesis, setExegesis] = useState<VerseExegesisData | null>(null);
  const [poetry, setPoetry] = useState<VersePoetryNote | null>(null);
  const [lexicon, setLexicon] = useState<VerseRootLexicon | null>(null);
  const [wordToWordEnabled, setWordToWordEnabled] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return window.localStorage.getItem(WORD_TO_WORD_KEY) === '1';
  });
  const containerRef = useRef<HTMLDivElement>(null);

  const verseKey = `${data.surah}:${data.ayah}`;
  // User highlights for this verse (shared store → the same marks appear in
  // reading mode). posMap answers per-word: highlighted? color? is it start?
  const { posMap } = useVerseHighlights(verseKey);
  const [hoverHl, setHoverHl] = useState<string | null>(null);
  const coarse = isCoarsePointer();
  const [copyActive, setCopyActive] = useState(() => getCopyContext()?.verseKey === verseKey);
  useEffect(
    () => subscribeCopyContext(() => setCopyActive(getCopyContext()?.verseKey === verseKey)),
    [verseKey],
  );

  // Words the reader is pointing at via a citation in the exegesis note.
  const [noteHover, setNoteHover] = useState(getWordHover);
  useEffect(() => subscribeWordHover(setNoteHover), []);

  const uthmaniWords = data.text_uthmani.split(/\s+/).filter(Boolean);

  // Build position -> Word lookup (positions are 1-indexed)
  const wordMap = new Map<number, Word>();
  data.words.forEach((w) => wordMap.set(w.position, w));

  // Build root_buckwalter -> cognate data lookup
  const rootCognateMap = new Map<string, CognateData>();
  data.roots_summary.forEach((r) => {
    if (r.cognate) {
      rootCognateMap.set(r.root_buckwalter, r.cognate);
    }
  });

  // Build root_buckwalter -> ordered list of word-level contexts. Each
  // entry carries the AI-derived per-word meaning for one occurrence of
  // the root in this verse, in word-position order. The TermChip layer
  // uses these to show context-specific tooltips on hover instead of
  // the generic root note.
  const contextByRoot = useMemo(() => {
    const map = new Map<string, WordContext[]>();
    const ordered = [...data.words].sort((a, b) => a.position - b.position);
    for (const word of ordered) {
      const rootSeg = word.segments.find((s) => s.root_buckwalter);
      if (!rootSeg) continue;
      const root = rootSeg.root_buckwalter;
      const wm = wordMeanings[String(word.position)];
      const list = map.get(root) ?? [];
      list.push({
        surah: data.surah,
        ayah: data.ayah,
        word_pos: word.position,
        meaning_short: wm?.preferred_translation || wm?.meaning_short,
        meaning_excerpt: wm?.meaning_excerpt,
        has_detail: wm?.has_detail,
      });
      map.set(root, list);
    }
    return map;
  }, [data, wordMeanings]);

  // Get cognate for a word (from its first root-bearing segment)
  function getCognateForWord(word: Word): CognateData | undefined {
    const rootBw = word.segments.find((s) => s.root_buckwalter)?.root_buckwalter;
    return rootBw ? rootCognateMap.get(rootBw) : undefined;
  }

  // Reset state when verse changes
  useEffect(() => {
    setSelectedPositions(new Set());
    setExpandedRoot(null);
    setResultCount(null);
    setWordMeanings({});
    setAiTranslation(null);
  }, [data]);

  // Fetch AI word meanings for this verse
  useEffect(() => {
    let cancelled = false;
    fetchWordMeanings(data.surah, data.ayah).then((res) => {
      if (!cancelled && res) setWordMeanings(res.meanings);
    });
    return () => { cancelled = true; };
  }, [data.surah, data.ayah]);

  // Fetch AI translation for this verse
  useEffect(() => {
    let cancelled = false;
    fetchAITranslation(data.surah, data.ayah).then((result) => {
      if (!cancelled) setAiTranslation(result);
    });
    return () => { cancelled = true; };
  }, [data.surah, data.ayah]);

  // Exegesis and Translation Notes sometimes reference a grammar-glossary
  // term (e.g. "causative form IV") that's opaque without a definition.
  // useGrammarTermsIfMentioned only fetches the (cached, ~600-term) glossary
  // when one of them actually mentions a curated term — most verses won't.
  const grammarTerms = useGrammarTermsIfMentioned([
    aiTranslation?.departure_notes,
    exegesis?.exegesis_markdown,
  ]);

  // Fetch the approved teacher-voice exegesis (if any) for this verse
  useEffect(() => {
    let cancelled = false;
    setExegesis(null);
    fetchVerseExegesis(data.surah, data.ayah).then((result) => {
      if (!cancelled) setExegesis(result);
    }).catch(() => { if (!cancelled) setExegesis(null); });
    return () => { cancelled = true; };
  }, [data.surah, data.ayah]);

  // Fetch the approved pre-Islamic poetry note (if any) — shown below exegesis
  useEffect(() => {
    let cancelled = false;
    setPoetry(null);
    fetchVersePoetry(data.surah, data.ayah).then((result) => {
      if (!cancelled) setPoetry(result);
    }).catch(() => { if (!cancelled) setPoetry(null); });
    return () => { cancelled = true; };
  }, [data.surah, data.ayah]);

  // Fetch the per-word contemporaneous-attestation lexicon (Qurʾān-only)
  useEffect(() => {
    let cancelled = false;
    setLexicon(null);
    fetchVerseRootLexicon(data.surah, data.ayah).then((result) => {
      if (!cancelled) setLexicon(result);
    }).catch(() => { if (!cancelled) setLexicon(null); });
    return () => { cancelled = true; };
  }, [data.surah, data.ayah]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(WORD_TO_WORD_KEY, wordToWordEnabled ? '1' : '0');
  }, [wordToWordEnabled]);

  const hasSelection = selectedPositions.size > 0;

  // Click outside the card to dismiss all selections
  useEffect(() => {
    if (!hasSelection) return;
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setSelectedPositions(new Set());
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [hasSelection]);

  // Build search terms from selected words — clicking a word searches by its
  // ROOT (broadest match, every derived form), not the specific word/lemma.
  // Words with no root (rare function words) contribute nothing to search.
  function buildAllSearchTerms(): SearchTerm[] {
    const terms: SearchTerm[] = [];
    const seenRoots = new Set<string>();

    for (const pos of selectedPositions) {
      const word = wordMap.get(pos);
      if (!word) continue;
      const seg = getContentSegment(word);
      const rootBw = seg?.root_buckwalter;
      if (!rootBw || seenRoots.has(rootBw)) continue;
      seenRoots.add(rootBw);
      terms.push({
        lemma_bw: null,
        root_bw: rootBw,
        form_bw: null,
        display_arabic: seg!.root_arabic || uthmaniWords[pos - 1] || seg!.form_arabic,
      });
    }

    return terms;
  }

  // Stable key for the current selection
  const selectionKey = Array.from(selectedPositions).sort((a, b) => a - b).join(',');

  // Auto-count results when selection changes
  useEffect(() => {
    if (!hasSelection) {
      setResultCount(null);
      return;
    }
    const terms = buildAllSearchTerms();
    if (terms.length === 0) {
      setResultCount(0);
      return;
    }
    let cancelled = false;
    setResultCount(null); // loading
    const timer = setTimeout(() => {
      searchWordsCount(terms, { surah: data.surah, ayah: data.ayah }).then(
        (count) => { if (!cancelled) setResultCount(count); },
        () => { if (!cancelled) setResultCount(0); },
      );
    }, 200);
    return () => { cancelled = true; clearTimeout(timer); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectionKey, data.surah, data.ayah]);

  // Find the root summary for the expanded root
  const expandedRootData: RootSummary | undefined = expandedRoot
    ? data.roots_summary.find((r) => r.root_buckwalter === expandedRoot)
    : undefined;

  // Build the header's root chips — one per distinct root among the selected
  // words (mirrors buildAllSearchTerms's dedup), so the header always shows
  // what's actually being searched (the root), not the clicked word's surface
  // form. Each chip remembers every position that fed it, so removing the
  // chip clears all of them.
  const selectedRootItems = (() => {
    const byRoot = new Map<string, { root_buckwalter: string; root_arabic: string; positions: number[] }>();
    for (const pos of Array.from(selectedPositions).sort((a, b) => a - b)) {
      const word = wordMap.get(pos);
      if (!word) continue;
      const seg = getContentSegment(word);
      const rootBw = seg?.root_buckwalter;
      if (!rootBw) continue;
      if (!byRoot.has(rootBw)) {
        byRoot.set(rootBw, { root_buckwalter: rootBw, root_arabic: seg!.root_arabic || rootBw, positions: [] });
      }
      byRoot.get(rootBw)!.positions.push(pos);
    }
    return Array.from(byRoot.values());
  })();

  function handleSearch() {
    if (!onWordSearch) return;
    const terms = buildAllSearchTerms();
    if (terms.length === 0) return;
    onWordSearch(terms, { surah: data.surah, ayah: data.ayah });
  }

  function clearAll() {
    setSelectedPositions(new Set());
  }

  // Delegated hover over the Arabic line: surface the delete-× for whichever
  // highlight the pointer is over.
  function handleHighlightHover(e: React.MouseEvent) {
    const el = (e.target as HTMLElement).closest('[data-word-pos]');
    const pos = el ? parseInt(el.getAttribute('data-word-pos') || '', 10) : NaN;
    const hl = Number.isFinite(pos) ? posMap.get(pos) : undefined;
    setHoverHl(hl ? hl.id : null);
  }

  function getWordToWordLabel(pos: number, word: Word | undefined): string {
    const wm = wordMeanings[String(pos)];
    if (wm?.preferred_translation) return wm.preferred_translation;
    if (wm?.meaning_short) return wm.meaning_short;
    return word?.translation || '';
  }

  return (
    <div
      ref={containerRef}
      className="relative rounded-xl border border-stone-200 bg-white p-6 shadow-sm"
      onClick={clearAll}
    >
      {/* Save + note buttons — top-left, floating on card border */}
      <div className="absolute -top-2.5 -left-2.5 z-10 flex items-center gap-1 rounded-full bg-white shadow-sm pr-1">
        <SaveButton
          type="verse"
          itemKey={`${data.surah}:${data.ayah}`}
          label={`Surah ${data.surah_name} ${data.surah}:${data.ayah}`}
          href={`/verse/${data.surah}:${data.ayah}`}
          subtitle={data.translation}
          arabic={data.text_uthmani}
          translation={data.translation}
        />
        <VersePlayButton surah={data.surah} ayah={data.ayah} />
        <NoteButton
          item={{
            type: 'verse',
            key: `${data.surah}:${data.ayah}`,
            label: `Surah ${data.surah_name} ${data.surah}:${data.ayah}`,
            href: `/verse/${data.surah}:${data.ayah}`,
            subtitle: data.translation,
            arabic: data.text_uthmani,
            translation: data.translation,
          }}
          accent="violet"
        />
        {copyActive && (
          <span data-copy-icon className="animate-chip-pop">
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); openCopyModal(); }}
              aria-label="Copy verse"
              title="Copy verse"
              className="flex h-7 w-7 items-center justify-center rounded-full text-stone-400 transition-colors hover:text-emerald-600"
            >
              <svg viewBox="0 0 16 16" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.5">
                <rect x="5.5" y="5.5" width="8" height="8" rx="1.5" />
                <path d="M3.5 10.5H3A1.5 1.5 0 011.5 9V3A1.5 1.5 0 013 1.5h6A1.5 1.5 0 0110.5 3v.5" strokeLinecap="round" />
              </svg>
            </button>
          </span>
        )}
      </div>
      {hasSelection && (
        <SelectionHeader
          selectedWords={[]}
          selectedRoots={selectedRootItems}
          onDeselectWord={() => {}}
          onDeselectRoot={(rbw) => {
            const item = selectedRootItems.find((r) => r.root_buckwalter === rbw);
            if (!item) return;
            setSelectedPositions((prev) => {
              const next = new Set(prev);
              item.positions.forEach((p) => next.delete(p));
              return next;
            });
          }}
          onClear={clearAll}
          onSearch={handleSearch}
          loading={wordSearchLoading}
          resultCount={resultCount}
        />
      )}

      <div className="mb-1 flex items-center justify-between gap-3">
        <div className="flex items-center gap-1 text-sm font-medium text-stone-500">
          {data.previous && (
            <button
              type="button"
              aria-label={`Previous verse ${data.previous.surah}:${data.previous.ayah}`}
              className="inline-flex h-6 w-6 items-center justify-center rounded-md text-stone-400 transition-colors hover:bg-stone-100 hover:text-stone-600"
              onClick={(e) => {
                e.stopPropagation();
                onNavigate?.(data.previous!.surah, data.previous!.ayah);
              }}
            >
              <svg
                aria-hidden="true"
                viewBox="0 0 20 20"
                fill="none"
                className="h-3.5 w-3.5"
              >
                <path
                  d="M12.5 4.5L7 10l5.5 5.5"
                  stroke="currentColor"
                  strokeWidth="1.7"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          )}
          <span>Surah {data.surah}, Ayah {data.ayah}</span>
          {data.next && (
            <button
              type="button"
              aria-label={`Next verse ${data.next.surah}:${data.next.ayah}`}
              className="inline-flex h-6 w-6 items-center justify-center rounded-md text-stone-400 transition-colors hover:bg-stone-100 hover:text-stone-600"
              onClick={(e) => {
                e.stopPropagation();
                onNavigate?.(data.next!.surah, data.next!.ayah);
              }}
            >
              <svg
                aria-hidden="true"
                viewBox="0 0 20 20"
                fill="none"
                className="h-3.5 w-3.5"
              >
                <path
                  d="M7.5 4.5L13 10l-5.5 5.5"
                  stroke="currentColor"
                  strokeWidth="1.7"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          )}
        </div>
        <label
          className="inline-flex items-center gap-2 text-xs font-medium text-stone-500 select-none"
          onClick={(e) => e.stopPropagation()}
        >
          <span>Word-to-Word</span>
          <button
            type="button"
            role="switch"
            aria-checked={wordToWordEnabled}
            aria-label="Toggle word-to-word translation"
            className={`relative h-5 w-9 rounded-full transition-colors ${
              wordToWordEnabled ? 'bg-emerald-500' : 'bg-stone-300'
            }`}
            onClick={() => setWordToWordEnabled((prev) => !prev)}
          >
            <span
              className={`absolute top-0.5 h-4 w-4 rounded-full bg-white transition-transform ${
                wordToWordEnabled ? 'translate-x-4 left-0.5' : 'translate-x-0 left-0.5'
              }`}
            />
          </button>
        </label>
      </div>

      <div
        dir="rtl"
        lang="ar"
        className="mb-4 text-3xl leading-[2.8] font-arabic text-stone-800 flex flex-wrap gap-x-2 gap-y-2"
        data-arabic-region
        data-verse-key={verseKey}
        data-verse-text={data.text_uthmani}
        data-verse-translation={data.translation}
        onMouseOver={handleHighlightHover}
        onMouseLeave={() => setHoverHl(null)}
      >
        {uthmaniWords.map((word, idx) => {
          const pos = idx + 1;
          const wordData = wordMap.get(pos);
          const isSelected = selectedPositions.has(pos);
          const isHovered = !hasSelection && hoveredPos === pos;
          const isActive = isSelected || isHovered;
          // Persistent user highlight (shows at rest; the transient
          // selection/hover colors take over while interacting).
          const hl = posMap.get(pos);
          const isHlStart = !!hl && pos === hl.start;
          // Pointed at from a citation in the note — outranks the resting
          // user highlight so the quoted phrase reads as one block.
          const fromNote = isWordHovered(noteHover, verseKey, pos);

          return (
            <span
              key={pos}
              data-word-pos={pos}
              // No colour transition: this background can change while the
              // pointer is far away (driven by hovering a citation in the note
              // below), and an animated background-color with nothing forcing a
              // repaint leaves a stale sliver of the old paint behind.
              className={`relative inline-flex flex-col items-center cursor-pointer rounded-md px-1 ${
                fromNote
                  ? 'bg-emerald-200 text-emerald-950'
                  : isSelected
                    ? 'bg-emerald-100 text-emerald-900 ring-1 ring-emerald-400'
                    : isHovered
                      ? 'bg-emerald-100 text-emerald-900'
                      : hl
                        ? HIGHLIGHT_BG[hl.color]
                        : 'hover:bg-stone-100'
              }`}
              onMouseEnter={() => {
                if (!hasSelection) setHoveredPos(pos);
              }}
              onMouseLeave={() => {
                if (!hasSelection) setHoveredPos(null);
              }}
              onClick={(e) => {
                e.stopPropagation();
                // If this "click" is the tail of a drag text-selection on this
                // word, it's a highlight gesture — don't also toggle morphology
                // selection (which would pop the tooltip + SelectionHeader).
                const sel = window.getSelection();
                if (sel && !sel.isCollapsed && sel.rangeCount > 0 &&
                    sel.getRangeAt(0).intersectsNode(e.currentTarget)) {
                  return;
                }
                setSelectedPositions((prev) => {
                  const next = new Set(prev);
                  if (next.has(pos)) {
                    next.delete(pos);
                  } else {
                    next.add(pos);
                  }
                  return next;
                });
              }}
            >
              {isHlStart && (
                <HighlightCross
                  visible={hoverHl === hl!.id || coarse}
                  onRemove={() => { removeHighlight(verseKey, hl!.id); setHoverHl(null); }}
                />
              )}
              <span>{word}</span>
              {wordToWordEnabled && getWordToWordLabel(pos, wordData) && (
                <span
                  dir="ltr"
                  lang="en"
                  className="mt-0.5 max-w-24 text-[10px] leading-tight font-sans text-stone-500 text-center normal-case"
                >
                  {wrapArabicRuns(getWordToWordLabel(pos, wordData))}
                </span>
              )}
              {isActive && wordData && (
                <WordTooltip
                  word={wordData}
                  cognate={getCognateForWord(wordData)}
                  aiMeaning={wordMeanings[String(pos)]?.meaning_short}
                  wordDetailUrl={wordMeanings[String(pos)]?.has_detail ? `/word/${data.surah}:${data.ayah}/${pos}` : undefined}
                  preferredTranslation={wordMeanings[String(pos)]?.preferred_translation}
                  preferredSource={wordMeanings[String(pos)]?.preferred_source}
                  highlight={{
                    verseKey,
                    pos,
                    activeColor: hl?.color,
                    meta: { arabic: data.text_uthmani, translation: data.translation },
                  }}
                />
              )}
            </span>
          );
        })}
      </div>

      <p className="text-stone-600 italic">
        <TranslationWithChips
          text={aiTranslation ? aiTranslation.translation : data.translation}
          surveyedRootsInVerse={data.roots_summary.map((r) => r.root_buckwalter)}
          contextByRoot={contextByRoot}
        />
      </p>

      {/* Exegesis leads (it's the synthesis); Translation Notes follows as the
          supporting detail. When exegesis prose refers to "the translation
          notes", that phrase becomes a smooth-scroll link down to them. */}
      {(exegesis || aiTranslation?.departure_notes) && (
        <div className="mt-4 rounded-lg bg-violet-50 border border-violet-100 p-3">
          {exegesis && (
            <div>
              <div className="flex items-center gap-1.5 mb-1.5">
                <span className="text-xs font-medium text-violet-600">Exegesis</span>
                <MethodologyTooltip />
              </div>
              <FormattedText
                text={linkifyGrammarTermRefs(linkifyTranslationNotesRefs(exegesis.exegesis_markdown))}
                anchors={
                  exegesis.word_anchors?.length
                    ? { verseKey, list: exegesis.word_anchors }
                    : undefined
                }
                translationNotesId={
                  aiTranslation?.departure_notes
                    ? `translation-notes-${data.surah}-${data.ayah}`
                    : undefined
                }
                grammarTerms={grammarTerms ?? undefined}
                className="text-sm text-violet-900/90 leading-relaxed"
              />
            </div>
          )}

          {aiTranslation?.departure_notes && (
            <div
              id={`translation-notes-${data.surah}-${data.ayah}`}
              className={`scroll-mt-6 ${exegesis ? 'mt-3 pt-3 border-t border-violet-200/70' : ''}`}
            >
              <div className="flex items-center gap-1.5 mb-1">
                <span className="text-xs font-medium text-violet-600">Translation Notes</span>
                <MethodologyTooltip />
              </div>
              <div className="text-sm text-violet-800 leading-relaxed">
                {splitDepartureNotes(aiTranslation.departure_notes).map((line, i) => (
                  <p key={i} className={i > 0 ? 'mt-1.5' : ''}>
                    <FormattedInline
                      text={linkifyGrammarTermRefs(line)}
                      grammarTerms={grammarTerms ?? undefined}
                      anchors={
                        aiTranslation.word_anchors?.length
                          ? { verseKey, list: aiTranslation.word_anchors }
                          : undefined
                      }
                    />
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Pre-Islamic poetry note — sits below the exegesis; auto-hides when none.
          Poetic lines are linked inline within the prose (not listed as blocks,
          so a reader can't mistake them for Qurʾān); no tier labels shown. */}
      {poetry && (
        <div className="mt-4 rounded-lg bg-amber-50 border border-amber-200 p-3">
          <div className="text-xs font-medium text-amber-700 mb-1.5">In Pre-Islamic Poetry</div>
          <FormattedText
            text={poetry.note_markdown}
            quotes={poetry.quoted_lines}
            className="text-sm text-amber-900/90 leading-relaxed"
          />
        </div>
      )}

      {/* Per-word contemporaneous-attestation lexicon — what each root is
          attested to mean in 6th-c. poetry (Qurʾān-only). Auto-hides when none. */}
      {lexicon && <RootLexiconPanel data={lexicon} />}

      {expandedRootData?.cognate && (
        <CognatePanel
          rootArabic={expandedRootData.root_arabic}
          rootBuckwalter={expandedRootData.root_buckwalter}
          cognate={expandedRootData.cognate}
          onClose={() => setExpandedRoot(null)}
        />
      )}
    </div>
  );
}
