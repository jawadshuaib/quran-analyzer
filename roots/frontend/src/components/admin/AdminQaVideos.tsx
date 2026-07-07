import { useCallback, useEffect, useRef, useState } from 'react';
import {
  getQaVideos, renderQaVideo, approveQaVideo, rejectQaVideo,
  saveQaPublishSchedule, fetchQaVideoObjectUrl,
  type QaVideoItem, type QaPublishSchedule,
} from '../../api/admin';

const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

const STATUS_STYLE: Record<string, string> = {
  gate_passed: 'bg-sky-100 text-sky-700',
  rendering: 'bg-amber-100 text-amber-700 animate-pulse',
  rendered: 'bg-violet-100 text-violet-700',
  approved: 'bg-emerald-100 text-emerald-700',
  uploaded: 'bg-emerald-600 text-white',
  rejected: 'bg-stone-200 text-stone-500',
};

/**
 * The Q&A video bank review queue: scripts drafted by Claude and validated
 * by the fail-closed gates arrive here as gate_passed. The reviewer renders,
 * WATCHES the video, and approves — only approved videos are ever uploaded,
 * by the Mon/Wed/Fri publish scheduler. This tab never generates content.
 */
export default function AdminQaVideos() {
  const [videos, setVideos] = useState<QaVideoItem[]>([]);
  const [schedule, setSchedule] = useState<QaPublishSchedule | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState<number | null>(null);
  const pollRef = useRef<number | undefined>(undefined);

  const refresh = useCallback(async () => {
    try {
      const data = await getQaVideos();
      setVideos(data.videos);
      setSchedule(data.publish_schedule);
      setError('');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  // Poll while anything is rendering so the row flips to `rendered`
  // without a manual reload.
  useEffect(() => {
    const anyRendering = videos.some((v) => v.status === 'rendering');
    if (anyRendering && pollRef.current === undefined) {
      pollRef.current = window.setInterval(refresh, 5000);
    }
    if (!anyRendering && pollRef.current !== undefined) {
      window.clearInterval(pollRef.current);
      pollRef.current = undefined;
    }
    return () => {
      if (pollRef.current !== undefined) {
        window.clearInterval(pollRef.current);
        pollRef.current = undefined;
      }
    };
  }, [videos, refresh]);

  async function act(id: number, fn: () => Promise<void>) {
    setBusyId(id);
    try {
      await fn();
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Action failed');
    } finally {
      setBusyId(null);
    }
  }

  const counts: Record<string, number> = {};
  for (const v of videos) counts[v.status] = (counts[v.status] || 0) + 1;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-xl font-semibold text-stone-800">Q&amp;A Video Bank</h1>
        <p className="mt-1 text-sm text-stone-500">
          Scripts drafted by Claude, verified by the highlight gates. Render,
          watch, approve — the scheduler uploads only what you approve.
        </p>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          {Object.entries(counts).map(([s, n]) => (
            <span key={s} className={`rounded-full px-2 py-0.5 ${STATUS_STYLE[s] || 'bg-stone-100 text-stone-600'}`}>
              {s}: {n}
            </span>
          ))}
        </div>
      </header>

      {schedule && (
        <ScheduleCard
          schedule={schedule}
          onSave={async (patch) => {
            const next = await saveQaPublishSchedule(patch);
            setSchedule(next);
          }}
        />
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}

      {loading ? (
        <div className="flex justify-center py-10">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-stone-200 border-t-stone-600" />
        </div>
      ) : videos.length === 0 ? (
        <p className="py-10 text-center text-sm text-stone-400">
          No scripts in the bank yet — run /qa-video-draft to fill it.
        </p>
      ) : (
        <ul className="space-y-4">
          {videos.map((v) => (
            <VideoCard key={v.id} video={v} busy={busyId === v.id} onAct={act} />
          ))}
        </ul>
      )}
    </div>
  );
}

function ScheduleCard({
  schedule,
  onSave,
}: {
  schedule: QaPublishSchedule;
  onSave: (patch: Partial<QaPublishSchedule>) => Promise<void>;
}) {
  const [saving, setSaving] = useState(false);

  async function patch(p: Partial<QaPublishSchedule>) {
    setSaving(true);
    try { await onSave(p); } finally { setSaving(false); }
  }

  return (
    <div className="rounded-xl border border-stone-200 bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-stone-700">Publish schedule</h2>
          <p className="text-xs text-stone-400">
            Uploads the oldest <span className="font-medium text-emerald-600">approved</span> video
            at {schedule.time} UTC on the selected days. Nothing unapproved ever uploads.
          </p>
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={schedule.enabled}
          onClick={() => patch({ enabled: !schedule.enabled })}
          disabled={saving}
          className={`relative h-6 w-11 rounded-full transition-colors ${schedule.enabled ? 'bg-emerald-500' : 'bg-stone-300'}`}
        >
          <span className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white transition-transform ${schedule.enabled ? 'translate-x-5' : ''}`} />
        </button>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        {DAY_LABELS.map((label, day) => {
          const on = schedule.days.includes(day);
          return (
            <button
              key={day}
              onClick={() => patch({ days: on ? schedule.days.filter((d) => d !== day) : [...schedule.days, day] })}
              disabled={saving}
              className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
                on ? 'bg-emerald-100 text-emerald-700' : 'bg-stone-100 text-stone-400 hover:text-stone-600'
              }`}
            >
              {label}
            </button>
          );
        })}
        <input
          type="time"
          defaultValue={schedule.time}
          onBlur={(e) => { if (e.target.value && e.target.value !== schedule.time) patch({ time: e.target.value }); }}
          className="rounded-md border border-stone-200 px-2 py-1 text-xs text-stone-600"
        />
        <select
          value={schedule.privacy}
          onChange={(e) => patch({ privacy: e.target.value })}
          disabled={saving}
          className="rounded-md border border-stone-200 px-2 py-1 text-xs text-stone-600"
        >
          <option value="public">public</option>
          <option value="unlisted">unlisted</option>
          <option value="private">private</option>
        </select>
        {schedule.last_fired_date && (
          <span className="text-[11px] text-stone-400">last published: {schedule.last_fired_date}</span>
        )}
      </div>
    </div>
  );
}

