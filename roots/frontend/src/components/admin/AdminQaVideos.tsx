import { useCallback, useEffect, useRef, useState } from 'react';
import {
  getQaVideos, renderQaVideo, approveQaVideo, rejectQaVideo,
  saveQaPublishSchedule, fetchQaVideoObjectUrl, editQaVideoScript,
  type QaVideoItem, type QaPublishSchedule, type QaVideoBeat,
} from '../../api/admin';

const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

const STATUS_STYLE: Record<string, string> = {
  gate_passed: 'bg-sky-100 text-sky-700',
  approved: 'bg-emerald-100 text-emerald-700',
  uploaded: 'bg-emerald-600 text-white',
  rejected: 'bg-stone-200 text-stone-500',
};

/**
 * Script-first review queue. Gate-passed SCRIPTS arrive here for reading;
 * the reviewer edits inline (every edit is re-validated by the fail-closed
 * gates server-side), then approves the script. Approved scripts render
 * automatically at publish time (Mon/Wed/Fri slots) and upload — or the
 * reviewer can render a preview manually at any point.
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

  // Poll while anything is rendering so cards update without a reload.
  useEffect(() => {
    const anyRendering = videos.some((v) => v.rendering === 1);
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

  async function act(id: number, fn: () => Promise<unknown>) {
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
          Read the script, edit inline if needed (every edit re-runs the
          gates), approve — approved scripts render and publish themselves
          on schedule.
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
        <div className="whitespace-pre-line rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
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
            <ScriptCard key={v.id} video={v} busy={busyId === v.id} onAct={act} />
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
            At {schedule.time} UTC on selected days: renders the oldest{' '}
            <span className="font-medium text-emerald-600">approved</span> script
            automatically, then uploads it. Nothing unapproved ever publishes.
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

const BEAT_ACCENT: Record<string, string> = {
  hook: 'bg-amber-100 text-amber-700',
  set: 'bg-sky-100 text-sky-700',
  turn: 'bg-violet-100 text-violet-700',
  land: 'bg-emerald-100 text-emerald-700',
};

function ScriptCard({
  video,
  busy,
  onAct,
}: {
  video: QaVideoItem;
  busy: boolean;
  onAct: (id: number, fn: () => Promise<unknown>) => Promise<void>;
}) {
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [loadingVideo, setLoadingVideo] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draftTitle, setDraftTitle] = useState(video.title);
  const [draftBeats, setDraftBeats] = useState<QaVideoBeat[]>(video.beats);

  // Reset drafts when the row refreshes from the server.
  useEffect(() => {
    if (!editing) {
      setDraftTitle(video.title);
      setDraftBeats(video.beats);
    }
  }, [video, editing]);

  useEffect(() => () => { if (videoUrl) URL.revokeObjectURL(videoUrl); }, [videoUrl]);

  async function loadPlayer() {
    setLoadingVideo(true);
    try {
      setVideoUrl(await fetchQaVideoObjectUrl(video.id));
    } finally {
      setLoadingVideo(false);
    }
  }

  const reviewable = video.status === 'gate_passed';
  const isRendering = video.rendering === 1;

  return (
    <li className="rounded-xl border border-stone-200 bg-white p-4">
      {/* header row */}
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${STATUS_STYLE[video.status] || 'bg-stone-100'}`}>
              {video.status}
            </span>
            {isRendering && (
              <span className="animate-pulse rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-medium text-amber-700">
                rendering…
              </span>
            )}
            <span className="text-[11px] text-stone-400">#{video.id} · {video.anchor_ref} · qa {video.qa_id}</span>
            <span className="text-[11px] text-emerald-600">gates ✓</span>
            {video.filename && !isRendering && (
              <span className="text-[11px] text-stone-400">preview rendered</span>
            )}
          </div>
          {editing ? (
            <input
              value={draftTitle}
              onChange={(e) => setDraftTitle(e.target.value)}
              className="mt-1 w-full rounded-md border border-sky-300 px-2 py-1 text-[15px] font-semibold text-stone-800 outline-none focus:ring-1 focus:ring-sky-400"
            />
          ) : (
            <h3 className="mt-1 text-[15px] font-semibold text-stone-800">{video.title}</h3>
          )}
          {video.error_message && (
            <p className="mt-1 text-xs text-rose-600">{video.error_message}</p>
          )}
        </div>

        {/* actions */}
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          {reviewable && !editing && (
            <>
              <ActionBtn label="Approve" busy={busy} onClick={() => onAct(video.id, () => approveQaVideo(video.id))} accent="emerald" />
              <ActionBtn label="Reject" busy={busy} onClick={() => onAct(video.id, () => rejectQaVideo(video.id))} accent="rose" />
            </>
          )}
          {video.status === 'approved' && (
            <>
              <span className="text-xs text-emerald-600">
                {video.filename ? 'publishes next slot' : 'renders + publishes next slot'}
              </span>
              <ActionBtn label="Unapprove" busy={busy} onClick={() => onAct(video.id, () => rejectQaVideo(video.id, 'pulled from queue'))} accent="rose" />
            </>
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

      {/* THE SCRIPT — front and center, inline-editable */}
      {video.status !== 'uploaded' && (
        <div className="mt-3 rounded-lg bg-stone-50 p-3">
          <ol className="space-y-2">
            {(editing ? draftBeats : video.beats).map((b, i) => (
              <li key={i} className="flex gap-2 text-sm">
                <span className={`mt-0.5 h-fit shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase ${BEAT_ACCENT[b.kind] || 'bg-stone-200 text-stone-500'}`}>
                  {b.kind}
                </span>
                <div className="min-w-0 flex-1">
                  {editing ? (
                    <textarea
                      value={b.narration}
                      onChange={(e) => {
                        const next = draftBeats.map((x, xi) =>
                          xi === i ? { ...x, narration: e.target.value } : x);
                        setDraftBeats(next);
                      }}
                      rows={2}
                      className="w-full resize-y rounded-md border border-sky-300 px-2 py-1 text-sm text-stone-700 outline-none focus:ring-1 focus:ring-sky-400"
                    />
                  ) : (
                    <p className="text-stone-700">{b.narration}</p>
                  )}
                  {b.verse && (
                    <p className="mt-0.5 text-[11px] text-stone-400">
                      {b.verse.ref}
                      {b.verse.highlight_words_ar && (
                        <span lang="ar" dir="rtl" className="mx-1 font-arabic text-[13px] text-stone-500">
                          {b.verse.highlight_words_ar.join(' ')}
                        </span>
                      )}
                      {b.verse.highlight_phrase_en && <span>· “{b.verse.highlight_phrase_en}”</span>}
                      <span className="ml-1 text-stone-300">(highlights are gate-locked)</span>
                    </p>
                  )}
                </div>
              </li>
            ))}
          </ol>

          {/* edit controls */}
          {(video.status === 'gate_passed' || video.status === 'approved' || video.status === 'rejected') && (
            <div className="mt-3 flex items-center gap-2">
              {editing ? (
                <>
                  <ActionBtn
                    label="Save (re-runs gates)"
                    busy={busy}
                    accent="sky"
                    onClick={() => onAct(video.id, async () => {
                      await editQaVideoScript(video.id, { title: draftTitle, beats: draftBeats });
                      setEditing(false);
                    })}
                  />
                  <button
                    onClick={() => { setEditing(false); setDraftTitle(video.title); setDraftBeats(video.beats); }}
                    className="text-xs text-stone-400 hover:text-stone-600"
                  >
                    cancel
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setEditing(true)}
                  disabled={isRendering}
                  className="text-xs font-medium text-sky-600 hover:text-sky-800 disabled:opacity-40"
                >
                  ✎ Edit script
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {/* optional preview render / player */}
      <div className="mt-3 flex flex-wrap items-center gap-3 text-xs">
        {(video.status === 'gate_passed' || video.status === 'approved') && !video.filename && !isRendering && (
          <button
            onClick={() => onAct(video.id, () => renderQaVideo(video.id))}
            disabled={busy}
            className="text-stone-400 hover:text-stone-600 disabled:opacity-40"
          >
            render preview (optional)
          </button>
        )}
        {video.filename && !videoUrl && !isRendering && (
          <button
            onClick={loadPlayer}
            disabled={loadingVideo}
            className="rounded-md bg-stone-800 px-3 py-1.5 font-medium text-white transition-colors hover:bg-stone-700 disabled:opacity-50"
          >
            {loadingVideo ? 'Loading…' : '▶ Watch preview'}
          </button>
        )}
        {video.file_size != null && video.file_size > 0 && (
          <span className="text-stone-300">{(video.file_size / 1024 / 1024).toFixed(1)} MB</span>
        )}
      </div>

      {videoUrl && (
        <div className="mt-3">
          <video src={videoUrl} controls className="max-h-[480px] rounded-lg border border-stone-200" />
        </div>
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
