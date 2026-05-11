import { useEffect, useState } from 'react';
import type { VerseGrammarInsights, V7GrammarInsight } from '../types';
import { fetchGrammarInsights } from '../api/quran';
import VerseRefText from './VerseRefText';
import { buckwalterRootToArabicSpaced, buckwalterToArabic } from '../utils/buckwalter';
import { wrapArabicRuns } from '../utils/arabic-runs';

interface Props {
  surah: number;
  ayah: number;
}

const TERM_NOTES: Array<{ term: RegExp; label: string; explain: string; example: string }> = [
  {
    term: /\bimperfective\b/i,
    label: 'Imperfective',
    explain: 'an ongoing/open action, not locked as completed',
    example: "e.g., 'keeps doing' vs 'did once'",
  },
  {
    term: /\bperfective\b/i,
    label: 'Perfective',
    explain: 'an action viewed as complete',
    example: "e.g., 'did' rather than 'is doing'",
  },
  {
    term: /\baccusative\b/i,
    label: 'Accusative',
    explain: 'marks the direct object/focus of an action',
    example: "e.g., in 'God fulfilled the promise', 'the promise' is accusative",
  },
  {
    term: /\bgenitive\b/i,
    label: 'Genitive',
    explain: 'marks possession/attachment',
    example: "e.g., 'book of wisdom' (X of Y relation)",
  },
  {
    term: /\bjussive\b/i,
    label: 'Jussive',
    explain: 'a curtailed verb form often used in command/conditional force',
    example: "e.g., 'let him do' / 'if ... then ...'",
  },
  {
    term: /\bsubjunctive\b/i,
    label: 'Subjunctive',
    explain: 'a verb form often tied to intended/purpose-like action',
    example: "e.g., 'so that he may ...'",
  },
  {
    term: /\b(passive voice|passive)\b/i,
    label: 'Passive',
    explain: 'shifts attention to what happened rather than naming the doer',
    example: "e.g., 'was destroyed' vs 'X destroyed'",
  },
  {
    term: /\bnominal sentence\b/i,
    label: 'Nominal sentence',
    explain: 'a clause built around a noun phrase (state/identity)',
    example: "e.g., 'God is forgiving'",
  },
  {
    term: /\bverbal sentence\b/i,
    label: 'Verbal sentence',
    explain: 'a clause led by a verb (event/action-forward)',
    example: "e.g., 'God forgave'",
  },
];

function detectTermNotes(text: string) {
  const found: Array<{ label: string; explain: string; example: string }> = [];
  for (const note of TERM_NOTES) {
    if (note.term.test(text)) found.push({ label: note.label, explain: note.explain, example: note.example });
  }
  return found;
}

function isSubstantialInsight(text: string): boolean {
  return (text || '').trim().length >= 90;
}

function isTierBInsight(item: { confidence?: number; morph_evidence?: Array<{ type: string }> ; insight: string }): boolean {
  if (!isSubstantialInsight(item.insight)) return false;
  if ((item.confidence ?? 0) < 0.8) return false;
  if ((item.morph_evidence ?? []).length < 1) return false;
  return true;
}

