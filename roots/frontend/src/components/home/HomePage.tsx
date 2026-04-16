import { useSEO } from '../../hooks/useSEO';
import HeroSection from './HeroSection';
import VerseOfTheDay from './VerseOfTheDay';
import LearningPathCard from './LearningPathCard';
import ApiCard from './ApiCard';

interface Props {
  onNavigateVerse: (surah: number, ayah: number) => void;
  onFullSemanticSearch: (query: string) => void;
  loading?: boolean;
}

export default function HomePage({ onNavigateVerse, onFullSemanticSearch, loading }: Props) {
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
      />
      <VerseOfTheDay onNavigate={onNavigateVerse} />
      <LearningPathCard />
      <ApiCard />
    </div>
  );
}