function VideoCard({
  video,
  busy,
  onAct,
}: {
  video: QaVideoItem;
  busy: boolean;
  onAct: (id: number, fn: () => Promise<void>) => Promise<void>;
}) {
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [showScript, setShowScript] = useState(false);
  const [loadingVideo, setLoadingVideo] = useState(false);

  // Revoke the blob URL on unmount / replacement.
  useEffect(() => () => { if (videoUrl) URL.revokeObjectURL(videoUrl); }, [videoUrl]);

  async function loadPlayer() {
    setLoadingVideo(true);
    try {
      const url = await fetchQaVideoObjectUrl(video.id);
      setVideoUrl(url);
    } catch {
      /* surfaced via error styling below */
    } finally {
      setLoadingVideo(false);
    }
  }

  const canRender = video.status === 'gate_passed' || video.status === 'rendered';
  const watchable = ['rendered', 'approved', 'uploaded'].includes(video.status) && video.filename;

  return (
    <li className="rounded-xl border border-stone-200 bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${STATUS_STYLE[video.status] || 'bg-stone-100'}`}>
              {video.status}
            </span>
            <span className="text-[11px] text-stone-400">#{video.id} · {video.anchor_ref} · qa {video.qa_id}</span>
            {video.punch_ok === 1 && video.match_ok === 1 && (
              <span className="text-[11px] text-emerald-600">gates ✓</span>
            )}
          </div>
          <h3 className="mt-1 text-[15px] font-semibold text-stone-800">{video.title}</h3>
          {video.error_message && (
            <p className="mt-1 text-xs text-rose-600">{video.error_message}</p>
          )}
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          {video.status === 'gate_passed' && (
            <ActionBtn label="Render" busy={busy} onClick={() => onAct(video.id, () => renderQaVideo(video.id))} accent="sky" />
          )}
          {video.status === 'rendered' && (
            <>
              <ActionBtn label="Approve" busy={busy} onClick={() => onAct(video.id, () => approveQaVideo(video.id))} accent="emerald" />
              <ActionBtn label="Reject" busy={busy} onClick={() => onAct(video.id, () => rejectQaVideo(video.id))} accent="rose" />
            </>
          )}
          {video.status === 'approved' && (
            <>
              <span className="text-xs text-emerald-600">queued for publish</span>
              <ActionBtn label="Unqueue" busy={busy} onClick={() => onAct(video.id, () => rejectQaVideo(video.id, 'pulled from queue'))} accent="rose" />
            </>
          )}
          {video.status === 'rejected' && canRender && (
            <ActionBtn label="Re-render" busy={busy} onClick={() => onAct(video.id, () => renderQaVideo(video.id))} accent="sky" />
          )}
          {video.status === 'uploaded' && video.youtube_video_id && (
            <a
              href={`https://youtu.be/${video.youtube_video_id}`}
              target="_blank" rel="noopener noreferrer"
              className="text-xs font-medium text-emerald-700 hover:underline"
            >
              watch on YouTube ↗
            </a>
          )}
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-3 text-xs">
        {watchable && !videoUrl && (
          <button
            onClick={loadPlayer}
            disabled={loadingVideo}
            className="rounded-md bg-stone-800 px-3 py-1.5 font-medium text-white transition-colors hover:bg-stone-700 disabled:opacity-50"
          >
            {loadingVideo ? 'Loading…' : '▶ Watch'}
          </button>
        )}
        <button onClick={() => setShowScript((s) => !s)} className="text-stone-400 hover:text-stone-600">
          {showScript ? 'hide script' : 'show script'}
        </button>
        {video.file_size != null && video.file_size > 0 && (
          <span className="text-stone-300">{(video.file_size / 1024 / 1024).toFixed(1)} MB</span>
        )}
      </div>

      {videoUrl && (
        <div className="mt-3">
          <video src={videoUrl} controls className="max-h-[480px] rounded-lg border border-stone-200" />
        </div>
      )}

      {showScript && (
        <ol className="mt-3 space-y-2 rounded-lg bg-stone-50 p-3">
          {video.beats.map((b, i) => (
            <li key={i} className="text-sm">
              <span className="mr-2 rounded bg-stone-200 px-1.5 py-0.5 text-[10px] font-medium uppercase text-stone-500">{b.kind}</span>
              <span className="text-stone-700">{b.narration}</span>
              {b.verse && (
                <span className="ml-2 text-[11px] text-stone-400">
                  [{b.verse.ref}{b.verse.highlight_words_ar ? ` → ${b.verse.highlight_words_ar.join(' ')}` : ''}]
                </span>
              )}
            </li>
          ))}
        </ol>
      )}
    </li>
  );
}

function ActionBtn({
  label, busy, onClick, accent,
}: {
  label: string; busy: boolean; onClick: () => void; accent: 'emerald' | 'rose' | 'sky';
}) {
  const styles = {
    emerald: 'bg-emerald-600 hover:bg-emerald-700 text-white',
    rose: 'border border-rose-200 text-rose-600 hover:bg-rose-50',
    sky: 'bg-sky-600 hover:bg-sky-700 text-white',
  };
  return (
    <button
      onClick={onClick}
      disabled={busy}
      className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50 ${styles[accent]}`}
    >
      {busy ? '…' : label}
    </button>
  );
}
