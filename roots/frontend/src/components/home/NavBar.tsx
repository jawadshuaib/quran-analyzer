import { useState, useEffect, type RefObject } from 'react';
import UnifiedSearch from '../UnifiedSearch';
import { getSavedCount, subscribeToSavedItems } from '../../utils/saved-items';

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
 *   - Saved (always; badge shows the count)
 *   - Methodology
 *   - Settings
 *   (Learn, Metres, Grammar + API live in the footer; Notes live inside
 *   the Saved page under their verses, so there's no top-nav Notes link.)
 */
interface Props {
  currentPath: string;
  searchAnchorRef?: RefObject<HTMLElement | null>;
  onNavigateVerse?: (surah: number, ayah: number) => void;
  onFullSemanticSearch?: (query: string) => void;
}

const STATIC_LINKS = [
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

  // Refresh the Saved badge when saved items change in this tab or another.
  useEffect(() => {
    return subscribeToSavedItems(() => setSavedCount(getSavedCount()));
  }, []);

  const handleNavigateVerse =
    onNavigateVerse ??
    ((surah: number, ayah: number) => {
      window.location.href = `/verse/${surah}:${ayah}`;
    });
  const handleFullSemanticSearch =
    onFullSemanticSearch ??
    ((query: string) => {
      window.location.href = `/search?q=${encodeURIComponent(query)}`;
    });

  // Saved is a real page now (/saved) — the link is always visible so the
  // feature is discoverable (the page has a proper empty state), with the
  // count badge preserving the "you have n things" signal. Notes live inside
  // the Saved page (under their verses), so there's no separate Notes link.
  const navLinks: Array<{ label: string; href: string; count: number }> = [
    { label: 'Saved', href: '/saved', count: savedCount },
  ];

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
            {navLinks.map((b) => (
              <a
                key={b.label}
                href={b.href}
                className={`hover:text-ink transition-colors inline-flex items-center gap-1 ${
                  currentPath.startsWith('/saved') ? 'text-ink font-medium' : ''
                }`}
              >
                {b.label}
                {b.count > 0 && (
                  <span className="text-[10px] text-ink-muted bg-ink/5 rounded-full px-1.5 py-0.5 leading-none">
                    {b.count}
                  </span>
                )}
              </a>
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
