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

  const load = useCallback(async () => {
    setErr('');
    try {
      const [s, r] = await Promise.all([
        getPipelineSchedules(),
        getPipelineScheduleRuns({ limit: 50 }),
      ]);
      setSchedules(s);
      setRuns(r);
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

      {/* ==================== Recitation pipelines (English/Arabic) ==================== */}
      <section>
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
      <EducationalScheduleSection />

      {/* ==================== YouTube upload ==================== */}
      <div className="my-10 border-t border-stone-200" />
      <YoutubeUploadSection />
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

function YoutubeUploadSection() {
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
  }, [load]);

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

      <YoutubeUploadCard schedule={schedule} onSaved={load} />

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

function YoutubeUploadCard({
  schedule,
  onSaved,
}: {
  schedule: YoutubeUploadSchedule;
  onSaved: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [enabled, setEnabled] = useState(schedule.enabled);
  const [times, setTimes] = useState<string[]>(schedule.times);
  const [newTime, setNewTime] = useState('');
  const [grace, setGrace] = useState(schedule.grace_minutes);
  const [sanity, setSanity] = useState(schedule.sanity_check_enabled);
  const [privacy, setPrivacy] = useState<'public' | 'unlisted' | 'private'>(schedule.privacy);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState('');
  const { confirm, dialog } = useConfirm();

  useEffect(() => {
    setEnabled(schedule.enabled);
    setTimes(schedule.times);
    setGrace(schedule.grace_minutes);
    setSanity(schedule.sanity_check_enabled);
    setPrivacy(schedule.privacy);
  }, [schedule]);

  // Compute smallest gap between times (for informational display)
  const smallestGap = computeSmallestGap(times);

  function addTime() {
    const m = newTime.trim().match(/^(\d{1,2}):(\d{2})$/);
    if (!m) { setErr('Use HH:MM, e.g. 09:00'); return; }
    const h = parseInt(m[1]); const mn = parseInt(m[2]);
    if (h < 0 || h > 23 || mn < 0 || mn > 59) { setErr('Invalid time'); return; }
    const padded = `${String(h).padStart(2,'0')}:${String(mn).padStart(2,'0')}`;
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
        title: 'Enable with no upload times?',
        message: 'The scheduler is enabled but has no configured times. Nothing will upload. Save anyway?',
        confirmLabel: 'Save',
      });
      if (!ok) return;
    }
    setSaving(true);
    setErr('');
    try {
      await saveYoutubeUploadSchedule({
        enabled, times, grace_minutes: grace,
        sanity_check_enabled: sanity, privacy,
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
    setEnabled(schedule.enabled);
    setTimes(schedule.times);
    setGrace(schedule.grace_minutes);
    setSanity(schedule.sanity_check_enabled);
    setPrivacy(schedule.privacy);
    setNewTime('');
    setErr('');
    setEditing(false);
  }

  return (
    <div className="rounded-xl border border-stone-200 bg-white p-5">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 className="font-semibold text-stone-800">Upload schedule</h3>
          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
            enabled ? 'bg-green-100 text-green-700' : 'bg-stone-200 text-stone-500'
          }`}>
            {enabled ? 'Enabled' : 'Disabled'}
          </span>
        </div>
        {!editing && (
          <button
            onClick={() => setEditing(true)}
            className="text-xs text-stone-500 hover:text-stone-700 cursor-pointer"
          >
            Edit
          </button>
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
            {smallestGap !== null && smallestGap < 3 && (
              <span className="ml-2 text-amber-600">
                ⚠ smallest gap is {smallestGap}h (you wanted ≥ 3h)
              </span>
            )}
          </span>
          <span>Privacy: <span className="font-medium">{privacy}</span></span>
          <span>Sanity check: {sanity ? 'on' : 'off'}</span>
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
            <span className="text-sm text-stone-700">Enable automated YouTube upload</span>
          </label>

          <div>
            <label className="block text-xs font-medium text-stone-600 mb-1">
              Upload times (server local)
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
                    type="button"
                    className="text-stone-400 hover:text-red-500 cursor-pointer text-sm leading-none"
                    title="Remove"
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
            <p className="mt-1 text-xs text-stone-400">
              Defaults to 09:00, 12:00, 15:00, 18:00, 21:00 (5 uploads/day with 3-hour gaps).
            </p>
          </div>

          <div>
            <label className="block text-xs font-medium text-stone-600 mb-1">Upload privacy</label>
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
          </div>

          <label className="flex items-start gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={sanity}
              onChange={(e) => setSanity(e.target.checked)}
              className="mt-0.5 rounded border-stone-300"
            />
            <span className="text-sm text-stone-700">
              Sanity check before upload
              <span className="block text-xs text-stone-400 font-normal">
                Ollama evaluates title/description/tags/verses one last time and rejects
                videos with obvious issues (broken metadata, incoherent passage, generic slop).
                Rejected videos are flagged and won't be retried automatically.
              </span>
            </span>
          </label>

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
