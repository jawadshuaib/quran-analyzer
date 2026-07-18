import { useState } from 'react';

/**
 * Inline per-verse note editor. Used by both the reader (ReaderVerse)
 * and the research view (/verse/<ref>) so the editing experience stays
 * identical no matter where the user is.
 *
 * Storage is the caller's responsibility — this component is purely
 * presentational and emits the new text via onSave / onClose.
 */
interface Props {
  initial: string;
  onSave: (text: string) => void;
  onClose: () => void;
  /** Optional accent — `gold` (default) on the reader, `violet` to
   *  match the research-view color palette. */
  accent?: 'gold' | 'violet';
  /** Placeholder text — defaults to the verse wording; word/root pages pass
   *  a generic string so it doesn't say "verse". */
  placeholder?: string;
}

export default function NoteEditor({
  initial,
  onSave,
  onClose,
  accent = 'gold',
  placeholder = 'Your note for this verse — saved locally, never sent anywhere.',
}: Props) {
  const [text, setText] = useState(initial);

  const buttonAccent =
    accent === 'violet'
      ? 'bg-violet-600 hover:bg-violet-700'
      : 'bg-gold/90 hover:bg-gold';
  const focusRing =
    accent === 'violet'
      ? 'focus:border-violet-400 focus:ring-violet-400/20'
      : 'focus:border-gold focus:ring-gold/20';

  function handleSave() {
    onSave(text);
    onClose();
  }
  function handleDelete() {
    onSave('');
    onClose();
  }

  return (
    <div className="rounded-lg border border-card-border bg-cream/50 p-3">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={placeholder}
        rows={4}
        className={`w-full bg-white border border-card-border rounded-md px-3 py-2 text-sm leading-relaxed focus:outline-none focus:ring-2 ${focusRing}`}
        autoFocus
      />
      <div className="mt-2 flex items-center justify-end text-[11px]">
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
            className={`text-white px-3 py-1.5 rounded-md transition-colors cursor-pointer ${buttonAccent}`}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
