import { useState, useEffect } from 'react';
import { useSEO } from '../../hooks/useSEO';
import LearningDashboard from './LearningDashboard';
import RootLesson from './RootLesson';
import ReviewSession from './ReviewSession';
import MnemonicSheet from './MnemonicSheet';

type View = 'dashboard' | 'lesson' | 'review' | 'mnemonic-sheet';

function getLearningRootFromPath(): string | null {
  const match = window.location.pathname.match(/^\/learning\/root\/(.+?)(?:\/)?$/);
  return match ? decodeURIComponent(match[1]) : null;
}

export default function LearningPage() {
  const [view, setView] = useState<View>('dashboard');
  const [activeRootBw, setActiveRootBw] = useState<string | null>(null);

  useSEO({
    title: 'Learn Quranic Arabic Through Root Words',
    description: 'Master Quranic vocabulary through its root words. Each root unlocks a family of words used across different verses — building both vocabulary and deeper understanding.',
    path: '/learning',
  });

  // Handle deep links to /learning/root/<rootBw> and /learning/mnemonic-sheet
  useEffect(() => {
    const rootBw = getLearningRootFromPath();
    if (rootBw) {
      setActiveRootBw(rootBw);
      setView('lesson');
    } else if (window.location.pathname === '/learning/mnemonic-sheet') {
      setView('mnemonic-sheet');
      document.title = 'Mnemonic Sheet — Learn Quranic Arabic | al-nuqta';
    } else {
      document.title = 'Learn Quranic Arabic Through Root Words | al-nuqta';
    }

    function handlePopState() {
      const rootBw = getLearningRootFromPath();
      if (rootBw) {
        setActiveRootBw(rootBw);
        setView('lesson');
      } else if (window.location.pathname === '/learning/mnemonic-sheet') {
        setView('mnemonic-sheet');
        setActiveRootBw(null);
      } else if (window.location.pathname === '/learning') {
        setView('dashboard');
        setActiveRootBw(null);
      }
    }

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  function handleSelectRoot(rootBw: string) {
    setActiveRootBw(rootBw);
    setView('lesson');
    window.history.pushState(null, '', `/learning/root/${encodeURIComponent(rootBw)}`);
  }

  function handleBack() {
    setView('dashboard');
    setActiveRootBw(null);
    window.history.pushState(null, '', '/learning');
    document.title = 'Learn Quranic Arabic Through Root Words | al-nuqta';
  }

  function handleStartReview() {
    setView('review');
    window.history.pushState(null, '', '/learning');
  }

  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 py-10 flex-1 w-full">
      {/* Page header */}
      {view === 'dashboard' && (
        <div className="text-center mb-10">
          <p className="text-xs text-ink-muted tracking-[0.08em] uppercase mb-3.5">Interactive Learning</p>
          <h1 className="font-serif text-2xl sm:text-[34px] font-medium tracking-tight leading-tight text-ink mb-2">
            Learn Quranic Arabic
          </h1>
          <p className="text-sm sm:text-[15px] text-ink-secondary leading-relaxed max-w-2xl mx-auto">
            Master vocabulary through the Quran itself. Each root unlocks a family
            of words used across different verses — building both vocabulary and deeper understanding.
          </p>
        </div>
      )}

      {view === 'dashboard' && (
        <LearningDashboard
          onSelectRoot={handleSelectRoot}
          onStartReview={handleStartReview}
        />
      )}

      {view === 'lesson' && activeRootBw && (
        <RootLesson rootBw={activeRootBw} onBack={handleBack} />
      )}

      {view === 'review' && (
        <ReviewSession onBack={handleBack} />
      )}

      {view === 'mnemonic-sheet' && (
        <MnemonicSheet onBack={handleBack} onSelectRoot={handleSelectRoot} />
      )}
    </div>
  );
}
