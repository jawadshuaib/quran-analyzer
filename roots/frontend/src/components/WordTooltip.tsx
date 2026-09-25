import { Fragment, type ReactNode } from 'react';
import type { CoreEvidence, Word } from '../types';
import { wrapArabicRuns } from '../utils/arabic-runs';
import { verseUrl } from '../utils/urls';
import { segmentRootSense } from '../utils/root-sense-links';
import {
  HIGHLIGHT_COLORS,
  HIGHLIGHT_SWATCH,
  HIGHLIGHT_LABEL,
  setWordHighlight,
  removeWordHighlight,
  type HighlightColor,
  type VerseMeta,
} from '../utils/verse-highlights';

/** Enables the per-word highlight picker at the foot of the tooltip. Omitted
 *  where highlighting doesn't apply (e.g. the root page's occurrence list). */
export interface WordHighlightTarget {
  verseKey: string;
  pos: number;
  /** Colour currently covering this word, from the caller's posMap. */
  activeColor?: HighlightColor;
  /** Verse text carried onto the auto-saved item, as with drag-highlighting. */
  meta?: VerseMeta;
}

const EVIDENCE_STYLE: Record<'poetry' | 'cognates' | 'dictionary', { cls: string; title: string }> = {
  poetry: {
    cls: 'text-amber-700 decoration-amber-400 hover:text-amber-900',
    title: 'See the pre-Islamic poetry for this root',
  },
  cognates: {
    cls: 'text-indigo-600 decoration-indigo-300 hover:text-indigo-800',
    title: 'See the Semitic cognates for this root',
  },
  dictionary: {
    cls: 'text-emerald-700 decoration-emerald-400 hover:text-emerald-900',
    title: 'See the classical dictionaries for this root',
  },
};

/** The root-sense passage with its references made checkable: each verse it
 *  cites opens that verse, and the first mention of each kind of evidence --
 *  the poetry, the sister languages, a lexicographer -- opens the root page at
 *  the section holding it. New tab so the reader keeps their place, unless the
 *  reader is already on that root's page, where the link just scrolls. Plain
 *  links rather than VerseRefText's hover previews: a second popup opening out
 *  of this one would fight it for the pointer. A range links to its first verse. */
function linkRootSense(text: string, evidence?: CoreEvidence | null): ReactNode {
  const segs = segmentRootSense(text, evidence);
  if (segs.length === 1 && segs[0].kind === 'text') return wrapArabicRuns(text);
  const onRootPage =
    evidence && decodeURIComponent(window.location.pathname) === `/root/${evidence.root}`;
  return segs.map((s, i) => {
    if (s.kind === 'text') return <Fragment key={i}>{wrapArabicRuns(s.text)}</Fragment>;
    if (s.kind === 'verse') {
      return (
        <a
          key={i}
          href={verseUrl(s.surah, s.ayah)}
          target="_blank"
          rel="noopener noreferrer"
          className="text-violet-600 underline decoration-violet-300 underline-offset-2 hover:text-violet-800 hover:decoration-violet-500"
          onClick={(e) => e.stopPropagation()}
        >
          {s.text}
        </a>
      );
    }
    const style = EVIDENCE_STYLE[s.category];
    const href = `${onRootPage ? '' : `/root/${encodeURIComponent(evidence!.root)}`}#${s.section}`;
    return (
      <a
        key={i}
        href={href}
        {...(onRootPage ? {} : { target: '_blank', rel: 'noopener noreferrer' })}
        title={style.title}
        className={`underline decoration-dotted underline-offset-2 ${style.cls}`}
        onClick={(e) => e.stopPropagation()}
      >
        {wrapArabicRuns(s.text)}
      </a>
    );
  });
}

interface Props {
  word: Word;
  /** The root's core-meaning passage for THIS word's sense. Replaces the
   *  Semitic-cognate list, which listed sister languages without deepening
   *  the reader's understanding of the word in front of them. */
  coreMeaning?: string | null;
  /** Which root-page sections back that passage; its mentions of poetry,
   *  sister languages and lexicographers link to them. */
  coreEvidence?: CoreEvidence | null;
  aiMeaning?: string;
  wordDetailUrl?: string;
  preferredTranslation?: string;
  preferredSource?: 'conventional' | 'ai' | 'judge';
  highlight?: WordHighlightTarget;
}

