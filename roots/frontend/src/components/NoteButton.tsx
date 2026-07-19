import { useState, useEffect } from 'react';
import { getItemNote, subscribeToNotes } from '../utils/user-notes';
import { setItemNote, type NoteDescriptor } from '../utils/saved-item-actions';
import NoteEditor from './NoteEditor';

interface Props {
  /** The item this note annotates (verse, word, or root). Carries the display
   *  fields so a first note can auto-save the item under it. */
  item: NoteDescriptor;
  /** Tone used by both the button and the inline editor — `gold` on the
   *  reader, `violet` on the research/word/root views. */
  accent?: 'gold' | 'violet';
  /** Which edge of the button the editor is anchored to. `left` (default) is
   *  right for a top-left button (verse card); a button sitting at the top-
   *  right of the page (word/root header) must use `right` so the wide editor
   *  opens leftward instead of overflowing off-screen. */
  align?: 'left' | 'right';
}

const NOUN: Record<NoteDescriptor['type'], string> = {
  verse: 'verse',
  word: 'word',
  root: 'root',
};

/**
 * Floating note button shown next to the SaveButton on verse / word / root
 * pages. Click toggles an inline editor that opens BELOW the button. Notes
 * persist to localStorage via utils/user-notes; writing a note auto-saves the
 * item so it appears in Saved with the note under it (coupled write path).
 */
export default function NoteButton({ item, accent = 'violet', align = 'left' }: Props) {
  const [note, setNoteState] = useState<string>(() => getItemNote(item.type, item.key));
  const [open, setOpen] = useState(false);

  useEffect(() => {
    return subscribeToNotes(() => {
      setNoteState(getItemNote(item.type, item.key));
    });
  }, [item.type, item.key]);

  function handleSave(text: string) {
    setItemNote(item, text);
    setNoteState(text);
  }

  const hasNote = !!note.trim();
  const noun = NOUN[item.type];
  const buttonColor = hasNote
    ? accent === 'violet'
      ? 'text-violet-600 hover:text-violet-700'
      : 'text-gold hover:text-gold-hover'
    : 'text-stone-300 hover:text-stone-500';

  return (
    <>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          e.preventDefault();
          setOpen(!open);
        }}
        aria-label={hasNote ? `Edit your note for this ${noun}` : `Add a note to this ${noun}`}
        aria-pressed={hasNote}
        className={`flex items-center justify-center rounded-full w-7 h-7 transition-colors ${buttonColor}`}
        title={hasNote ? 'Your note' : 'Add a note'}
      >
        <svg
          viewBox="0 0 16 16"
          className="w-4 h-4"
          fill={hasNote ? 'currentColor' : 'none'}
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinejoin="round"
        >
          <path d="M11.5 1.7L14.3 4.5 5 13.8l-3 .5.5-3z" />
        </svg>
      </button>

      {open && (
        // Anchored to the floating-button pill, but the pill itself is only
        // ~100px wide — use a fixed width that fits a typical card, capped to
        // viewport so it doesn't overflow on mobile.
        <div
          className={`absolute z-20 top-8 w-[min(28rem,calc(100vw-2.5rem))] ${
            align === 'right' ? 'right-0' : 'left-0'
          }`}
          onClick={(e) => e.stopPropagation()}
        >
          <NoteEditor
            initial={note}
            onSave={handleSave}
            onClose={() => setOpen(false)}
            accent={accent}
            placeholder={`Your note for this ${noun} — saved locally, never sent anywhere.`}
          />
        </div>
      )}
    </>
  );
}