function formatBuckwalterForDisplay(text: string): string {
  if (!text) return '';
  // Handle common generated pattern: "(<form_bw>, root <root_bw>)"
  let out = text.replace(/\(([^,()]+),\s*root\s+([A-Za-z<>\|&}'`~^]+)\)/g, (_m, formBw: string, rootBw: string) => {
    const formAr = buckwalterToArabic(formBw.trim());
    const rootAr = buckwalterRootToArabicSpaced(rootBw.trim());
    return `(${formAr}, root ${rootAr})`;
  });
  // Handle standalone "root <root_bw>"
  out = out.replace(/\broot\s+([A-Za-z<>\|&}'`~^]{2,})\b/g, (_m, rootBw: string) => {
    return `root ${buckwalterRootToArabicSpaced(rootBw.trim())}`;
  });
  return out;
}

function toEvidenceChipLabel(featureType: string, featureValue: string): string | null {
  const t = (featureType || '').trim().toLowerCase();
  const v = (featureValue || '').trim();
  const vu = v.toUpperCase();
  if (!t || !v) return null;

  if (t === 'root_bw') return `Root: ${buckwalterRootToArabicSpaced(v)}`;
  if (t === 'form_bw') return `Form: ${buckwalterToArabic(v)}`;
  if (t === 'lemma_bw') return `Lemma: ${buckwalterToArabic(v)}`;

  if (t === 'feature') {
    if (vu === 'PERF') return 'Perfective form (completed framing)';
    if (vu === 'IMPF') return 'Imperfective form (open-ended framing)';
    if (vu === 'IMPV') return 'Imperative form (command)';
    if (vu === '1S') return '1st person singular (I)';
    if (vu === '1P') return '1st person plural (We)';
    if (vu.startsWith('2')) return '2nd person address (you)';
    if (vu.startsWith('3')) return '3rd person reference (he/they)';
    return null;
  }

  if (t === 'case') {
    if (vu === 'ACC') return 'Accusative role (direct focus/object)';
    if (vu === 'GEN') return 'Genitive role (of/attachment)';
    if (vu === 'NOM') return 'Nominative role (subject/topic)';
    return null;
  }
  if (t === 'voice') {
    if (vu === 'ACTIVE') return 'Active voice';
    if (vu === 'PASSIVE' || vu === 'PASS') return 'Passive voice';
    return null;
  }
  if (t === 'state') {
    if (vu === 'DEF') return 'Definite form';
    if (vu === 'INDEF' || vu === 'INDEFINITE') return 'Indefinite form';
    return null;
  }

  return null;
}

export default function GrammarInsights({ surah, ayah }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<VerseGrammarInsights | null>(null);
  const [checked, setChecked] = useState(false);
  const [displayMode, setDisplayMode] = useState<'full' | 'single' | null>(null);

  const getDisplayMode = (value: VerseGrammarInsights | null): 'full' | 'single' | null => {
    if (!value) return null;
    const insights = value.insights ?? [];
    const substantial = insights.filter((i) => isSubstantialInsight(i.insight || ''));
    const tierA = (value.signal_score ?? 0) >= 0.7 && substantial.length >= 2;
    const tierB = (value.signal_score ?? 0) >= 0.5 && insights.some((i) => isTierBInsight({
      confidence: i.confidence,
      morph_evidence: i.morph_evidence,
      insight: i.insight || '',
    }));
    if (tierA) return 'full';
    if (tierB) return 'single';
    return null;
  };

  useEffect(() => {
    setExpanded(false);
    setLoading(true);
    setData(null);
    setChecked(false);
    fetchGrammarInsights(surah, ayah)
      .then((res) => {
        const next = res?.grammar_insights ?? null;
        const mode = getDisplayMode(next);
        setDisplayMode(mode);
        setData(mode ? next : null);
      })
      .catch(() => {
        setDisplayMode(null);
        setData(null);
      })
      .finally(() => {
        setLoading(false);
        setChecked(true);
      });
  }, [surah, ayah]);

  async function handleToggle() {
    if (expanded) {
      setExpanded(false);
      return;
    }
    setExpanded(true);
  }

  if (checked && !data) return null;
  const displayedInsights =
    displayMode === 'single'
      ? (data?.insights ?? []).filter((i) => isTierBInsight({
          confidence: i.confidence,
          morph_evidence: i.morph_evidence,
          insight: i.insight || '',
        })).slice(0, 1)
      : (data?.insights ?? []);
  const v7DisplayedInsights: V7GrammarInsight[] =
    (data?.insights_v7 ?? [])
      .filter((i) => i?.display?.eligible)
      .sort((a, b) => (b?.quality?.overall_confidence ?? 0) - (a?.quality?.overall_confidence ?? 0))
      .slice(0, 2);

  return (
    <div className="rounded-xl border border-stone-200 bg-white shadow-sm overflow-hidden">
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-stone-50 transition-colors cursor-pointer"
      >
        <span className="text-sm font-semibold text-stone-700">
          Grammar Insights
        </span>
        <svg
          className={`h-4 w-4 text-stone-400 transition-transform duration-200 ${
            expanded ? 'rotate-180' : ''
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <div className="border-t border-stone-100 px-6 py-4">
          {loading ? (
            <div className="flex justify-center py-2">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-violet-200 border-t-violet-600" />
            </div>
          ) : !data ? (
            <p className="text-sm text-stone-400">Loading grammar insights...</p>
          ) : (
            <div className="space-y-4">
              {v7DisplayedInsights.length > 0 && (
                <div className="space-y-3">
                  {v7DisplayedInsights.map((item) => (
                    <div key={item.id} className="rounded-lg border border-violet-100 bg-white p-4">
                      {(() => {
                        const obs = (item.claim?.observation || '').trim();
                        const payoff = (item.meaning_payoff?.text || '').trim();
                        const showPayoff = obs.length > 0 && payoff.length > 0 && obs.toLowerCase() !== payoff.toLowerCase();
                        return (
                          <>
                      <p className="text-sm font-semibold text-stone-800">{wrapArabicRuns(item.title)}</p>
                      <p className="text-xs font-semibold text-violet-700 mt-2">Observation</p>
                      <VerseRefText
                        text={formatBuckwalterForDisplay(item.claim?.observation || '')}
                        className="text-sm text-stone-700 mt-1 block"
                        disableVerseNavigation
                      />
                      {showPayoff && (
                        <>
                          <p className="text-xs font-semibold text-violet-700 mt-2">Why This Matters</p>
                          <VerseRefText
                            text={formatBuckwalterForDisplay(item.meaning_payoff?.text || '')}
                            className="text-sm text-stone-700 mt-1 block"
                            disableVerseNavigation
                          />
                        </>
                      )}
                      {!!item.educational_note?.text && (
                        <div className="mt-2 rounded-md bg-amber-50 border border-amber-100 p-2">
                          <p className="text-[11px] font-semibold text-amber-700 mb-1">Simple Note</p>
                          <p className="text-xs text-amber-900">{wrapArabicRuns(item.educational_note.text)}</p>
                        </div>
                      )}
                      {!!item.evidence_trace?.length && (
                        <div className="mt-2 flex flex-wrap gap-1.5">
                          {item.evidence_trace
                            .slice(0, 6)
                            .map((e) => ({
                              key: `${item.id}-${e.token_ref}-${e.feature_type}-${e.feature_value}`,
                              label: toEvidenceChipLabel(e.feature_type, e.feature_value),
                            }))
                            .filter((e) => !!e.label)
                            .map((e) => (
                              <span
                                key={e.key}
                                className="inline-flex items-center rounded-full border border-violet-200 bg-violet-50 px-2 py-0.5 text-[11px] text-violet-800"
                              >
                                {e.label}
                              </span>
                            ))}
                        </div>
                      )}
                          </>
                        );
                      })()}
                    </div>
                  ))}
                </div>
              )}

              {v7DisplayedInsights.length === 0 && displayedInsights.length > 0 && (
                <div className="space-y-3">
                  {displayedInsights.map((item, i) => (
                    <div key={`${i}-${item.title}`} className="rounded-lg border border-violet-100 bg-white p-4">
                      <p className="text-sm font-semibold text-stone-800">{wrapArabicRuns(item.title)}</p>
                      <VerseRefText
                        text={formatBuckwalterForDisplay(item.insight)}
                        className="text-sm text-stone-700 mt-1 block"
                        disableVerseNavigation
                      />
                      {item.educational_note && (
                        <div className="mt-2 rounded-md bg-amber-50 border border-amber-100 p-2">
                          <p className="text-[11px] font-semibold text-amber-700 mb-1">For Non-Experts</p>
                          <p className="text-xs text-amber-900">{wrapArabicRuns(item.educational_note)}</p>
                        </div>
                      )}
                      {detectTermNotes(item.insight).length > 0 && (
                        <div className="mt-2 rounded-md bg-violet-50 border border-violet-100 p-2">
                          <p className="text-[11px] font-semibold text-violet-700 mb-1">Quick Grammar Note</p>
                          <div className="space-y-1">
                            {detectTermNotes(item.insight).map((n) => (
                              <p key={`${item.title}-${n.label}`} className="text-xs text-violet-800">
                                <span className="font-semibold">{n.label}:</span> {n.explain} ({n.example})
                              </p>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
