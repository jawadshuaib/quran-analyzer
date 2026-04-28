import { useState, useEffect, type RefObject } from 'react';
import UnifiedSearch from '../UnifiedSearch';
import { getNotesCount, subscribeToNotes } from '../../utils/user-notes';
import { getSavedCount } from '../../utils/saved-items';
import { SAVED_ITEMS_CHANGED, openSavedPanel } from '../SavedItemsPanel';

/**
 * Sticky top nav. On scroll past a threshold (or past an explicitly-
 * passed search anchor), the right-side links fade out and a compact
 * search bar fades in. The two share the same absolute container so
 * the nav doesn't jump in height during the swap.
 *
 * Pages with their own prominent search at the top (homepage hero,
 * active-state search on the verse page) pass a `searchAnchorRef` so
 * the swap only fires once that search has scrolled out of view. Pages
 * without their own search use the default 80px scroll threshold.
 *
 * Right-side links:
 *   - Notes (only when user has notes)
 *   - Saved (only when user has saved items)
 *   - Learn
 *   - Methodology
 *   - Settings
 *   (Grammar + API moved to footer to make room for Notes / Saved.)
 */
interface Props {
  currentPath: string;
  searchAnchorRef?: RefObject<HTMLElement | null>;
  onNavigateVerse?: (surah: number, ayah: number) => void;
  onFullSemanticSearch?: (query: string) => void;
}

const STATIC_LINKS = [
  { label: 'Learn', href: '/learning' },
  { label: 'Methodology', href: '/methodology' },
  { label: 'Settings', href: '/settings' },
];

const SCROLL_THRESHOLD = 80;

export default function NavBar({
  currentPath,
  searchAnchorRef,
  onNavigateVerse,
  onFullSemanticSearch,
}: Props) {
  const [compact, setCompact] = useState(false);
  const [notesCount, setNotesCount] = useState(() => getNotesCount());
  const [savedCount, setSavedCount] = useState(() => getSavedCount());

  useEffect(() => {
    function check() {
      const anchor = searchAnchorRef?.current;
      if (anchor) {
        const rect = anchor.getBoundingClientRect();
        setCompact(rect.bottom < 8);
      } else {
        setCompact(window.scrollY > SCROLL_THRESHOLD);
      }
    }
    check();
    window.addEventListener('scroll', check, { passive: true });
    window.addEventListener('resize', check);
    return () => {
      window.removeEventListener('scroll', check);
      window.removeEventListener('resize', check);
    };
  }, [searchAnchorRef]);

  // Refresh nav badges when notes / saved items change in this tab or another.
  useEffect(() => {
    return subscribeToNotes(() => setNotesCount(getNotesCount()));
  }, []);
  useEffect(() => {
    function refreshSaved() {
      setSavedCount(getSavedCount());
    }
    window.addEventListener(SAVED_ITEMS_CHANGED, refreshSaved);
    window.addEventListener('storage', refreshSaved);
    return () => {
      window.removeEventListener(SAVED_ITEMS_CHANGED, refreshSaved);
      window.removeEventListener('storage', refreshSaved);
    };
  }, []);

  const handleNavigateVerse =
    onNavigateVerse ??
    ((surah: number, ayah: number) => {
      window.location.href = `/verse/${surah}:${ayah}`;
    });
  const handleFullSemanticSearch =
    onFullSemanticSearch ??
    ((query: string) => {
      window.location.href = `/?q=${encodeURIComponent(query)}`;
    });

  // Notes + Saved appear ONLY when the user has something there. Both
  // open the same SavedItemsPanel via a global event (so we don't
  // duplicate the panel UI). Phase C will wire a Notes tab inside the
  // panel; for now the tab hint is just a forward-compat field.
  const dynamicButtons: Array<{ label: string; count: number; tab: 'saved' | 'notes' }> = [];
  if (notesCount > 0) dynamicButtons.push({ label: 'Notes', count: notesCount, tab: 'notes' });
  if (savedCount > 0) dynamicButtons.push({ label: 'Saved', count: savedCount, tab: 'saved' });

  return (
    <nav className="w-full bg-cream/90 backdrop-blur-sm border-b border-card-border sticky top-0 z-30">
      <div className="max-w-3xl mx-auto px-4 flex items-center gap-4 py-3 sm:py-4">
        <a
          href="/"
          className="font-serif text-lg sm:text-xl font-medium tracking-tight text-ink hover:opacity-80 transition-opacity flex-shrink-0"
        >
          al-nuqta
        </a>

        <div className="relative flex-1 min-h-[36px] flex items-center justify-end">
          {/* Nav links (default) */}
          <div
            className={`absolute inset-0 flex items-center justify-end gap-3 sm:gap-5 text-[12px] sm:text-[13px] text-ink-secondary transition-opacity duration-200 ${
              compact ? 'opacity-0 pointer-events-none' : 'opacity-100'
            }`}
            aria-hidden={compact}
          >
            {dynamicButtons.map((b) => (
              <button
                key={b.label}
                type="button"
                onClick={() => openSavedPanel(b.tab)}
                className="hover:text-ink transition-colors inline-flex items-center gap-1 cursor-pointer"
              >
                {b.label}
                <span className="text-[10px] text-ink-muted bg-ink/5 rounded-full px-1.5 py-0.5 leading-none">
                  {b.count}
                </span>
              </button>
            ))}
            {STATIC_LINKS.map((link) => {
              const isActive =
                link.href === '/'
                  ? currentPath === '/'
                  : currentPath.startsWith(link.href);
              return (
                <a
                  key={link.label}
                  href={link.href}
                  className={`hover:text-ink transition-colors ${
                    isActive ? 'text-ink font-medium' : ''
                  }`}
                >
                  {link.label}
                </a>
              );
            })}
          </div>

          {/* Compact search (appears on scroll) */}
          <div
            className={`absolute inset-0 flex items-center justify-end transition-opacity duration-200 ${
              compact ? 'opacity-100' : 'opacity-0 pointer-events-none'
            }`}
            aria-hidden={!compact}
          >
            <div className="w-full max-w-[360px]">
              <UnifiedSearch
                onNavigateVerse={handleNavigateVerse}
                onFullSemanticSearch={handleFullSemanticSearch}
                compact
              />
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
