import { useState, useEffect } from 'react';
import {
  getVocabStudio,
  runVocabSurvey,
  saveVocabEdits,
  applyVocabTransliteration,
  revertVocabTransliteration,
} from '../../api/admin';
import type { VocabStudioState } from '../../api/admin';

/**
 * Per-root studio. Routed at /admin/vocabulary/<root_buckwalter>.
 *
 * Phase 1 panels:
 *   1. Survey  — run Claude Opus over all occurrences; canonical / reasoning /
 *                counter-examples editable; saves to term_surveys.
 *   2. Apply   — bulk apply transliteration to hard-case verses (Sonnet),
 *                with per-verse revert.
 *
 * Future phases will add: translation_note editor, hard_cases editor,
 * grammar_notes apply, word_meanings apply, audit log.
 */
export default function AdminVocabularyStudio() {
  const rootBw = decodeURIComponent(
    window.location.pathname.match(/^\/admin\/vocabulary\/([^/]+)/)?.[1] ?? '',
  );

  const [state, setState] = useState<VocabStudioState | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  // Edit form mirrors survey
  const [canonical, setCanonical] = useState('');
  const [reasoning, setReasoning] = useState('');
  const [translationNote, setTranslationNote] = useState('');
  const [confidence, setConfidence] = useState(0.85);
  const [leaveUntranslated, setLeaveUntranslated] = useState(false);

  const [surveying, setSurveying] = useState(false);
  const [saving, setSaving] = useState(false);
  const [applyingTransliteration, setApplyingTransliteration] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');

  async function refresh() {
    setLoading(true);
    setError('');
    try {
      const s = await getVocabStudio(rootBw);
      setState(s);
      const surv = s.survey;
      if (surv) {
        setCanonical(surv.canonical_english ?? '');
        setReasoning(surv.reasoning ?? '');
        setTranslationNote(surv.translation_note ?? '');
        setConfidence(surv.confidence ?? 0.85);
        setLeaveUntranslated(!!surv.leave_untranslated);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!rootBw) return;
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rootBw]);

  async function handleRunSurvey(force: boolean) {
    setSurveying(true);
    setStatusMsg('');
    setError('');
    try {
      const result = await runVocabSurvey(rootBw, { force });
      setStatusMsg(`Survey complete in ${(result.elapsed_ms / 1000).toFixed(1)}s using ${result.model}`);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Survey failed');
    } finally {
      setSurveying(false);
    }
  }

  async function handleSaveEdits() {
    setSaving(true);
    setError('');
    try {
      await saveVocabEdits(rootBw, {
        canonical_english: canonical,
        reasoning,
        translation_note: translationNote,
        confidence,
        leave_untranslated: leaveUntranslated ? 1 : 0,
      });
      setStatusMsg('Edits saved.');
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  }

  async function handleApplyTransliteration() {
    if (!confirm('Apply transliteration to all hard-case verses for this root? Originals are preserved and any revision can be reverted per verse.')) {
      return;
    }
    setApplyingTransliteration(true);
    setError('');
    try {
      const r = await applyVocabTransliteration(rootBw);
      setStatusMsg(`Transliteration applied to ${r.results.length} verses`);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Apply failed');
    } finally {
      setApplyingTransliteration(false);
    }
  }

  async function handleRevertVerse(chapter: number, verse: number) {
    setError('');
    try {
      await revertVocabTransliteration(rootBw, chapter, verse);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Revert failed');
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-stone-300 border-t-stone-600" />
      </div>
    );
  }

  if (error && !state) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {error}
      </div>
    );
  }
  if (!state) return null;

  const survey = state.survey;
  const hardCases = survey?.hard_cases ?? [];
  const hasSurvey = !!survey;

  return (
    <div>
      {/* Breadcrumb-ish header */}
      <div className="mb-4 flex items-baseline gap-3">
        <a href="/admin/vocabulary" className="text-xs text-stone-400 hover:text-stone-700">
          ← Back to Vocabulary
        </a>
      </div>
      <div className="flex items-baseline gap-4 mb-2">
        <h1 className="font-serif text-3xl text-stone-800" lang="ar">
          {state.root_arabic}
        </h1>
        <code className="text-stone-500">{state.root_buckwalter}</code>
        {hasSurvey && (
          <>
            <span className="text-stone-300">→</span>
            <span className="text-lg font-medium text-amber-700">
              {survey.canonical_english ?? '(no canonical yet)'}
            </span>
          </>
        )}
        <span className="ml-auto text-xs text-stone-400">
          {state.occurrence_count} occurrences
        </span>
      </div>
      {survey?.surveyor_model && (
        <div className="text-[11px] text-stone-400 mb-6">
          Last survey: {survey.surveyor_model}{' '}
          {survey.surveyor_run_at ? `· ${new Date(survey.surveyor_run_at).toLocaleString()}` : ''}
        </div>
      )}

      {/* Status / error toasts */}
      {statusMsg && (
        <div className="mb-4 rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-2 text-sm text-emerald-700">
          {statusMsg}
        </div>
      )}
      {error && (
        <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* PANEL 1 — Survey */}
      <section className="rounded-xl border border-stone-200 bg-white p-5 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold tracking-wide uppercase text-stone-500">
            1 · Semantic survey
          </h2>
          {hasSurvey ? (
            <button
              onClick={() => handleRunSurvey(true)}
              disabled={surveying}
              className="text-xs px-3 py-1.5 rounded-md border border-stone-300 text-stone-700 hover:bg-stone-50 disabled:opacity-50 cursor-pointer"
            >
              {surveying ? 'Re-running…' : 'Re-survey (Opus)'}
            </button>
          ) : (
            <button
              onClick={() => handleRunSurvey(false)}
              disabled={surveying}
              className="text-xs px-4 py-1.5 rounded-md bg-stone-800 text-white hover:bg-stone-700 disabled:opacity-50 cursor-pointer"
            >
              {surveying ? 'Surveying…' : 'Run survey (Claude Opus)'}
            </button>
          )}
        </div>

        {hasSurvey ? (
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">
                Canonical English
              </label>
              <input
                value={canonical}
                onChange={(e) => setCanonical(e.target.value)}
                className="w-full px-3 py-2 rounded-md border border-stone-300 text-sm font-medium text-amber-700"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">
                Reasoning (semantic thread through all usages)
              </label>
              <textarea
                value={reasoning}
                onChange={(e) => setReasoning(e.target.value)}
                rows={4}
                className="w-full px-3 py-2 rounded-md border border-stone-300 text-sm leading-relaxed"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">
                Translation note (reader-facing tooltip text)
              </label>
              <textarea
                value={translationNote}
                onChange={(e) => setTranslationNote(e.target.value)}
                rows={5}
                className="w-full px-3 py-2 rounded-md border border-stone-300 text-sm leading-relaxed"
              />
            </div>

            {survey.counter_examples && survey.counter_examples.length > 0 && (
              <div>
                <label className="block text-xs font-medium text-stone-600 mb-1">
                  Counter-examples checked ({survey.counter_examples.length})
                </label>
                <ul className="text-xs text-stone-600 space-y-1.5 pl-4 list-disc">
                  {survey.counter_examples.map((ce, i) => (
                    <li key={i}>
                      <a
                        href={`/verse/${ce.ref}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-amber-700 hover:underline font-mono"
                      >
                        {ce.ref}
                      </a>
                      {' — '}
                      {ce.how_canonical_fits}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="flex items-center gap-4 pt-2">
              <label className="text-xs text-stone-600 flex items-center gap-2">
                <span>Confidence:</span>
                <input
                  type="number"
                  min={0}
                  max={1}
                  step={0.05}
                  value={confidence}
                  onChange={(e) => setConfidence(parseFloat(e.target.value))}
                  className="w-20 px-2 py-1 rounded border border-stone-300 text-xs"
                />
              </label>
              <label className="text-xs text-stone-600 flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={leaveUntranslated}
                  onChange={(e) => setLeaveUntranslated(e.target.checked)}
                />
                Leave untranslated (no English canonical fits)
              </label>
              <button
                onClick={handleSaveEdits}
                disabled={saving}
                className="ml-auto text-xs px-4 py-1.5 rounded-md bg-stone-800 text-white hover:bg-stone-700 disabled:opacity-50 cursor-pointer"
              >
                {saving ? 'Saving…' : 'Save edits'}
              </button>
            </div>
          </div>
        ) : (
          <div className="text-sm text-stone-500">
            <p className="mb-3">
              No survey yet. Running the survey calls Claude Opus with all
              {' '}<strong>{state.occurrence_count}</strong> occurrences of this root
              and asks for the abstract semantic core that fits every usage —
              including counter-examples that resist the conventional reading.
            </p>
            <p className="text-xs text-stone-400">
              Cost ≈ $0.15 per survey · runtime 15–30 s.
            </p>
          </div>
        )}
      </section>

      {/* PANEL 2 — Apply */}
      <section className="rounded-xl border border-stone-200 bg-white p-5 mb-6">
        <h2 className="text-sm font-semibold tracking-wide uppercase text-stone-500 mb-4">
          2 · Apply revisions
        </h2>

        {/* Hard-case transliteration */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-stone-700">
              Hard-case transliteration ({state.revisions.translations_revised} of {state.revisions.hard_cases_total} applied)
            </h3>
            <button
              onClick={handleApplyTransliteration}
              disabled={applyingTransliteration || state.revisions.hard_cases_total === 0}
              className="text-xs px-4 py-1.5 rounded-md bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50 cursor-pointer"
            >
              {applyingTransliteration
                ? 'Applying…'
                : state.revisions.hard_cases_total === 0
                  ? 'No hard cases'
                  : 'Apply to all hard cases'}
            </button>
          </div>
          {hardCases.length > 0 ? (
            <ul className="space-y-2 mt-3">
              {hardCases.map((hc) => {
                const [chStr, vsStr] = hc.ref.split(':');
                const ch = parseInt(chStr, 10);
                const vs = parseInt(vsStr, 10);
                return (
                  <li key={hc.ref} className="rounded-md border border-stone-200 bg-stone-50 px-3 py-2">
                    <div className="flex items-center gap-3 flex-wrap">
                      <a
                        href={`/verse/${hc.ref}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-mono text-xs text-amber-700 hover:underline"
                      >
                        {hc.ref}
                      </a>
                      <span className="font-serif text-base text-stone-700" lang="ar">
                        {hc.arabic_word}
                      </span>
                      <span className="text-stone-400 text-xs">→</span>
                      <span className="text-sm italic font-medium text-stone-700">
                        {hc.transliteration}
                      </span>
                      <button
                        onClick={() => handleRevertVerse(ch, vs)}
                        className="ml-auto text-[11px] text-stone-400 hover:text-red-600 cursor-pointer"
                      >
                        Revert this verse
                      </button>
                    </div>
                    <p className="mt-1 text-xs text-stone-500">{hc.reason}</p>
                  </li>
                );
              })}
            </ul>
          ) : hasSurvey ? (
            <p className="text-xs text-stone-400">
              No hard cases identified. The canonical English fits every occurrence cleanly.
            </p>
          ) : (
            <p className="text-xs text-stone-400">Run the survey first.</p>
          )}
        </div>

        {/* Other surfaces (Phase 2 will hook these up) */}
        <div className="text-xs text-stone-400 italic pt-3 border-t border-stone-100">
          Coming next: bulk apply across grammar notes ({state.revisions.grammar_notes_revised} touched) and word meanings ({state.revisions.word_meanings_revised} of {state.revisions.total_word_occurrences} occurrences).
        </div>
      </section>

      {/* PANEL 3 — Occurrences (read-only browse) */}
      <section className="rounded-xl border border-stone-200 bg-white p-5">
        <h2 className="text-sm font-semibold tracking-wide uppercase text-stone-500 mb-4">
          All {state.occurrence_count} occurrences
        </h2>
        <details>
          <summary className="text-xs text-stone-500 hover:text-stone-700 cursor-pointer">
            Show occurrence list
          </summary>
          <ul className="mt-3 space-y-1 max-h-96 overflow-y-auto pr-2">
            {state.occurrences.map((o, i) => (
              <li key={i} className="flex items-baseline gap-3 text-xs leading-relaxed">
                <a
                  href={`/verse/${o.chapter}:${o.verse}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-mono text-amber-700 hover:underline min-w-[3.5rem]"
                >
                  {o.chapter}:{o.verse}
                </a>
                <span className="font-serif text-sm text-stone-700 min-w-[5rem]" lang="ar">
                  {o.arabic_word}
                </span>
                <span className="text-stone-500 truncate">{o.translation}</span>
              </li>
            ))}
          </ul>
        </details>
      </section>
    </div>
  );
}
