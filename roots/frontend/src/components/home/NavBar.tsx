import { useState, useEffect, type RefObject } from 'react';
import UnifiedSearch from '../UnifiedSearch';

/**
 * Sticky top nav. On scroll past a threshold (or past an explicitly-passed
 * search anchor), the right-side links fade out and a compact search bar
 * fades in. The two share the same absolute container so the nav doesn't
 * jump in height during the swap.
 *
 * Pages with their own prominent search at the top of the viewport
 * (homepage HeroSection, the active-state UnifiedSearch on the verse
 * page) pass a `searchAnchorRef` so the swap only kicks in once that
 * search has scrolled out of view. Pages without their own search use
 * the default 80px scroll threshold.
 */
interface Props {
  currentPath: string;
  /** When provided, the compact-search swap fires once this element's
   *  bottom edge has scrolled above the viewport. Lets pages that
   *  already display a prominent search avoid duplicating it in the nav
   *  while the user is still looking at the original. */
  searchAnchorRef?: RefObject<HTMLElement | null>;
  /** When clicking a verse-result in the compact search, the page can
   *  handle navigation in-place via this callback. Falls back to a
   *  hard navigate if not provided. */
  onNavigateVerse?: (surah: number, ayah: number) => void;
  /** Same idea for full semantic search. */
  onFullSemanticSearch?: (query: string) => void;
}

const NAV_LINKS = [
  { label: 'Learn', href: '/learning' },
  { label: 'Methodology', href: '/methodology' },
  { label: 'Grammar', href: '/grammar-glossary' },
  { label: 'API', href: '/developers' },
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

  useEffect(() => {
    function check() {
      const anchor = searchAnchorRef?.current;
      if (anchor) {
        // Compact when the anchor's bottom edge has scrolled above the
        // viewport top (with a small offset so the swap doesn't flash on
        // and off at the exact boundary).
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

  // Fallback navigation handlers — used when the page didn't supply
  // them (e.g. /word/X:Y/Z, /root/Y, /learning, etc.).
  const handleNavigateVerse =
    onNavigateVerse ??
    ((surah: number, ayah: number) => {
      window.location.href = `/verse/${surah}:${ayah}`;
    });
  const handleFullSemanticSearch =
    onFullSemanticSearch ??
    ((query: string) => {
      // Land on the homepage with the query pre-filled in the URL —
      // a very small extension we can implement later. For now, just
      // route home; the user can paste again.
      window.location.href = `/?q=${encodeURIComponent(query)}`;
    });

  return (
    <nav className="w-full bg-cream/90 backdrop-blur-sm border-b border-card-border sticky top-0 z-30">
      <div className="max-w-3xl mx-auto px-4 flex items-center gap-4 py-3 sm:py-4">
        <a
          href="/"
          className="font-serif text-lg sm:text-xl font-medium tracking-tight text-ink hover:opacity-80 transition-opacity flex-shrink-0"
        >
          al-nuqta
        </a>

        {/* Right-side region — fixed height so absolute children don't
            cause vertical layout shift when toggling between modes.
            The two children stack on top of each other; CSS opacity
            decides which one the user sees. */}
        <div className="relative flex-1 min-h-[36px] flex items-center justify-end">
          {/* Nav links (default) */}
          <div
            className={`absolute inset-0 flex items-center justify-end gap-3 sm:gap-5 text-[12px] sm:text-[13px] text-ink-secondary transition-opacity duration-200 ${
              compact ? 'opacity-0 pointer-events-none' : 'opacity-100'
            }`}
            aria-hidden={compact}
          >
            {NAV_LINKS.map((link) => {
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
            <div className="w-full max-w-[300px]">
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
