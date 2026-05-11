import { useState, useEffect, useRef } from 'react';
import {
  listProperNouns,
  detectProperNouns,
  clearProperNouns,
  runProperNounsOllama,
  runProperNounsSonnet,
  reviewProperNoun,
  applyProperNoun,
  revertProperNoun,
} from '../../api/admin';
import type { ProperNounCandidate, ProperNounStats } from '../../api/admin';
import { useConfirm } from './shared/useConfirm';

/**
 * Admin: Proper Nouns review queue.
 *
 * UI flow:
 *   1. Click "Detect candidates (Stage 0)" — runs the mechanical
 *      pre-filter once. Idempotent (UNIQUE on chapter+verse+word_pos).
 *   2. Click "Run Ollama (Stage 1)" — auto-loops in 5-row chunks,
 *      filling in qwen + gptoss verdicts on each candidate.
 *   3. Click "Run Sonnet (Stage 2)" — auto-loops in 5-row chunks,
 *      filling in sonnet_verdict + alternatives + reasoning.
 *   4. For each adjudicated candidate, expand the row to see verse
 *      context + LLM reasoning + alternative translations. Pick one
 *      and click "Apply", or "Reject", or "Edit" to type your own.
 *   5. "Apply" updates ai_word_meanings.preferred_translation. The
 *      chip layer + verse page reflect the change immediately.
 *   6. "Revert" undoes any apply, restoring the prior translation.
 *
 * Phase 4: also expose a "Refresh verse translation" button per applied
 * candidate that calls revise_verse_translations on the affected verse.
 */
