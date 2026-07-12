import { useState, useEffect, useCallback, useRef } from 'react';
import {
  getPipelineSchedules, savePipelineSchedule, getPipelineScheduleRuns,
  getYoutubeUploadSchedule, saveYoutubeUploadSchedule, getYoutubeUploadRuns,
  testYoutubeOAuth, resetYoutubeOAuthCircuitBreaker,
  getPreferences,
  getAllEducationalSchedules, getAllEducationalScheduleRuns,
  upsertEducationalSchedule,
  getServerTime,
  getQaPublishStatus, saveQaPublishSchedule,
} from '../../api/admin';
import type {
  PipelineSchedule, PipelineScheduleRun,
  YoutubeUploadSchedule, YoutubeUploadRun,
  EducationalScheduleListItem, EducationalScheduleRunGlobal,
  ServerTime, QaPublishStatus,
} from '../../api/admin';
import { useConfirm } from './shared/useConfirm';

type TabKey = 'overview' | 'youtube' | 'recitation' | 'educational';

// URL-hash sync. Use hash so the tab persists across reloads and
// deep-links work (e.g. /admin/scheduler#youtube). Backward compat:
// the page used to use #youtube-upload, so we accept the old form
// and map it to the new tab key.
const HASH_TO_TAB: Record<string, TabKey> = {
  '#overview': 'overview',
  '#youtube': 'youtube',
  '#youtube-upload': 'youtube',  // old anchor name
  '#recitation': 'recitation',
  '#educational': 'educational',
};

function readHashTab(): TabKey {
  if (typeof window === 'undefined') return 'overview';
  return HASH_TO_TAB[window.location.hash] ?? 'overview';
}

/** One shared fetch of the shorts publish status for the whole page
 *  (tab dot, hero panel, next-fire aggregate, up-next list). Polls
 *  every 60s; re-fetches when refreshKey bumps (any save on the page)
 *  or when reload() is called (hero toggle). skewMs = server − client
 *  clock difference, captured per fetch, so countdowns tick against
 *  the server's clock. */
