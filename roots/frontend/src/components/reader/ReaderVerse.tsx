import { forwardRef, Fragment, useEffect, useState } from 'react';
import type { SurahVerse, AITranslationData, GrammarNotesData, VerseExegesisData, VersePoetryNote } from '../../types';
import { toggleManualSave, isSaved } from '../../utils/saved-items';
import { useVerseHighlights } from '../../hooks/useVerseHighlights';
import { HIGHLIGHT_BG, removeHighlight, isCoarsePointer } from '../../utils/verse-highlights';
import HighlightCross from '../HighlightCross';
import {
  notifySavedItemsChanged,
  SAVED_ITEMS_CHANGED,
} from '../SavedItemsPanel';
import { getNote, setNote, subscribeToNotes } from '../../utils/user-notes';
import { getSurahName } from '../../utils/surah-names';
import { fetchAITranslation, fetchGrammarNotes, fetchVerseExegesis, fetchVersePoetry } from '../../api/quran';
import {
  isReaderNotesVisible,
  setReaderNotesVisible,
  subscribeToReaderPrefs,
} from '../../utils/reader-prefs';
import FormattedText, { FormattedInline } from '../FormattedText';
import { NotesBody } from '../GrammarNotes';
import { splitDepartureNotes } from '../../utils/departure-notes';
import { TranslationWithChips } from '../TermChip';
import NoteEditor from '../NoteEditor';
import WordTooltip from '../WordTooltip';
import { wrapArabicRuns } from '../../utils/arabic-runs';
import type { Word, Segment } from '../../types';
import type { DefaultReciter } from '../../api/quran';
import { reciterAudioUrl } from '../../api/quran';
import {
  getVerseAudioStatus,
  toggleVerseAudio,
  subscribeVerseAudio,
} from '../../utils/verse-audio';

interface Props {
  surah: number;
  verse: SurahVerse;
  /** When true, renders an Arabic-+-English-gloss row beneath the
   *  Arabic text in addition to the full sentence translation. The
   *  reader fetches verse.words only when this is on, so absence of
   *  the array also means "skip word-by-word render". */
  wordByWord?: boolean;
  /** When set, the gutter shows a play button that streams this verse's
   *  recitation from the configured default reciter. */
  reciter?: DefaultReciter | null;
  /** Light highlight applied for ~2s after deep-link landing on this
   *  verse via /read/<surah>:<verse>. Helps the user spot where they
   *  were dropped. */
  highlighted?: boolean;
}

/**
 * One verse block in the reader. The left "gutter" holds subtle
 * affordance icons — they appear ONLY when relevant data exists for
 * that verse, so a verse without notes / saved state shows an empty
 * gutter and stays visually quiet.
 *
 * Translation notes and grammar notes share a single "Notes" icon: if
 * either one exists for this verse, the icon is shown, and clicking
 * expands a single panel that renders whichever sections are
 * available. They're related concepts and a combined panel reads
 * better than two competing affordances.
 *
 * Each icon click expands a small inline panel BELOW this verse
 * (constrained to this block) so the surrounding content never moves
 * around.
 */
