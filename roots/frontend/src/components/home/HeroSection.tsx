import { useState, useEffect, useRef } from 'react';
import UnifiedSearch from '../UnifiedSearch';
import type { UnifiedSearchHandle } from '../UnifiedSearch';

// "Try" chip data — a mix of verse refs, roots, and semantic queries
const TRY_CHIPS = [
  { label: '2:255', value: '2:255' },
  { label: 'r-ḥ-m', value: 'r-h-m' },
  { label: 'khalaq', value: 'khalaq' },
  { label: 'خَلَقَ', value: 'خَلَقَ' },
  { label: 'helping those in need', value: 'helping those in need', hideOnMobile: true },
];

interface Props {
  onNavigateVerse: (surah: number, ayah: number) => void;
  onFullSemanticSearch: (query: string) => void;
  loading?: boolean;
}

export default function HeroSection({ onNavigateVerse, onFullSemanticSearch, loading }: Props) {
  // Track which chips have appeared (index-based)
  const [visibleCount, setVisibleCount] = useState(0);
  const searchRef = useRef<UnifiedSearchHandle | null>(null);

  useEffect(() => {
    // Stagger each chip's appearance
    const timers: ReturnType<typeof setTimeout>[] = [];
    TRY_CHIPS.forEach((_, i) => {
      timers.push(setTimeout(() => setVisibleCount(i + 1), 500 + i * 150));
    });
    // Focus search after all chips have animated in
    const lastChipTime = 500 + (TRY_CHIPS.length - 1) * 150;
    timers.push(setTimeout(() => searchRef.current?.focus(), lastChipTime + 400));
    return () => timers.forEach(clearTimeout);
  }, []);

  function handleChipClick(value: string) {
    searchRef.current?.fill(value);
  }

  return (
    <div className="pt-8 sm:pt-14 pb-10 sm:pb-12 text-center max-w-[720px] mx-auto">
      <p className="text-xs text-ink-muted mb-3 sm:mb-3.5 tracking-[0.08em] uppercase">
        al-nuqta
      </p>
      <h1 className="font-serif text-2xl sm:text-[34px] font-medium tracking-tight leading-tight text-ink mb-2">
        A Root Based Translation of the Quran
      </h1>
      <p className="text-sm sm:text-[15px] text-ink-secondary mb-7 sm:mb-9 leading-relaxed">
        Search by reference, trace any word back to its root, compare how the
        Quran uses it elsewhere.
      </p>

      <UnifiedSearch
        onNavigateVerse={onNavigateVerse}
        onFullSemanticSearch={onFullSemanticSearch}
        loading={loading}
        handleRef={searchRef}
      />

      {/* "Try" chips — staggered pop-in */}
      <div className="flex items-center justify-center gap-2 flex-wrap mt-5 min-h-[32px]">
        <span
          className="text-xs text-ink-muted transition-opacity duration-300"
          style={{ opacity: visibleCount > 0 ? 1 : 0 }}
        >
          Try
        </span>
        {TRY_CHIPS.map((chip, i) => (
          <button
            key={chip.value}
            onClick={() => handleChipClick(chip.value)}
            className={`text-xs text-ink-secondary bg-white border border-card-border px-3 py-1.5 rounded-full
                       hover:border-gold hover:text-gold-hover transition-colors
                       ${chip.hideOnMobile ? 'hidden sm:inline-flex' : ''}
                       ${i < visibleCount ? 'animate-chip-pop' : 'opacity-0 scale-75'}`}
            style={{
              transitionProperty: 'opacity, transform',
              transitionDuration: '300ms',
            }}
          >
            {chip.label}
          </button>
        ))}
      </div>
    </div>
  );
}
