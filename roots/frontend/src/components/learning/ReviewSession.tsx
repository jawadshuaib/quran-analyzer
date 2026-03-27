import { useState, useEffect } from 'react';
import type { ReviewVerseData, LearningProgress } from '../../types/learning';
import { fetchReviewVerses } from '../../api/learning';
import { loadProgress, saveProgress, updateReviewResult, getRootProgress } from '../../utils/learning-storage';
import { updateSM2, isDue, reviewRatingToQuality } from '../../utils/spaced-repetition';

interface Props {
  onBack: () => void;
}

export default function ReviewSession({ onBack }: Props) {
  const [progress, setProgress] = useState<LearningProgress>(loadProgress);
  const [dueRoots, setDueRoots] = useState<string[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [verse, setVerse] = useState<ReviewVerseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [flipped, setFlipped] = useState(false);
  const [rated, setRated] = useState(false);
  const [sessionComplete, setSessionComplete] = useState(false);
  const [reviewCount, setReviewCount] = useState(0);

  // Find due roots on mount
  useEffect(() => {
    const p = loadProgress();
    setProgress(p);
    const due = p.reviewQueue.filter(isDue).map((r) => r.rootBw);
    setDueRoots(due);
    if (due.length === 0) {
      setSessionComplete(true);
      setLoading(false);
    }
  }, []);

  // Load verse for current root
  useEffect(() => {
    if (dueRoots.length === 0 || currentIdx >= dueRoots.length) return;
    const rootBw = dueRoots[currentIdx];
    const rp = getRootProgress(progress, rootBw);
    const exclude = rp.versesExposed || [];

    let cancelled = false;
    setLoading(true);
    setFlipped(false);
    setRated(false);
    setError('');

    fetchReviewVerses(rootBw, exclude)
      .then((res) => {
        if (!cancelled && res.verses.length > 0) {
          setVerse(res.verses[0]);
        } else if (!cancelled) {
          // No fresh verses available, use any verse
          return fetchReviewVerses(rootBw, []).then((res2) => {
            if (!cancelled && res2.verses.length > 0) setVerse(res2.verses[0]);
          });
        }
      })
      .catch((e) => { if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load review verse'); })
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, [dueRoots, currentIdx]);

  function handleRate(label: 'again' | 'hard' | 'good' | 'easy') {
    const rootBw = dueRoots[currentIdx];
    const quality = reviewRatingToQuality(label);
    const rp = getRootProgress(progress, rootBw);
    const newSM2 = updateSM2(rp.sm2, quality);
    const verseRef = verse ? `${verse.chapter}:${verse.verse}` : '';

    const updated = updateReviewResult(progress, rootBw, newSM2, verseRef);
    saveProgress(updated);
    setProgress(updated);
    setRated(true);
    setReviewCount((c) => c + 1);

    // Move to next after a brief delay
    setTimeout(() => {
      if (currentIdx + 1 < dueRoots.length) {
        setCurrentIdx(currentIdx + 1);
      } else {
        setSessionComplete(true);
      }
    }, 600);
  }

  if (sessionComplete) {
    return (
      <div className="rounded-xl border border-stone-200 bg-white p-8 text-center shadow-sm">
        <div className="text-4xl mb-3">&#127881;</div>
        <h2 className="text-xl font-semibold text-stone-800 mb-2">
          {reviewCount > 0 ? 'Review Complete!' : 'Nothing to Review'}
        </h2>
        <p className="text-sm text-stone-500 mb-6">
          {reviewCount > 0
            ? `You reviewed ${reviewCount} root${reviewCount > 1 ? 's' : ''} today.`
            : 'All your roots are up to date. Come back later!'}
        </p>
        <button
          onClick={onBack}
          className="px-6 py-2 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 transition-colors"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center text-red-700">
        {error}
        <button onClick={onBack} className="block mx-auto mt-3 text-sm text-stone-600 underline">
          Back to dashboard
        </button>
      </div>
    );
  }

  if (loading || !verse) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button onClick={onBack} className="text-sm text-stone-500 hover:text-stone-700 flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Exit Review
        </button>
        <span className="text-xs text-stone-400">
          {currentIdx + 1} of {dueRoots.length}
        </span>
      </div>

      <p className="text-sm text-stone-600 text-center">
        Can you identify the highlighted root word?
      </p>

      {/* Verse card */}
      <div className="perspective-1000">
        <div
          className={`relative w-full transition-transform duration-500 transform-style-preserve-3d cursor-pointer ${
            flipped ? 'rotate-y-180' : ''
          }`}
          onClick={() => !rated && setFlipped(!flipped)}
          style={{ minHeight: '180px' }}
        >
          {/* Front */}
          <div className="absolute inset-0 backface-hidden rounded-xl border border-stone-200 bg-white p-6 shadow-sm flex flex-col items-center justify-center">
            <p className="text-xs text-stone-400 mb-3">
              {verse.surah_name} {verse.chapter}:{verse.verse}
            </p>
            <p className="font-arabic text-2xl sm:text-3xl leading-loose text-stone-800 text-center" dir="rtl" lang="ar">
              {verse.text_uthmani.split(' ').map((word, i) => {
                const isTarget = verse.target_positions.includes(i + 1);
                return (
                  <span key={i}>
                    {i > 0 && ' '}
                    <span className={isTarget ? 'text-emerald-700 font-bold underline decoration-emerald-300 decoration-2 underline-offset-4' : ''}>
                      {word}
                    </span>
                  </span>
                );
              })}
            </p>
            <p className="text-xs text-stone-400 mt-4">Tap to reveal</p>
          </div>

          {/* Back */}
          <div className="absolute inset-0 backface-hidden rotate-y-180 rounded-xl border border-emerald-200 bg-emerald-50 p-6 shadow-sm overflow-y-auto">
            <p className="text-xs text-stone-400 mb-2">
              {verse.surah_name} {verse.chapter}:{verse.verse}
            </p>
            <p className="text-stone-700 text-sm leading-relaxed mb-4">
              {verse.translation}
            </p>
            {verse.target_words.map((tw) => (
              <div key={tw.pos} className="mb-2">
                <span className="font-arabic text-lg text-emerald-800" dir="rtl">{tw.arabic}</span>
                <span className="text-stone-500 mx-2">—</span>
                <span className="text-stone-700 text-sm">{tw.gloss}</span>
                {tw.lemma_ar && (
                  <span className="ml-2 text-xs text-stone-400">
                    (lemma: <span className="font-arabic" dir="rtl">{tw.lemma_ar}</span>)
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Rating buttons (only show after flip) */}
      {flipped && !rated && (
        <div className="text-center space-y-3">
          <p className="text-sm text-stone-600">How did you do?</p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => handleRate('again')}
              className="px-4 py-2 rounded-lg border border-red-200 bg-red-50 text-red-700 text-sm font-medium hover:bg-red-100 transition-colors"
            >
              Again
            </button>
            <button
              onClick={() => handleRate('hard')}
              className="px-4 py-2 rounded-lg border border-amber-200 bg-amber-50 text-amber-700 text-sm font-medium hover:bg-amber-100 transition-colors"
            >
              Hard
            </button>
            <button
              onClick={() => handleRate('good')}
              className="px-4 py-2 rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-700 text-sm font-medium hover:bg-emerald-100 transition-colors"
            >
              Good
            </button>
            <button
              onClick={() => handleRate('easy')}
              className="px-4 py-2 rounded-lg border border-sky-200 bg-sky-50 text-sky-700 text-sm font-medium hover:bg-sky-100 transition-colors"
            >
              Easy
            </button>
          </div>
        </div>
      )}

      {rated && (
        <p className="text-center text-sm text-emerald-600 animate-pulse">
          Loading next...
        </p>
      )}
    </div>
  );
}
