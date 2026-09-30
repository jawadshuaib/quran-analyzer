import { useState, useEffect, useRef, type RefObject } from 'react';
import { flushSync } from 'react-dom';
import UnifiedSearch, { type UnifiedSearchHandle } from '../UnifiedSearch';
import { getSavedCount, subscribeToSavedItems } from '../../utils/saved-items';

/**
 * Sticky top nav with the site search.
 *
 * Pages with their own prominent search at the top (homepage hero, the verse
 * page, /search) pass a `searchAnchorRef`: the right-side links show until that
 * search scrolls out of view, then fade out and a compact search fades in, in
 * the same absolute container so the nav doesn't jump in height.
 *
 * Every other page (a word, a root, the reader…) has no search of its own, so
 * the nav carries one from the start instead of waiting for a scroll:
 *   - sm and up: the compact search sits beside the links, always.
 *   - phones: there's no room for both, so a search button leads the links and
 *     swaps the search in (the page still swaps it in on scroll, as before).
 *
 * Right-side links:
 *   - Saved (always; badge shows the count)
 *   - Dictionary
 *   (Methodology, Settings, Metres, Grammar + API live in the footer; Notes
 *   live inside the Saved page under their verses, so there's no top-nav
 *   Notes link.)
 */
interface Props {
  currentPath: string;
  searchAnchorRef?: RefObject<HTMLElement | null>;
  onNavigateVerse?: (surah: number, ayah: number) => void;
  onFullSemanticSearch?: (query: string) => void;
}

const STATIC_LINKS = [
  { label: 'Dictionary', href: '/dictionary' },
];

const SCROLL_THRESHOLD = 80;
// Tailwind's `sm` breakpoint, where the search fits beside the links.
const WIDE_QUERY = '(min-width: 640px)';

function useIsWide(): boolean {
  const [wide, setWide] = useState(() => window.matchMedia(WIDE_QUERY).matches);
  useEffect(() => {
    const mq = window.matchMedia(WIDE_QUERY);
    const onChange = () => setWide(mq.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);
  return wide;
}

export default function NavBar({
  currentPath,
  searchAnchorRef,
  onNavigateVerse,
  onFullSemanticSearch,
}: Props) {
  const [scrolled, setScrolled] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [savedCount, setSavedCount] = useState(() => getSavedCount());
  const wide = useIsWide();
  const searchHandle = useRef<UnifiedSearchHandle | null>(null);
  const searchBoxRef = useRef<HTMLDivElement>(null);

  // No search of the page's own: the nav always offers one.
  const persistent = !searchAnchorRef;
  // Beside the links (wide screens) rather than swapped in over them.
  const inline = persistent && wide;
  const swapped = !inline && (scrolled || searchOpen);

  useEffect(() => {
    function check() {
      const anchor = searchAnchorRef?.current;
      if (anchor) {
        const rect = anchor.getBoundingClientRect();
        setScrolled(rect.bottom < 8);
      } else {
        setScrolled(window.scrollY > SCROLL_THRESHOLD);
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

  // A search opened from the phone button closes on a tap anywhere else.
  useEffect(() => {
    if (!searchOpen) return;
    function onPointerDown(e: PointerEvent) {
      if (!searchBoxRef.current?.contains(e.target as Node)) setSearchOpen(false);
    }
    document.addEventListener('pointerdown', onPointerDown);
    return () => document.removeEventListener('pointerdown', onPointerDown);
  }, [searchOpen]);

  // Refresh the Saved badge when saved items change in this tab or another.
  useEffect(() => {
    return subscribeToSavedItems(() => setSavedCount(getSavedCount()));
  }, []);

  function openSearch() {
    // Commit the swap before focusing: the hidden search is inert, and iOS only
    // raises the keyboard for a focus made inside the tap itself.
    flushSync(() => setSearchOpen(true));
    searchHandle.current?.focus();
  }

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
  // With nothing saved yet the Saved link is hidden, and the Dictionary link
  // uses the room to spell out its full name.
  const navLinks: Array<{ label: string; href: string; count: number }> =
    savedCount > 0 ? [{ label: 'Saved', href: '/saved', count: savedCount }] : [];
  const staticLinks = STATIC_LINKS.map((l) =>
    l.href === '/dictionary' && savedCount === 0 ? { ...l, label: 'Quranic Dictionary' } : l,
  );

  return (
    <nav className="w-full bg-cream/90 backdrop-blur-sm border-b border-card-border sticky top-0 z-30">
      <div className="max-w-3xl mx-auto px-4 flex items-center gap-4 py-1.5 sm:py-4">
        <a
          href="/"
          className="font-serif text-lg sm:text-xl font-medium tracking-tight text-ink hover:opacity-80 transition-opacity flex-shrink-0"
        >
          al-nuqta
        </a>

        <div className="relative flex-1 min-w-0 min-h-[44px] sm:min-h-[36px] flex items-center justify-end gap-5">
          {/* Search: beside the links, or swapped in over them */}
          <div
            ref={searchBoxRef}
            className={
              inline
                ? 'flex-1 min-w-0 flex items-center justify-end'
                : `absolute inset-0 flex items-center justify-end transition-opacity duration-200 ${
                    swapped ? 'opacity-100' : 'opacity-0 pointer-events-none'
                  }`
            }
            aria-hidden={!inline && !swapped}
            inert={!inline && !swapped}
            onKeyDown={(e) => {
              if (e.key === 'Escape' && searchOpen) setSearchOpen(false);
            }}
          >
            <div className="w-full max-w-[360px]">
              <UnifiedSearch
                onNavigateVerse={handleNavigateVerse}
                onFullSemanticSearch={handleFullSemanticSearch}
                handleRef={searchHandle}
                compact
              />
            </div>
          </div>

          {/* Nav links */}
          <div
            className={
              inline
                ? 'flex flex-shrink-0 items-center gap-5 text-[13px] text-ink-secondary'
                : `absolute inset-0 flex items-center justify-end gap-1 sm:gap-5 -mr-2.5 sm:mr-0 text-[14px] sm:text-[13px] text-ink-secondary transition-opacity duration-200 ${
                    swapped ? 'opacity-0 pointer-events-none' : 'opacity-100'
                  }`
            }
            aria-hidden={swapped}
            inert={swapped}
          >
            {persistent && !wide && (
              <button
                type="button"
                onClick={openSearch}
                aria-label="Search"
                className="min-h-[44px] px-2.5 rounded-md active:bg-ink/5 inline-flex items-center hover:text-ink transition-colors cursor-pointer"
              >
                <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </button>
            )}
            {navLinks.map((b) => (
              <a
                key={b.label}
                href={b.href}
                className={`min-h-[44px] sm:min-h-0 px-2.5 sm:px-0 rounded-md active:bg-ink/5 sm:active:bg-transparent hover:text-ink transition-colors inline-flex items-center gap-1 ${
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
            {staticLinks.map((link) => {
              const isActive =
                link.href === '/'
                  ? currentPath === '/'
                  : currentPath.startsWith(link.href);
              return (
                <a
                  key={link.label}
                  href={link.href}
                  className={`min-h-[44px] sm:min-h-0 px-2.5 sm:px-0 rounded-md active:bg-ink/5 sm:active:bg-transparent inline-flex items-center hover:text-ink transition-colors ${
                    isActive ? 'text-ink font-medium' : ''
                  }`}
                >
                  {link.label}
                </a>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