export default function AdminProperNouns() {
  const { confirm, dialog: confirmDialog } = useConfirm();

  const [candidates, setCandidates] = useState<ProperNounCandidate[]>([]);
  const [stats, setStats] = useState<ProperNounStats | null>(null);
  const [totalMatched, setTotalMatched] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusMsg, setStatusMsg] = useState('');

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [verdictFilter, setVerdictFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [rootFilter, setRootFilter] = useState<string>('');
  const [order, setOrder] = useState<string>('rooted');

  // Action runners (Stage 0/1/2)
  const [detecting, setDetecting] = useState(false);
  const [clearing, setClearing] = useState(false);
  const ollamaRunningRef = useRef(false);
  const [ollamaRunning, setOllamaRunning] = useState(false);
  const [ollamaProgress, setOllamaProgress] = useState<{ processed: number; remaining: number } | null>(null);
  const sonnetRunningRef = useRef(false);
  const [sonnetRunning, setSonnetRunning] = useState(false);
  const [sonnetProgress, setSonnetProgress] = useState<{ processed: number; adjudicated: number; remaining: number } | null>(null);

  // Per-row state
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});
  const [editing, setEditing] = useState<Record<number, string>>({});

  async function refresh() {
    setLoading(true);
    setError('');
    try {
      const r = await listProperNouns({
        status: statusFilter || undefined,
        verdict: verdictFilter || undefined,
        type: typeFilter || undefined,
        root: rootFilter || undefined,
        order,
        limit: 200,
      });
      setCandidates(r.candidates);
      setStats(r.stats);
      setTotalMatched(r.total_matched);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, verdictFilter, typeFilter, rootFilter, order]);

  // -------------------- Action handlers --------------------

  async function handleDetect() {
    const ok = await confirm({
      title: 'Run Stage 0 detection?',
      message: 'Mechanically scans the entire corpus for capitalized translation tokens that look like calqued proper names. Free, ~10-30s. Idempotent — already-flagged candidates are skipped.',
      confirmLabel: 'Run',
    });
    if (!ok) return;
    setDetecting(true);
    setError('');
    setStatusMsg('');
    try {
      const r = await detectProperNouns();
      setStatusMsg(`Stage 0 complete: ${r.inserted} new candidates (${r.skipped_existing} already existed, ${r.skipped_no_translation} skipped without translation).`);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Detection failed');
    } finally {
      setDetecting(false);
    }
  }

  async function handleClear(force: boolean) {
    const ok = await confirm({
      title: force ? 'Force-clear ALL candidates?' : 'Clear all unreviewed candidates?',
      message: force
        ? 'Wipes the entire proper_noun_candidates table — including any that have been adjudicated, reviewed, or applied. Applied translations stay in ai_word_meanings (revert those individually first if you want them back).'
        : 'Wipes candidates that haven\'t been adjudicated, reviewed, or applied yet. Useful when re-running Stage 0 after a heuristic update. Refuses if any candidate has review state — pass force-clear in that case.',
      confirmLabel: force ? 'Force-clear' : 'Clear',
      tone: 'danger',
    });
    if (!ok) return;
    setClearing(true);
    setError('');
    setStatusMsg('');
    try {
      const r = await clearProperNouns(force);
      setStatusMsg(`Cleared ${r.cleared} candidate${r.cleared === 1 ? '' : 's'}.`);
      await refresh();
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Clear failed';
      // If protected, offer force option in the error
      if (msg.includes('force=true')) {
        setError(`${msg} Click "Force-clear" instead if you really mean it.`);
      } else {
        setError(msg);
      }
    } finally {
      setClearing(false);
    }
  }

  async function handleRunOllama() {
    if (ollamaRunningRef.current) {
      ollamaRunningRef.current = false;
      setStatusMsg('Stopping after current batch…');
      return;
    }
    const pending = (stats?.total ?? 0) - (stats?.stage1_done ?? 0);
    if (pending === 0) return;
    const ok = await confirm({
      title: `Run Stage 1 on ${pending} candidate${pending === 1 ? '' : 's'}?`,
      message: `Asks Qwen 397B (free Ollama cloud) for a verdict on each pending candidate. Auto-loops in batches of 5. ~10-15s per candidate. Free.`,
      confirmLabel: 'Run',
    });
    if (!ok) return;
    ollamaRunningRef.current = true;
    setOllamaRunning(true);
    setOllamaProgress({ processed: 0, remaining: pending });
    setError('');
    setStatusMsg('');
    let totalProcessed = 0;
    let consecutiveFailures = 0;
    try {
      while (ollamaRunningRef.current) {
        let r;
        try {
          // One candidate per chunk — Qwen 397B's response time on
          // Ollama Cloud is variable (10-30s) and any limit > 1 risks
          // exceeding the proxy timeout. The auto-loop overhead is
          // negligible compared to the LLM call itself.
          r = await runProperNounsOllama({ limit: 1, models: 'qwen' });
          consecutiveFailures = 0;
        } catch (chunkErr) {
          consecutiveFailures++;
          const msg = chunkErr instanceof Error ? chunkErr.message : String(chunkErr);
          if (consecutiveFailures >= 3) throw chunkErr;
          const waitSec = 2 ** consecutiveFailures;
          setStatusMsg(`Network error (${consecutiveFailures}/3): ${msg.slice(0, 80)}. Retrying in ${waitSec}s…`);
          await new Promise((resolve) => setTimeout(resolve, waitSec * 1000));
          continue;
        }
        totalProcessed += r.processed;
        setOllamaProgress({ processed: totalProcessed, remaining: r.remaining });
        setStats(r.summary);
        if (r.remaining > 0 && r.processed > 0) {
          setStatusMsg(`Auto-continuing… ${totalProcessed} processed, ${r.remaining} remaining`);
        }
        if (r.remaining === 0 || r.processed === 0) break;
      }
      setStatusMsg(`Stage 1 complete: ${totalProcessed} candidates processed.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Stage 1 failed');
    } finally {
      ollamaRunningRef.current = false;
      setOllamaRunning(false);
      await refresh();
    }
  }

  async function handleRunSonnet() {
    if (sonnetRunningRef.current) {
      sonnetRunningRef.current = false;
      setStatusMsg('Stopping after current batch…');
      return;
    }
    const pending = (stats?.stage1_done ?? 0) - (stats?.stage2_done ?? 0);
    if (pending === 0) return;
    const ok = await confirm({
      title: `Adjudicate ${pending} candidate${pending === 1 ? '' : 's'} with Sonnet?`,
      message: `Claude Sonnet 4 issues a final verdict + alternative translations. ≈ $${(pending * 0.02).toFixed(2)}. Auto-loops in batches of 5. ~5-8s per candidate.`,
      confirmLabel: 'Run',
    });
    if (!ok) return;
    sonnetRunningRef.current = true;
    setSonnetRunning(true);
    setSonnetProgress({ processed: 0, adjudicated: 0, remaining: pending });
    setError('');
    setStatusMsg('');
    let totalProcessed = 0, totalAdjudicated = 0;
    let consecutiveFailures = 0;
    try {
      while (sonnetRunningRef.current) {
        let r;
        try {
          r = await runProperNounsSonnet({ limit: 3 });
          consecutiveFailures = 0;
        } catch (chunkErr) {
          consecutiveFailures++;
          const msg = chunkErr instanceof Error ? chunkErr.message : String(chunkErr);
          if (consecutiveFailures >= 3) throw chunkErr;
          const waitSec = 2 ** consecutiveFailures;
          setStatusMsg(`Network error (${consecutiveFailures}/3): ${msg.slice(0, 80)}. Retrying in ${waitSec}s…`);
          await new Promise((resolve) => setTimeout(resolve, waitSec * 1000));
          continue;
        }
        totalProcessed += r.processed;
        totalAdjudicated += r.adjudicated;
        setSonnetProgress({ processed: totalProcessed, adjudicated: totalAdjudicated, remaining: r.remaining });
        setStats(r.summary);
        if (r.remaining > 0 && r.processed > 0) {
          setStatusMsg(`Auto-continuing… ${totalAdjudicated} adjudicated, ${r.remaining} remaining`);
        }
        if (r.remaining === 0 || r.processed === 0) break;
      }
      setStatusMsg(`Stage 2 complete: ${totalAdjudicated} candidates adjudicated.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Stage 2 failed');
    } finally {
      sonnetRunningRef.current = false;
      setSonnetRunning(false);
      await refresh();
    }
  }

  async function handleApprove(c: ProperNounCandidate, translation: string) {
    const ok = await confirm({
      title: `Apply "${translation}" for ${c.chapter}:${c.verse}?`,
      message: `Updates ai_word_meanings.preferred_translation for word_pos ${c.word_pos}. The original is captured so revert is one click.`,
      confirmLabel: 'Apply',
    });
    if (!ok) return;
    setError('');
    try {
      await reviewProperNoun(c.id, { action: 'approved', translation });
      const r = await applyProperNoun(c.id);
      setStats(r.summary);
      setStatusMsg(`Applied for ${c.chapter}:${c.verse}.`);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Apply failed');
    }
  }

  async function handleReject(c: ProperNounCandidate) {
    const ok = await confirm({
      title: `Reject candidate at ${c.chapter}:${c.verse}?`,
      message: 'Marks this candidate as a real proper name (no revision needed). Can be undone by re-running Stage 2 with --refresh.',
      confirmLabel: 'Reject',
      tone: 'danger',
    });
    if (!ok) return;
    setError('');
    try {
      await reviewProperNoun(c.id, { action: 'rejected' });
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Reject failed');
    }
  }

  async function handleEdit(c: ProperNounCandidate) {
    const text = (editing[c.id] || '').trim();
    if (!text) {
      setError('Please type a translation before saving.');
      return;
    }
    const ok = await confirm({
      title: `Apply your edit "${text}"?`,
      message: `Updates ai_word_meanings.preferred_translation for ${c.chapter}:${c.verse}/p${c.word_pos}. Captures the prior value so revert is one click.`,
      confirmLabel: 'Apply',
    });
    if (!ok) return;
    setError('');
    try {
      await reviewProperNoun(c.id, { action: 'edited', translation: text });
      const r = await applyProperNoun(c.id);
      setStats(r.summary);
      setStatusMsg(`Applied edit for ${c.chapter}:${c.verse}.`);
      setEditing((s) => ({ ...s, [c.id]: '' }));
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Edit-apply failed');
    }
  }

  async function handleRevert(c: ProperNounCandidate) {
    const ok = await confirm({
      title: `Revert ${c.chapter}:${c.verse}?`,
      message: 'Restores the previous preferred_translation in ai_word_meanings. The candidate stays in the queue.',
      confirmLabel: 'Revert',
      tone: 'danger',
    });
    if (!ok) return;
    setError('');
    try {
      const r = await revertProperNoun(c.id);
      setStats(r.summary);
      setStatusMsg(`Reverted ${c.chapter}:${c.verse}.`);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Revert failed');
    }
  }

  // -------------------- Render --------------------

  const stage1Pending = (stats?.total ?? 0) - (stats?.stage1_done ?? 0);
  const stage2Pending = (stats?.stage1_done ?? 0) - (stats?.stage2_done ?? 0);

  return (
    <div>
      <div className="mb-4 flex items-baseline gap-3">
        <a href="/admin/revisions" className="text-xs text-stone-400 hover:text-stone-700">
          ← Revisions
        </a>
      </div>
      <h1 className="text-xl font-semibold text-stone-800 mb-2">Proper Nouns</h1>
      <p className="text-sm text-stone-500 mb-6 max-w-2xl">
        Identify and revise translations that treat descriptive Arabic phrases as
        proper names (e.g.{' '}
        <span className="font-mono text-amber-700">Abu Lahab</span> →
        &quot;father of [burning] flame&quot;). Two-stage LLM pipeline with
        operator review.
      </p>

      {/* Stats grid */}
      {stats && (
        <div className="mb-6 grid grid-cols-3 md:grid-cols-6 gap-2 max-w-4xl">
          <StatCard label="Total" value={stats.total} />
          <StatCard label="Stage 1 done" value={stats.stage1_done} />
          <StatCard label="Stage 2 done" value={stats.stage2_done} />
          <StatCard label="Literal" value={stats.literal} accent="amber" />
          <StatCard label="Approved" value={stats.approved} accent="emerald" />
          <StatCard label="Applied" value={stats.applied} accent="emerald" />
        </div>
      )}

      {/* Action buttons */}
      <div className="mb-6 flex flex-wrap items-center gap-2">
        <button
          onClick={handleDetect}
          disabled={detecting}
          className="text-xs px-4 py-2 rounded-md bg-stone-800 text-white hover:bg-stone-700 disabled:opacity-50 cursor-pointer"
        >
          {detecting ? 'Detecting…' : 'Detect candidates (Stage 0)'}
        </button>
        {(stats?.total ?? 0) > 0 && (
          <>
            <button
              onClick={() => handleClear(false)}
              disabled={clearing}
              className="text-xs px-3 py-2 rounded-md border border-stone-300 text-stone-600 hover:bg-stone-50 disabled:opacity-50 cursor-pointer"
              title="Wipes unreviewed candidates so Stage 0 can run from scratch with the latest heuristic"
            >
              {clearing ? 'Clearing…' : 'Clear unreviewed'}
            </button>
            <button
              onClick={() => handleClear(true)}
              disabled={clearing}
              className="text-xs px-3 py-2 rounded-md border border-red-300 text-red-700 hover:bg-red-50 disabled:opacity-50 cursor-pointer"
              title="Force-wipes EVERYTHING in the table including reviewed and applied rows. Applied ai_word_meanings revisions are not touched."
            >
              Force-clear all
            </button>
          </>
        )}
        <button
          onClick={handleRunOllama}
          disabled={!ollamaRunning && stage1Pending === 0}
          className={`text-xs px-4 py-2 rounded-md text-white disabled:opacity-50 cursor-pointer ${
            ollamaRunning ? 'bg-red-600 hover:bg-red-700' : 'bg-amber-600 hover:bg-amber-700'
          }`}
        >
          {ollamaRunning
            ? 'Stop'
            : stage1Pending === 0
              ? 'Stage 1 — all done'
              : `Run Ollama on ${stage1Pending} pending`}
        </button>
        <button
          onClick={handleRunSonnet}
          disabled={!sonnetRunning && stage2Pending === 0}
          className={`text-xs px-4 py-2 rounded-md text-white disabled:opacity-50 cursor-pointer ${
            sonnetRunning ? 'bg-red-600 hover:bg-red-700' : 'bg-amber-600 hover:bg-amber-700'
          }`}
        >
          {sonnetRunning
            ? 'Stop'
            : stage2Pending === 0
              ? 'Stage 2 — all done'
              : `Run Sonnet on ${stage2Pending} pending`}
        </button>
      </div>

      {/* Live progress */}
      {(ollamaProgress && ollamaRunning) && (
        <div className="mb-3 text-xs text-stone-600">
          Stage 1: {ollamaProgress.processed} processed, {ollamaProgress.remaining} remaining
        </div>
      )}
      {(sonnetProgress && sonnetRunning) && (
        <div className="mb-3 text-xs text-stone-600">
          Stage 2: {sonnetProgress.adjudicated}/{sonnetProgress.processed} adjudicated, {sonnetProgress.remaining} remaining
        </div>
      )}

      {/* Status / error */}
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

      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-center gap-2 text-xs">
        <FilterSelect label="Status" value={statusFilter} onChange={setStatusFilter} options={[
          { value: '', label: 'All' },
          { value: 'pending', label: 'Pending Stage 2' },
          { value: 'adjudicated', label: 'Adjudicated, awaiting review' },
          { value: 'approved', label: 'Approved (not applied)' },
          { value: 'rejected', label: 'Rejected' },
          { value: 'applied', label: 'Applied' },
        ]} />
        <FilterSelect label="Verdict" value={verdictFilter} onChange={setVerdictFilter} options={[
          { value: '', label: 'All' },
          { value: 'literal', label: 'Literal' },
          { value: 'name', label: 'Name' },
          { value: 'ambiguous', label: 'Ambiguous' },
        ]} />
        <FilterSelect label="Type" value={typeFilter} onChange={setTypeFilter} options={[
          { value: '', label: 'All' },
          { value: 'compound', label: 'Compound (Abu/Ibn/...)' },
          { value: 'single', label: 'Single' },
        ]} />
        <input
          type="text"
          placeholder="Filter by root (Buckwalter)…"
          value={rootFilter}
          onChange={(e) => setRootFilter(e.target.value)}
          className="px-2 py-1 rounded border border-stone-300 font-mono"
        />
        <FilterSelect label="Order" value={order} onChange={setOrder} options={[
          { value: 'rooted', label: 'By root + verse' },
          { value: 'recent', label: 'Most recent' },
          { value: 'random', label: 'Random' },
        ]} />
        <span className="text-stone-400">{totalMatched} match{totalMatched === 1 ? '' : 'es'}</span>
      </div>

      {/* Candidate table */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-stone-300 border-t-stone-600" />
        </div>
      ) : candidates.length === 0 ? (
        <div className="rounded-lg border border-stone-200 bg-stone-50 p-6 text-center text-sm text-stone-500">
          No candidates match the current filters. Try clicking <strong>Detect candidates (Stage 0)</strong> to seed the queue.
        </div>
      ) : (
        <div className="rounded-lg border border-stone-200 bg-white overflow-hidden">
          {candidates.map((c) => (
            <CandidateRow
              key={c.id}
              c={c}
              expanded={!!expanded[c.id]}
              onToggle={() => setExpanded((s) => ({ ...s, [c.id]: !s[c.id] }))}
              editText={editing[c.id] || ''}
              onEditChange={(v) => setEditing((s) => ({ ...s, [c.id]: v }))}
              onApprove={(t) => handleApprove(c, t)}
              onReject={() => handleReject(c)}
              onApplyEdit={() => handleEdit(c)}
              onRevert={() => handleRevert(c)}
            />
          ))}
        </div>
      )}

      {confirmDialog}
    </div>
  );
}

