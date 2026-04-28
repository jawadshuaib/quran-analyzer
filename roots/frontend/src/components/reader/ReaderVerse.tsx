import { forwardRef, useEffect, useState } from 'react';
import type { SurahVerse } from '../../types';
import { toggleSavedItem, isSaved } from '../../utils/saved-items';
import {
  notifySavedItemsChanged,
  SAVED_ITEMS_CHANGED,
} from '../SavedItemsPanel';
import { getNote, setNote, subscribeToNotes } from '../../utils/user-notes';
import { getSurahName } from '../../utils/surah-names';

interface Props {
  surah: number;
  verse: SurahVerse;
  /** Light highlight applied for ~2s after deep-link landing on this
   *  verse via /read/<surah>:<verse>. Helps the user spot where they
   *  were dropped. */
  highlighted?: boolean;
}

/**
 * One verse block in the reader. The left "gutter" holds subtle
 * affordance icons — they appear ONLY when relevant data exists for
 * that verse, so a verse without a note / grammar note / saved state
 * shows an empty gutter and stays visually quiet.
 *
 * Each icon click expands a small inline panel BELOW this verse
 * (constrained to this block) so the surrounding content never moves
 * around. Phase B will wire grammar / related-verses panels; Phase A
 * has notes + save + research-link working.
 */
const ReaderVerse = forwardRef<HTMLElement, Props>(function ReaderVerse(
  { surah, verse, highlighted },
  ref,
) {
  const verseKey = `${surah}:${verse.verse}`;
  const [note, setNoteState] = useState<string>(() => getNote(surah, verse.verse));
  const [saved, setSaved] = useState<boolean>(() => isSaved('verse', verseKey));
  const [activePanel, setActivePanel] = useState<'note' | 'translation-note' | null>(null);
  const [highlightFlash, setHighlightFlash] = useState(highlighted);

  // Sync notes / saved state across tabs + components
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
    const isSaved = toggleSavedItem({
      type: 'verse',
      key: verseKey,
      label: `${getSurahName(surah)} ${verseKey}`,
      href: `/verse/${verseKey}`,
      subtitle: verse.translation.slice(0, 80),
    });
    setSaved(isSaved);
    notifySavedItemsChanged();
  }

  function handleSaveNote(text: string) {
    setNote(surah, verse.verse, text);
    setNoteState(text);
  }

  const hasNote = !!note.trim();
  const hasTranslationNote = !!verse.has_translation_note;

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
          {hasTranslationNote && (
            <GutterIcon
              label="Translation note"
              active={activePanel === 'translation-note'}
              onClick={() => setActivePanel(activePanel === 'translation-note' ? null : 'translation-note')}
            >
              <svg viewBox="0 0 16 16" className="w-3.5 h-3.5" fill="currentColor">
                <path d="M8 1a1 1 0 011 1v.5h2A1.5 1.5 0 0112.5 4v9A1.5 1.5 0 0111 14.5H5A1.5 1.5 0 013.5 13V4A1.5 1.5 0 015 2.5h2V2a1 1 0 011-1zm0 1.6V3h-1.5V2.6a.4.4 0 01.4-.4h.7a.4.4 0 01.4.4zM6 7h4a.5.5 0 010 1H6a.5.5 0 010-1zm0 2h4a.5.5 0 010 1H6a.5.5 0 010-1z" />
              </svg>
            </GutterIcon>
          )}
          <GutterIcon
            label={saved ? 'Saved' : 'Save verse'}
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
        <div className="font-serif text-2xl sm:text-3xl leading-[2.2] text-ink mb-3 text-right" lang="ar" dir="rtl">
          {verse.text_uthmani}
        </div>
        <div className="text-[15px] sm:text-base leading-relaxed text-ink-secondary">
          {verse.translation}
        </div>

        {/* Inline expansions (only one open at a time) */}
        {activePanel === 'note' && (
          <NoteEditor
            initial={note}
            onSave={handleSaveNote}
            onClose={() => setActivePanel(null)}
          />
        )}
        {activePanel === 'translation-note' && (
          <TranslationNotePanel surah={surah} verse={verse.verse} />
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
  const cls = `flex items-center justify-center w-6 h-6 rounded-full transition-colors ${
    active
      ? 'text-gold bg-gold/10'
      : 'text-ink-muted/60 hover:text-gold hover:bg-gold/10'
  }`;
  if (href) {
    return (
      <a href={href} title={label} aria-label={label} className={cls} target="_blank" rel="noopener noreferrer">
        {children}
      </a>
    );
  }
  return (
    <button
      type="button"
      onClick={onClick}
      title={label}
      aria-label={label}
      className={`${cls} cursor-pointer`}
    >
      {children}
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

// ----- Translation-note panel (Phase B will fetch the actual note) ---------

function TranslationNotePanel({ surah, verse }: { surah: number; verse: number }) {
  return (
    <div className="mt-4 rounded-lg border border-card-border bg-cream/50 p-3 text-sm">
      <p className="text-ink-secondary mb-2">
        Translation notes for this verse are coming next phase. For now,
        click{' '}
        <a
          href={`/verse/${surah}:${verse}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-gold hover:underline"
        >
          open in research view
        </a>{' '}
        to see them.
      </p>
    </div>
  );
}
