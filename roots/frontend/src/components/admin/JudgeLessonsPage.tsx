import { useState, useEffect, useCallback } from 'react';
import { getToken } from '../../api/admin';
import { useConfirm } from './shared/useConfirm';

/**
 * /admin/judge-lessons
 *
 * Surface for the performance-driven judge-tuning loop.
 *
 *   - "Settings" card: toggle the auto-refresh cron, set the every-N
 *     -days interval, the minimum video age + view floor that gate
 *     which uploads feed the analyzer, and a "Refresh now" button.
 *
 *   - "Lessons" grid: one column per pipeline type (recitation, word
 *     origins, translation hides, grammar insights). Each lesson is
 *     editable inline; auto lessons can be promoted to manual so the
 *     next cron run won't retire them. Operator can add manual
 *     lessons directly.
 *
 * The lessons themselves get appended to the interestingness judge's
 * system prompt at candidate-evaluation time — so every change here
 * is a real lever on what shipping decisions the pipeline makes next.
 */

const PIPELINE_LABELS: Record<string, string> = {
  word_origins: 'Word Origins',
  translation_hides: 'Translation Hides',
  grammar_insights: 'Grammar Insights',
  recitation: 'Recitation (English / Arabic)',
  all: 'Applies to ALL pipelines',
};

interface Lesson {
  id: number;
  pipeline_type: string;
  lesson: string;
  evidence_video_ids: string[];
  generation_id: number | null;
  source: 'auto' | 'manual';
  active: boolean;
  operator_note: string | null;
  generated_at: string;
}

interface Settings {
  lessons_auto_refresh_enabled: string | null;
  lessons_refresh_interval_days: string | null;
  lessons_min_age_days: string | null;
  lessons_min_views: string | null;
  lessons_last_refresh_at: string | null;
}

interface ListResponse {
  lessons: Lesson[];
  settings: Settings;
  pipeline_types: string[];
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = init?.headers
    ? { ...(init.headers as Record<string, string>) }
    : {};
  headers['Authorization'] = `Bearer ${getToken()}`;
  if (init?.body && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }
  const resp = await fetch(path, { ...init, headers });
  const body = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error(body.error || `${resp.status}`);
  }
  return body as T;
}