// ---------- subcomponents ----------

function StatCard({ label, value, accent = 'stone' }: {
  label: string;
  value: number;
  accent?: 'stone' | 'amber' | 'emerald';
}) {
  const colors = {
    stone: 'border-stone-200 bg-white text-stone-800',
    amber: 'border-amber-200 bg-amber-50 text-amber-800',
    emerald: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  };
  return (
    <div className={`rounded-lg border px-3 py-2 ${colors[accent]}`}>
      <div className="text-[10px] uppercase tracking-wide text-stone-500">{label}</div>
      <div className="text-lg font-semibold">{value.toLocaleString()}</div>
    </div>
  );
}

function FilterSelect({ label, value, onChange, options }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: Array<{ value: string; label: string }>;
}) {
  return (
    <label className="flex items-center gap-1.5 text-stone-600">
      <span className="text-stone-500">{label}:</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="px-2 py-1 rounded border border-stone-300 bg-white"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </label>
  );
}

function VerdictBadge({ verdict, confidence }: { verdict: string | null; confidence?: number | null }) {
  if (!verdict) return <span className="text-[10px] text-stone-400">—</span>;
  const colors: Record<string, string> = {
    literal: 'bg-amber-100 text-amber-800 border-amber-200',
    name: 'bg-stone-100 text-stone-700 border-stone-200',
    ambiguous: 'bg-violet-100 text-violet-800 border-violet-200',
  };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border ${colors[verdict] || colors.name}`}>
      {verdict}
      {typeof confidence === 'number' && (
        <span className="text-stone-500">{Math.round(confidence * 100)}%</span>
      )}
    </span>
  );
}

function CandidateRow({
  c, expanded, onToggle,
  editText, onEditChange,
  onApprove, onReject, onApplyEdit, onRevert,
}: {
  c: ProperNounCandidate;
  expanded: boolean;
  onToggle: () => void;
  editText: string;
  onEditChange: (v: string) => void;
  onApprove: (t: string) => void;
  onReject: () => void;
  onApplyEdit: () => void;
  onRevert: () => void;
}) {
  const ref = `${c.chapter}:${c.verse}`;
  const isApplied = !!c.applied_at;
  const isApproved = c.operator_action === 'approved' || c.operator_action === 'edited';
  const isRejected = c.operator_action === 'rejected';

  return (
    <div className="border-b border-stone-100 last:border-b-0">
      <div className="px-4 py-3 flex items-center gap-3 flex-wrap hover:bg-stone-50 cursor-pointer" onClick={onToggle}>
        <a
          href={`/verse/${ref}`}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="font-mono text-xs text-amber-700 hover:underline min-w-[4rem]"
        >
          {ref}
        </a>
        <span className="font-arabic text-base text-stone-800 min-w-[5rem]" lang="ar">
          {c.arabic_word}
        </span>
        <span className="font-mono text-[11px] text-stone-500 min-w-[3rem]">
          {c.root_buckwalter}
        </span>
        <span className="text-sm text-stone-700 min-w-[10rem]">
          &quot;{c.surface_translation}&quot;
        </span>
        <div className="flex items-center gap-1.5">
          <VerdictBadge verdict={c.qwen_verdict} confidence={c.qwen_confidence} />
          <VerdictBadge verdict={c.gptoss_verdict} confidence={c.gptoss_confidence} />
          <VerdictBadge verdict={c.sonnet_verdict} />
        </div>
        <div className="ml-auto flex items-center gap-2 text-[11px]">
          {isApplied && <span className="text-emerald-700 font-medium">applied</span>}
          {!isApplied && isApproved && <span className="text-emerald-700">approved</span>}
          {isRejected && <span className="text-stone-400">rejected</span>}
          {c.has_compound_marker && (
            <span className="text-stone-400 italic">{c.has_compound_marker}+</span>
          )}
          <span className="text-stone-300">{expanded ? '▼' : '▶'}</span>
        </div>
      </div>
      {expanded && (
        <div className="px-4 pb-4 bg-stone-50/50 border-t border-stone-100">
          {/* Stage 1 reasoning */}
          {(c.qwen_reasoning || c.gptoss_reasoning) && (
            <details className="mt-2 text-xs text-stone-600">
              <summary className="cursor-pointer text-stone-500 hover:text-stone-700">
                Stage 1 (Ollama) reasoning
              </summary>
              <div className="mt-1 pl-2 border-l-2 border-stone-200 space-y-1">
                {c.qwen_reasoning && (
                  <div>
                    <span className="font-mono text-[10px] text-stone-500">qwen 397B:</span>{' '}
                    <span>{c.qwen_reasoning}</span>
                  </div>
                )}
                {c.gptoss_reasoning && (
                  <div>
                    <span className="font-mono text-[10px] text-stone-500">gpt-oss:</span>{' '}
                    <span>{c.gptoss_reasoning}</span>
                  </div>
                )}
              </div>
            </details>
          )}

          {/* Stage 2 reasoning + alternatives */}
          {c.sonnet_reasoning && (
            <div className="mt-3">
              <div className="text-xs font-medium text-stone-700 mb-1">Sonnet reasoning</div>
              <p className="text-xs text-stone-600 leading-relaxed">{c.sonnet_reasoning}</p>
              {c.sonnet_supporting_refs && c.sonnet_supporting_refs.length > 0 && (
                <div className="mt-1 text-[11px] text-stone-500">
                  Supporting:{' '}
                  {c.sonnet_supporting_refs.map((r, i) => (
                    <span key={i}>
                      <a href={`/verse/${r}`} target="_blank" rel="noopener noreferrer" className="font-mono text-amber-700 hover:underline">
                        {r}
                      </a>
                      {i < c.sonnet_supporting_refs.length - 1 && ', '}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Alternatives */}
          {c.sonnet_alternatives && c.sonnet_alternatives.length > 0 && !isApplied && (
            <div className="mt-3">
              <div className="text-xs font-medium text-stone-700 mb-1.5">Suggested alternatives</div>
              <div className="space-y-1.5">
                {c.sonnet_alternatives.map((a, i) => (
                  <div key={i} className="flex items-start gap-2 rounded-md border border-stone-200 bg-white p-2">
                    <span className="text-[10px] font-mono text-stone-400 mt-0.5">#{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-stone-800">{a.translation}</div>
                      {a.rationale && <div className="mt-0.5 text-[11px] text-stone-500 leading-relaxed">{a.rationale}</div>}
                    </div>
                    <button
                      onClick={(e) => { e.stopPropagation(); onApprove(a.translation); }}
                      className="text-[11px] px-3 py-1 rounded bg-emerald-600 text-white hover:bg-emerald-700 cursor-pointer flex-shrink-0"
                    >
                      Apply
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Edit your own */}
          {!isApplied && (
            <div className="mt-3">
              <div className="text-xs font-medium text-stone-700 mb-1.5">Or write your own</div>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={editText}
                  onChange={(e) => onEditChange(e.target.value)}
                  placeholder='e.g. "father of flame"'
                  className="flex-1 px-2 py-1.5 rounded border border-stone-300 text-sm"
                  onClick={(e) => e.stopPropagation()}
                />
                <button
                  onClick={(e) => { e.stopPropagation(); onApplyEdit(); }}
                  disabled={!editText.trim()}
                  className="text-[11px] px-3 py-1.5 rounded bg-stone-800 text-white hover:bg-stone-700 disabled:opacity-50 cursor-pointer"
                >
                  Apply edit
                </button>
              </div>
            </div>
          )}

          {/* Action row */}
          <div className="mt-3 pt-3 border-t border-stone-100 flex items-center gap-2">
            {!isApplied && !isRejected && (
              <button
                onClick={(e) => { e.stopPropagation(); onReject(); }}
                className="text-[11px] px-3 py-1 rounded border border-stone-300 text-stone-600 hover:bg-stone-50 cursor-pointer"
              >
                Reject (it&apos;s a real name)
              </button>
            )}
            {isApplied && (
              <>
                <span className="text-[11px] text-emerald-700">
                  Applied {c.operator_translation && <>as &quot;{c.operator_translation}&quot;</>} on {c.applied_at?.slice(0, 10)}
                </span>
                <button
                  onClick={(e) => { e.stopPropagation(); onRevert(); }}
                  className="ml-auto text-[11px] px-3 py-1 rounded border border-stone-300 text-stone-600 hover:bg-red-50 hover:border-red-200 cursor-pointer"
                >
                  Revert
                </button>
              </>
            )}
            {c.candidate_type && (
              <span className="ml-auto text-[10px] text-stone-400 italic">
                type: {c.candidate_type}{c.is_indefinite ? ' · indefinite' : ''} · root used {c.root_quran_frequency ?? '?'}× in corpus
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
