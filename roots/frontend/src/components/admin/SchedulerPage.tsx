import { useState, useEffect, useCallback } from 'react';
import {
  getPipelineSchedules, savePipelineSchedule, getPipelineScheduleRuns,
  getYoutubeUploadSchedule, saveYoutubeUploadSchedule, getYoutubeUploadRuns,
  getPreferences,
  getAllEducationalSchedules, getAllEducationalScheduleRuns,
  upsertEducationalSchedule,
} from '../../api/admin';
import type {
  PipelineSchedule, PipelineScheduleRun,
  YoutubeUploadSchedule, YoutubeUploadRun,
  EducationalScheduleListItem, EducationalScheduleRunGlobal,
} from '../../api/admin';
import { useConfirm } from './shared/useConfirm';

/**
 * Scheduler page — manages automated pipeline runs.
 *
 * Each pipeline gets one schedule row with:
 *   - times: a list of HH:MM strings (server local time)
 *   - max_runs_per_day: safety cap (only scheduler-triggered runs count)
 *   - enabled: master toggle
 *   - grace_minutes: how late after a scheduled time we're still allowed
 *     to fire (protects against stale fires after long downtime)
 *
 * Audit log at the bottom shows what fired (or why it was skipped).
 */
export default function SchedulerPage() {
  const [schedules, setSchedules] = useState<PipelineSchedule[]>([]);
  const [runs, setRuns] = useState<PipelineScheduleRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  // Bumped by every save anywhere on the page so the
  // AutoPublishStatusPanel re-fetches its health summary. Without
  // this the panel shows stale data after the user edits the
  // upload schedule or one of the pipeline schedules.
  const [refreshKey, setRefreshKey] = useState(0);

  const load = useCallback(async () => {
    setErr('');
    try {
      const [s, r] = await Promise.all([
        getPipelineSchedules(),
        getPipelineScheduleRuns({ limit: 50 }),
      ]);
      setSchedules(s);
      setRuns(r);
      setRefreshKey((k) => k + 1);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load schedules');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    // Refresh audit log every 60s so new fires appear without reload
    const t = setInterval(load, 60_000);
    return () => clearInterval(t);
  }, [load]);

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-stone-300 border-t-stone-600" />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-stone-800 mb-1">Scheduler</h1>
        <p className="text-sm text-stone-500">
          Automate pipeline video generation and YouTube upload on daily
          schedules. All times are in server local time.
        </p>
      </div>

      {err && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {err}
        </div>
      )}

      {/* Health check at the top — answers "is auto-publishing working?"
          across the three pieces (credentials, generation schedules,
          upload schedule) so an operator doesn't have to scroll
          through three sections to figure out why nothing's flowing.
          The refreshKey is bumped by the parent's load() so the panel
          re-fetches whenever any child card saves. */}
      <section id="status">
        <AutoPublishStatusPanel refreshKey={refreshKey} />
      </section>

      {/* Quick-nav. The page has four logical sections; without this
          row a user landing here from /admin/pipelines/educational
          has no signal that the YouTube upload card or the
          educational schedules even exist below the fold. */}
      <nav className="mt-4 mb-8 flex flex-wrap gap-2 text-xs">
        <span className="text-stone-400">Jump to:</span>
        <a href="#youtube-upload" className="text-stone-600 hover:text-stone-900 underline decoration-dotted underline-offset-2">YouTube upload</a>
        <span className="text-stone-300">·</span>
        <a href="#recitation" className="text-stone-600 hover:text-stone-900 underline decoration-dotted underline-offset-2">Recitation generation</a>
        <span className="text-stone-300">·</span>
        <a href="#educational" className="text-stone-600 hover:text-stone-900 underline decoration-dotted underline-offset-2">Educational generation</a>
      </nav>

      {/* ==================== YouTube upload schedule ====================
          Promoted to right-under-status because it's THE thing
          operators come here to manage. The status panel above
          tells you whether it's running; the card below lets you
          fix it. Used to be buried at the bottom of the page below
          two unrelated sections. */}
      <section id="youtube-upload" className="scroll-mt-4">
        <YoutubeUploadSection refreshTrigger={refreshKey} onSaved={load} />
      </section>

      <div className="my-10 border-t border-stone-200" />

      {/* ==================== Recitation pipelines (English/Arabic) ==================== */}
      <section id="recitation" className="scroll-mt-4">
        <div className="flex items-baseline justify-between mb-3">
          <h2 className="text-base font-semibold text-stone-800">Recitation pipelines (English / Arabic)</h2>
          <span className="text-xs text-stone-400">
            Only scheduler-triggered runs count against the daily cap — manual runs don't consume budget.
          </span>
        </div>
        <div className="space-y-4">
          {schedules.length === 0 && (
            <p className="text-sm text-stone-400 italic">
              No recitation pipelines configured.{' '}
              <a href="/admin/pipelines/recitation" className="underline hover:text-stone-600">
                Create one →
              </a>
            </p>
          )}
          {schedules.map((s) => (
            <ScheduleCard key={s.pipeline_id} schedule={s} onSaved={load} />
          ))}
        </div>

        <div className="mt-6">
          <h3 className="text-sm font-semibold text-stone-600 mb-3">
            Recent scheduler activity
          </h3>
          {runs.length === 0 ? (
            <p className="text-sm text-stone-400">No scheduler activity yet.</p>
          ) : (
            <div className="rounded-xl border border-stone-200 bg-white overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-stone-50 text-xs text-stone-500">
                  <tr>
                    <th className="text-left px-3 py-2 font-medium">Pipeline</th>
                    <th className="text-left px-3 py-2 font-medium">Scheduled</th>
                    <th className="text-left px-3 py-2 font-medium">Fired</th>
                    <th className="text-left px-3 py-2 font-medium">Status</th>
                    <th className="text-left px-3 py-2 font-medium">Note</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map((r) => (
                    <tr key={r.id} className="border-t border-stone-100">
                      <td className="px-3 py-2 text-stone-700">
                        <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                          r.pipeline_language === 'arabic'
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-emerald-100 text-emerald-700'
                        }`}>
                          #{r.pipeline_id}
                        </span>
                        <span className="ml-2">{r.pipeline_name}</span>
                      </td>
                      <td className="px-3 py-2 text-stone-600 font-mono text-xs">
                        {r.scheduled_time}
                      </td>
                      <td className="px-3 py-2 text-stone-500 text-xs">
                        {new Date(r.fired_at).toLocaleString()}
                      </td>
                      <td className="px-3 py-2">
                        <StatusBadge status={r.status} />
                        {r.video_id && (
                          <span className="ml-2 text-xs text-stone-400">→ video #{r.video_id}</span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-xs text-stone-500">
                        {r.note || ''}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>

      {/* ==================== Educational pipelines (word origins / etc.) ==================== */}
      <div className="my-10 border-t border-stone-200" />
      <section id="educational" className="scroll-mt-4">
        <EducationalScheduleSection />
      </section>
    </div>
  );
}

/* ------------------------------------------------------------ */

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    fired:            { label: 'Fired',              cls: 'bg-emerald-50 text-emerald-700 border-emerald-100' },
    uploaded:         { label: 'Uploaded',           cls: 'bg-emerald-50 text-emerald-700 border-emerald-100' },
    running:          { label: 'Running',            cls: 'bg-blue-50 text-blue-700 border-blue-100' },
    skipped_cap:      { label: 'Skipped (cap)',      cls: 'bg-stone-50  text-stone-600   border-stone-200' },
    skipped_active:   { label: 'Skipped (active)',   cls: 'bg-stone-50 text-stone-600 border-stone-200' },
    skipped_grace:    { label: 'Skipped (grace)',    cls: 'bg-stone-50 text-stone-600 border-stone-200' },
    skipped_no_videos:{ label: 'Skipped (no videos)',cls: 'bg-stone-50 text-stone-600 border-stone-200' },
    skipped_sanity:   { label: 'Skipped (sanity)',   cls: 'bg-amber-50 text-amber-700 border-amber-100' },
    error:            { label: 'Error',              cls: 'bg-red-50 text-red-700 border-red-100' },
  };
  const m = map[status] || { label: status, cls: 'bg-stone-50 text-stone-600 border-stone-200' };
  return (
    <span className={`inline-block rounded border px-1.5 py-0.5 text-[10px] font-medium ${m.cls}`}>
      {m.label}
    </span>
  );
}

/* ------------------------------------------------------------ */

function ScheduleCard({
  schedule,
  onSaved,
}: {
  schedule: PipelineSchedule;
  onSaved: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [times, setTimes] = useState<string[]>(schedule.times);
  const [newTime, setNewTime] = useState('');
  const [cap, setCap] = useState(schedule.max_runs_per_day);
  const [enabled, setEnabled] = useState(schedule.enabled);
  const [grace, setGrace] = useState(schedule.grace_minutes);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState('');
  const { confirm, dialog } = useConfirm();

  // Re-sync when parent refreshes (e.g. after save)
  useEffect(() => {
    setTimes(schedule.times);
    setCap(schedule.max_runs_per_day);
    setEnabled(schedule.enabled);
    setGrace(schedule.grace_minutes);
  }, [schedule]);

  function addTime() {
    const m = newTime.trim().match(/^(\d{1,2}):(\d{2})$/);
    if (!m) {
      setErr('Use HH:MM, e.g. 02:00');
      return;
    }
    const h = parseInt(m[1]); const mn = parseInt(m[2]);
    if (h < 0 || h > 23 || mn < 0 || mn > 59) {
      setErr('Invalid time');
      return;
    }
    const padded = `${String(h).padStart(2,'0')}:${String(mn).padStart(2,'0')}`;
    if (times.includes(padded)) {
      setErr(`${padded} is already in the list`);
      return;
    }
    setTimes([...times, padded].sort());
    setNewTime('');
    setErr('');
  }

  function removeTime(t: string) {
    setTimes(times.filter((x) => x !== t));
  }

  async function handleSave() {
    if (enabled && times.length === 0) {
      const ok = await confirm({
        title: 'Enable with no scheduled times?',
        message: 'This schedule is enabled but has no times. Nothing will fire. Save anyway?',
        confirmLabel: 'Save',
      });
      if (!ok) return;
    }
    setSaving(true);
    setErr('');
    try {
      await savePipelineSchedule(schedule.pipeline_id, {
        times,
        max_runs_per_day: cap,
        enabled,
        grace_minutes: grace,
      });
      setEditing(false);
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  }

  function handleCancel() {
    setTimes(schedule.times);
    setCap(schedule.max_runs_per_day);
    setEnabled(schedule.enabled);
    setGrace(schedule.grace_minutes);
    setNewTime('');
    setErr('');
    setEditing(false);
  }

  return (
    <div className="rounded-xl border border-stone-200 bg-white p-5">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-mono text-stone-400 bg-stone-100 px-2 py-0.5 rounded">
            #{schedule.pipeline_id}
          </span>
          <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
            schedule.pipeline_language === 'arabic'
              ? 'bg-amber-100 text-amber-700'
              : 'bg-emerald-100 text-emerald-700'
          }`}>
            {schedule.pipeline_language === 'arabic' ? 'Arabic' : 'English'}
          </span>
          <h3 className="font-semibold text-stone-800">{schedule.pipeline_name}</h3>
          <span className={`ml-2 text-[10px] font-semibold px-2 py-0.5 rounded ${
            enabled
              ? 'bg-green-100 text-green-700'
              : 'bg-stone-200 text-stone-500'
          }`}>
            {enabled ? 'Enabled' : 'Disabled'}
          </span>
        </div>
        {!editing && (
          <div className="flex items-center gap-3">
            <a
              href={`/admin/pipelines/recitation?lang=${schedule.pipeline_language}`}
              className="text-xs text-stone-400 hover:text-stone-700"
              title="Open this pipeline's editor"
            >
              Open pipeline →
            </a>
            <button
              onClick={() => setEditing(true)}
              className="text-xs text-stone-500 hover:text-stone-700 cursor-pointer"
            >
              Edit schedule
            </button>
          </div>
        )}
      </div>

      {!editing ? (
        <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-xs text-stone-500">
          <span>
            Times:{' '}
            {times.length === 0 ? (
              <span className="text-stone-400 italic">none set</span>
            ) : (
              <span className="font-mono text-stone-700">{times.join(', ')}</span>
            )}
          </span>
          <span>Cap: {cap}/day</span>
          <span>Grace: {grace} min</span>
        </div>
      ) : (
        <div className="mt-4 space-y-4 max-w-lg">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              className="rounded border-stone-300"
            />
            <span className="text-sm text-stone-700">Enable this schedule</span>
          </label>

          <div>
            <label className="block text-xs font-medium text-stone-600 mb-1">
              Daily times (server local)
            </label>
            <div className="flex flex-wrap gap-2 mb-2">
              {times.length === 0 && (
                <span className="text-xs text-stone-400 italic">no times yet</span>
              )}
              {times.map((t) => (
                <span
                  key={t}
                  className="inline-flex items-center gap-1 rounded-full bg-stone-100 px-2.5 py-1 text-xs font-mono text-stone-700"
                >
                  {t}
                  <button
                    onClick={() => removeTime(t)}
                    className="text-stone-400 hover:text-red-500 cursor-pointer text-sm leading-none"
                    title="Remove"
                    type="button"
                  >×</button>
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={newTime}
                onChange={(e) => setNewTime(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addTime(); } }}
                placeholder="HH:MM"
                className="w-28 px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
              />
              <button
                onClick={addTime}
                type="button"
                className="px-3 py-2 rounded-lg border border-stone-300 bg-white text-stone-700 text-xs font-medium hover:bg-stone-50 cursor-pointer"
              >
                Add time
              </button>
            </div>
          </div>

          <div className="flex gap-4">
            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">
                Max runs / day
              </label>
              <input
                type="number"
                min={1}
                max={20}
                value={cap}
                onChange={(e) => setCap(parseInt(e.target.value) || 1)}
                className="w-24 px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">
                Grace (min)
              </label>
              <input
                type="number"
                min={1}
                max={240}
                value={grace}
                onChange={(e) => setGrace(parseInt(e.target.value) || 1)}
                className="w-24 px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400"
              />
            </div>
          </div>

          {err && <p className="text-xs text-red-600">{err}</p>}

          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 rounded-lg bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 disabled:opacity-50 cursor-pointer"
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
            <button
              onClick={handleCancel}
              className="px-4 py-2 rounded-lg text-sm text-stone-500 hover:text-stone-700 cursor-pointer"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
      {dialog}
    </div>
  );
}

/* ============================================================ */
/*  Educational pipelines section                                */
/* ============================================================ */
/* Mirrors the recitation pipeline section above so operators have
 * one place to see + edit every pipeline schedule, regardless of
 * family. Uses the same StatusBadge + edit-mode pattern. The audit
 * log is a global view (not per-pipeline) so a glance shows what
 * the scheduler has been doing across all educational series.
 */

function EducationalScheduleSection() {
  const [schedules, setSchedules] = useState<EducationalScheduleListItem[]>([]);
  const [runs, setRuns] = useState<EducationalScheduleRunGlobal[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');

  const load = useCallback(async () => {
    setErr('');
    try {
      const [s, r] = await Promise.all([
        getAllEducationalSchedules(),
        getAllEducationalScheduleRuns(50),
      ]);
      setSchedules(s);
      setRuns(r);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load educational schedules');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 60_000);
    return () => clearInterval(t);
  }, [load]);

  return (
    <section>
      <div className="flex items-baseline justify-between mb-3">
        <h2 className="text-base font-semibold text-stone-800">
          Educational pipelines (word origins / translation hides / grammar insights)
        </h2>
        <span className="text-xs text-stone-400">
          Same cap + grace semantics as recitation pipelines.
        </span>
      </div>

      {err && (
        <div className="mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {err}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-stone-400">Loading…</p>
      ) : schedules.length === 0 ? (
        <p className="text-sm text-stone-400 italic">
          No educational pipelines configured.{' '}
          <a href="/admin/pipelines/educational" className="underline hover:text-stone-600">
            Create one →
          </a>
        </p>
      ) : (
        <div className="space-y-4">
          {schedules.map((s) => (
            <EducationalScheduleCard key={s.pipeline_id} schedule={s} onSaved={load} />
          ))}
        </div>
      )}

      <div className="mt-6">
        <h3 className="text-sm font-semibold text-stone-600 mb-3">
          Recent educational scheduler activity
        </h3>
        {runs.length === 0 ? (
          <p className="text-sm text-stone-400">No educational scheduler activity yet.</p>
        ) : (
          <div className="rounded-xl border border-stone-200 bg-white overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-stone-50 text-xs text-stone-500">
                <tr>
                  <th className="text-left px-3 py-2 font-medium">Pipeline</th>
                  <th className="text-left px-3 py-2 font-medium">Scheduled</th>
                  <th className="text-left px-3 py-2 font-medium">Fired</th>
                  <th className="text-left px-3 py-2 font-medium">Status</th>
                  <th className="text-left px-3 py-2 font-medium">Note</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.id} className="border-t border-stone-100">
                    <td className="px-3 py-2 text-stone-700">
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-violet-100 text-violet-700">
                        #{r.pipeline_id}
                      </span>
                      <span className="ml-2">{r.pipeline_name || '—'}</span>
                      {r.pipeline_type && (
                        <span className="ml-2 text-[10px] text-stone-400 font-mono">
                          {r.pipeline_type}
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-stone-600 font-mono text-xs">
                      {r.scheduled_time}
                    </td>
                    <td className="px-3 py-2 text-stone-500 text-xs">
                      {new Date(r.fired_at).toLocaleString()}
                    </td>
                    <td className="px-3 py-2">
                      <StatusBadge status={r.status} />
                      {r.video_id && (
                        <span className="ml-2 text-xs text-stone-400">→ video #{r.video_id}</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-xs text-stone-500">{r.note || ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

function EducationalScheduleCard({
  schedule,
  onSaved,
}: {
  schedule: EducationalScheduleListItem;
  onSaved: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [times, setTimes] = useState<string[]>(schedule.times);
  const [newTime, setNewTime] = useState('');
  const [cap, setCap] = useState(schedule.max_runs_per_day);
  const [enabled, setEnabled] = useState(schedule.enabled);
  const [grace, setGrace] = useState(schedule.grace_minutes);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState('');
  const { confirm, dialog } = useConfirm();

  useEffect(() => {
    setTimes(schedule.times);
    setCap(schedule.max_runs_per_day);
    setEnabled(schedule.enabled);
    setGrace(schedule.grace_minutes);
  }, [schedule]);

  function addTime() {
    const m = newTime.trim().match(/^(\d{1,2}):(\d{2})$/);
    if (!m) { setErr('Use HH:MM, e.g. 02:00'); return; }
    const h = parseInt(m[1]); const mn = parseInt(m[2]);
    if (h < 0 || h > 23 || mn < 0 || mn > 59) { setErr('Invalid time'); return; }
    const padded = `${String(h).padStart(2, '0')}:${String(mn).padStart(2, '0')}`;
    if (times.includes(padded)) { setErr(`${padded} is already in the list`); return; }
    setTimes([...times, padded].sort());
    setNewTime('');
    setErr('');
  }

  function removeTime(t: string) {
    setTimes(times.filter((x) => x !== t));
  }

  async function handleSave() {
    if (enabled && times.length === 0) {
      const ok = await confirm({
        title: 'Enable with no scheduled times?',
        message: 'This schedule is enabled but has no times. Nothing will fire. Save anyway?',
        confirmLabel: 'Save',
      });
      if (!ok) return;
    }
    setSaving(true);
    setErr('');
    try {
      await upsertEducationalSchedule(schedule.pipeline_id, {
        times,
        max_runs_per_day: cap,
        enabled,
        grace_minutes: grace,
      });
      setEditing(false);
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  }

  function handleCancel() {
    setTimes(schedule.times);
    setCap(schedule.max_runs_per_day);
    setEnabled(schedule.enabled);
    setGrace(schedule.grace_minutes);
    setNewTime('');
    setErr('');
    setEditing(false);
  }

  return (
    <div className="rounded-xl border border-stone-200 bg-white p-5">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-mono text-stone-400 bg-stone-100 px-2 py-0.5 rounded">
            #{schedule.pipeline_id}
          </span>
          <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-violet-100 text-violet-700">
            {schedule.pipeline_type}
          </span>
          <h3 className="font-semibold text-stone-800">{schedule.pipeline_name}</h3>
          {!schedule.pipeline_enabled && (
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-stone-200 text-stone-500">
              Pipeline disabled
            </span>
          )}
          <span className={`ml-2 text-[10px] font-semibold px-2 py-0.5 rounded ${
            enabled ? 'bg-green-100 text-green-700' : 'bg-stone-200 text-stone-500'
          }`}>
            {enabled ? 'Schedule enabled' : 'Schedule disabled'}
          </span>
        </div>
        {!editing && (
          <div className="flex items-center gap-3">
            <a
              href="/admin/pipelines/educational"
              className="text-xs text-stone-400 hover:text-stone-700"
              title="Open this pipeline's editor"
            >
              Open pipeline →
            </a>
            <button
              onClick={() => setEditing(true)}
              className="text-xs text-stone-500 hover:text-stone-700 cursor-pointer"
            >
              Edit schedule
            </button>
          </div>
        )}
      </div>

      {!editing ? (
        <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-xs text-stone-500">
          <span>
            Times:{' '}
            {times.length === 0 ? (
              <span className="text-stone-400 italic">none set</span>
            ) : (
              <span className="font-mono text-stone-700">{times.join(', ')}</span>
            )}
          </span>
          <span>Cap: {cap}/day</span>
          <span>Grace: {grace} min</span>
        </div>
      ) : (
        <div className="mt-4 space-y-4 max-w-lg">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              className="rounded border-stone-300"
            />
            <span className="text-sm text-stone-700">Enable this schedule</span>
          </label>

          <div>
            <label className="block text-xs font-medium text-stone-600 mb-1">
              Daily times (server local)
            </label>
            <div className="flex flex-wrap gap-2 mb-2">
              {times.length === 0 && (
                <span className="text-xs text-stone-400 italic">no times yet</span>
              )}
              {times.map((t) => (
                <span
                  key={t}
                  className="inline-flex items-center gap-1 rounded-full bg-stone-100 px-2.5 py-1 text-xs font-mono text-stone-700"
                >
                  {t}
                  <button
                    onClick={() => removeTime(t)}
                    className="text-stone-400 hover:text-red-500 cursor-pointer text-sm leading-none"
                    title="Remove"
                    type="button"
                  >×</button>
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={newTime}
                onChange={(e) => setNewTime(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addTime(); } }}
                placeholder="HH:MM"
                className="w-28 px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
              />
              <button
                onClick={addTime}
                type="button"
                className="px-3 py-2 rounded-lg border border-stone-300 bg-white text-stone-700 text-xs font-medium hover:bg-stone-50 cursor-pointer"
              >
                Add time
              </button>
            </div>
          </div>

          <div className="flex gap-4">
            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">
                Max runs / day
              </label>
              <input
                type="number"
                min={1}
                max={20}
                value={cap}
                onChange={(e) => setCap(parseInt(e.target.value) || 1)}
                className="w-24 px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">
                Grace (min)
              </label>
              <input
                type="number"
                min={1}
                max={240}
                value={grace}
                onChange={(e) => setGrace(parseInt(e.target.value) || 1)}
                className="w-24 px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400"
              />
            </div>
          </div>

          {err && <p className="text-xs text-red-600">{err}</p>}

          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 rounded-lg bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 disabled:opacity-50 cursor-pointer"
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
            <button
              onClick={handleCancel}
              className="px-4 py-2 rounded-lg text-sm text-stone-500 hover:text-stone-700 cursor-pointer"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
      {dialog}
    </div>
  );
}

/* ============================================================ */
/*  YouTube Upload Section                                       */
/* ============================================================ */

function YoutubeUploadSection({
  refreshTrigger = 0,
  onSaved,
}: {
  refreshTrigger?: number;
  onSaved?: () => void;
} = {}) {
  const [schedule, setSchedule] = useState<YoutubeUploadSchedule | null>(null);
  const [runs, setRuns] = useState<YoutubeUploadRun[]>([]);
  const [ytConfigured, setYtConfigured] = useState<boolean | null>(null);
  const [err, setErr] = useState('');

  const load = useCallback(async () => {
    setErr('');
    try {
      const [s, r, prefs] = await Promise.all([
        getYoutubeUploadSchedule(),
        getYoutubeUploadRuns(50),
        getPreferences().catch(() => ({} as Record<string, string>)),
      ]);
      setSchedule(s);
      setRuns(r);
      setYtConfigured(
        !!(prefs.youtube_client_id && prefs.youtube_client_secret && prefs.youtube_refresh_token),
      );
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load YouTube schedule');
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 60_000);
    return () => clearInterval(t);
  }, [load, refreshTrigger]);

  // When the upload card saves, the parent's load() (passed in as
  // onSaved) bumps refreshKey which propagates to the status panel.
  // We also re-fetch our own data so the audit log + schedule view
  // update immediately.
  const handleCardSaved = useCallback(() => {
    load();
    if (onSaved) onSaved();
  }, [load, onSaved]);

  if (!schedule) {
    return (
      <section>
        <h2 className="text-base font-semibold text-stone-800 mb-3">YouTube upload</h2>
        <p className="text-sm text-stone-400">Loading...</p>
      </section>
    );
  }

  return (
    <section>
      <div className="flex items-baseline justify-between mb-3">
        <h2 className="text-base font-semibold text-stone-800">YouTube upload</h2>
        <span className="text-xs text-stone-400">
          One slot drains one video, oldest-first.
        </span>
      </div>

      <p className="text-xs text-stone-500 mb-3 max-w-3xl">
        This is the <strong>single global YouTube upload schedule</strong>. Each
        configured time picks the oldest scheduler-generated video from{' '}
        <em>any</em> pipeline (recitation or educational) and uploads it. If
        you've enabled an educational pipeline schedule above but
        videos aren't reaching YouTube, check that this section is{' '}
        <strong>enabled</strong> with at least one daily time — the
        pipeline schedule above only generates the video; this schedule
        is what uploads it.
      </p>

      {ytConfigured === false && (
        <div className="mb-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
          YouTube credentials aren't configured — uploads will fail until you set them up in{' '}
          <a href="/admin/settings" className="underline font-medium">Admin Settings → YouTube</a>.
        </div>
      )}

      {err && (
        <div className="mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {err}
        </div>
      )}

      <YoutubeUploadCard schedule={schedule} onSaved={handleCardSaved} />

      <div className="mt-6">
        <h3 className="text-sm font-semibold text-stone-600 mb-3">
          Recent upload activity
        </h3>
        {runs.length === 0 ? (
          <p className="text-sm text-stone-400">No uploads yet.</p>
        ) : (
          <div className="rounded-xl border border-stone-200 bg-white overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-stone-50 text-xs text-stone-500">
                <tr>
                  <th className="text-left px-3 py-2 font-medium">Scheduled</th>
                  <th className="text-left px-3 py-2 font-medium">Fired</th>
                  <th className="text-left px-3 py-2 font-medium">Status</th>
                  <th className="text-left px-3 py-2 font-medium">Video</th>
                  <th className="text-left px-3 py-2 font-medium">Note</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.id} className="border-t border-stone-100">
                    <td className="px-3 py-2 text-stone-600 font-mono text-xs">
                      {r.scheduled_time}
                    </td>
                    <td className="px-3 py-2 text-stone-500 text-xs">
                      {new Date(r.fired_at).toLocaleString()}
                    </td>
                    <td className="px-3 py-2">
                      <StatusBadge status={r.status} />
                    </td>
                    <td className="px-3 py-2 text-xs">
                      {r.video_id && (
                        <span className="text-stone-400">video #{r.video_id}</span>
                      )}
                      {r.youtube_video_id && (
                        <a
                          href={`https://youtube.com/watch?v=${r.youtube_video_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="ml-2 text-red-600 hover:text-red-700 font-medium"
                        >
                          ▶ YT
                        </a>
                      )}
                    </td>
                    <td className="px-3 py-2 text-xs text-stone-500">
                      {r.note || ''}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

// Predefined upload-time presets. Operators almost always want one of
// these — defining a custom schedule is rare. Presets nuke the
// type-HH:MM-and-pray flow that was the biggest friction point in the
// old card. "Custom" doesn't replace times; it just keeps whatever
// you've already got and lets you edit individual times.
const PRESETS: { id: string; label: string; help: string; times: string[] }[] = [
  { id: 'once', label: '1×/day',  help: '9 AM',                   times: ['09:00'] },
  { id: 'three', label: '3×/day', help: '9 AM, 1 PM, 8 PM',       times: ['09:00', '13:00', '20:00'] },
  { id: 'five',  label: '5×/day', help: '9 AM – 9 PM, every 3h',  times: ['09:00', '12:00', '15:00', '18:00', '21:00'] },
];

function YoutubeUploadCard({
  schedule,
  onSaved,
}: {
  schedule: YoutubeUploadSchedule;
  onSaved: () => void;
}) {
  // Form state — always editable. We track unsaved changes so the
  // Save button only shows when there's something to save, and
  // Cancel reverts to the last-saved state.
  const [enabled, setEnabled] = useState(schedule.enabled);
  const [times, setTimes] = useState<string[]>(schedule.times);
  const [newTime, setNewTime] = useState('09:00');
  const [grace, setGrace] = useState(schedule.grace_minutes);
  const [sanity, setSanity] = useState(schedule.sanity_check_enabled);
  const [privacy, setPrivacy] = useState<'public' | 'unlisted' | 'private'>(schedule.privacy);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState('');
  const { confirm, dialog } = useConfirm();

  // Re-sync when the parent re-fetches.
  useEffect(() => {
    setEnabled(schedule.enabled);
    setTimes(schedule.times);
    setGrace(schedule.grace_minutes);
    setSanity(schedule.sanity_check_enabled);
    setPrivacy(schedule.privacy);
  }, [schedule]);

  // Did the form change since last save? Sort both sides before
  // comparing — the backend doesn't promise sorted times, and our
  // form state is always sorted post-add. Without this sort, a load
  // of unsorted data flags the form dirty before any user input.
  const dirty =
    enabled !== schedule.enabled ||
    JSON.stringify([...times].sort()) !== JSON.stringify([...schedule.times].sort()) ||
    grace !== schedule.grace_minutes ||
    sanity !== schedule.sanity_check_enabled ||
    privacy !== schedule.privacy;

  // Identify which preset (if any) matches the current times list.
  // Used to highlight the active preset button.
  const activePresetId = PRESETS.find(
    (p) => JSON.stringify([...p.times].sort()) === JSON.stringify([...times].sort()),
  )?.id ?? 'custom';

  // Next-fire preview — only meaningful when enabled + times exist.
  const next = enabled ? nextFireFromTimes(times) : null;

  function applyPreset(p: typeof PRESETS[number]) {
    setTimes(p.times);
    setErr('');
  }

  function addTime() {
    if (!/^\d{1,2}:\d{2}$/.test(newTime)) { setErr('Pick a time'); return; }
    const [h, m] = newTime.split(':').map((x) => parseInt(x));
    if (h < 0 || h > 23 || m < 0 || m > 59) { setErr('Invalid time'); return; }
    const padded = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
    if (times.includes(padded)) { setErr(`${padded} is already in the list`); return; }
    setTimes([...times, padded].sort());
    setErr('');
  }

  function removeTime(t: string) {
    setTimes(times.filter((x) => x !== t));
  }

  async function handleSave() {
    setErr('');
    // Guardrail: enabled + no times = silently broken. Confirm before
    // letting the operator save into that state.
    if (enabled && times.length === 0) {
      const ok = await confirm({
        title: 'Enable with no upload times?',
        message: 'The scheduler is enabled but has no configured times — nothing will upload. Save anyway?',
        confirmLabel: 'Save',
      });
      if (!ok) return;
    }
    // Privacy guardrail: switching TO public should be deliberate.
    // The previous default was public-everywhere with no warning;
    // we now explicitly confirm before saving a public schedule
    // for the first time (or re-enabling one).
    if (enabled && privacy === 'public' && schedule.privacy !== 'public') {
      const ok = await confirm({
        title: 'Publish videos publicly on YouTube?',
        message:
          'Public videos are immediately visible to everyone on YouTube. ' +
          '"Unlisted" lets you share via link without showing up in search or recommendations — usually safer for a new pipeline. Continue with public?',
        confirmLabel: 'Yes, publish public',
        tone: 'danger',
      });
      if (!ok) return;
    }
    setSaving(true);
    try {
      await saveYoutubeUploadSchedule({
        enabled, times, grace_minutes: grace,
        sanity_check_enabled: sanity, privacy,
      });
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  }

  function handleCancel() {
    setEnabled(schedule.enabled);
    setTimes(schedule.times);
    setGrace(schedule.grace_minutes);
    setSanity(schedule.sanity_check_enabled);
    setPrivacy(schedule.privacy);
    setNewTime('09:00');
    setErr('');
  }

  const smallestGap = computeSmallestGap(times);

  return (
    <div className="rounded-xl border border-stone-200 bg-white p-5">
      {/* Header — toggle is the headline action; the small status
          pill confirms the current saved state in case the operator
          left the form mid-edit. */}
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-stone-800">Upload schedule</h3>
            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
              schedule.enabled
                ? 'bg-green-100 text-green-700'
                : 'bg-stone-200 text-stone-500'
            }`}>
              {schedule.enabled ? 'Enabled' : 'Disabled'}
            </span>
          </div>
          <p className="text-xs text-stone-500 mt-1 max-w-md">
            How often the queue gets drained to YouTube. One slot = one upload.
          </p>
        </div>
        {next && next.date && (
          <div className="text-right">
            <div className="text-[10px] uppercase tracking-wider text-stone-400">Next upload</div>
            <div className="text-sm font-semibold text-stone-800">{formatTimeOfDay(next.date)}</div>
            <div className="text-[11px] text-stone-500">{next.isTomorrow ? `tomorrow · ${next.human}` : next.human}</div>
          </div>
        )}
      </div>

      <div className="mt-5 space-y-5 max-w-2xl">
        {/* Master toggle */}
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
            className="rounded border-stone-300"
          />
          <span className="text-sm font-medium text-stone-700">
            Enable automated YouTube upload
          </span>
        </label>

        {/* Quick presets — covers ≥95% of operator intent without
            touching the times list manually. */}
        <div>
          <label className="block text-xs font-medium text-stone-600 mb-2">
            Quick preset
          </label>
          <div className="flex flex-wrap gap-2">
            {PRESETS.map((p) => {
              const active = activePresetId === p.id;
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => applyPreset(p)}
                  className={`px-3 py-2 rounded-lg text-xs font-medium border transition-colors cursor-pointer ${
                    active
                      ? 'bg-stone-800 text-white border-stone-800'
                      : 'bg-white text-stone-700 border-stone-300 hover:border-stone-400'
                  }`}
                  title={p.help}
                >
                  <div className="font-semibold">{p.label}</div>
                  <div className={`text-[10px] mt-0.5 ${active ? 'text-stone-200' : 'text-stone-500'}`}>{p.help}</div>
                </button>
              );
            })}
            {activePresetId === 'custom' && (
              <span className="px-3 py-2 rounded-lg text-xs font-medium border bg-stone-50 text-stone-600 border-stone-300">
                <div className="font-semibold">Custom</div>
                <div className="text-[10px] mt-0.5 text-stone-500">{times.length} time{times.length === 1 ? '' : 's'}</div>
              </span>
            )}
          </div>
        </div>

        {/* Times list with HTML time picker — no more HH:MM typo errors */}
        <div>
          <label className="block text-xs font-medium text-stone-600 mb-2">
            Upload times <span className="font-normal text-stone-400">(server local)</span>
          </label>
          <div className="flex flex-wrap gap-2 mb-2">
            {times.length === 0 && (
              <span className="text-xs text-stone-400 italic py-1">No times yet — pick a preset above or add one below.</span>
            )}
            {times.map((t) => (
              <span
                key={t}
                className="inline-flex items-center gap-1 rounded-full bg-stone-100 px-2.5 py-1 text-xs font-mono text-stone-700"
              >
                {t}
                <button
                  onClick={() => removeTime(t)}
                  type="button"
                  className="text-stone-400 hover:text-red-500 cursor-pointer text-sm leading-none"
                  title="Remove"
                  aria-label={`Remove ${t}`}
                >×</button>
              </span>
            ))}
          </div>
          <div className="flex gap-2 items-center">
            <input
              type="time"
              value={newTime}
              onChange={(e) => setNewTime(e.target.value)}
              className="px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
            />
            <button
              onClick={addTime}
              type="button"
              className="px-3 py-2 rounded-lg border border-stone-300 bg-white text-stone-700 text-xs font-medium hover:bg-stone-50 cursor-pointer"
            >
              Add time
            </button>
            {smallestGap !== null && smallestGap < 3 && times.length >= 2 && (
              <span className="text-[11px] text-amber-600">
                ⚠ smallest gap is {smallestGap}h
              </span>
            )}
          </div>
        </div>

        {/* Privacy with built-in safety message under "Public" */}
        <div>
          <label className="block text-xs font-medium text-stone-600 mb-2">
            Upload privacy
          </label>
          <div className="flex gap-2">
            {(['public', 'unlisted', 'private'] as const).map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => setPrivacy(p)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border cursor-pointer ${
                  privacy === p
                    ? 'bg-stone-800 text-white border-stone-800'
                    : 'bg-white text-stone-600 border-stone-300 hover:bg-stone-50'
                }`}
              >
                {p.charAt(0).toUpperCase() + p.slice(1)}
              </button>
            ))}
          </div>
          <p className="mt-1.5 text-[11px] text-stone-500">
            {privacy === 'public' && 'Visible to everyone on YouTube the moment it uploads.'}
            {privacy === 'unlisted' && 'Hidden from search/recommendations. Anyone with the link can watch.'}
            {privacy === 'private' && 'Only you can see uploaded videos. Useful for review-before-publishing.'}
          </p>
        </div>

        {/* Advanced — collapsed by default. Holds the technical knobs
            most operators don't need to touch. */}
        <div>
          <button
            type="button"
            onClick={() => setAdvancedOpen((s) => !s)}
            className="text-xs font-medium text-stone-500 hover:text-stone-700 cursor-pointer flex items-center gap-1"
          >
            <span>{advancedOpen ? '▾' : '▸'}</span>
            Advanced settings
          </button>
          {advancedOpen && (
            <div className="mt-3 space-y-4 pl-4 border-l-2 border-stone-100">
              <label className="flex items-start gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={sanity}
                  onChange={(e) => setSanity(e.target.checked)}
                  className="mt-0.5 rounded border-stone-300"
                />
                <span className="text-sm text-stone-700">
                  Run a quality check before each upload
                  <span className="block text-xs text-stone-500 font-normal mt-0.5">
                    Asks Ollama to scan the title, description, tags, and verses
                    for obvious problems (broken text, generic AI filler) and
                    skips uploading any video that's clearly not ready.
                    Rejected videos can be re-armed manually.
                  </span>
                </span>
              </label>

              <div>
                <label className="block text-xs font-medium text-stone-600 mb-1">
                  Grace window
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min={1}
                    max={240}
                    value={grace}
                    onChange={(e) => setGrace(parseInt(e.target.value) || 1)}
                    className="w-24 px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400"
                  />
                  <span className="text-xs text-stone-500">minutes</span>
                </div>
                <p className="mt-1 text-[11px] text-stone-500">
                  How late after a slot we'll still fire. If the server
                  was down at 9 AM and comes back at 9:25, a 30-minute
                  grace catches the missed upload.
                </p>
              </div>
            </div>
          )}
        </div>

        {err && <p className="text-xs text-red-600">{err}</p>}

        {/* Save bar — only visible when there's something to save.
            Keeps the form quiet during read-only browsing. */}
        {dirty && (
          <div className="flex items-center gap-2 pt-2 border-t border-stone-100">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 rounded-lg bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 disabled:opacity-50 cursor-pointer"
            >
              {saving ? 'Saving…' : 'Save changes'}
            </button>
            <button
              onClick={handleCancel}
              className="px-4 py-2 rounded-lg text-sm text-stone-500 hover:text-stone-700 cursor-pointer"
            >
              Cancel
            </button>
            <span className="text-xs text-stone-400 ml-2">Unsaved changes</span>
          </div>
        )}
      </div>
      {dialog}
    </div>
  );
}

function computeSmallestGap(times: string[]): number | null {
  if (times.length < 2) return null;
  const sorted = [...times].sort();
  let min = Infinity;
  for (let i = 1; i < sorted.length; i++) {
    const a = parseInt(sorted[i-1].split(':')[0]) + parseInt(sorted[i-1].split(':')[1]) / 60;
    const b = parseInt(sorted[i].split(':')[0]) + parseInt(sorted[i].split(':')[1]) / 60;
    if (b - a < min) min = b - a;
  }
  return Math.round(min);
}

/* =================================================================== */
/*  Auto-publish status panel                                          */
/* =================================================================== */

/**
 * Pure-display function: given a list of HH:MM strings, returns the
 * next one that hasn't passed yet today (or "tomorrow's first" if
 * we're past all of today's slots), as both a Date object and a
 * human-readable "in 2h 15m" string. Returns null if `times` is
 * empty.
 */
function nextFireFromTimes(times: string[], now: Date = new Date()): {
  date: Date;
  human: string;
  isTomorrow: boolean;
} | null {
  if (!times || times.length === 0) return null;
  const sorted = [...times].sort();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  for (const t of sorted) {
    const m = t.match(/^(\d{1,2}):(\d{2})$/);
    if (!m) continue;
    const slot = new Date(today);
    slot.setHours(parseInt(m[1]), parseInt(m[2]), 0, 0);
    if (slot.getTime() > now.getTime()) {
      return { date: slot, human: humanizeDelta(slot.getTime() - now.getTime()), isTomorrow: false };
    }
  }
  // All today's slots have passed — next is the first slot tomorrow.
  const m = sorted[0].match(/^(\d{1,2}):(\d{2})$/);
  if (!m) return null;
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  tomorrow.setHours(parseInt(m[1]), parseInt(m[2]), 0, 0);
  return { date: tomorrow, human: humanizeDelta(tomorrow.getTime() - now.getTime()), isTomorrow: true };
}

function humanizeDelta(ms: number): string {
  const totalMin = Math.round(ms / 60000);
  if (totalMin < 1) return 'now';
  if (totalMin < 60) return `in ${totalMin} min`;
  const h = Math.floor(totalMin / 60);
  const m = totalMin % 60;
  if (h < 24) return m === 0 ? `in ${h}h` : `in ${h}h ${m}m`;
  const d = Math.floor(h / 24);
  return d === 1 ? 'tomorrow' : `in ${d} days`;
}

function formatTimeOfDay(date: Date): string {
  const h = date.getHours();
  const m = date.getMinutes();
  const ampm = h < 12 ? 'AM' : 'PM';
  const h12 = h % 12 === 0 ? 12 : h % 12;
  return `${h12}:${String(m).padStart(2, '0')} ${ampm}`;
}

interface HealthCell {
  label: string;
  state: 'ok' | 'warn' | 'bad';
  detail: string;
  fixHref?: string;
  fixLabel?: string;
}

function AutoPublishStatusPanel({ refreshKey = 0 }: { refreshKey?: number }) {
  const [creds, setCreds] = useState<{ ok: boolean; tokenAgeDays?: number } | null>(null);
  const [pipelineCount, setPipelineCount] = useState<{
    enabledWithTimes: number;
    enabledNoTimes: number;
    total: number;
  } | null>(null);
  const [upload, setUpload] = useState<YoutubeUploadSchedule | null>(null);

  // refreshKey is bumped by the parent on every save. Listing it as
  // a dep makes the panel re-fetch on any save anywhere on the page.
  useEffect(() => {
    Promise.all([
      getPreferences().catch(() => ({} as Record<string, string>)),
      getPipelineSchedules().catch(() => []),
      getAllEducationalSchedules().catch(() => []),
      getYoutubeUploadSchedule().catch(() => null),
    ]).then(([prefs, recScheds, eduScheds, ytSched]) => {
      const hasCreds = !!(prefs.youtube_client_id && prefs.youtube_client_secret && prefs.youtube_refresh_token);
      let tokenAgeDays: number | undefined;
      if (prefs.youtube_refresh_token_saved_at) {
        const days = (Date.now() - new Date(prefs.youtube_refresh_token_saved_at).getTime()) / 86_400_000;
        if (!isNaN(days)) tokenAgeDays = Math.round(days);
      }
      setCreds({ ok: hasCreds, tokenAgeDays });

      const all = [
        ...recScheds.map((s) => ({ enabled: s.enabled, times: s.times })),
        ...eduScheds.map((s) => ({ enabled: s.enabled, times: s.times })),
      ];
      setPipelineCount({
        enabledWithTimes: all.filter((s) => s.enabled && s.times.length > 0).length,
        enabledNoTimes: all.filter((s) => s.enabled && s.times.length === 0).length,
        total: all.length,
      });
      setUpload(ytSched);
    });
  }, [refreshKey]);

  if (!creds || !pipelineCount || upload === null) {
    return (
      <div className="rounded-xl border border-stone-200 bg-white p-5">
        <div className="text-sm text-stone-400">Loading status…</div>
      </div>
    );
  }

  // Build the three health cells.
  const cells: HealthCell[] = [];

  // 1. YouTube credentials
  if (!creds.ok) {
    cells.push({
      label: 'YouTube credentials',
      state: 'bad',
      detail: 'Not connected — uploads will fail.',
      fixHref: '/admin/settings',
      fixLabel: 'Connect',
    });
  } else if ((creds.tokenAgeDays ?? 0) >= 7) {
    cells.push({
      label: 'YouTube credentials',
      state: 'bad',
      detail: `Refresh token is ${creds.tokenAgeDays}d old — likely expired.`,
      fixHref: '/admin/settings',
      fixLabel: 'Refresh',
    });
  } else if ((creds.tokenAgeDays ?? 0) >= 5) {
    cells.push({
      label: 'YouTube credentials',
      state: 'warn',
      detail: `Refresh token is ${creds.tokenAgeDays}d old — refresh soon.`,
      fixHref: '/admin/settings',
      fixLabel: 'Refresh',
    });
  } else {
    cells.push({
      label: 'YouTube credentials',
      state: 'ok',
      detail: creds.tokenAgeDays != null
        ? `Connected, token ${creds.tokenAgeDays}d old.`
        : 'Connected.',
    });
  }

  // 2. Pipeline schedules (the things that GENERATE the videos)
  if (pipelineCount.total === 0) {
    cells.push({
      label: 'Pipeline schedules',
      state: 'bad',
      detail: 'No pipelines exist. Create one to start generating videos.',
      fixHref: '/admin/pipelines',
      fixLabel: 'Create',
    });
  } else if (pipelineCount.enabledWithTimes === 0 && pipelineCount.enabledNoTimes === 0) {
    cells.push({
      label: 'Pipeline schedules',
      state: 'bad',
      detail: `${pipelineCount.total} pipeline(s) exist but none are scheduled — no videos will be generated.`,
      fixHref: '/admin/pipelines',
      fixLabel: 'Schedule',
    });
  } else if (pipelineCount.enabledNoTimes > 0) {
    cells.push({
      label: 'Pipeline schedules',
      state: 'warn',
      detail: `${pipelineCount.enabledNoTimes} schedule(s) enabled but missing times — they'll never fire.`,
    });
  } else {
    cells.push({
      label: 'Pipeline schedules',
      state: 'ok',
      detail: `${pipelineCount.enabledWithTimes} schedule(s) firing.`,
    });
  }

  // 3. YouTube upload schedule (drains the queue → publishes)
  const next = upload && upload.enabled ? nextFireFromTimes(upload.times) : null;
  if (!upload.enabled) {
    cells.push({
      label: 'Upload schedule',
      state: 'bad',
      detail: 'Disabled — generated videos will queue up but never publish.',
    });
  } else if (upload.times.length === 0) {
    cells.push({
      label: 'Upload schedule',
      state: 'bad',
      detail: 'Enabled but no times set — nothing will publish.',
    });
  } else {
    cells.push({
      label: 'Upload schedule',
      state: 'ok',
      detail: `${upload.times.length} slot${upload.times.length === 1 ? '' : 's'}/day, privacy: ${upload.privacy}.`,
    });
  }

  // Aggregate. ONE bad → ✕ Off. ONE warn → ⚠ Setup incomplete. All ok → ✓ Running.
  const aggregate: 'ok' | 'warn' | 'bad' =
    cells.some((c) => c.state === 'bad') ? 'bad'
    : cells.some((c) => c.state === 'warn') ? 'warn'
    : 'ok';

  const aggregateUI = {
    ok:   { label: 'Running', dot: 'bg-emerald-500', text: 'text-emerald-700', bg: 'bg-emerald-50', ring: 'ring-emerald-200' },
    warn: { label: 'Setup incomplete', dot: 'bg-amber-500', text: 'text-amber-700', bg: 'bg-amber-50', ring: 'ring-amber-200' },
    bad:  { label: 'Not publishing', dot: 'bg-red-500', text: 'text-red-700', bg: 'bg-red-50', ring: 'ring-red-200' },
  }[aggregate];

  return (
    <section>
      <div className={`rounded-xl border border-stone-200 bg-white p-5 ring-1 ${aggregateUI.ring}`}>
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <div className="flex items-center gap-2">
              <span className={`h-2.5 w-2.5 rounded-full ${aggregateUI.dot}`} />
              <h2 className="text-base font-semibold text-stone-800">Auto-publishing to YouTube</h2>
              <span className={`text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded ${aggregateUI.bg} ${aggregateUI.text}`}>
                {aggregateUI.label}
              </span>
            </div>
            <p className="text-xs text-stone-500 mt-1.5 max-w-xl">
              Three pieces have to be configured for a video to reach YouTube on its own:
              YouTube credentials, at least one pipeline schedule with daily times, and the
              global upload schedule below.
            </p>
          </div>
          {aggregate === 'ok' && next && (
            <div className="text-right">
              <div className="text-[10px] uppercase tracking-wider text-stone-400">Next upload</div>
              <div className="text-lg font-semibold text-stone-800">{formatTimeOfDay(next.date)}</div>
              <div className="text-xs text-stone-500">{next.isTomorrow ? `tomorrow · ${next.human}` : next.human}</div>
            </div>
          )}
        </div>

        <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
          {cells.map((c, i) => (
            <HealthCellView key={i} cell={c} />
          ))}
        </div>
      </div>
    </section>
  );
}

function HealthCellView({ cell }: { cell: HealthCell }) {
  const ring =
    cell.state === 'ok' ? 'border-emerald-200 bg-emerald-50/40'
    : cell.state === 'warn' ? 'border-amber-200 bg-amber-50/40'
    : 'border-red-200 bg-red-50/40';
  const dot =
    cell.state === 'ok' ? 'bg-emerald-500'
    : cell.state === 'warn' ? 'bg-amber-500'
    : 'bg-red-500';
  return (
    <div className={`rounded-lg border ${ring} px-3 py-2.5`}>
      <div className="flex items-center gap-1.5 mb-1">
        <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
        <div className="text-[10px] uppercase tracking-wider text-stone-500 font-semibold">{cell.label}</div>
      </div>
      <div className="text-xs text-stone-700 leading-snug">{cell.detail}</div>
      {cell.fixHref && cell.fixLabel && (
        <a
          href={cell.fixHref}
          className="mt-1.5 inline-block text-[11px] font-medium text-stone-700 hover:text-stone-900 underline decoration-dotted underline-offset-2"
        >
          {cell.fixLabel} →
        </a>
      )}
    </div>
  );
}