export default function JudgeLessonsPage() {
  const [data, setData] = useState<ListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState<number | null>(null);
  const [editText, setEditText] = useState('');
  const [newType, setNewType] = useState<string>('translation_hides');
  const [newText, setNewText] = useState('');
  const { confirm, dialog: confirmDialog } = useConfirm();

  const load = useCallback(async () => {
    setError('');
    try {
      const r = await api<ListResponse>('/api/admin/judge-lessons');
      setData(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'load failed');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function updateSettings(patch: Partial<Record<string, unknown>>) {
    setError('');
    try {
      await api('/api/admin/judge-lessons/settings', {
        method: 'PUT',
        body: JSON.stringify(patch),
      });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'save failed');
    }
  }

  async function triggerRefresh(only_type?: string) {
    setRefreshing(true);
    setError('');
    try {
      await api('/api/admin/judge-lessons/refresh', {
        method: 'POST',
        body: JSON.stringify(only_type ? { pipeline_type: only_type } : {}),
      });
      // Poll until last_refresh_at advances. Cap at 4 min so we don't
      // spin forever if Ollama is wedged.
      const start = data?.settings?.lessons_last_refresh_at || '';
      for (let i = 0; i < 24; i++) {
        await new Promise((r) => setTimeout(r, 10_000));
        const r = await api<ListResponse>('/api/admin/judge-lessons');
        if ((r.settings.lessons_last_refresh_at || '') !== start) {
          setData(r);
          break;
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'refresh failed');
    } finally {
      setRefreshing(false);
    }
  }

  async function toggleActive(lesson: Lesson) {
    try {
      await api(`/api/admin/judge-lessons/${lesson.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ active: !lesson.active }),
      });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'toggle failed');
    }
  }

  async function promoteToManual(lesson: Lesson) {
    try {
      await api(`/api/admin/judge-lessons/${lesson.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ source: 'manual' }),
      });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'promote failed');
    }
  }

  async function deleteLesson(lesson: Lesson) {
    const ok = await confirm({
      title: 'Delete this lesson?',
      message: `Permanently remove "${lesson.lesson.slice(0, 80)}…" from the judge's rubric. This cannot be undone.`,
      confirmLabel: 'Delete',
      tone: 'danger',
    });
    if (!ok) return;
    try {
      await api(`/api/admin/judge-lessons/${lesson.id}`, { method: 'DELETE' });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'delete failed');
    }
  }

  async function saveEdit(id: number) {
    if (!editText.trim()) return;
    try {
      await api(`/api/admin/judge-lessons/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ lesson: editText.trim() }),
      });
      setEditing(null);
      setEditText('');
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'save failed');
    }
  }

  async function createManual() {
    if (!newText.trim()) return;
    try {
      await api('/api/admin/judge-lessons', {
        method: 'POST',
        body: JSON.stringify({
          pipeline_type: newType,
          lesson: newText.trim(),
        }),
      });
      setNewText('');
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'create failed');
    }
  }

  if (loading) {
    return <div className="text-stone-500">Loading…</div>;
  }
  if (!data) {
    return <div className="text-red-600">{error || 'No data'}</div>;
  }

  const grouped: Record<string, Lesson[]> = {};
  for (const t of data.pipeline_types) grouped[t] = [];
  grouped['all'] = [];
  for (const l of data.lessons) {
    (grouped[l.pipeline_type] = grouped[l.pipeline_type] || []).push(l);
  }

  const enabled =
    (data.settings.lessons_auto_refresh_enabled || '0').toLowerCase() === '1' ||
    data.settings.lessons_auto_refresh_enabled === 'true';
  const interval = data.settings.lessons_refresh_interval_days || '3';
  const minAge = data.settings.lessons_min_age_days || '7';
  const minViews = data.settings.lessons_min_views || '30';
  const last = data.settings.lessons_last_refresh_at;

  return (
    <div>
      <h1 className="text-xl font-semibold text-stone-800 mb-1">
        Judge Lessons
      </h1>
      <p className="text-sm text-stone-500 mb-6 max-w-3xl">
        Performance-driven refinements to the interestingness judge. Every few
        days, an Ollama-powered analyzer reads YouTube engagement on past
        uploads + the judge's own rejected candidates, then writes concrete
        lessons the judge applies to <em>future</em> candidates of the same
        pipeline. Hand-written rubric still wins on conflict — these only
        refine.
      </p>

      {error && (
        <div className="mb-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      {/* Settings card */}
      <div className="mb-8 rounded-lg border border-stone-200 bg-white p-5 max-w-3xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-stone-800">Auto-refresh cron</h2>
          <button
            onClick={() => triggerRefresh()}
            disabled={refreshing}
            className="px-3 py-1.5 text-sm rounded-md bg-stone-800 text-white hover:bg-stone-700 disabled:opacity-50"
          >
            {refreshing ? 'Refreshing…' : 'Refresh now'}
          </button>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => updateSettings({ enabled: e.target.checked })}
              className="rounded"
            />
            <span>Enabled (runs automatically every N days)</span>
          </label>
          <label className="flex items-center gap-2">
            <span className="text-stone-600 w-32">Interval (days):</span>
            <input
              type="number"
              min={1}
              max={60}
              defaultValue={interval}
              onBlur={(e) => {
                const n = parseInt(e.target.value, 10);
                if (Number.isFinite(n) && String(n) !== interval) {
                  updateSettings({ interval_days: n });
                }
              }}
              className="w-20 rounded border border-stone-300 px-2 py-1"
            />
          </label>
          <label className="flex items-center gap-2">
            <span className="text-stone-600 w-32">Min video age (days):</span>
            <input
              type="number"
              min={0}
              max={90}
              defaultValue={minAge}
              onBlur={(e) => {
                const n = parseInt(e.target.value, 10);
                if (Number.isFinite(n) && String(n) !== minAge) {
                  updateSettings({ min_age_days: n });
                }
              }}
              className="w-20 rounded border border-stone-300 px-2 py-1"
            />
            <span className="text-xs text-stone-400">
              Videos newer than this are ignored
            </span>
          </label>
          <label className="flex items-center gap-2">
            <span className="text-stone-600 w-32">Min views:</span>
            <input
              type="number"
              min={0}
              defaultValue={minViews}
              onBlur={(e) => {
                const n = parseInt(e.target.value, 10);
                if (Number.isFinite(n) && String(n) !== minViews) {
                  updateSettings({ min_views: n });
                }
              }}
              className="w-20 rounded border border-stone-300 px-2 py-1"
            />
            <span className="text-xs text-stone-400">
              Below this, like-rate is noise
            </span>
          </label>
        </div>
        <div className="mt-4 text-xs text-stone-500">
          Last refresh:{' '}
          <span className="font-mono">
            {last ? new Date(last).toLocaleString() : 'never'}
          </span>
        </div>
      </div>

      {/* Add manual lesson */}
      <div className="mb-8 rounded-lg border border-stone-200 bg-stone-50 p-5 max-w-3xl">
        <h2 className="text-base font-semibold text-stone-800 mb-3">
          Add a manual lesson
        </h2>
        <p className="text-xs text-stone-500 mb-3">
          Manual lessons sit alongside the auto-generated ones and survive cron
          retirements. Use these for editorial calls the analyzer can't see
          (e.g. "don't run videos near a Friday prayer time" — channel-level
          knowledge).
        </p>
        <div className="flex flex-col gap-2">
          <select
            value={newType}
            onChange={(e) => setNewType(e.target.value)}
            className="rounded border border-stone-300 px-2 py-1 text-sm w-fit"
          >
            {data.pipeline_types.map((t) => (
              <option key={t} value={t}>
                {PIPELINE_LABELS[t] || t}
              </option>
            ))}
            <option value="all">All pipelines</option>
          </select>
          <textarea
            value={newText}
            onChange={(e) => setNewText(e.target.value)}
            placeholder="Prefer X when Y. Skip Z when W. (One sentence, ≤30 words.)"
            rows={2}
            className="rounded border border-stone-300 px-2 py-1 text-sm"
          />
          <button
            onClick={createManual}
            disabled={!newText.trim()}
            className="self-start px-3 py-1.5 text-sm rounded-md bg-stone-800 text-white hover:bg-stone-700 disabled:opacity-50"
          >
            Add lesson
          </button>
        </div>
      </div>

      {/* Lessons per pipeline */}
      <div className="space-y-6">
        {[...data.pipeline_types, 'all'].map((ptype) => {
          const items = grouped[ptype] || [];
          return (
            <div key={ptype} className="rounded-lg border border-stone-200 bg-white">
              <div className="flex items-center justify-between px-5 py-3 border-b border-stone-200 bg-stone-50">
                <h3 className="font-semibold text-stone-800">
                  {PIPELINE_LABELS[ptype] || ptype}
                </h3>
                <div className="text-xs text-stone-500">
                  {items.length} {items.length === 1 ? 'lesson' : 'lessons'}
                  {ptype !== 'all' && (
                    <button
                      onClick={() => triggerRefresh(ptype)}
                      disabled={refreshing}
                      className="ml-3 text-stone-600 underline hover:text-stone-800 disabled:opacity-50"
                    >
                      Refresh just this
                    </button>
                  )}
                </div>
              </div>
              {items.length === 0 ? (
                <div className="px-5 py-6 text-sm text-stone-400 italic">
                  No lessons yet — run a refresh once you have more uploads
                  with engagement data.
                </div>
              ) : (
                <ul className="divide-y divide-stone-200">
                  {items.map((lsn) => (
                    <li key={lsn.id} className="px-5 py-3">
                      <div className="flex items-start gap-3">
                        <input
                          type="checkbox"
                          checked={lsn.active}
                          onChange={() => toggleActive(lsn)}
                          title={lsn.active ? 'Disable' : 'Enable'}
                          className="mt-1.5 rounded"
                        />
                        <div className="flex-1 min-w-0">
                          {editing === lsn.id ? (
                            <div className="flex flex-col gap-2">
                              <textarea
                                value={editText}
                                onChange={(e) => setEditText(e.target.value)}
                                rows={2}
                                className="rounded border border-stone-300 px-2 py-1 text-sm"
                                autoFocus
                              />
                              <div className="flex gap-2">
                                <button
                                  onClick={() => saveEdit(lsn.id)}
                                  className="px-3 py-1 text-xs rounded bg-stone-800 text-white"
                                >
                                  Save
                                </button>
                                <button
                                  onClick={() => {
                                    setEditing(null);
                                    setEditText('');
                                  }}
                                  className="px-3 py-1 text-xs rounded border border-stone-300"
                                >
                                  Cancel
                                </button>
                              </div>
                            </div>
                          ) : (
                            <>
                              <div
                                className={`text-sm ${
                                  lsn.active ? 'text-stone-800' : 'text-stone-400 line-through'
                                }`}
                              >
                                {lsn.lesson}
                              </div>
                              <div className="mt-1 text-xs text-stone-400 flex flex-wrap items-center gap-3">
                                <span
                                  className={`px-1.5 py-0.5 rounded text-[10px] uppercase tracking-wide ${
                                    lsn.source === 'manual'
                                      ? 'bg-amber-100 text-amber-700'
                                      : 'bg-stone-100 text-stone-600'
                                  }`}
                                >
                                  {lsn.source}
                                </span>
                                {lsn.evidence_video_ids.length > 0 && (
                                  <span>
                                    evidence:{' '}
                                    <span className="font-mono">
                                      {lsn.evidence_video_ids.join(', ')}
                                    </span>
                                  </span>
                                )}
                                <span>
                                  added {new Date(lsn.generated_at + 'Z').toLocaleDateString()}
                                </span>
                              </div>
                            </>
                          )}
                        </div>
                        {editing !== lsn.id && (
                          <div className="flex gap-2 text-xs">
                            <button
                              onClick={() => {
                                setEditing(lsn.id);
                                setEditText(lsn.lesson);
                              }}
                              className="text-stone-600 hover:text-stone-800"
                            >
                              edit
                            </button>
                            {lsn.source === 'auto' && (
                              <button
                                onClick={() => promoteToManual(lsn)}
                                className="text-amber-700 hover:text-amber-900"
                                title="Promote to manual so the next cron run won't retire it"
                              >
                                pin
                              </button>
                            )}
                            <button
                              onClick={() => deleteLesson(lsn)}
                              className="text-red-600 hover:text-red-800"
                            >
                              delete
                            </button>
                          </div>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          );
        })}
      </div>

      {confirmDialog}
    </div>
  );
}
