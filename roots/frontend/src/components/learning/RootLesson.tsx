import { useState, useEffect } from 'react';
import type { LearningRootDetail } from '../../types/learning';
import { fetchLearningRoot } from '../../api/learning';
import { loadProgress, saveProgress, markRootLearned } from '../../utils/learning-storage';
import { selfAssessmentToQuality } from '../../utils/spaced-repetition';
import { wrapArabicRuns } from '../../utils/arabic-runs';
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

const FILL_BLANKS_KEY = 'learning.fillInBlanks';

export default function RootLesson({ rootBw, onBack }: Props) {
  const [data, setData] = useState<LearningRootDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [step, setStep] = useState<Step>('anchor');
  const [assessed, setAssessed] = useState(false);
  const [anchorFlipped, setAnchorFlipped] = useState(false);
  const [flipTrigger, setFlipTrigger] = useState(0);
  const [fillInBlanks, setFillInBlanks] = useState<boolean>(() => {
    const stored = window.localStorage.getItem(FILL_BLANKS_KEY);
    return stored === null ? true : stored === '1';
  });

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');
    fetchLearningRoot(rootBw)
      .then((d) => {
        if (!cancelled) {
          setData(d);
          document.title = `Root ${d.root_arabic} (${d.root_buckwalter}) — ${d.unit_theme || 'Learn Quranic Arabic'} | al-nuqta`;
        }
      })
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

  function toggleFillInBlanks() {
    setFillInBlanks((prev) => {
      const next = !prev;
      window.localStorage.setItem(FILL_BLANKS_KEY, next ? '1' : '0');
      return next;
    });
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
        {data.mnemonic_image_url && (
          <div className="flex justify-center mb-3">
            <img
              src={data.mnemonic_image_url}
              alt={`Mnemonic for ${data.root_arabic}`}
              className="w-16 h-16 rounded-full object-cover border-2 border-emerald-200 shadow-sm"
            />
          </div>
        )}
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
          <div className="space-y-5">
            {data.mnemonic_image_url && (
              <div className="flex flex-col items-center gap-2">
                <img
                  src={data.mnemonic_image_url}
                  alt={`Mnemonic image for ${data.root_arabic}`}
                  className="w-full max-w-sm rounded-2xl object-cover shadow-md border border-stone-100 cursor-pointer hover:shadow-lg transition-shadow"
                  style={{ maxHeight: '280px' }}
                  onClick={() => setFlipTrigger((n) => n + 1)}
                />
                {anchorFlipped && data.mnemonic_caption ? (
                  <p className="text-sm text-stone-600 italic text-center max-w-sm leading-relaxed animate-in fade-in duration-500">
                    {data.mnemonic_caption}
                  </p>
                ) : !anchorFlipped ? (
                  <p className="text-xs text-stone-400 italic">
                    Tap the image or verse to reveal meaning
                  </p>
                ) : null}
              </div>
            )}
            <p className="text-base text-stone-600 text-center">
              {anchorFlipped ? 'Now connect the image above to the meaning below.' : 'Read the verse below, then tap to reveal its meaning.'}
            </p>

            {/* Fill in the Blanks toggle */}
            <div className="flex items-center justify-center gap-2.5">
              <button
                onClick={toggleFillInBlanks}
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                  fillInBlanks ? 'bg-emerald-500' : 'bg-stone-300'
                }`}
                aria-label="Toggle fill in the blanks mode"
              >
                <span
                  className={`inline-block h-3.5 w-3.5 rounded-full bg-white shadow-sm transition-transform ${
                    fillInBlanks ? 'translate-x-[18px]' : 'translate-x-[3px]'
                  }`}
                />
              </button>
              <span className="text-sm text-stone-500">Fill in the Blanks</span>
            </div>

            <VerseCard verse={anchorVerse} onFlip={setAnchorFlipped} flipTrigger={flipTrigger} fillInBlanks={fillInBlanks} />
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
                    <span className="text-stone-700">{wrapArabicRuns(d.displayed_text || d.word || '')}</span>
                    <span className="text-stone-400">= {wrapArabicRuns(d.meaning || d.concept || '')}</span>
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
          <div className="flex items-center justify-between">
            <p className="text-base text-stone-600">
              See how the same root is used in different contexts:
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={toggleFillInBlanks}
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                  fillInBlanks ? 'bg-emerald-500' : 'bg-stone-300'
                }`}
                aria-label="Toggle fill in the blanks mode"
              >
                <span
                  className={`inline-block h-3.5 w-3.5 rounded-full bg-white shadow-sm transition-transform ${
                    fillInBlanks ? 'translate-x-[18px]' : 'translate-x-[3px]'
                  }`}
                />
              </button>
              <span className="text-xs text-stone-500">Blanks</span>
            </div>
          </div>
          {contextVerses.length > 0 ? (
            contextVerses.map((cv, i) => (
              <VerseCard
                key={i}
                verse={cv.verse_data!}
                teachingNote={cv.teaching_note}
                fillInBlanks={fillInBlanks}
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
