import { useState, useEffect } from 'react';
import LearningDashboard from './LearningDashboard';
import RootLesson from './RootLesson';
import ReviewSession from './ReviewSession';

type View = 'dashboard' | 'lesson' | 'review';

function getLearningRootFromPath(): string | null {
  const match = window.location.pathname.match(/^\/learning\/root\/(.+?)(?:\/)?$/);
  return match ? decodeURIComponent(match[1]) : null;
}

export default function LearningPage() {
  const [view, setView] = useState<View>('dashboard');
  const [activeRootBw, setActiveRootBw] = useState<string | null>(null);

  // Handle deep links to /learning/root/<rootBw>
  useEffect(() => {
    const rootBw = getLearningRootFromPath();
    if (rootBw) {
      setActiveRootBw(rootBw);
      setView('lesson');
    }

    function handlePopState() {
      const rootBw = getLearningRootFromPath();
      if (rootBw) {
        setActiveRootBw(rootBw);
        setView('lesson');
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
          <h1 className="text-3xl sm:text-4xl font-bold text-stone-800 mb-3 tracking-tight">
            Learn Quranic Arabic
          </h1>
          <p className="text-base text-stone-500 max-w-2xl mx-auto leading-relaxed">
            Master vocabulary through the Quran itself. Each root unlocks a family
            of words used across different verses — building both vocabulary and deeper understanding.
          </p>
          <div className="mt-4">
            <a href="/" className="text-sm text-stone-400 hover:text-stone-600 underline">
              Back to Explorer
            </a>
          </div>
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
    </div>
  );
}
