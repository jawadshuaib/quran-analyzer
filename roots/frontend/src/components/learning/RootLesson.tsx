import { useState, useEffect } from 'react';
import type { LearningRootDetail } from '../../types/learning';
import { fetchLearningRoot } from '../../api/learning';
import { loadProgress, saveProgress, markRootLearned, getRootProgress } from '../../utils/learning-storage';
import { selfAssessmentToQuality } from '../../utils/spaced-repetition';
import VerseCard from './VerseCard';
import DerivativeMap from './DerivativeMap';
import AskPanel from './AskPanel';

interface Props {
  rootBw: string;
  onBack: () => void;
}

type Step = 'anchor' | 'derivatives' | 'story' | 'context' | 'assess';

export default function RootLesson({ rootBw, onBack }: Props) {
  const [data, setData] = useState<LearningRootDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [step, setStep] = useState<Step>('anchor');
  const [assessed, setAssessed] = useState(false);
  const [showStory, setShowStory] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');
    fetchLearningRoot(rootBw)
      .then((d) => { if (!cancelled) setData(d); })
      .catch((e) => { if (!cancelled) setError(e.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [rootBw]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center text-red-700">
        {error || 'Failed to load lesson'}
        <button onClick={onBack} className="block mx-auto mt-3 text-sm text-stone-600 underline">
          Back to dashboard
        </button>
      </div>
    );
  }

  const progress = getRootProgress(loadProgress(), rootBw);
  const anchorVerse = data.anchor_verse.verse_data;
  const contextVerses = data.context_verses.filter((cv) => cv.verse_role !== 'anchor' && cv.verse_data);

  function handleAssessment(label: 'new' | 'recognized' | 'knew') {
    const quality = selfAssessmentToQuality(label);
    const vd = data!.anchor_verse.verse_data;
    const verseRef = vd ? `${vd.chapter}:${vd.verse}` : '';
    const updated = markRootLearned(loadProgress(), rootBw, quality, verseRef);
    saveProgress(updated);
    setAssessed(true);
  }

  const steps: Step[] = ['anchor', 'derivatives', 'story', 'context', 'assess'];
  const currentIdx = steps.indexOf(step);

  function nextStep() {
    if (currentIdx < steps.length - 1) {
      setStep(steps[currentIdx + 1]);
    }
  }

  function prevStep() {
    if (currentIdx > 0) {
      setStep(steps[currentIdx - 1]);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="text-sm text-stone-500 hover:text-stone-700 flex items-center gap-1"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Dashboard
        </button>
        <div className="text-xs text-stone-400">
          Unit {data.unit_number}: {data.unit_theme}
        </div>
      </div>

      {/* Root title */}
      <div className="text-center">
        <h2 className="font-arabic text-4xl text-stone-800 font-bold" dir="rtl">
          {data.root_arabic}
        </h2>
        <p className="text-sm text-stone-500 mt-1">
          Root: {data.root_buckwalter}
          {data.theological_importance >= 0.7 && (
            <span className="ml-2 inline-flex items-center gap-1 text-xs text-violet-600">
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              Theologically important
            </span>
          )}
        </p>
      </div>

      {/* Step indicator */}
      <div className="flex items-center justify-center gap-2">
        {steps.map((s, i) => (
          <button
            key={s}
            onClick={() => setStep(s)}
            className={`w-2.5 h-2.5 rounded-full transition-colors ${
              i === currentIdx
                ? 'bg-emerald-500 scale-125'
                : i < currentIdx
                  ? 'bg-emerald-300'
                  : 'bg-stone-200'
            }`}
            title={s}
          />
        ))}
      </div>

      {/* Step content */}
      {step === 'anchor' && (
        anchorVerse ? (
          <div className="space-y-4">
            <p className="text-sm text-stone-600 text-center">
              Read the verse below, then tap to reveal its meaning.
            </p>
            <VerseCard verse={anchorVerse} targetRootBw={rootBw} />
          </div>
        ) : (
          <p className="text-sm text-stone-400 text-center py-8">
            Anchor verse data unavailable. Tap Next to continue.
          </p>
        )
      )}

      {step === 'derivatives' && (
        <DerivativeMap
          rootArabic={data.root_arabic}
          rootBw={data.root_buckwalter}
          derivatives={data.derivatives}
        />
      )}

      {step === 'story' && (
        <div className="space-y-4">
          <div className="rounded-xl border border-violet-200 bg-violet-50 p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-violet-700 uppercase tracking-wide">
                Root Story
              </h3>
              <span className="text-xs text-violet-400">AI-generated</span>
            </div>
            <div className="text-sm text-stone-700 leading-relaxed whitespace-pre-line">
              {data.root_story}
            </div>
          </div>

          {data.cognate && data.cognate.derivatives.length > 0 && (
            <div className="rounded-xl border border-indigo-200 bg-indigo-50 p-5">
              <h3 className="text-sm font-semibold text-indigo-700 uppercase tracking-wide mb-3">
                Semitic Cognates
              </h3>
              <p className="text-xs text-stone-500 mb-2">
                The same root appears in other Semitic languages:
              </p>
              <div className="space-y-1.5">
                {data.cognate.derivatives.slice(0, 6).map((d, i) => (
                  <div key={i} className="flex items-baseline gap-2 text-sm">
                    <span className="text-xs font-medium text-indigo-600 min-w-[70px]">
                      {d.language}
                    </span>
                    <span className="text-stone-700">{d.displayed_text || d.word}</span>
                    <span className="text-stone-400">= {d.meaning || d.concept}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Ask Panel */}
          <AskPanel rootBw={rootBw} rootArabic={data.root_arabic} />
        </div>
      )}

      {step === 'context' && (
        <div className="space-y-4">
          <p className="text-sm text-stone-600 text-center">
            See how the same root is used in different contexts:
          </p>
          {contextVerses.length > 0 ? (
            contextVerses.map((cv, i) => (
              <VerseCard
                key={i}
                verse={cv.verse_data!}
                targetRootBw={rootBw}
                teachingNote={cv.teaching_note}
              />
            ))
          ) : (
            <p className="text-sm text-stone-400 text-center py-8">
              No additional context verses available for this root.
            </p>
          )}
        </div>
      )}

      {step === 'assess' && (
        <div className="rounded-xl border border-stone-200 bg-white p-6 text-center shadow-sm">
          {!assessed ? (
            <>
              <h3 className="text-lg font-semibold text-stone-800 mb-2">
                How well do you know this root?
              </h3>
              <p className="text-sm text-stone-500 mb-6">
                Be honest — this helps schedule your reviews.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={() => handleAssessment('new')}
                  className="px-5 py-2.5 rounded-lg border border-red-200 bg-red-50 text-red-700 text-sm font-medium hover:bg-red-100 transition-colors"
                >
                  New to me
                </button>
                <button
                  onClick={() => handleAssessment('recognized')}
                  className="px-5 py-2.5 rounded-lg border border-amber-200 bg-amber-50 text-amber-700 text-sm font-medium hover:bg-amber-100 transition-colors"
                >
                  Recognized it
                </button>
                <button
                  onClick={() => handleAssessment('knew')}
                  className="px-5 py-2.5 rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-700 text-sm font-medium hover:bg-emerald-100 transition-colors"
                >
                  Knew it well
                </button>
              </div>
            </>
          ) : (
            <>
              <div className="text-3xl mb-3">&#10003;</div>
              <h3 className="text-lg font-semibold text-emerald-700 mb-2">
                Root learned!
              </h3>
              <p className="text-sm text-stone-500 mb-4">
                This root will come up for review based on your rating.
              </p>

              {/* Related roots */}
              {data.related_roots.length > 0 && (
                <div className="border-t border-stone-200 pt-4 mt-4">
                  <p className="text-xs font-semibold text-stone-500 uppercase tracking-wide mb-3">
                    Connected Concepts
                  </p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {data.related_roots.map((rr) => (
                      <a
                        key={rr.root_buckwalter}
                        href={`/learning/root/${encodeURIComponent(rr.root_buckwalter)}`}
                        className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 border border-emerald-200 bg-emerald-50 text-sm text-emerald-700 hover:bg-emerald-100 transition-colors"
                      >
                        <span className="font-arabic" dir="rtl">{rr.root_arabic}</span>
                        <span className="text-xs text-stone-400">{rr.unit_theme}</span>
                      </a>
                    ))}
                  </div>
                </div>
              )}

              <button
                onClick={onBack}
                className="mt-6 px-6 py-2 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 transition-colors"
              >
                Back to Dashboard
              </button>
            </>
          )}
        </div>
      )}

      {/* Navigation */}
      {!assessed && (
        <div className="flex justify-between">
          <button
            onClick={prevStep}
            disabled={currentIdx === 0}
            className="px-4 py-2 rounded-lg text-sm text-stone-600 hover:bg-stone-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            Previous
          </button>
          <button
            onClick={nextStep}
            disabled={currentIdx === steps.length - 1}
            className="px-4 py-2 rounded-lg text-sm bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            {currentIdx === steps.length - 2 ? 'Self-Assess' : 'Next'}
          </button>
        </div>
      )}
    </div>
  );
}