export default function WordTooltip({ word, coreMeaning, coreEvidence, aiMeaning, wordDetailUrl, preferredTranslation, highlight }: Props) {
  const mainRootSeg = word.segments.find((s) => s.root_arabic);
  const mainRoot = mainRootSeg?.root_arabic;
  const mainRootBw = mainRootSeg?.root_buckwalter;
  const mainLemma = word.segments.find((s) => s.lemma_arabic)?.lemma_arabic;
  const posLabels = word.segments
    .map((s) => s.pos)
    .filter((p) => p && p !== 'Prefix' && p !== 'Suffix');

  return (
    <div
      dir="ltr"
      className="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-50
                 bg-white rounded-lg shadow-lg border border-stone-200 p-3
                 w-max min-w-[150px] max-w-[320px] text-sm text-stone-700"
      onClick={(e) => e.stopPropagation()}
    >
      {/* w-max is load-bearing: this panel is absolutely positioned inside a
          word span only ~70px wide, so width:auto shrink-wraps to that narrow
          containing block and collapses to min-w. With the old cognate rows
          that was invisible; a 380-character passage rendered as a 150px
          column 635px tall. max-content sizing caps against max-w instead. */}
      {/* Arrow */}
      <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3
                      bg-white border-l border-t border-stone-200 rotate-45" />

      {preferredTranslation ? (
        /* Judged: show single preferred translation — no AI label needed */
        <div className="mb-1.5 text-center">
          {wordDetailUrl ? (
            <a
              href={wordDetailUrl}
              className="inline-flex items-center gap-1 hover:opacity-80 transition-opacity"
              onClick={(e) => e.stopPropagation()}
            >
              <span className="font-semibold text-stone-900">{wrapArabicRuns(preferredTranslation)}</span>
            </a>
          ) : (
            <span className="font-semibold text-stone-900">{wrapArabicRuns(preferredTranslation)}</span>
          )}
        </div>
      ) : (
        /* Unjudged: show dual display (conventional + AI) */
        <>
          {word.translation && (
            <div className="font-semibold text-stone-900 mb-1.5 text-center">
              {wrapArabicRuns(word.translation)}
            </div>
          )}

          {aiMeaning && (
            <div className="mb-1.5 text-center">
              {wordDetailUrl ? (
                <a
                  href={wordDetailUrl}
                  className="inline-flex items-center gap-1 text-violet-700 hover:text-violet-900 transition-colors"
                  onClick={(e) => e.stopPropagation()}
                >
                  {word.translation && (
                    <span className="text-[10px] font-bold bg-violet-100 text-violet-600 rounded px-1 py-px uppercase">
                      AI
                    </span>
                  )}
                  <span className="text-xs font-medium">{wrapArabicRuns(aiMeaning)}</span>
                </a>
              ) : (
                <div className="inline-flex items-center gap-1">
                  {word.translation && (
                    <span className="text-[10px] font-bold bg-violet-100 text-violet-600 rounded px-1 py-px uppercase">
                      AI
                    </span>
                  )}
                  <span className="text-xs font-medium text-violet-700">{wrapArabicRuns(aiMeaning)}</span>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {posLabels.length > 0 && (
        <div className="flex flex-wrap justify-center gap-1 mb-1.5">
          {posLabels.map((pos, i) => (
            <span
              key={i}
              className="text-xs bg-stone-100 text-stone-600 rounded-full px-2 py-0.5"
            >
              {pos}
            </span>
          ))}
        </div>
      )}

      <div className="space-y-0.5 text-xs text-stone-500">
        {mainRoot && (
          <div className="flex justify-between gap-3">
            <span>Root</span>
            <span
              dir="rtl"
              lang="ar"
              className="font-arabic text-sm text-stone-700"
            >
              {mainRoot}
            </span>
          </div>
        )}
        {mainLemma && (
          <div className="flex justify-between gap-3">
            <span>Lemma</span>
            <span
              dir="rtl"
              lang="ar"
              className="font-arabic text-sm text-stone-700"
            >
              {mainLemma}
            </span>
          </div>
        )}
      </div>

      {coreMeaning && (
        <div className="mt-2 pt-2 border-t border-stone-100">
          {/* Ibn Fāris's aṣl: the one sense the letters carry through all their uses. */}
          <div className="text-[10px] font-semibold uppercase tracking-wider text-stone-400 mb-1">
            Root Sense
          </div>
          <div className="text-xs leading-relaxed text-stone-600">
            {linkRootSense(coreMeaning, coreEvidence)}
          </div>
        </div>
      )}

      {(wordDetailUrl || mainRootBw) && (
        <div className="mt-2 pt-2 border-t border-stone-100 space-y-1.5">
          {wordDetailUrl && (
            <a
              href={wordDetailUrl}
              className="flex items-center justify-center gap-1.5 w-full px-2 py-1.5 rounded-md
                         bg-violet-50 text-violet-600 hover:bg-violet-100 hover:text-violet-700
                         text-xs font-medium transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              View Word Details
              <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
            </a>
          )}
          {mainRootBw && (
            <>
              <a
                href={`/root/${encodeURIComponent(mainRootBw)}`}
                className="flex items-center justify-center gap-1.5 w-full px-2 py-1.5 rounded-md
                           bg-emerald-50 text-emerald-700 hover:bg-emerald-100 hover:text-emerald-800
                           text-xs font-medium transition-colors"
                onClick={(e) => e.stopPropagation()}
              >
                Root Dictionary
                <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
                </svg>
              </a>
              <a
                href={`https://corpus.quran.com/qurandictionary.jsp?q=${encodeURIComponent(mainRootBw)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-1.5 w-full px-2 py-1.5 rounded-md
                           bg-indigo-50 text-indigo-600 hover:bg-indigo-100 hover:text-indigo-700
                           text-xs font-medium transition-colors"
                onClick={(e) => e.stopPropagation()}
              >
                Quranic Corpus
                <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                  <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
                </svg>
              </a>
            </>
          )}
        </div>
      )}

      {/* Per-word highlight picker. Dragging across several words is fiddly at
          this text size and easily catches neighbours, so a word can be
          coloured on its own from here. */}
      {highlight && (
        <div className="mt-2 pt-2 border-t border-stone-100">
          <div
            role="toolbar"
            aria-label="Highlight this word"
            className="flex items-center justify-center gap-1.5"
          >
            {HIGHLIGHT_COLORS.map((c) => {
              const active = highlight.activeColor === c;
              return (
                <button
                  key={c}
                  type="button"
                  aria-label={`Highlight ${HIGHLIGHT_LABEL[c]}`}
                  aria-pressed={active}
                  title={HIGHLIGHT_LABEL[c]}
                  onClick={(e) => {
                    e.stopPropagation();
                    setWordHighlight(highlight.verseKey, highlight.pos, c, highlight.meta);
                  }}
                  className={`h-5 w-5 rounded-full ${HIGHLIGHT_SWATCH[c]} cursor-pointer transition-transform hover:scale-110 ${
                    active ? 'ring-2 ring-offset-1 ring-stone-500' : 'ring-1 ring-black/5'
                  }`}
                />
              );
            })}
            {highlight.activeColor && (
              <>
                <span className="mx-0.5 h-4 w-px bg-stone-200" aria-hidden />
                <button
                  type="button"
                  aria-label="Remove highlight"
                  title="Remove highlight"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeWordHighlight(highlight.verseKey, highlight.pos);
                  }}
                  className="flex h-5 w-5 cursor-pointer items-center justify-center rounded-full text-stone-400 transition-colors hover:bg-rose-50 hover:text-rose-600"
                >
                  <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M4 4l8 8M12 4l-8 8" strokeLinecap="round" />
                  </svg>
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