function usePublishStatus(refreshKey: number): {
  status: QaPublishStatus | null;
  error: boolean;
  loading: boolean;
  skewMs: number;
  reload: () => void;
} {
  const [status, setStatus] = useState<QaPublishStatus | null>(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);
  const skewRef = useRef(0);

  const reload = useCallback(async () => {
    try {
      const s = await getQaPublishStatus();
      skewRef.current = new Date(s.server_now).getTime() - Date.now();
      setStatus(s);
      setError(false);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
    const poll = setInterval(reload, 60_000);
    return () => clearInterval(poll);
  }, [reload, refreshKey]);

  return { status, error, loading, skewMs: skewRef.current, reload };
}

const DAY_SHORT = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

function shortsDaysLabel(days: number[]): string {
  const valid = (days || []).filter((d) => d >= 0 && d <= 6).sort((a, b) => a - b);
  return valid.length ? valid.map((d) => DAY_SHORT[d]).join(' · ') : 'no days set';
}

function relativeTimeFrom(iso: string): string {
  // SQLite stamps completed_at in UTC without a zone suffix.
  const t = new Date(iso.includes('T') || iso.endsWith('Z') ? iso : iso.replace(' ', 'T') + 'Z');
  const mins = Math.round((Date.now() - t.getTime()) / 60_000);
  if (!isFinite(mins)) return iso;
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins} min ago`;
  const h = Math.round(mins / 60);
  if (h < 48) return `${h}h ago`;
  return `${Math.round(h / 24)}d ago`;
}

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
  const [tab, setTab] = useState<TabKey>(readHashTab);

  // Sync URL hash with tab state. Bidirectional: hashchange (e.g.
  // user clicks a #youtube link) updates state; tab clicks push to
  // history.replaceState (no scroll jump from the browser auto-
  // anchoring to the now-removed section ids).
  useEffect(() => {
    function onHashChange() { setTab(readHashTab()); }
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  function changeTab(next: TabKey) {
    setTab(next);
    const hash = `#${next}`;
    if (window.location.hash !== hash) {
      // replaceState avoids polluting history with every tab click.
      window.history.replaceState(null, '', hash);
    }
  }

  // Refresh key bumped after any save anywhere on the page so the
  // Overview's status panel + countdown re-fetch with fresh data.
  const [refreshKey, setRefreshKey] = useState(0);
  const bumpRefresh = useCallback(() => setRefreshKey((k) => k + 1), []);

  const publish = usePublishStatus(refreshKey);

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-xl font-semibold text-stone-800 mb-1">Scheduler</h1>
        <p className="text-sm text-stone-500">
          Live shorts publishing plus the legacy generation pipelines.
          Pipeline times are in server local time; shorts slots are UTC.
        </p>
      </div>

      <TabBar current={tab} onChange={changeTab} publish={publish.status} />

      <div className="mt-6">
        {tab === 'overview' && (
          <OverviewTab
            refreshKey={refreshKey}
            onTabChange={changeTab}
            publish={publish}
          />
        )}
        {tab === 'youtube' && (
          <YoutubeUploadSection refreshTrigger={refreshKey} onSaved={bumpRefresh} />
        )}
        {tab === 'recitation' && (
          <RecitationSection onSaved={bumpRefresh} />
        )}
        {tab === 'educational' && (
          <EducationalScheduleSection onSaved={bumpRefresh} />
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------ */

function TabBar({
  current, onChange, publish,
}: {
  current: TabKey;
  onChange: (t: TabKey) => void;
  publish: QaPublishStatus | null;
}) {
  const tabs: { key: TabKey; label: string; sub: string }[] = [
    { key: 'overview',    label: 'Overview',     sub: 'shorts publishing & status' },
    { key: 'youtube',     label: 'YouTube',      sub: 'legacy · upload slots' },
    { key: 'recitation',  label: 'Recitation',   sub: 'legacy · EN / AR' },
    { key: 'educational', label: 'Educational',  sub: 'legacy · grammar / origins' },
  ];
  const shortsDot = publish
    ? (publish.prefs.enabled && !publish.health.breaker_open
        ? 'bg-emerald-500' : 'bg-amber-400')
    : null;
  return (
    <div className="border-b border-stone-200">
      <nav className="-mb-px flex flex-wrap gap-1" aria-label="Scheduler sections">
        {tabs.map((t) => {
          const active = current === t.key;
          return (
            <button
              key={t.key}
              type="button"
              onClick={() => onChange(t.key)}
              aria-current={active ? 'page' : undefined}
              className={`group relative px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors cursor-pointer ${
                active
                  ? 'border-stone-800 text-stone-900'
                  : 'border-transparent text-stone-500 hover:text-stone-800 hover:border-stone-300'
              }`}
            >
              <span>{t.label}</span>
              {t.key === 'overview' && shortsDot && (
                <span
                  className={`w-1.5 h-1.5 rounded-full inline-block ml-1.5 align-middle ${shortsDot}`}
                  title={shortsDot === 'bg-emerald-500'
                    ? 'Shorts publishing is live'
                    : 'Shorts publishing needs attention'}
                />
              )}
              <span className={`block text-[10px] mt-0.5 ${active ? 'text-stone-500' : 'text-stone-400'}`}>
                {t.sub}
              </span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}

/* ============================================================ */
/*  Overview tab                                                 */
/* ============================================================ */
/* Single-screen "is everything healthy and what's next" view.
 * Combines the AutoPublishStatusPanel that used to sit at the top
 * of the page with a large server-clock + countdown to the next
 * scheduled fire across ALL schedules, plus a list of the next 5
 * things to fire. Clicking any item jumps to the relevant tab.
 */

function OverviewTab({
  refreshKey, onTabChange, publish,
}: {
  refreshKey: number;
  onTabChange: (t: TabKey) => void;
  publish: ReturnType<typeof usePublishStatus>;
}) {
  return (
    <div className="space-y-6">
      <ShortsPublishPanel publish={publish} />
      <ServerClockPanel publish={publish} />
      <UpNextPanel onTabChange={onTabChange} publish={publish} />
      <LegacySystemsPanel refreshKey={refreshKey} onTabChange={onTabChange} />
    </div>
  );
}

/* ------------------------------------------------------------ */
/*  Shorts publishing hero — the live pipeline. Answers, at a    */
/*  glance: is it on, when is the next upload, what will it be,  */
/*  how deep is the queue, did the last one work.                */
/* ------------------------------------------------------------ */

const SERIES_CHIP: Record<string, string> = {
  poetry: 'bg-rose-100 text-rose-700',
  root: 'bg-emerald-100 text-emerald-700',
  exegesis: 'bg-violet-100 text-violet-700',
  qa: 'bg-amber-100 text-amber-700',
};

function ShortsPublishPanel({
  publish,
}: { publish: ReturnType<typeof usePublishStatus> }) {
  const { status, error, loading, skewMs, reload } = publish;
  const [, setTick] = useState(0);
  const [confirmResume, setConfirmResume] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const t = setInterval(() => setTick((x) => x + 1), 1000);
    return () => clearInterval(t);
  }, []);

  if (loading) {
    return (
      <section className="rounded-xl border border-stone-200 bg-white p-5">
        <div className="h-4 w-40 bg-stone-100 rounded animate-pulse mb-3" />
        <div className="h-8 w-64 bg-stone-100 rounded animate-pulse" />
      </section>
    );
  }
  if (error || !status) {
    return (
      <section className="rounded-xl border border-red-200 border-l-4 border-l-red-500 bg-white p-5">
        <h2 className="text-base font-semibold text-stone-800">Shorts publishing</h2>
        <p className="text-sm text-red-600 mt-2">Couldn't load publishing status.</p>
        <button
          type="button"
          onClick={reload}
          className="mt-2 text-sm font-medium text-stone-700 underline decoration-dotted underline-offset-2 cursor-pointer"
        >
          Retry
        </button>
      </section>
    );
  }

  const { prefs, counts, health, next_up, next_slot, last_upload } = status;
  const state: 'blocked' | 'paused' | 'empty' | 'live' =
    health.breaker_open ? 'blocked'
    : !prefs.enabled ? 'paused'
    : counts.approved === 0 ? 'empty'
    : 'live';

  const pill = {
    live:    { label: 'LIVE',        cls: 'bg-emerald-50 text-emerald-700' },
    paused:  { label: 'PAUSED',      cls: 'bg-amber-50 text-amber-700' },
    blocked: { label: 'BLOCKED',     cls: 'bg-red-50 text-red-700' },
    empty:   { label: 'QUEUE EMPTY', cls: 'bg-amber-50 text-amber-700' },
  }[state];
  const accent = {
    live: 'border-l-emerald-500',
    paused: 'border-l-amber-400',
    blocked: 'border-l-red-500',
    empty: 'border-l-amber-400',
  }[state];

  const serverNowMs = Date.now() + skewMs;
  const slotMs = next_slot ? new Date(next_slot).getTime() - serverNowMs : null;
  const firedToday = !!prefs.last_fired_date &&
    prefs.last_fired_date === new Date(serverNowMs).toISOString().slice(0, 10);
  const publishDays = Math.max(1, (prefs.days || []).length);
  const runwayWeeks = Math.ceil(counts.approved / publishDays);

  async function toggleEnabled(next: boolean) {
    setSaving(true);
    try {
      await saveQaPublishSchedule({ enabled: next });
      setConfirmResume(false);
      reload();
    } catch {
      // leave the switch as-is; next poll shows truth
    } finally {
      setSaving(false);
    }
  }

  const healthChips: { text: string; cls: string; href?: string }[] = [];
  if (health.breaker_open) {
    healthChips.push({ text: 'Upload breaker OPEN', cls: 'bg-red-50 text-red-700', href: '/admin/settings' });
  } else if (health.oauth_failures > 0) {
    healthChips.push({ text: `${health.oauth_failures} recent YouTube failure${health.oauth_failures === 1 ? '' : 's'}`, cls: 'bg-amber-50 text-amber-700', href: '/admin/settings' });
  }
  if (!health.elevenlabs_ok) {
    healthChips.push({ text: 'ElevenLabs key missing — voice render will fail at publish time', cls: 'bg-amber-50 text-amber-700', href: '/admin/settings' });
  }
  if (!health.voice_ok) {
    healthChips.push({ text: 'No narration voice configured', cls: 'bg-amber-50 text-amber-700', href: '/admin/qa-videos' });
  }

  return (
    <section
      id="shorts-publish-panel"
      className={`rounded-xl border border-stone-200 border-l-4 ${accent} bg-white p-5`}
    >
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <h2 className="text-base font-semibold text-stone-800">Shorts publishing</h2>
          <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded uppercase tracking-wider ${pill.cls}`}>
            {pill.label}
          </span>
        </div>
        <div className="flex items-center gap-3">
          {confirmResume ? (
            <span className="text-xs text-stone-600 flex items-center gap-2">
              Resume {prefs.privacy} publishing {shortsDaysLabel(prefs.days)} {prefs.time} UTC?
              <button
                type="button"
                disabled={saving}
                onClick={() => toggleEnabled(true)}
                className="font-semibold text-emerald-700 hover:text-emerald-800 cursor-pointer disabled:opacity-50"
              >
                Resume
              </button>
              <button
                type="button"
                onClick={() => setConfirmResume(false)}
                className="text-stone-500 hover:text-stone-700 cursor-pointer"
              >
                Cancel
              </button>
            </span>
          ) : (
            <label className="flex items-center gap-2 text-xs text-stone-500 cursor-pointer">
              Publishing
              <button
                type="button"
                role="switch"
                aria-checked={prefs.enabled}
                disabled={saving}
                onClick={() => prefs.enabled ? toggleEnabled(false) : setConfirmResume(true)}
                className={`relative h-5 w-9 rounded-full transition-colors cursor-pointer disabled:opacity-50 ${prefs.enabled ? 'bg-emerald-500' : 'bg-stone-300'}`}
              >
                <span className={`absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white transition-transform ${prefs.enabled ? 'translate-x-4' : ''}`} />
              </button>
            </label>
          )}
          <a
            href="/admin/qa-videos"
            className="text-xs font-medium text-stone-600 hover:text-stone-900 underline decoration-dotted underline-offset-2"
          >
            Edit schedule →
          </a>
        </div>
      </div>

      <p className="text-xs text-stone-500 mt-1.5">
        {shortsDaysLabel(prefs.days)} at {prefs.time} UTC · round-robin across 4 series
        · uploads {prefs.privacy}
        {health.voice_name ? ` · voice: ${health.voice_name}` : ''}
        {firedToday && <span className="text-emerald-600 font-medium"> · fired today ✓</span>}
      </p>

      {state === 'paused' && (
        <div className="mt-3 rounded-md bg-amber-50 text-amber-800 text-xs px-3 py-2">
          Publishing is paused — approved scripts will accumulate but nothing uploads.
        </div>
      )}
      {state === 'blocked' && (
        <div className="mt-3 rounded-md bg-red-50 text-red-700 text-xs px-3 py-2">
          Uploads halted — circuit breaker opened after {health.oauth_failures} consecutive
          YouTube failures. Slots are skipped until it's fixed.{' '}
          <a href="/admin/settings" className="font-semibold underline underline-offset-2">Fix credentials →</a>
        </div>
      )}
      {state === 'empty' && (
        <div className="mt-3 rounded-md bg-amber-50 text-amber-800 text-xs px-3 py-2">
          0 approved scripts — nothing will publish at the next slot.
          {counts.awaiting_review > 0 && (
            <>
              {' '}
              <a href="/admin/qa-videos" className="font-semibold underline underline-offset-2">
                Review {counts.awaiting_review} waiting script{counts.awaiting_review === 1 ? '' : 's'} →
              </a>
            </>
          )}
        </div>
      )}

      <div className={`mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4 ${state === 'paused' ? 'opacity-60' : ''}`}>
        <div>
          <div className="text-[10px] uppercase tracking-wider text-stone-400">Next upload</div>
          {state === 'paused' || !next_slot ? (
            <div className="text-3xl font-mono text-stone-400 mt-1">—</div>
          ) : slotMs !== null && slotMs <= 0 ? (
            <>
              <div className="text-3xl font-mono font-semibold text-stone-800 mt-1">due now</div>
              <div className="text-xs text-stone-500 mt-1">
                waiting for scheduler (grace {prefs.grace_minutes ?? 120} min)
                {state === 'blocked' && <span className="text-red-600 font-medium"> · this slot will be skipped</span>}
              </div>
            </>
          ) : (
            <>
              <div
                className="text-3xl font-mono font-semibold text-stone-800 mt-1"
                style={{ fontVariantNumeric: 'tabular-nums' }}
              >
                {humanizeCountdown(slotMs ?? 0)}
              </div>
              <div className="text-xs text-stone-500 mt-1">
                {new Date(next_slot).toLocaleString(undefined, {
                  weekday: 'short', month: 'short', day: 'numeric',
                  hour: '2-digit', minute: '2-digit',
                })}
                {state === 'blocked' && <span className="text-red-600 font-medium"> · this slot will be skipped</span>}
              </div>
            </>
          )}
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-wider text-stone-400">Will publish</div>
          {next_up ? (
            <a href="/admin/qa-videos" className="block group mt-1">
              <div className="text-sm font-medium text-stone-800 group-hover:text-stone-950 leading-snug">
                {next_up.title}
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${SERIES_CHIP[next_up.source_type] || 'bg-sky-100 text-sky-700'}`}>
                  {next_up.source_type}
                </span>
                <span className="text-[11px] text-stone-400">{next_up.anchor_ref}</span>
              </div>
              <div className="text-[10px] text-stone-400 mt-1">
                Chosen by the same round-robin picker the scheduler runs.
              </div>
            </a>
          ) : counts.approved > 0 ? (
            <div className="text-sm text-stone-400 mt-1">Determining next video…</div>
          ) : (
            <div className="text-sm text-stone-400 mt-1">Nothing approved yet.</div>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-x-6 gap-y-2 mt-4 pt-4 border-t border-stone-100 text-sm">
        <a href="/admin/qa-videos" className="text-stone-700 hover:text-stone-900">
          <span className="font-semibold">{counts.approved}</span> approved
          <span className="text-stone-400 text-xs"> · ≈{runwayWeeks} week{runwayWeeks === 1 ? '' : 's'} at {publishDays}/week</span>
        </a>
        <a href="/admin/qa-videos" className="text-stone-700 hover:text-stone-900">
          <span className={`font-semibold ${counts.approved < 3 && counts.awaiting_review > 0 ? 'text-amber-600' : ''}`}>
            {counts.awaiting_review}
          </span> awaiting review
        </a>
        <span className="text-stone-700">
          <span className="font-semibold">{counts.uploaded}</span> uploaded
        </span>
      </div>

      <div className="mt-3 text-xs text-stone-500">
        {last_upload ? (
          <span className="inline-flex items-center gap-1.5 flex-wrap">
            <svg className="w-3.5 h-3.5 text-emerald-500 shrink-0" viewBox="0 0 20 20" fill="currentColor" aria-hidden>
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Last upload: {last_upload.title}
            {last_upload.completed_at && <> · {relativeTimeFrom(last_upload.completed_at)}</>}
            {last_upload.youtube_video_id && (
              <a
                href={`https://youtube.com/watch?v=${last_upload.youtube_video_id}`}
                target="_blank"
                rel="noreferrer"
                className="font-medium text-stone-700 hover:text-stone-900 underline decoration-dotted underline-offset-2"
              >
                Watch →
              </a>
            )}
          </span>
        ) : (
          <span>No uploads yet — the first will go at the next slot.</span>
        )}
      </div>

      {healthChips.length > 0 ? (
        <div className="flex flex-wrap gap-2 mt-3">
          {healthChips.map((c, i) => c.href ? (
            <a key={i} href={c.href} className={`text-[11px] font-medium px-2 py-1 rounded ${c.cls} underline decoration-dotted underline-offset-2`}>
              {c.text}
            </a>
          ) : (
            <span key={i} className={`text-[11px] font-medium px-2 py-1 rounded ${c.cls}`}>{c.text}</span>
          ))}
        </div>
      ) : (
        <div className="mt-3">
          <span className="text-[11px] font-medium px-2 py-1 rounded bg-emerald-50 text-emerald-700">
            All systems ok
          </span>
        </div>
      )}
    </section>
  );
}

/* ------------------------------------------------------------ */

function ServerClockPanel({
  publish,
}: { publish: ReturnType<typeof usePublishStatus> }) {
  // Anchor on a server-time fetch then tick locally. Re-sync every
  // 5 minutes (clock drift is tiny, but a long-open tab will drift
  // a few seconds an hour from the server's wall clock). Operator
  // sees the SERVER's time of day, which is what the scheduler
  // uses to decide when to fire — not the browser's.
  const [serverTime, setServerTime] = useState<ServerTime | null>(null);
  // Difference between server and browser epochs (server - browser),
  // captured at fetch time. We extrapolate by adding it to Date.now().
  const offsetRef = useRef<number>(0);
  const [tick, setTick] = useState(0);

  const sync = useCallback(async () => {
    try {
      const t = await getServerTime();
      offsetRef.current = t.now_epoch_ms - Date.now();
      setServerTime(t);
    } catch {
      // Silently fall back to browser time. Operator sees a slight
      // mismatch but the page still works.
    }
  }, []);

  useEffect(() => {
    sync();
    const resync = setInterval(sync, 5 * 60_000);
    const ticker = setInterval(() => setTick((x) => x + 1), 1000);
    return () => {
      clearInterval(resync);
      clearInterval(ticker);
    };
  }, [sync]);

  // Recompute "now on server" each tick.
  void tick;
  const serverNow = new Date(Date.now() + offsetRef.current);
  const tzLabel = serverTime?.tz_name || 'server';

  return (
    <section className="rounded-xl border border-stone-200 bg-white p-5">
      <div className="flex items-baseline justify-between flex-wrap gap-3">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-stone-400">
            Server time · {tzLabel}
          </div>
          <div
            className="font-mono font-semibold text-stone-900 leading-none mt-1"
            style={{ fontSize: 56, fontVariantNumeric: 'tabular-nums' }}
          >
            {String(serverNow.getHours()).padStart(2, '0')}
            {/* Blinking colon is the only "I'm alive" signal now that
                seconds are hidden — operator wanted HH:MM, not HH:MM:SS,
                because the second-level churn distracted from the rest
                of the dashboard. The colon still pulses each second
                (tick state still updates 1Hz so the Up Next countdowns
                stay smooth). */}
            <span className={tick % 2 === 0 ? 'opacity-100' : 'opacity-30'}>:</span>
            {String(serverNow.getMinutes()).padStart(2, '0')}
          </div>
          <div className="text-xs text-stone-500 mt-1">
            {serverNow.toLocaleDateString(undefined, {
              weekday: 'long', month: 'short', day: 'numeric', year: 'numeric',
            })}
          </div>
        </div>
        <NextFireCountdown publish={publish.status} />
      </div>
      {!serverTime && (
        <p className="mt-3 text-[11px] text-amber-600">
          Couldn't reach the server-time endpoint — clock is showing browser time.
        </p>
      )}
    </section>
  );
}

/* ------------------------------------------------------------ */

interface UpcomingFire {
  source: 'shorts' | 'youtube' | 'recitation' | 'educational';
  pipelineName: string;     // human label for "what" will fire
  pipelineId?: number;
  /** Computed next-fire moment, in the server's clock. */
  nextDate: Date;
  /** ms until fire, computed against server-now. */
  msUntil: number;
  /** Shorts only: queue has nothing approved. */
  queueEmpty?: boolean;
}

function NextFireCountdown({ publish }: { publish: QaPublishStatus | null }) {
  // Aggregates next-fire across the shorts publisher and the three
  // legacy schedule families; shows a live countdown to the soonest.
  const [next, setNext] = useState<UpcomingFire | null>(null);
  const [, setTick] = useState(0);

  const load = useCallback(async () => {
    try {
      const [yt, rec, edu] = await Promise.all([
        getYoutubeUploadSchedule().catch(() => null),
        getPipelineSchedules().catch(() => []),
        getAllEducationalSchedules().catch(() => []),
      ]);
      const all = collectUpcoming(yt, rec, edu, publish);
      setNext(all[0] || null);
    } catch {
      setNext(null);
    }
  }, [publish]);

  useEffect(() => {
    load();
    const reload = setInterval(load, 60_000);
    const ticker = setInterval(() => setTick((x) => x + 1), 1000);
    return () => {
      clearInterval(reload);
      clearInterval(ticker);
    };
  }, [load]);

  if (!next) {
    return (
      <div className="text-right">
        <div className="text-[10px] uppercase tracking-wider text-stone-400">Next fire</div>
        <div className="text-sm text-stone-500 mt-1">No active schedules</div>
      </div>
    );
  }

  const ms = next.nextDate.getTime() - Date.now();
  return (
    <div className="text-right">
      <div className="text-[10px] uppercase tracking-wider text-stone-400">Next fire</div>
      <div
        className="font-mono font-semibold text-stone-800 leading-none mt-1"
        style={{ fontSize: 32, fontVariantNumeric: 'tabular-nums' }}
      >
        {humanizeCountdown(ms)}
      </div>
      <div className="text-xs text-stone-500 mt-1">
        {sourceLabel(next.source)} · {next.pipelineName}
      </div>
      <div className="text-[11px] text-stone-400">
        at {formatTimeOfDay(next.nextDate)} server time
      </div>
    </div>
  );
}

function humanizeCountdown(ms: number): string {
  if (ms <= 0) return '00:00:00';
  const totalSec = Math.floor(ms / 1000);
  const d = Math.floor(totalSec / 86_400);
  const h = Math.floor((totalSec % 86_400) / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  const hms = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return d > 0 ? `${d}d ${hms}` : hms;
}

function sourceLabel(s: UpcomingFire['source']): string {
  return s === 'shorts' ? 'Shorts publish'
    : s === 'youtube' ? 'YouTube upload'
    : s === 'recitation' ? 'Recitation'
    : 'Educational';
}

function collectUpcoming(
  yt: YoutubeUploadSchedule | null,
  rec: PipelineSchedule[],
  edu: EducationalScheduleListItem[],
  publish: QaPublishStatus | null = null,
  now: Date = new Date(),
): UpcomingFire[] {
  const out: UpcomingFire[] = [];
  // Shorts publisher: use the server-computed next_slot verbatim —
  // it honors the M/W/F day set, the grace window, and today's
  // already-fired flag. nextFireFromTimes is daily-only and would
  // invent fires on off days.
  if (publish && publish.prefs.enabled && publish.next_slot) {
    const d = new Date(publish.next_slot);
    out.push({
      source: 'shorts',
      pipelineName: publish.next_up
        ? `Publish: ${publish.next_up.title}`
        : 'Publish (queue empty)',
      nextDate: d,
      msUntil: d.getTime() - now.getTime(),
      queueEmpty: !publish.next_up,
    });
  }
  if (yt && yt.enabled && yt.times.length > 0) {
    const n = nextFireFromTimes(yt.times, now);
    if (n) {
      out.push({
        source: 'youtube',
        pipelineName: 'Drains queue → YouTube',
        nextDate: n.date,
        msUntil: n.date.getTime() - now.getTime(),
      });
    }
  }
  for (const s of rec) {
    if (!s.enabled || s.times.length === 0) continue;
    const n = nextFireFromTimes(s.times, now);
    if (n) {
      out.push({
        source: 'recitation',
        pipelineName: `${s.pipeline_name} (${s.pipeline_language === 'arabic' ? 'AR' : 'EN'})`,
        pipelineId: s.pipeline_id,
        nextDate: n.date,
        msUntil: n.date.getTime() - now.getTime(),
      });
    }
  }
  for (const s of edu) {
    if (!s.enabled || !s.pipeline_enabled || s.times.length === 0) continue;
    const n = nextFireFromTimes(s.times, now);
    if (n) {
      out.push({
        source: 'educational',
        pipelineName: `${s.pipeline_name} · ${s.pipeline_type}`,
        pipelineId: s.pipeline_id,
        nextDate: n.date,
        msUntil: n.date.getTime() - now.getTime(),
      });
    }
  }
  out.sort((a, b) => a.msUntil - b.msUntil);
  return out;
}

function UpNextPanel({
  onTabChange, publish,
}: {
  onTabChange: (t: TabKey) => void;
  publish: ReturnType<typeof usePublishStatus>;
}) {
  const [items, setItems] = useState<UpcomingFire[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [, setTick] = useState(0);

  const load = useCallback(async () => {
    try {
      const [yt, rec, edu] = await Promise.all([
        getYoutubeUploadSchedule().catch(() => null),
        getPipelineSchedules().catch(() => []),
        getAllEducationalSchedules().catch(() => []),
      ]);
      setItems(collectUpcoming(yt, rec, edu, publish.status).slice(0, 8));
      setFailed(false);
    } catch {
      setItems([]);
      setFailed(true);
    }
  }, [publish.status]);

  useEffect(() => {
    load();
    const reload = setInterval(load, 60_000);
    const ticker = setInterval(() => setTick((x) => x + 1), 1000);
    return () => { clearInterval(reload); clearInterval(ticker); };
  }, [load]);

  if (items === null) {
    return (
      <div className="rounded-xl border border-stone-200 bg-white p-5 text-sm text-stone-400">
        Loading upcoming…
      </div>
    );
  }
  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-stone-200 bg-white p-5">
        <div className="text-base font-semibold text-stone-800 mb-1">Up next</div>
        <p className="text-sm text-stone-500">
          {failed
            ? "Couldn't load schedules."
            : 'Nothing scheduled. Enable shorts publishing above, or a legacy pipeline, to start firing.'}
        </p>
      </div>
    );
  }

  const onlyShorts = items.every((it) => it.source === 'shorts');

  return (
    <section className="rounded-xl border border-stone-200 bg-white p-5">
      <div className="flex items-baseline justify-between mb-3">
        <h2 className="text-base font-semibold text-stone-800">Up next</h2>
        <span className="text-[11px] text-stone-400">
          Across all schedules. Click a row to jump to its section.
        </span>
      </div>
      <ul className="divide-y divide-stone-100">
        {items.map((it, i) => {
          const ms = it.nextDate.getTime() - Date.now();
          return (
            <li
              key={`${it.source}-${it.pipelineId ?? 'yt'}-${i}`}
              onClick={() => {
                if (it.source === 'shorts') {
                  onTabChange('overview');
                  document.getElementById('shorts-publish-panel')?.scrollIntoView({ behavior: 'smooth' });
                } else {
                  onTabChange(it.source === 'youtube' ? 'youtube'
                    : it.source === 'recitation' ? 'recitation' : 'educational');
                }
              }}
              className="py-2.5 flex items-center justify-between gap-3 cursor-pointer hover:bg-stone-50 -mx-2 px-2 rounded-md"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
                    it.source === 'shorts' ? 'bg-sky-100 text-sky-700'
                    : it.source === 'youtube' ? 'bg-red-100 text-red-700'
                    : it.source === 'recitation' ? 'bg-emerald-100 text-emerald-700'
                    : 'bg-violet-100 text-violet-700'
                  }`}>
                    {sourceLabel(it.source)}
                  </span>
                  <span className="text-sm text-stone-700 truncate">
                    {it.pipelineName}
                  </span>
                  {it.queueEmpty && (
                    <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-amber-100 text-amber-700">
                      queue empty
                    </span>
                  )}
                </div>
                <div className="text-[11px] text-stone-400 mt-0.5 font-mono">
                  {formatTimeOfDay(it.nextDate)}
                  {it.nextDate.toDateString() !== new Date().toDateString() && ' · tomorrow'}
                </div>
              </div>
              <div
                className="text-right font-mono text-sm text-stone-700 shrink-0"
                style={{ fontVariantNumeric: 'tabular-nums' }}
              >
                {humanizeCountdown(ms)}
              </div>
            </li>
          );
        })}
      </ul>
      {onlyShorts && (
        <p className="mt-3 text-[11px] text-stone-400">
          Recitation, Educational and upload-slot pipelines are paused — see their tabs.
        </p>
      )}
    </section>
  );
}

/* ------------------------------------------------------------ */
/*  One-line pointer shown at the top of a legacy tab when that  */
/*  family is fully off — self-removes when anything re-enables. */
/* ------------------------------------------------------------ */

function LegacyPointerBar() {
  return (
    <div className="text-xs text-stone-500 bg-stone-50 rounded-md px-3 py-2 mb-4">
      This legacy pipeline is paused. Live shorts publishing runs from the{' '}
      <a href="#overview" className="underline decoration-dotted underline-offset-2 hover:text-stone-700">
        Overview tab
      </a>.
    </div>
  );
}

/* ============================================================ */
/*  Recitation tab section (extracted from old top-level body)   */
/* ============================================================ */

function RecitationSection({ onSaved }: { onSaved: () => void }) {
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
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load schedules');
    } finally {
      setLoading(false);
    }
  }, [onSaved]);

  useEffect(() => {
    load();
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
    <section>
      {err && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {err}
        </div>
      )}
      {schedules.length > 0 && schedules.every((s) => !s.enabled) && <LegacyPointerBar />}
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
                  <th className="text-left px-3 py-2 font-medium">Title</th>
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
                    <td className="px-3 py-2 text-xs text-stone-600 max-w-[260px] truncate" title={r.video_title || ''}>
                      <TitleOrStatus title={r.video_title} videoStatus={r.video_status} videoError={null} />
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
  );
}

/* ------------------------------------------------------------ */

/** Title cell helper: prefer the video's youtube_title; when that's
 *  not yet populated (downstream still in progress, or the video
 *  failed before metadata-gen), fall back to a small status chip
 *  showing the video's lifecycle state. The error_message tooltip
 *  on a "failed" chip surfaces the actual cause without making the
 *  operator click into the video detail page. */
function TitleOrStatus({
  title, videoStatus, videoError,
}: {
  title: string | null;
  videoStatus: string | null;
  videoError: string | null;
}) {
  if (title) return <>{title}</>;
  if (!videoStatus) return <span className="text-stone-300">—</span>;
  const cls =
    videoStatus === 'failed' ? 'bg-red-50 text-red-700 border-red-100'
    : videoStatus === 'uploaded' ? 'bg-emerald-50 text-emerald-700 border-emerald-100'
    : 'bg-stone-50 text-stone-600 border-stone-200';
  // Truncate the error to a tooltip-friendly size; full text is in
  // the `title` attr for hover.
  const tooltip = videoStatus === 'failed' && videoError
    ? videoError
    : `Video state: ${videoStatus}`;
  return (
    <span
      className={`inline-block rounded border px-1.5 py-0.5 text-[10px] font-medium ${cls}`}
      title={tooltip}
    >
      {videoStatus === 'failed' ? 'Video failed' : `Video ${videoStatus}`}
    </span>
  );
}


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

function EducationalScheduleSection({
  onSaved,
}: { onSaved?: () => void } = {}) {
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
      if (onSaved) onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load educational schedules');
    } finally {
      setLoading(false);
    }
  }, [onSaved]);

  useEffect(() => {
    load();
    const t = setInterval(load, 60_000);
    return () => clearInterval(t);
  }, [load]);

  return (
    <section>
      {schedules.length > 0 && schedules.every((s) => !s.enabled) && <LegacyPointerBar />}
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
                  <th className="text-left px-3 py-2 font-medium">Title</th>
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
                    <td className="px-3 py-2 text-xs text-stone-600 max-w-[260px] truncate" title={r.video_title || ''}>
                      <TitleOrStatus title={r.video_title} videoStatus={r.video_status} videoError={r.video_error} />
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
  // OAuth circuit-breaker UI state — testing/resetting the OAuth
  // refresh-token flow, with feedback inline so the operator doesn't
  // have to navigate elsewhere to see whether the fix worked.
  const [oauthTesting, setOauthTesting] = useState(false);
  const [oauthFeedback, setOauthFeedback] = useState<{
    ok: boolean;
    message: string;
  } | null>(null);
  const [oauthResetting, setOauthResetting] = useState(false);

  async function handleTestOauth() {
    setOauthTesting(true);
    setOauthFeedback(null);
    try {
      const r = await testYoutubeOAuth();
      setOauthFeedback({
        ok: !!r.ok,
        message: r.ok ? (r.message || 'OAuth refresh succeeded.') : (r.error || 'OAuth refresh failed.'),
      });
      // Reload so the breaker badge updates immediately.
      const fresh = await getYoutubeUploadSchedule().catch(() => null);
      if (fresh) setSchedule(fresh);
    } catch (e) {
      setOauthFeedback({
        ok: false,
        message: e instanceof Error ? e.message : String(e),
      });
    } finally {
      setOauthTesting(false);
    }
  }

  async function handleResetBreaker() {
    setOauthResetting(true);
    try {
      await resetYoutubeOAuthCircuitBreaker();
      const fresh = await getYoutubeUploadSchedule().catch(() => null);
      if (fresh) setSchedule(fresh);
      setOauthFeedback({
        ok: true,
        message: 'Circuit breaker reset. Next scheduled slot will try uploading again.',
      });
    } catch (e) {
      setOauthFeedback({
        ok: false,
        message: e instanceof Error ? e.message : String(e),
      });
    } finally {
      setOauthResetting(false);
    }
  }

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
      {schedule && !schedule.enabled && <LegacyPointerBar />}
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

      {/* OAuth circuit-breaker banner. Trips after N consecutive token-
          exchange failures so the scheduler stops re-attempting the
          same broken upload every slot. Surfaces the actual Google
          remediation message (not the unhelpful 'Bad Request') and
          gives the operator a Test + Reset workflow inline. */}
      {schedule?.oauth_circuit_breaker?.open && (
        <div className="mb-3 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800">
          <div className="font-semibold mb-1">
            ⚠ Upload schedule paused — YouTube OAuth is broken
          </div>
          <div className="mb-2">
            {schedule.oauth_circuit_breaker.consecutive_failures} consecutive token-exchange failures.
            All upcoming slots are skipping uploads until this is fixed.
          </div>
          {schedule.oauth_circuit_breaker.last_failure && (
            <div className="mb-2 px-3 py-2 bg-white border border-red-200 rounded text-xs font-mono text-red-700 whitespace-pre-wrap">
              {schedule.oauth_circuit_breaker.last_failure}
            </div>
          )}
          <div className="mb-3 text-xs text-red-700">
            After fixing credentials at{' '}
            <a href="/admin/settings" className="underline font-medium">Admin Settings → YouTube</a>,
            click <em>Test OAuth</em> below. A successful test auto-clears
            the breaker; or click <em>Reset breaker</em> to clear it manually.
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleTestOauth}
              disabled={oauthTesting}
              className="px-3 py-1.5 text-xs rounded-md bg-stone-800 text-white hover:bg-stone-700 disabled:opacity-50"
            >
              {oauthTesting ? 'Testing…' : 'Test OAuth'}
            </button>
            <button
              onClick={handleResetBreaker}
              disabled={oauthResetting}
              className="px-3 py-1.5 text-xs rounded-md border border-red-400 text-red-700 hover:bg-red-100 disabled:opacity-50"
            >
              {oauthResetting ? 'Resetting…' : 'Reset breaker'}
            </button>
          </div>
        </div>
      )}

      {oauthFeedback && (
        <div
          className={`mb-3 rounded-lg border px-3 py-2 text-sm ${
            oauthFeedback.ok
              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
              : 'border-red-200 bg-red-50 text-red-700'
          }`}
        >
          {oauthFeedback.ok ? '✓ ' : '✗ '}
          {oauthFeedback.message}
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
                  <th className="text-left px-3 py-2 font-medium">Title</th>
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
                    <td className="px-3 py-2 text-xs text-stone-700 max-w-[280px] truncate" title={r.video_title || ''}>
                      {r.video_title || <span className="text-stone-300">—</span>}
                    </td>
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

function LegacySystemsPanel({
  refreshKey = 0, onTabChange,
}: { refreshKey?: number; onTabChange: (t: TabKey) => void }) {
  const [creds, setCreds] = useState<{ ok: boolean; tokenAgeDays?: number } | null>(null);
  const [pipelineCount, setPipelineCount] = useState<{
    enabledWithTimes: number;
    enabledNoTimes: number;
    total: number;
  } | null>(null);
  const [upload, setUpload] = useState<YoutubeUploadSchedule | null>(null);
  const [open, setOpen] = useState<boolean>(() => {
    try { return localStorage.getItem('scheduler.legacyPanelOpen') === '1'; }
    catch { return false; }
  });
  function toggleOpen() {
    setOpen((o) => {
      try { localStorage.setItem('scheduler.legacyPanelOpen', o ? '0' : '1'); }
      catch { /* private mode */ }
      return !o;
    });
  }

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
      label: 'Generation schedules (legacy)',
      state: 'bad',
      detail: `${pipelineCount.total} pipeline(s) exist but none are scheduled — no videos will be generated.`,
      fixHref: '/admin/pipelines',
      fixLabel: 'Schedule',
    });
  } else if (pipelineCount.enabledNoTimes > 0) {
    cells.push({
      label: 'Generation schedules (legacy)',
      state: 'warn',
      detail: `${pipelineCount.enabledNoTimes} schedule(s) enabled but missing times — they'll never fire.`,
    });
  } else {
    cells.push({
      label: 'Generation schedules (legacy)',
      state: 'ok',
      detail: `${pipelineCount.enabledWithTimes} schedule(s) firing.`,
    });
  }

  // 3. YouTube upload schedule (drains the legacy queue → publishes)
  if (!upload.enabled) {
    cells.push({
      label: 'Upload-slot drainer (legacy)',
      state: 'warn',
      detail: 'Disabled — legacy generated videos would queue up without publishing.',
    });
  } else if (upload.times.length === 0) {
    cells.push({
      label: 'Upload-slot drainer (legacy)',
      state: 'bad',
      detail: 'Enabled but no times set — nothing will publish.',
    });
  } else {
    cells.push({
      label: 'Upload-slot drainer (legacy)',
      state: 'ok',
      detail: `${upload.times.length} slot${upload.times.length === 1 ? '' : 's'}/day, privacy: ${upload.privacy}.`,
    });
  }

  // The legacy family counts as ACTIVE when anything in it is switched
  // on. Demotion is data-driven: the panel collapses only while all of
  // it is off, and re-expands by itself the moment something is enabled.
  const active =
    pipelineCount.enabledWithTimes + pipelineCount.enabledNoTimes > 0 ||
    upload.enabled;
  const effectiveOpen = open || active;
  const enabledCount = pipelineCount.enabledWithTimes + pipelineCount.enabledNoTimes;

  return (
    <section className="rounded-xl border border-stone-200 bg-white overflow-hidden">
      <button
        type="button"
        onClick={toggleOpen}
        disabled={active}
        aria-expanded={effectiveOpen}
        className={`w-full flex items-center gap-2 px-5 py-3.5 text-left bg-stone-50 ${active ? '' : 'cursor-pointer hover:bg-stone-100'}`}
      >
        <svg
          className={`w-3.5 h-3.5 text-stone-400 shrink-0 transition-transform ${effectiveOpen ? 'rotate-90' : ''}`}
          viewBox="0 0 20 20" fill="currentColor" aria-hidden
        >
          <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
        </svg>
        <span className="text-sm font-semibold text-stone-700">Legacy pipelines</span>
        <span className={`text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded ${
          active ? 'bg-emerald-50 text-emerald-700' : 'bg-stone-200 text-stone-600'
        }`}>
          {active ? 'ACTIVE' : 'PAUSED'}
        </span>
        <span className="text-xs text-stone-500 truncate">
          recitation &amp; educational generation, upload-slot drainer
          · {enabledCount} of {pipelineCount.total} schedules enabled
          · drainer {upload.enabled ? 'on' : 'off'}
        </span>
      </button>

      {effectiveOpen && (
        <div className="px-5 pb-5 pt-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {cells.map((c, i) => (
              <HealthCellView key={i} cell={c} />
            ))}
          </div>
          <p className="mt-3 text-[11px] text-stone-400">
            Manage in the{' '}
            <button type="button" onClick={() => onTabChange('youtube')} className="underline decoration-dotted underline-offset-2 cursor-pointer hover:text-stone-600">YouTube</button>,{' '}
            <button type="button" onClick={() => onTabChange('recitation')} className="underline decoration-dotted underline-offset-2 cursor-pointer hover:text-stone-600">Recitation</button> and{' '}
            <button type="button" onClick={() => onTabChange('educational')} className="underline decoration-dotted underline-offset-2 cursor-pointer hover:text-stone-600">Educational</button> tabs above.
          </p>
        </div>
      )}
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
