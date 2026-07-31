import { useState } from 'react';
import { setFolderNote, type Folder } from '../../utils/saved-items';
import NoteEditor from '../NoteEditor';
import { FormattedInline } from '../FormattedText';

interface Props {
  /** The folder currently being viewed. */
  folder: Folder;
}

/**
 * A folder's overarching note, shown above its items on /saved — the place to
 * write what ties the collection together, as opposed to ItemNoteBlock's note
 * on a single card. Same violet note language as elsewhere; FormattedInline
 * auto-links verse refs and roots, since these notes tend to cite the items
 * they're about. Collapses to a quiet "Add a note" affordance when empty so an
 * unannotated folder costs no vertical space.
 *
 * Render this KEYED BY FOLDER ID (`key={folder.id}`) so switching folders
 * remounts it. Without that, an open editor would survive the switch and show
 * the previous folder's draft under the new folder's heading.
 */
export default function FolderNote({ folder }: Props) {
  const [editing, setEditing] = useState(false);
  const note = folder.note ?? '';

  if (editing) {
    return (
      <div className="mb-3">
        <NoteEditor
          initial={note}
          accent="violet"
          placeholder={`What ties "${folder.name}" together? Saved locally, never sent anywhere.`}
          onSave={(text) => setFolderNote(folder.id, text)}
          onClose={() => setEditing(false)}
        />
      </div>
    );
  }

  if (!note) {
    return (
      <button
        type="button"
        onClick={() => setEditing(true)}
        className="mb-3 flex w-full items-center gap-2 rounded-lg border border-dashed border-violet-300
                   bg-violet-50/40 px-3 py-2.5 text-left text-xs text-violet-700
                   hover:border-violet-400 hover:bg-violet-50 transition-colors cursor-pointer"
      >
        <svg viewBox="0 0 16 16" className="h-3.5 w-3.5 shrink-0 text-violet-500" fill="currentColor" aria-hidden>
          <path d="M11.5 1.7L14.3 4.5 5 13.8l-3 .5.5-3z" />
        </svg>
        <span>
          <span className="font-medium">Describe this folder</span>
          <span className="text-violet-500/80">
            {' '}— what ties “{folder.name}” together?
          </span>
        </span>
      </button>
    );
  }

  return (
    <div className="group/foldernote mb-3 rounded-lg border-l-2 border-violet-300 bg-violet-50/60 px-3 py-2">
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
        <span className="flex shrink-0 items-center gap-1.5 opacity-0 transition-opacity group-hover/foldernote:opacity-100 group-focus-within/foldernote:opacity-100">
          <button
            type="button"
            onClick={() => setEditing(true)}
            className="text-[10px] text-stone-400 hover:text-violet-600 cursor-pointer"
            aria-label={`Edit the note on folder ${folder.name}`}
          >
            Edit
          </button>
          <button
            type="button"
            onClick={() => {
              if (window.confirm('Delete this folder note? This cannot be undone.')) {
                setFolderNote(folder.id, '');
              }
            }}
            className="text-[10px] text-stone-400 hover:text-red-600 cursor-pointer"
            aria-label={`Delete the note on folder ${folder.name}`}
          >
            Delete
          </button>
        </span>
      </div>
    </div>
  );
}
