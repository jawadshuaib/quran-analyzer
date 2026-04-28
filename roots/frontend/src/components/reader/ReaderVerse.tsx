import { forwardRef, useEffect, useState } from 'react';
import type { SurahVerse, AITranslationData, GrammarNotesData } from '../../types';
import { toggleSavedItem, isSaved } from '../../utils/saved-items';
import {
  notifySavedItemsChanged,
  SAVED_ITEMS_CHANGED,
} from '../SavedItemsPanel';
import { getNote, setNote, subscribeToNotes } from '../../utils/user-notes';
import { getSurahName } from '../../utils/surah-names';
import { fetchAITranslation, fetchGrammarNotes } from '../../api/quran';
import VerseRefText from '../VerseRefText';
import { NotesBody } from '../GrammarNotes';
import { splitDepartureNotes } from '../../utils/departure-notes';
import { TranslationWithChips } from '../TermChip';

interface Props {
  surah: number;
  verse: SurahVerse;
  /** When true, renders an Arabic-+-English-gloss row beneath the
   *  Arabic text in addition to the full sentence translation. The
   *  reader fetches verse.words only when this is on, so absence of
   *  the array also means "skip word-by-word render". */
  wordByWord?: boolean;
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
  { surah, verse, wordByWord, highlighted },
  ref,
) {
  const verseKey = `${surah}:${verse.verse}`;
  const [note, setNoteState] = useState<string>(() => getNote(surah, verse.verse));
  const [saved, setSaved] = useState<boolean>(() => isSaved('verse', verseKey));
  const [activePanel, setActivePanel] = useState<'note' | 'verse-notes' | null>(null);
  const [highlightFlash, setHighlightFlash] = useState(highlighted);

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
    const isSavedNow = toggleSavedItem({
      type: 'verse',
      key: verseKey,
      label: `${getSurahName(surah)} ${verseKey}`,
      href: `/verse/${verseKey}`,
      subtitle: verse.translation.slice(0, 80),
    });
    setSaved(isSavedNow);
    notifySavedItemsChanged();
  }

  function handleSaveNote(text: string) {
    setNote(surah, verse.verse, text);
    setNoteState(text);
  }

  const hasNote = !!note.trim();
  const hasVerseNotes = verse.has_translation_note || verse.has_grammar_note;

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
      <div className="flex flex-col items-end gap-1.5 pt-1 text-ink-muted">
        <span className="font-mono text-[12px] text-ink-muted/80 leading-none">
          {verse.verse}
        </span>
        <div className="flex flex-col items-center gap-1.5 mt-1">
          {hasVerseNotes && (
            <GutterIcon
              label={
                verse.has_translation_note && verse.has_grammar_note
                  ? 'Translation + grammar notes'
                  : verse.has_translation_note
                    ? 'Translation notes'
                    : 'Grammar notes'
              }
              active={activePanel === 'verse-notes'}
              onClick={() => setActivePanel(activePanel === 'verse-notes' ? null : 'verse-notes')}
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
          // beneath. Reads right-to-left for the Arabic, but the gloss
          // pair flows naturally inside each cell. Wraps to multiple
          // rows on narrow screens.
          <div
            className="mb-3 flex flex-wrap-reverse justify-end gap-x-4 gap-y-3 text-right"
            lang="ar"
            dir="rtl"
          >
            {verse.words.map((w) => (
              <span
                key={w.position}
                className="inline-flex flex-col items-center min-w-[3.5rem] max-w-[14rem]"
              >
                <span className="font-serif text-2xl sm:text-3xl leading-tight text-ink">
                  {w.form_arabic}
                </span>
                {w.translation && (
                  <span
                    lang="en"
                    dir="ltr"
                    className="mt-1 text-[11px] sm:text-xs text-ink-muted leading-tight text-center"
                  >
                    {w.translation}
                  </span>
                )}
              </span>
            ))}
          </div>
        ) : (
          <div className="font-serif text-2xl sm:text-3xl leading-[2.2] text-ink mb-3 text-right" lang="ar" dir="rtl">
            {verse.text_uthmani}
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
          <NoteEditor
            initial={note}
            onSave={handleSaveNote}
            onClose={() => setActivePanel(null)}
          />
        )}
        {activePanel === 'verse-notes' && (
          <VerseNotesPanel
            surah={surah}
            verse={verse.verse}
            hasTranslation={verse.has_translation_note}
            hasGrammar={verse.has_grammar_note}
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

// ----- Inline note editor --------------------------------------------------

function NoteEditor({
  initial,
  onSave,
  onClose,
}: {
  initial: string;
  onSave: (text: string) => void;
  onClose: () => void;
}) {
  const [text, setText] = useState(initial);

  function handleSave() {
    onSave(text);
    onClose();
  }

  function handleDelete() {
    onSave('');
    onClose();
  }

  return (
    <div className="mt-4 rounded-lg border border-card-border bg-cream/50 p-3">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Your note for this verse — saved locally, never sent anywhere."
        rows={4}
        className="w-full bg-white border border-card-border rounded-md px-3 py-2 text-sm leading-relaxed focus:border-gold focus:outline-none focus:ring-2 focus:ring-gold/20"
        autoFocus
      />
      <div className="mt-2 flex items-center justify-between text-[11px]">
        <span className="text-ink-muted">Stored locally in your browser.</span>
        <div className="flex items-center gap-2">
          {initial && (
            <button
              type="button"
              onClick={handleDelete}
              className="text-red-700 hover:underline cursor-pointer"
            >
              Delete
            </button>
          )}
          <button
            type="button"
            onClick={onClose}
            className="text-ink-muted hover:text-ink-secondary cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="bg-gold/90 text-white px-3 py-1.5 rounded-md hover:bg-gold transition-colors cursor-pointer"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}

// ----- Combined translation + grammar notes panel --------------------------

function VerseNotesPanel({
  surah,
  verse,
  hasTranslation,
  hasGrammar,
}: {
  surah: number;
  verse: number;
  hasTranslation: boolean;
  hasGrammar: boolean;
}) {
  const [translation, setTranslation] = useState<AITranslationData | null>(null);
  const [grammar, setGrammar] = useState<GrammarNotesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');
    Promise.all([
      hasTranslation ? fetchAITranslation(surah, verse).catch(() => null) : Promise.resolve(null),
      hasGrammar ? fetchGrammarNotes(surah, verse).catch(() => null) : Promise.resolve(null),
    ]).then(([t, g]) => {
      if (cancelled) return;
      setTranslation(t);
      setGrammar(g);
      setLoading(false);
      if (!t && !g) setError('No notes available for this verse.');
    });
    return () => { cancelled = true; };
  }, [surah, verse, hasTranslation, hasGrammar]);

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
          {/* VerseRefText auto-links verse refs (2:155), Arabic root refs
              (ر ح م), and italicizes quoted strings — same hover-preview
              behavior as the research view, so notes feel consistent
              across both surfaces. */}
          <div className="text-sm leading-relaxed text-ink-secondary">
            {splitDepartureNotes(translation.departure_notes).map((line, i) => (
              <p key={i} className={i > 0 ? 'mt-1.5' : ''}>
                <VerseRefText text={line} />
              </p>
            ))}
          </div>
        </div>
      )}
      {grammar?.notes_markdown && (
        <div className={translation?.departure_notes ? 'pt-3 border-t border-card-border/70' : ''}>
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
