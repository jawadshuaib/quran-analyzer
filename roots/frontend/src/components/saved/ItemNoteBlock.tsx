import { useState } from 'react';
import { setItemNote } from '../../utils/saved-item-actions';
import type { SavedItem } from '../../utils/saved-items';
import NoteEditor from '../NoteEditor';
import { FormattedInline } from '../FormattedText';

interface Props {
  /** The saved item this note annotates (any type). */
  item: SavedItem;
  note: string;
}

/**
 * A saved item's personal note, rendered UNDER its card in the Saved surfaces
 * (page cards + quick panel rows) — a note is part of its item, not a detached
 * list entry. Works for verses, words, and roots: edits/deletes go through the
 * coupled write path (setItemNote), so deleting the note of an item that was
 * only saved FOR the note releases the card too. Violet accent matches the note
 * affordances elsewhere; FormattedInline auto-links verse refs + roots per line.
 */
export default function ItemNoteBlock({ item, note }: Props) {
  const [editing, setEditing] = useState(false);

  const descriptor = {
    type: item.type,
    key: item.key,
    label: item.label,
    href: item.href,
    subtitle: item.subtitle,
    arabic: item.arabic,
    translation: item.translation,
    meta: item.meta,
  };

  if (editing) {
    return (
      <div className="mt-2">
        <NoteEditor
          initial={note}
          accent="violet"
          onSave={(text) => setItemNote(descriptor, text)}
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
            aria-label={`Edit note on ${item.label}`}
          >
            Edit
          </button>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              if (window.confirm('Delete this note? This cannot be undone.')) {
                setItemNote(descriptor, '');
              }
            }}
            className="text-[10px] text-stone-400 hover:text-red-600 cursor-pointer"
            aria-label={`Delete note on ${item.label}`}
          >
            Delete
          </button>
        </span>
      </div>
    </div>
  );
}