const ReaderVerse = forwardRef<HTMLElement, Props>(function ReaderVerse(
  { surah, verse, wordByWord, reciter, highlighted },
  ref,
) {
  const verseKey = `${surah}:${verse.verse}`;
  const [note, setNoteState] = useState<string>(() => getNote(surah, verse.verse));
  const [saved, setSaved] = useState<boolean>(() => isSaved('verse', verseKey));
  // Personal-note editor is per-verse; the translation/grammar/exegesis notes
  // are a GLOBAL toggle (one click shows them under every verse), remembered
  // in localStorage and synced across verses via the reader-prefs event.
  const [activePanel, setActivePanel] = useState<'note' | null>(null);
  const [notesVisible, setNotesVisibleState] = useState<boolean>(() => isReaderNotesVisible());
  const [highlightFlash, setHighlightFlash] = useState(highlighted);
  // Track which word position is hovered (or focus-active) for the
  // morphology tooltip. -1 = no hover.
  const [hoveredWord, setHoveredWord] = useState<number>(-1);
  const [audioState, setAudioState] = useState(() => getVerseAudioStatus(verseKey));
  // User highlights for this verse (yellow by default; auto-saved). The
  // posMap answers "is word N highlighted, in what color, is N its start?".
  const { posMap } = useVerseHighlights(verseKey);
  // Which highlight's delete-× is currently shown (set by hovering any word
  // in that highlight; cleared when the pointer leaves the Arabic region).
  const [hoverHl, setHoverHl] = useState<string | null>(null);
  // On touch devices there's no hover, so the × is shown on highlights always.
  const coarse = isCoarsePointer();

  useEffect(() => {
    const update = () => setAudioState(getVerseAudioStatus(verseKey));
    update();
    return subscribeVerseAudio(update);
  }, [verseKey]);

  // Keep the global notes-visibility toggle in sync across every verse.
  useEffect(
    () => subscribeToReaderPrefs(() => setNotesVisibleState(isReaderNotesVisible())),
    [],
  );

  // Per-word Arabic for the word-by-word display. We split the verse's
  // Uthmani text on whitespace — same approach /verse/<ref> uses —
  // because each whitespace-separated token is one user-visible word
  // and corresponds to one word_pos in the morphology table.
  const uthmaniWords = verse.text_uthmani.split(/\s+/).filter(Boolean);

  useEffect(() => {
    return subscribeToNotes(() => {
      setNoteState(getNote(surah, verse.verse));
    });
  }, [surah, verse.verse]);

  useEffect(() => {
    function refreshSaved() {
      setSaved(isSaved('verse', verseKey));
    }
    window.addEventListener(SAVED_ITEMS_CHANGED, refreshSaved);
    window.addEventListener('storage', refreshSaved);
    return () => {
      window.removeEventListener(SAVED_ITEMS_CHANGED, refreshSaved);
      window.removeEventListener('storage', refreshSaved);
    };
  }, [verseKey]);

  useEffect(() => {
    if (highlighted) {
      setHighlightFlash(true);
      const t = setTimeout(() => setHighlightFlash(false), 2200);
      return () => clearTimeout(t);
    }
  }, [highlighted]);

  function handleSave() {
    // toggleManualSave: unsaved → save; highlight-saved → promote to sticky
    // manual; manual → remove. So pressing Save on a highlight-auto-saved
    // verse makes it permanent rather than paradoxically unsaving it.
    const isSavedNow = toggleManualSave({
      type: 'verse',
      key: verseKey,
      label: `${getSurahName(surah)} ${verseKey}`,
      href: `/verse/${verseKey}`,
      subtitle: verse.translation.slice(0, 80),
      arabic: verse.text_uthmani,
      translation: verse.translation,
    });
    setSaved(isSavedNow);
    notifySavedItemsChanged();
  }

  function handleSaveNote(text: string) {
    setNote(surah, verse.verse, text);
    setNoteState(text);
  }

  // Delegated hover over the Arabic region: show the delete-× for whichever
  // highlight the pointer is currently over (keeps the affordance alive while
  // travelling along a multi-word highlight toward the × at its start).
  function handleHighlightHover(e: React.MouseEvent) {
    const el = (e.target as HTMLElement).closest('[data-word-pos]');
    const pos = el ? parseInt(el.getAttribute('data-word-pos') || '', 10) : NaN;
    const hl = Number.isFinite(pos) ? posMap.get(pos) : undefined;
    setHoverHl(hl ? hl.id : null);
  }

  const hasNote = !!note.trim();
  const hasVerseNotes = verse.has_translation_note || verse.has_grammar_note || !!verse.has_exegesis || !!verse.has_poetry_note;

  return (
    <article
      ref={ref}
      data-verse={verse.verse}
      id={`v${verse.verse}`}
      className={`relative grid grid-cols-[2.5rem_1fr] gap-3 sm:gap-4 py-5 sm:py-6 border-b border-card-border/50 transition-colors duration-1000 ${
        highlightFlash ? 'bg-gold/10' : ''
      }`}
    >
      {/* Left gutter — verse number + subtle icons (only when relevant) */}
      <div className="flex flex-col items-center gap-1.5 pt-1 text-ink-muted">
        {reciter && (
          <GutterIcon
            label={
              audioState === 'playing'
                ? 'Stop recitation'
                : audioState === 'loading'
                  ? 'Loading recitation…'
                  : `Play recitation (${reciter.name})`
            }
            active={audioState !== 'idle'}
            onClick={() => toggleVerseAudio(verseKey, reciterAudioUrl(reciter, surah, verse.verse))}
          >
            {audioState === 'loading' ? (
              <svg viewBox="0 0 16 16" className="w-3.5 h-3.5 animate-spin" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M8 2a6 6 0 016 6" strokeLinecap="round" />
              </svg>
            ) : audioState === 'playing' ? (
              <svg viewBox="0 0 16 16" className="w-3.5 h-3.5" fill="currentColor">
                <rect x="4" y="3" width="3" height="10" rx="0.5" />
                <rect x="9" y="3" width="3" height="10" rx="0.5" />
              </svg>
            ) : (
              <svg viewBox="0 0 16 16" className="w-3.5 h-3.5" fill="currentColor">
                <path d="M5 3.2v9.6a.5.5 0 00.76.43l8-4.8a.5.5 0 000-.86l-8-4.8A.5.5 0 005 3.2z" />
              </svg>
            )}
          </GutterIcon>
        )}
        <span className="font-mono text-[12px] text-ink-muted/80 leading-none self-end">
          {verse.verse}
        </span>
        <div className="flex flex-col items-center gap-1.5 mt-1">
          {hasVerseNotes && (
            <GutterIcon
              label={notesVisible ? 'Hide notes' : 'Show notes for all verses'}
              active={notesVisible}
              onClick={() => setReaderNotesVisible(!notesVisible)}
            >
              <svg viewBox="0 0 16 16" className="w-3.5 h-3.5" fill="currentColor">
                <path d="M8 1a1 1 0 011 1v.5h2A1.5 1.5 0 0112.5 4v9A1.5 1.5 0 0111 14.5H5A1.5 1.5 0 013.5 13V4A1.5 1.5 0 015 2.5h2V2a1 1 0 011-1zm0 1.6V3h-1.5V2.6a.4.4 0 01.4-.4h.7a.4.4 0 01.4.4zM6 7h4a.5.5 0 010 1H6a.5.5 0 010-1zm0 2h4a.5.5 0 010 1H6a.5.5 0 010-1z" />
              </svg>
            </GutterIcon>
          )}
          <GutterIcon
            label={saved ? 'Unsave verse' : 'Save verse'}
            active={saved}
            onClick={handleSave}
          >
            <svg viewBox="0 0 16 16" className="w-3.5 h-3.5" fill={saved ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="1.5">
              <path d="M4 1.5h8a.5.5 0 01.5.5v12L8 11l-4.5 3V2a.5.5 0 01.5-.5z" />
            </svg>
          </GutterIcon>
          <GutterIcon
            label={hasNote ? 'Edit your note' : 'Add a note'}
            active={activePanel === 'note' || hasNote}
            onClick={() => setActivePanel(activePanel === 'note' ? null : 'note')}
          >
            <svg viewBox="0 0 16 16" className="w-3.5 h-3.5" fill={hasNote ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="1.5">
              <path d="M11.5 1.7L14.3 4.5 5 13.8l-3 .5.5-3z" strokeLinejoin="round" />
            </svg>
          </GutterIcon>
          <GutterIcon
            label="Open in research view"
            active={false}
            href={`/verse/${verseKey}`}
          >
            <svg viewBox="0 0 16 16" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M9.5 3.5h3v3M12 4L7 9M6 3.5H3.5v9h9V10" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </GutterIcon>
        </div>
      </div>

      {/* Right column — verse content */}
      <div className="min-w-0">
        {wordByWord && verse.words && verse.words.length > 0 ? (
          // Word-by-word: each Arabic word with English gloss directly
          // beneath. dir="rtl" + justify-start aligns words to the
          // right edge with natural right-to-left reading order; plain
          // flex-wrap keeps subsequent rows below the first.
          //
          // Visible Arabic per word comes from text_uthmani split by
          // whitespace — same approach as /verse/<ref> — so compound
          // words like فَصَلِّ stay visually intact instead of being
          // split into prefix-only display fragments.
          <div
            className="mb-3 flex flex-wrap justify-start gap-x-4 gap-y-3"
            lang="ar"
            dir="rtl"
            data-allow-no-font-arabic
            data-arabic-region
            data-verse-key={verseKey}
            data-verse-text={verse.text_uthmani}
            data-verse-translation={verse.translation}
            onMouseOver={handleHighlightHover}
            onMouseLeave={() => setHoverHl(null)}
          >
            {verse.words.map((w) => {
              const display = uthmaniWords[w.position - 1] ?? joinSegmentArabic(w.segments);
              const isActive = hoveredWord === w.position;
              const hl = posMap.get(w.position);
              const isHlStart = !!hl && w.position === hl.start;
              const wordObj: Word = {
                position: w.position,
                segments: w.segments as Segment[],
                translation: w.translation || undefined,
              };
              return (
                <span
                  key={w.position}
                  data-word-pos={w.position}
                  className={`relative inline-flex flex-col items-center min-w-[3.5rem] max-w-[14rem] cursor-help ${
                    hl ? `${HIGHLIGHT_BG[hl.color]} rounded` : ''
                  }`}
                  onMouseEnter={() => setHoveredWord(w.position)}
                  onMouseLeave={() => setHoveredWord((p) => (p === w.position ? -1 : p))}
                  onFocus={() => setHoveredWord(w.position)}
                  onBlur={() => setHoveredWord((p) => (p === w.position ? -1 : p))}
                  tabIndex={0}
                >
                  {isHlStart && (
                    <HighlightCross
                      visible={hoverHl === hl!.id || coarse}
                      onRemove={() => { removeHighlight(verseKey, hl!.id); setHoverHl(null); }}
                    />
                  )}
                  <span className="font-arabic text-2xl sm:text-3xl leading-tight text-ink">
                    {display}
                  </span>
                  {w.translation && (
                    <span
                      lang="en"
                      dir="ltr"
                      className={`mt-1 text-[11px] sm:text-xs leading-tight text-center ${
                        w.translation_source === 'root'
                          ? 'italic text-ink-muted/70'
                          : 'text-ink-muted'
                      }`}
                      title={
                        w.translation_source === 'root'
                          ? 'Per-word translation unavailable; showing the root’s primary meaning as a hint.'
                          : undefined
                      }
                    >
                      {wrapArabicRuns(
                        w.translation_source === 'root'
                          ? `(${w.translation.toLowerCase()})`
                          : w.translation
                      )}
                    </span>
                  )}
                  {isActive && (
                    <WordTooltip
                      word={wordObj}
                      aiMeaning={w.translation || undefined}
                      preferredTranslation={w.translation || undefined}
                      wordDetailUrl={`/word/${surah}:${verse.verse}/${w.position}`}
                    />
                  )}
                </span>
              );
            })}
          </div>
        ) : (
          // Plain reading: render each Arabic word as its own token span (with
          // a stable data-word-pos) so highlighting has a target here too. The
          // tokens flow inline separated by spaces, so it reads identically to
          // the original single text node.
          <div
            className="font-arabic text-2xl sm:text-3xl leading-[2.2] text-ink mb-3 text-right"
            lang="ar"
            dir="rtl"
            data-arabic-region
            data-verse-key={verseKey}
            data-verse-text={verse.text_uthmani}
            data-verse-translation={verse.translation}
            onMouseOver={handleHighlightHover}
            onMouseLeave={() => setHoverHl(null)}
          >
            {uthmaniWords.map((word, idx) => {
              const pos = idx + 1;
              const hl = posMap.get(pos);
              const isHlStart = !!hl && pos === hl.start;
              return (
                <Fragment key={pos}>
                  <span
                    data-word-pos={pos}
                    className={`relative ${hl ? `${HIGHLIGHT_BG[hl.color]} rounded` : ''}`}
                  >
                    {isHlStart && (
                      <HighlightCross
                        visible={hoverHl === hl!.id || coarse}
                        onRemove={() => { removeHighlight(verseKey, hl!.id); setHoverHl(null); }}
                      />
                    )}
                    {word}
                  </span>
                  {idx < uthmaniWords.length - 1 ? ' ' : ''}
                </Fragment>
              );
            })}
          </div>
        )}
        <div className="text-[15px] sm:text-base leading-relaxed text-ink-secondary">
          {/* TranslationWithChips auto-applies the surveyed-roots chip
              tooltip layer (italic markers + word-family matches),
              same behavior as the research view at /verse/<ref>. */}
          <TranslationWithChips
            text={verse.translation}
            surveyedRootsInVerse={verse.surveyed_roots}
          />
        </div>

        {/* Inline expansions (only one open at a time) */}
        {activePanel === 'note' && (
          <div className="mt-4">
            <NoteEditor
              initial={note}
              onSave={handleSaveNote}
              onClose={() => setActivePanel(null)}
            />
          </div>
        )}
        {notesVisible && hasVerseNotes && (
          <VerseNotesPanel
            surah={surah}
            verse={verse.verse}
            hasTranslation={verse.has_translation_note}
            hasGrammar={verse.has_grammar_note}
            hasExegesis={!!verse.has_exegesis}
            hasPoetry={!!verse.has_poetry_note}
          />
        )}
      </div>
    </article>
  );
});

export default ReaderVerse;

// ----- Gutter icon ---------------------------------------------------------

interface GutterIconProps {
  label: string;
  active: boolean;
  onClick?: () => void;
  href?: string;
  children: React.ReactNode;
}

function GutterIcon({ label, active, onClick, href, children }: GutterIconProps) {
  const cls = `relative group flex items-center justify-center w-6 h-6 rounded-full transition-colors ${
    active
      ? 'text-gold bg-gold/10'
      : 'text-ink-muted/60 hover:text-gold hover:bg-gold/10'
  }`;
  // Custom tooltip — appears on hover after only ~80ms (vs ~700ms for
  // the browser's native `title`), stays under the icon and arrow up.
  const tooltip = (
    <span
      role="tooltip"
      className="pointer-events-none absolute left-full ml-2 top-1/2 -translate-y-1/2 z-20
                 whitespace-nowrap rounded-md bg-ink text-cream text-[11px] font-medium px-2 py-1
                 opacity-0 transition-opacity duration-75 delay-75
                 group-hover:opacity-100 group-focus-visible:opacity-100"
    >
      {label}
    </span>
  );
  if (href) {
    return (
      <a href={href} aria-label={label} className={cls} target="_blank" rel="noopener noreferrer">
        {children}
        {tooltip}
      </a>
    );
  }
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      className={`${cls} cursor-pointer`}
    >
      {children}
      {tooltip}
    </button>
  );
}

// ----- Helpers -------------------------------------------------------------

/** Fallback when text_uthmani's whitespace-split has fewer tokens than
 *  expected — concatenate every segment's form_arabic for the word. */
function joinSegmentArabic(segments: Array<{ form_arabic: string }>): string {
  return segments.map((s) => s.form_arabic || '').join('');
}

// ----- Combined translation + grammar notes panel --------------------------

function VerseNotesPanel({
  surah,
  verse,
  hasTranslation,
  hasGrammar,
  hasExegesis,
  hasPoetry,
}: {
  surah: number;
  verse: number;
  hasTranslation: boolean;
  hasGrammar: boolean;
  hasExegesis: boolean;
  hasPoetry: boolean;
}) {
  const [translation, setTranslation] = useState<AITranslationData | null>(null);
  const [grammar, setGrammar] = useState<GrammarNotesData | null>(null);
  const [exegesis, setExegesis] = useState<VerseExegesisData | null>(null);
  const [poetry, setPoetry] = useState<VersePoetryNote | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');
    Promise.all([
      hasTranslation ? fetchAITranslation(surah, verse).catch(() => null) : Promise.resolve(null),
      hasGrammar ? fetchGrammarNotes(surah, verse).catch(() => null) : Promise.resolve(null),
      hasExegesis ? fetchVerseExegesis(surah, verse).catch(() => null) : Promise.resolve(null),
      hasPoetry ? fetchVersePoetry(surah, verse).catch(() => null) : Promise.resolve(null),
    ]).then(([t, g, ex, p]) => {
      if (cancelled) return;
      setTranslation(t);
      setGrammar(g);
      setExegesis(ex);
      setPoetry(p);
      setLoading(false);
      if (!t && !g && !ex && !p) setError('No notes available for this verse.');
    });
    return () => { cancelled = true; };
  }, [surah, verse, hasTranslation, hasGrammar, hasExegesis, hasPoetry]);

  if (loading) {
    return (
      <div className="mt-4 rounded-lg border border-card-border bg-cream/50 p-3">
        <div className="flex items-center gap-2 text-xs text-ink-muted">
          <span className="h-3 w-3 animate-spin rounded-full border-2 border-card-border border-t-gold" />
          Loading notes…
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-4 rounded-lg border border-card-border bg-cream/50 p-3 text-xs text-ink-muted">
        {error}
      </div>
    );
  }

  return (
    <div className="mt-4 rounded-lg border border-card-border bg-cream/50 p-4 space-y-4">
      {translation?.departure_notes && (
        <div>
          <h4 className="text-[11px] uppercase tracking-wide font-medium text-gold mb-1.5">
            Translation Notes
          </h4>
          {/* FormattedInline applies *italic* / **bold** emphasis AND auto-links
              verse refs (2:155) + transliterated/Arabic roots — same inline
              rendering as the research view, so notes feel consistent across
              both surfaces. */}
          <div className="text-sm leading-relaxed text-ink-secondary">
            {splitDepartureNotes(translation.departure_notes).map((line, i) => (
              <p key={i} className={i > 0 ? 'mt-1.5' : ''}>
                <FormattedInline text={line} />
              </p>
            ))}
          </div>
        </div>
      )}
      {exegesis?.exegesis_markdown && (
        <div className={translation?.departure_notes ? 'pt-3 border-t border-card-border/70' : ''}>
          <h4 className="text-[11px] uppercase tracking-wide font-medium text-gold mb-1.5">
            Exegesis
          </h4>
          {/* FormattedText linkifies verse refs and transliterated roots
              (e.g. f-l-q) with the same hover tooltips as the research view. */}
          <div className="text-sm leading-relaxed text-ink-secondary">
            <FormattedText text={exegesis.exegesis_markdown} />
          </div>
        </div>
      )}
      {poetry?.note_markdown && (
        <div className={(translation?.departure_notes || exegesis?.exegesis_markdown) ? 'pt-3 border-t border-card-border/70' : ''}>
          <h4 className="text-[11px] uppercase tracking-wide font-medium text-gold mb-1.5">
            In Pre-Islamic Poetry
          </h4>
          {/* FormattedText resolves the [[q:…]] markers against quoted_lines
              into the same hover-tooltip quote links the research view uses. */}
          <div className="text-sm leading-relaxed text-ink-secondary">
            <FormattedText text={poetry.note_markdown} quotes={poetry.quoted_lines} />
          </div>
        </div>
      )}
      {grammar?.notes_markdown && (
        <div className={(translation?.departure_notes || exegesis?.exegesis_markdown || poetry?.note_markdown) ? 'pt-3 border-t border-card-border/70' : ''}>
          <h4 className="text-[11px] uppercase tracking-wide font-medium text-gold mb-1.5">
            Grammar Notes
          </h4>
          {/* NotesBody renders [[term]] markers as the same wavy-underline
              chips with hover-popover definition cards used on /verse/<ref>. */}
          <div className="text-sm leading-relaxed text-ink-secondary">
            <NotesBody markdown={grammar.notes_markdown} terms={grammar.terms} />
          </div>
        </div>
      )}
      <div className="pt-2 text-[11px] text-ink-muted text-right">
        <a
          href={`/verse/${surah}:${verse}`}
          className="hover:text-gold"
          target="_blank"
          rel="noopener noreferrer"
        >
          Open in research view ↗
        </a>
      </div>
    </div>
  );
}
