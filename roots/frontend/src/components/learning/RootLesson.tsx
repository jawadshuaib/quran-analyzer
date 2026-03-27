import { useState, useEffect } from 'react';
import type { LearningRootDetail } from '../../types/learning';
import { fetchLearningRoot } from '../../api/learning';
import { loadProgress, saveProgress, markRootLearned } from '../../utils/learning-storage';
import { selfAssessmentToQuality } from '../../utils/spaced-repetition';
import VerseCard from './VerseCard';
import DerivativeMap from './DerivativeMap';
import AskPanel from './AskPanel';

interface Props {
  rootBw: string;
  onBack: () => void;
}

type Step = 'anchor' | 'derivatives' | 'story' | 'context' | 'assess';

const STEP_LABELS: Record<Step, string> = {
  anchor: 'Verse',
  derivatives: 'Word Family',
  story: 'Root Story',
  context: 'Context',
  assess: 'Self-Assess',
};

export default function RootLesson({ rootBw, onBack }: Props) {
  const [data, setData] = useState<LearningRootDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [step, setStep] = useState<Step>('anchor');
  const [assessed, setAssessed] = useState(false);

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
      <div className="flex items-center justify-center py-24">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-center text-red-700 text-base">
        {error || 'Failed to load lesson'}
        <button onClick={onBack} className="block mx-auto mt-4 text-sm text-stone-600 underline">
          Back to dashboard
        </button>
      </div>
    );
  }

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
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="text-sm text-stone-500 hover:text-stone-700 flex items-center gap-1.5 font-medium"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Dashboard
        </button>
        <div className="text-sm text-stone-400">
          Unit {data.unit_number}: {data.unit_theme}
        </div>
      </div>

      {/* Root title */}
      <div className="text-center">
        <h2 className="font-arabic text-5xl sm:text-6xl text-stone-800 font-bold" dir="rtl">
          {data.root_arabic}
        </h2>
        <p className="text-sm text-stone-500 mt-2">
          Root: <span className="font-mono">{data.root_buckwalter}</span>
          {data.theological_importance >= 0.7 && (
            <span className="ml-3 inline-flex items-center gap-1 text-sm text-violet-600 font-medium">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              Theologically important
            </span>
          )}
        </p>
      </div>

      {/* Step tabs */}
      <div className="flex items-center justify-center gap-1 bg-stone-100 rounded-xl p-1">
        {steps.map((s, i) => (
          <button
            key={s}
            onClick={() => setStep(s)}
            className={`px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all ${
              i === currentIdx
                ? 'bg-white text-emerald-700 shadow-sm'
                : i < currentIdx
                  ? 'text-emerald-600 hover:bg-white/50'
                  : 'text-stone-400 hover:bg-white/50'
            }`}
          >
            {STEP_LABELS[s]}
          </button>
        ))}
      </div>

      {/* Step content */}
      {step === 'anchor' && (
        anchorVerse ? (
          <div className="space-y-4">
            <p className="text-base text-stone-600 text-center">
              Read the verse below, then tap to reveal its meaning.
            </p>
            <VerseCard verse={anchorVerse} />
          </div>
        ) : (
          <p className="text-base text-stone-400 text-center py-12">
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
        <div className="space-y-5">
          <div className="rounded-2xl border border-violet-200 bg-violet-50 p-6 sm:p-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-violet-700 uppercase tracking-wider">
                Root Story
              </h3>
              <span className="text-xs text-violet-400 bg-violet-100 px-2 py-0.5 rounded-full">AI-generated</span>
            </div>
            <div className="text-base text-stone-700 leading-relaxed whitespace-pre-line">
              {data.root_story}
            </div>
          </div>

          {data.cognate && data.cognate.derivatives.length > 0 && (
            <div className="rounded-2xl border border-indigo-200 bg-indigo-50 p-6 sm:p-8">
              <h3 className="text-sm font-semibold text-indigo-700 uppercase tracking-wider mb-4">
                Semitic Cognates
              </h3>
              <p className="text-sm text-stone-500 mb-3">
                The same root appears in other Semitic languages:
              </p>
              <div className="space-y-2">
                {data.cognate.derivatives.slice(0, 6).map((d, i) => (
                  <div key={i} className="flex items-baseline gap-3 text-base">
                    <span className="text-sm font-semibold text-indigo-600 min-w-[80px]">
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
        <div className="space-y-5">
          <p className="text-base text-stone-600 text-center">
            See how the same root is used in different contexts:
          </p>
          {contextVerses.length > 0 ? (
            contextVerses.map((cv, i) => (
              <VerseCard
                key={i}
                verse={cv.verse_data!}
                teachingNote={cv.teaching_note}
              />
            ))
          ) : (
            <p className="text-base text-stone-400 text-center py-12">
              No additional context verses available for this root.
            </p>
          )}
        </div>
      )}

      {step === 'assess' && (
        <div className="rounded-2xl border border-stone-200 bg-white p-8 sm:p-10 text-center shadow-sm">
          {!assessed ? (
            <>
              <h3 className="text-xl font-semibold text-stone-800 mb-2">
                How well do you know this root?
              </h3>
              <p className="text-base text-stone-500 mb-8">
                Be honest — this helps schedule your reviews.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <button
                  onClick={() => handleAssessment('new')}
                  className="px-6 py-3 rounded-xl border-2 border-red-200 bg-red-50 text-red-700 text-base font-semibold hover:bg-red-100 hover:border-red-300 transition-all"
                >
                  New to me
                </button>
                <button
                  onClick={() => handleAssessment('recognized')}
                  className="px-6 py-3 rounded-xl border-2 border-amber-200 bg-amber-50 text-amber-700 text-base font-semibold hover:bg-amber-100 hover:border-amber-300 transition-all"
                >
                  Recognized it
                </button>
                <button
                  onClick={() => handleAssessment('knew')}
                  className="px-6 py-3 rounded-xl border-2 border-emerald-200 bg-emerald-50 text-emerald-700 text-base font-semibold hover:bg-emerald-100 hover:border-emerald-300 transition-all"
                >
                  Knew it well
                </button>
              </div>
            </>
          ) : (
            <>
              <div className="text-4xl mb-4">&#10003;</div>
              <h3 className="text-xl font-semibold text-emerald-700 mb-2">
                Root learned!
              </h3>
              <p className="text-base text-stone-500 mb-6">
                This root will come up for review based on your rating.
              </p>

              {/* Related roots */}
              {data.related_roots.length > 0 && (
                <div className="border-t border-stone-200 pt-6 mt-6">
                  <p className="text-sm font-semibold text-stone-500 uppercase tracking-wider mb-4">
                    Connected Concepts
                  </p>
                  <div className="flex flex-wrap gap-2.5 justify-center">
                    {data.related_roots.map((rr) => (
                      <a
                        key={rr.root_buckwalter}
                        href={`/learning/root/${encodeURIComponent(rr.root_buckwalter)}`}
                        className="inline-flex items-center gap-2 rounded-xl px-4 py-2 border border-emerald-200 bg-emerald-50 text-base text-emerald-700 hover:bg-emerald-100 transition-colors"
                      >
                        <span className="font-arabic text-lg" dir="rtl">{rr.root_arabic}</span>
                        <span className="text-xs text-stone-400">{rr.unit_theme}</span>
                      </a>
                    ))}
                  </div>
                </div>
              )}

              <button
                onClick={onBack}
                className="mt-8 px-8 py-3 rounded-xl bg-emerald-600 text-white text-base font-semibold hover:bg-emerald-700 transition-colors shadow-sm"
              >
                Back to Dashboard
              </button>
            </>
          )}
        </div>
      )}

      {/* Navigation */}
      {!assessed && (
        <div className="flex justify-between pt-2">
          <button
            onClick={prevStep}
            disabled={currentIdx === 0}
            className="px-5 py-2.5 rounded-xl text-base text-stone-600 hover:bg-stone-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors font-medium"
          >
            &larr; Previous
          </button>
          <button
            onClick={nextStep}
            disabled={currentIdx === steps.length - 1}
            className="px-5 py-2.5 rounded-xl text-base bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors font-medium shadow-sm"
          >
            {currentIdx === steps.length - 2 ? 'Self-Assess' : 'Next'} &rarr;
          </button>
        </div>
      )}
    </div>
  );
}
