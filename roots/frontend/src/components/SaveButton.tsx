import { useState, useCallback, useEffect } from 'react';
import {
  isSaved,
  toggleSavedItem,
  toggleManualSave,
  type SavedItemType,
} from '../utils/saved-items';
import { SAVED_ITEMS_CHANGED } from './SavedItemsPanel';

interface Props {
  type: SavedItemType;
  itemKey: string;
  label: string;
  href: string;
  subtitle?: string;
  /** Verse-only: stored so the Saved panel can show the verse + highlights. */
  arabic?: string;
  translation?: string;
  /** Called after toggle so parent can update counts */
  onToggle?: (nowSaved: boolean) => void;
}

/**
 * Heart-shaped save/unsave button.
 *
 * Renders as a small floating button (positioned by the parent)
 * with a filled heart when saved, outlined heart when not.
 */
export default function SaveButton({
  type,
  itemKey,
  label,
  href,
  subtitle,
  arabic,
  translation,
  onToggle,
}: Props) {
  const [saved, setSaved] = useState(() => isSaved(type, itemKey));
  const [animating, setAnimating] = useState(false);

  // Keep the icon in sync when the saved state changes elsewhere — notably
  // when highlighting a verse auto-saves it (or clearing the last highlight
  // auto-removes it). Other tabs sync via the storage event.
  useEffect(() => {
    const refresh = () => setSaved(isSaved(type, itemKey));
    refresh();
    window.addEventListener(SAVED_ITEMS_CHANGED, refresh);
    window.addEventListener('storage', refresh);
    return () => {
      window.removeEventListener(SAVED_ITEMS_CHANGED, refresh);
      window.removeEventListener('storage', refresh);
    };
  }, [type, itemKey]);

  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      e.preventDefault();
      // Verses use the highlight-aware toggle (promote a highlight-save to a
      // sticky manual save instead of unsaving it); other kinds toggle plainly.
      const nowSaved =
        type === 'verse'
          ? toggleManualSave({ type, key: itemKey, label, href, subtitle, arabic, translation })
          : toggleSavedItem({ type, key: itemKey, label, href, subtitle });
      setSaved(nowSaved);
      onToggle?.(nowSaved);

      if (nowSaved) {
        setAnimating(true);
        setTimeout(() => setAnimating(false), 400);
      }
    },
    [type, itemKey, label, href, subtitle, arabic, translation, onToggle],
  );

  return (
    <button
      type="button"
      onClick={handleClick}
      aria-label={saved ? 'Remove from saved' : 'Save this item'}
      aria-pressed={saved}
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
  );
}
