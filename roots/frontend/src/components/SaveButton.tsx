import { useState, useCallback } from 'react';
import {
  isSaved,
  toggleSavedItem,
  type SavedItemType,
} from '../utils/saved-items';

interface Props {
  type: SavedItemType;
  itemKey: string;
  label: string;
  href: string;
  subtitle?: string;
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
  onToggle,
}: Props) {
  const [saved, setSaved] = useState(() => isSaved(type, itemKey));
  const [animating, setAnimating] = useState(false);

  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      e.preventDefault();
      const nowSaved = toggleSavedItem({ type, key: itemKey, label, href, subtitle });
      setSaved(nowSaved);
      onToggle?.(nowSaved);

      if (nowSaved) {
        setAnimating(true);
        setTimeout(() => setAnimating(false), 400);
      }
    },
    [type, itemKey, label, href, subtitle, onToggle],
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
      {saved ? (
        /* Filled heart */
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="w-4 h-4 drop-shadow-sm"
        >
          <path d="M11.645 20.91l-.007-.003-.022-.012a15.247 15.247 0 01-.383-.218 25.18 25.18 0 01-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0112 5.052 5.5 5.5 0 0116.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 01-4.244 3.17 15.247 15.247 0 01-.383.219l-.022.012-.007.004-.003.001a.752.752 0 01-.704 0l-.003-.001z" />
        </svg>
      ) : (
        /* Outlined heart */
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
          className="w-4 h-4"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M21.75 8.25c0-3.15-2.35-5.25-5.437-5.25A5.5 5.5 0 0012 5.052 5.5 5.5 0 007.688 3C4.6 3 2.25 5.1 2.25 8.25c0 7.22 9.75 12.75 9.75 12.75s9.75-5.53 9.75-12.75z"
          />
        </svg>
      )}
    </button>
  );
}
