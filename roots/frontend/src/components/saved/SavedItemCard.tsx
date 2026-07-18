import { useRef, useState } from 'react';
import {
  removeItemFromFolder,
  type Folder,
  type SavedItem,
} from '../../utils/saved-items';
import { removeSavedItemAndCleanup } from '../../utils/saved-item-actions';
import SavedVerseContent from './SavedVerseContent';
import VerseNoteBlock from './VerseNoteBlock';
import VerseQABlock from './VerseQABlock';
import FolderPopover from '../folders/FolderPopover';
import { wrapArabicRuns } from '../../utils/arabic-runs';
import type { SessionQAEntry } from '../../api/assistant';

interface Props {
  item: SavedItem;
  folders: Folder[];
  selected: boolean;
  onToggleSelect: () => void;
  /** The verse's personal note (verse items only) — rendered under the verse. */
  note?: string;
  /** The user's own Ask-the-Quran Q&A on this verse (verse items only). */
  qa?: SessionQAEntry[];
}

/**
 * One saved item on the /saved page: selectable, navigable, with its note
 * rendered beneath the verse and its folder chips inline (× unfiles from
 * that folder — never unsaves; the trash removes entirely, clearing verse
 * highlights AND deleting the note via the shared helper, with a confirm).
 */
export default function SavedItemCard({ item, folders, selected, onToggleSelect, note, qa }: Props) {
  const [editFolders, setEditFolders] = useState(false);
  const addBtnRef = useRef<HTMLButtonElement>(null);
  const isVerse = item.type === 'verse';

  const memberFolders = (item.folders ?? [])
    .map((id) => folders.find((f) => f.id === id))
    .filter((f): f is Folder => !!f);

  function handleRemove() {
    const verseExtras = note
      ? ' Its highlights are cleared and its note is deleted too.'
      : ' Its highlights are cleared too.';
    if (
      window.confirm(
        `Remove ${isVerse ? `verse ${item.key}` : item.label} from Saved?${
          isVerse ? verseExtras : ''
        }`,
      )
    ) {
      removeSavedItemAndCleanup(item.type, item.key);
    }
  }

  return (
    <div
      className={`group rounded-lg border bg-white p-3 transition-colors ${
        selected ? 'border-rose-300 bg-rose-50/40' : 'border-stone-200 hover:border-amber-300 hover:bg-amber-50/40'
      }`}
    >
      <div className="flex items-start gap-3">
        {/* Bulk-select checkbox */}
        <input
          type="checkbox"
          checked={selected}
          onChange={onToggleSelect}
          aria-label={`Select ${item.label}`}
          className="mt-1 h-3.5 w-3.5 shrink-0 accent-rose-500 cursor-pointer"
        />

        {/* Content — navigates */}
        <a href={item.href} className="flex-1 min-w-0 block">
          {isVerse ? (
            <>
              <span className="block text-[11px] font-medium text-rose-600/80">
                {item.label}
              </span>
              <SavedVerseContent item={item} />
            </>
          ) : (
            <>
              <span className="text-sm font-medium text-stone-700 line-clamp-1">
                {wrapArabicRuns(item.label)}
              </span>
              {item.subtitle && (
                <span className="block text-xs text-stone-400 mt-0.5 line-clamp-2 leading-relaxed">
                  {wrapArabicRuns(item.subtitle)}
                </span>
              )}
            </>
          )}
        </a>

        {/* Remove entirely */}
        <button
          type="button"
          onClick={handleRemove}
          className="mt-0.5 shrink-0 rounded p-1 text-stone-300 hover:text-rose-500 hover:bg-rose-50 transition-colors cursor-pointer"
          aria-label={`Remove ${item.label} from saved`}
          title="Remove from Saved"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
            <path fillRule="evenodd" d="M8.75 1A2.75 2.75 0 006 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 10.23 1.482l.149-.022.841 10.518A2.75 2.75 0 007.596 19h4.807a2.75 2.75 0 002.742-2.53l.841-10.519.149.023a.75.75 0 00.23-1.482A41.03 41.03 0 0014 4.193V3.75A2.75 2.75 0 0011.25 1h-2.5zM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4zM8.58 7.72a.75.75 0 00-1.5.06l.3 7.5a.75.75 0 101.5-.06l-.3-7.5zm4.34.06a.75.75 0 10-1.5-.06l-.3 7.5a.75.75 0 101.5.06l.3-7.5z" clipRule="evenodd" />
          </svg>
        </button>
      </div>

      {/* Personal note — lives under its verse */}
      {isVerse && note && (
        <div className="pl-6">
          <VerseNoteBlock verseKey={item.key} note={note} />
        </div>
      )}

      {/* The user's own Ask-the-Quran answers — an AI note under the verse */}
      {isVerse && qa && qa.length > 0 && (
        <div className="pl-6">
          <VerseQABlock items={qa} />
        </div>
      )}

      {/* Folder chips */}
      <div className="mt-2 flex flex-wrap items-center gap-1 pl-6">
        {memberFolders.map((f) => (
          <span
            key={f.id}
            className="group/chip inline-flex items-center gap-0.5 rounded-full bg-amber-50 border border-amber-200/70
                       px-2 py-0.5 text-[10px] font-medium text-amber-700"
          >
            {f.name}
            <button
              type="button"
              onClick={() => removeItemFromFolder(item.type, item.key, f.id)}
              aria-label={`Remove from ${f.name}`}
              title={`Remove from "${f.name}" (stays saved)`}
              className="ml-0.5 rounded-full text-amber-400 hover:text-amber-700 cursor-pointer"
            >
              <svg viewBox="0 0 20 20" className="h-2.5 w-2.5" fill="currentColor">
                <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
              </svg>
            </button>
          </span>
        ))}
        <button
          ref={addBtnRef}
          type="button"
          onClick={() => setEditFolders((v) => !v)}
          aria-label="Add to folder"
          aria-expanded={editFolders}
          title="Add to folder"
          className="inline-flex items-center gap-0.5 rounded-full border border-dashed border-stone-300
                     px-2 py-0.5 text-[10px] font-medium text-stone-400 hover:border-rose-300
                     hover:text-rose-500 transition-colors cursor-pointer"
        >
          <svg viewBox="0 0 20 20" className="h-2.5 w-2.5" fill="currentColor">
            <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
          </svg>
          folder
        </button>
      </div>

      {editFolders && (
        <FolderPopover
          anchorEl={addBtnRef.current}
          item={{ type: item.type, key: item.key }}
          mode="edit"
          onClose={() => setEditFolders(false)}
        />
      )}
    </div>
  );
}
