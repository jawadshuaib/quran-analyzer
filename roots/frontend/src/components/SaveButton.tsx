import { useState, useCallback, useEffect, useRef } from 'react';
import {
  isSaved,
  toggleSavedItem,
  toggleManualSave,
  getItemFolderIds,
  getSavedItemSource,
  subscribeToSavedItems,
  type SavedItemType,
  type SavedItemMeta,
} from '../utils/saved-items';
import { removeSavedItemAndCleanup } from '../utils/saved-item-actions';
import { getItemNote } from '../utils/user-notes';
import FolderPopover, { type FolderPopoverMode } from './folders/FolderPopover';

interface Props {
  type: SavedItemType;
  itemKey: string;
  label: string;
  href: string;
  subtitle?: string;
  /** The Arabic to store for instant Saved rendering: verse Uthmani text,
   *  word host-verse text, or root glyph. */
  arabic?: string;
  translation?: string;
  /** Structured extras for rich word/root cards (root/lemma/field/counts). */
  meta?: SavedItemMeta;
  /** Called after toggle so parent can update counts */
  onToggle?: (nowSaved: boolean) => void;
}

/**
 * Heart-shaped save/unsave button.
 *
 * Renders as a small floating button (positioned by the parent)
 * with a filled heart when saved, outlined heart when not.
 *
 * Saving opens the FolderPopover (GitHub-star model): the save has already
 * happened; the popover is the confirmation, offering optional folder
 * filing. Once saved, a sibling folder icon lets the user edit memberships
 * without re-toggling the save.
 */
export default function SaveButton({
  type,
  itemKey,
  label,
  href,
  subtitle,
  arabic,
  translation,
  meta,
  onToggle,
}: Props) {
  const [saved, setSaved] = useState(() => isSaved(type, itemKey));
  const [inFolders, setInFolders] = useState(() => getItemFolderIds(type, itemKey).length > 0);
  const [animating, setAnimating] = useState(false);
  const [popover, setPopover] = useState<FolderPopoverMode | null>(null);
  const saveRef = useRef<HTMLButtonElement>(null);
  const folderRef = useRef<HTMLButtonElement>(null);

  // Keep the icons in sync when the saved state changes elsewhere — notably
  // when highlighting a verse auto-saves it (or clearing the last highlight
  // auto-removes it). Other tabs sync via the storage event.
  useEffect(() => {
    const refresh = () => {
      setSaved(isSaved(type, itemKey));
      setInFolders(getItemFolderIds(type, itemKey).length > 0);
    };
    refresh();
    return subscribeToSavedItems(refresh);
  }, [type, itemKey]);

  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      e.preventDefault();

      // Will this press REMOVE the item? Non-verse types toggle plainly (saved
      // → removed). A verse only removes when it's a sticky manual save; a
      // highlight/note auto-save PROMOTES instead (stays saved), so it can't
      // orphan a note.
      const currentlySaved = isSaved(type, itemKey);
      const source = currentlySaved ? getSavedItemSource(type, itemKey) : undefined;
      const willRemove =
        currentlySaved && (type !== 'verse' || source === 'manual' || source === undefined);

      // Removing an item that carries a note must delete the note too, else it
      // is orphaned and would resurrect on re-save. Confirm first (notes are
      // user data), then clean up highlights + note + the item together.
      if (willRemove && getItemNote(type, itemKey)) {
        if (!window.confirm('Remove this from Saved and delete its note?')) return;
        removeSavedItemAndCleanup(type, itemKey);
        setSaved(false);
        onToggle?.(false);
        setPopover(null);
        return;
      }

      const nowSaved =
        type === 'verse'
          ? toggleManualSave({ type, key: itemKey, label, href, subtitle, arabic, translation, meta })
          : toggleSavedItem({ type, key: itemKey, label, href, subtitle, arabic, translation, meta });
      setSaved(nowSaved);
      onToggle?.(nowSaved);
      setPopover(nowSaved ? 'save' : null);

      if (nowSaved) {
        setAnimating(true);
        setTimeout(() => setAnimating(false), 400);
      }
    },
    [type, itemKey, label, href, subtitle, arabic, translation, meta, onToggle],
  );

  return (
    <>
      <button
        ref={saveRef}
        type="button"
        onClick={handleClick}
        aria-label={saved ? 'Remove from saved' : 'Save this item'}
        aria-pressed={saved}
        aria-expanded={popover !== null}
        className={`group flex items-center justify-center rounded-full
                    w-7 h-7
                    transition-all duration-200
                    ${saved
                      ? 'text-rose-500 hover:text-rose-600'
                      : 'text-stone-300 hover:text-rose-400'}
                    ${animating ? 'scale-125' : 'scale-100'}`}
        title={saved ? 'Saved' : 'Save'}
      >
        {/* Bookmark icon — same shape used in the surah reader gutter so
            the saved-state affordance is consistent across surfaces. */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 16 16"
          fill={saved ? 'currentColor' : 'none'}
          stroke="currentColor"
          strokeWidth={1.5}
          className="w-4 h-4"
        >
          <path d="M4 1.5h8a.5.5 0 01.5.5v12L8 11l-4.5 3V2a.5.5 0 01.5-.5z" strokeLinejoin="round" />
        </svg>
      </button>
      {saved && (
        <button
          ref={folderRef}
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            e.preventDefault();
            setPopover((p) => (p === 'edit' ? null : 'edit'));
          }}
          aria-label="Add to folder"
          aria-expanded={popover === 'edit'}
          className={`flex items-center justify-center rounded-full w-7 h-7 transition-colors
                      ${inFolders
                        ? 'text-rose-400 hover:text-rose-500'
                        : 'text-stone-300 hover:text-rose-400'}`}
          title="Add to folder"
        >
          <svg viewBox="0 0 16 16" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5}>
            <path d="M1.75 4A1.25 1.25 0 013 2.75h2.6c.33 0 .65.13.88.37l1.1 1.13H13A1.25 1.25 0 0114.25 5.5v6.5A1.25 1.25 0 0113 13.25H3A1.25 1.25 0 011.75 12V4z" strokeLinejoin="round" />
          </svg>
        </button>
      )}
      {popover !== null && (
        <FolderPopover
          anchorEl={(popover === 'edit' ? folderRef.current : saveRef.current) ?? saveRef.current}
          item={{ type, key: itemKey }}
          mode={popover}
          onClose={() => setPopover(null)}
        />
      )}
    </>
  );
}
