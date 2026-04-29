import { useState, useEffect } from 'react';
import { getNote, setNote, subscribeToNotes } from '../utils/user-notes';
import NoteEditor from './NoteEditor';

interface Props {
  surah: number;
  ayah: number;
  /** Tone used by both the button and the inline editor — `gold` on the
   *  reader, `violet` on the research view. */
  accent?: 'gold' | 'violet';
}

/**
 * Floating note button shown on /verse/<ref> next to the SaveButton.
 * Click toggles an inline editor that opens BELOW the button at the
 * top-left of the verse card. Notes persist to localStorage via
 * utils/user-notes — the same store the reader's gutter editor uses,
 * so any note written in either view shows up in both.
 */
export default function NoteButton({ surah, ayah, accent = 'violet' }: Props) {
  const [note, setNoteState] = useState<string>(() => getNote(surah, ayah));
  const [open, setOpen] = useState(false);

  useEffect(() => {
    return subscribeToNotes(() => {
      setNoteState(getNote(surah, ayah));
    });
  }, [surah, ayah]);

  function handleSave(text: string) {
    setNote(surah, ayah, text);
    setNoteState(text);
  }

  const hasNote = !!note.trim();
  const buttonColor =
    hasNote
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
        aria-label={hasNote ? 'Edit your note for this verse' : 'Add a note to this verse'}
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
        // Anchored to the floating-button pill, but the pill itself is
        // only ~100px wide — without an explicit width the editor would
        // collapse to that. Use a fixed width that fits a typical verse
        // card, capped to viewport so it doesn't overflow on mobile.
        <div
          className="absolute z-20 left-0 top-8 w-[min(28rem,calc(100vw-2.5rem))]"
          onClick={(e) => e.stopPropagation()}
        >
          <NoteEditor
            initial={note}
            onSave={handleSave}
            onClose={() => setOpen(false)}
            accent={accent}
          />
        </div>
      )}
    </>
  );
}
