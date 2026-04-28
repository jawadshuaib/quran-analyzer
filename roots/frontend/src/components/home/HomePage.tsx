import { useSEO } from '../../hooks/useSEO';
import HeroSection from './HeroSection';
import ContinueReading from './ContinueReading';
import VerseOfTheDay from './VerseOfTheDay';
import SurahList from './SurahList';

interface Props {
  onNavigateVerse: (surah: number, ayah: number) => void;
  onFullSemanticSearch: (query: string) => void;
  loading?: boolean;
  /** Threaded down to HeroSection so the NavBar can detect when the
   *  user has scrolled past the prominent hero search. */
  searchAnchorRef?: React.RefObject<HTMLDivElement | null>;
}

export default function HomePage({ onNavigateVerse, onFullSemanticSearch, loading, searchAnchorRef }: Props) {
  useSEO({
    title: 'A Root Based Translation of the Quran',
    description: 'Explore Quranic Arabic through its root words. Trace any word back to its Semitic origins, compare cross-references across 6,236 verses, and study morphology — all grounded in the Quran\'s own usage.',
    path: '/',
  });

  return (
    <div className="max-w-3xl mx-auto px-4 pb-10">
      <HeroSection
        onNavigateVerse={onNavigateVerse}
        onFullSemanticSearch={onFullSemanticSearch}
        loading={loading}
        searchAnchorRef={searchAnchorRef}
      />
      <ContinueReading />
      <VerseOfTheDay onNavigate={onNavigateVerse} />
      <SurahList />
    </div>
  );
}
