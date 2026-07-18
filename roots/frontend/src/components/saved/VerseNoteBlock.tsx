import { useState } from 'react';
import { setVerseNote } from '../../utils/saved-item-actions';
import NoteEditor from '../NoteEditor';
import { FormattedInline } from '../FormattedText';

interface Props {
  /** "surah:ayah" of the verse this note annotates. */
  verseKey: string;
  note: string;
}

/**
 * A verse's personal note, rendered UNDER its verse in the Saved surfaces
 * (page cards + quick panel rows) — a note is part of its verse, not a
 * detached list entry. Violet accent matches the note affordances elsewhere.
 * Edits/deletes go through the coupled write path, so deleting the note of a
 * verse that was only saved FOR the note releases the verse card too.
 */
export default function VerseNoteBlock({ verseKey, note }: Props) {
  const [editing, setEditing] = useState(false);
  const [surah, verse] = verseKey.split(':').map(Number);

  if (editing) {
    return (
      <div className="mt-2">
        <NoteEditor
          initial={note}
          accent="violet"
          onSave={(text) => setVerseNote(surah, verse, text)}
          onClose={() => setEditing(false)}
        />
      </div>
    );
  }

  return (
    <div className="group/note mt-2 rounded-md border-l-2 border-violet-300 bg-violet-50/60 px-2.5 py-1.5">
      <div className="flex items-start gap-2">
        <svg
          viewBox="0 0 16 16"
          className="mt-0.5 h-3 w-3 shrink-0 text-violet-400"
          fill="currentColor"
          aria-hidden
        >
          <path d="M11.5 1.7L14.3 4.5 5 13.8l-3 .5.5-3z" />
        </svg>
        {/* FormattedInline per line = the same auto-linking the translation
            notes and exegesis get: verse refs (2:155), spaced root letters
            (s b r / س ب ر), and Arabic glyphs — while keeping the note's
            plain-text line breaks. */}
        <div className="flex-1 min-w-0 text-xs leading-relaxed text-stone-700">
          {note.split('\n').map((line, i) =>
            line.trim() === '' ? (
              <div key={i} className="h-2" />
            ) : (
              <p key={i}>
                <FormattedInline text={line} />
              </p>
            ),
          )}
        </div>
        <span className="flex shrink-0 items-center gap-1.5 opacity-0 transition-opacity group-hover/note:opacity-100 group-focus-within/note:opacity-100">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setEditing(true);
            }}
            className="text-[10px] text-stone-400 hover:text-violet-600 cursor-pointer"
            aria-label={`Edit note on ${verseKey}`}
          >
            Edit
          </button>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              if (window.confirm('Delete this note? This cannot be undone.')) {
                setVerseNote(surah, verse, '');
              }
            }}
            className="text-[10px] text-stone-400 hover:text-red-600 cursor-pointer"
            aria-label={`Delete note on ${verseKey}`}
          >
            Delete
          </button>
        </span>
      </div>
    </div>
  );
}
