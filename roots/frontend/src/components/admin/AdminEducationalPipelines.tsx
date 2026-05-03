import { useEffect, useMemo, useState } from 'react';
import {
  getEducationalPipelines,
  getEducationalPipeline,
  createEducationalPipeline,
  updateEducationalPipeline,
  deleteEducationalPipeline,
  deleteEducationalVideo,
  uploadEducationalVideoToYouTube,
  retryEducationalPlaylistAdd,
  getEducationalYouTubeStats,
  uploadEducationalOutroAudio,
  deleteEducationalOutroAudio,
  educationalOutroAudioUrl,
  runEducationalPipeline,
  getVoices,
  type EducationalPipeline,
  type EducationalPipelineDetail,
  type EducationalPipelineInput,
  type EducationalType,
  type Voice,
  type EducationalVideo,
} from '../../api/admin';
import { useConfirm } from './shared/useConfirm';

/**
 * Educational Pipeline manager — equivalent to the recitation
 * PipelineManager but for the three educational sub-types
 * (word_origins / translation_hides / grammar_insights).
 *
 * Layout matches the recitation pipeline UX:
 *   - Left column: list of saved pipelines (one per type)
 *   - Right column: detail / form for the selected pipeline
 *   - Each pipeline gets a "Run now" button + a list of the
 *     videos it has produced (status + open mp4 link)
 *
 * Scheduling lives in a later phase; this page is the manual
 * authoring + per-pipeline run-once UI.
 */

const TYPE_LABEL: Record<EducationalType, string> = {
  word_origins: 'Word Origins',
  translation_hides: 'What Translators Hide',
  grammar_insights: 'Grammar Insights',
};

const FORMAT_LABEL: Record<'short' | 'long', string> = {
  short: 'Short Form (≤55s)',
  long: 'Long Form (~2 min)',
};

export default function AdminEducationalPipelines() {
  const [pipelines, setPipelines] = useState<EducationalPipeline[] | null>(null);
  const [voices, setVoices] = useState<Voice[]>([]);
  const [selectedId, setSelectedId] = useState<number | 'new' | null>(null);
  const [bumpKey, setBumpKey] = useState(0);
  const [err, setErr] = useState('');

  useEffect(() => {
    getEducationalPipelines().then(setPipelines).catch((e) => setErr(String(e)));
    getVoices().then(setVoices).catch(() => setVoices([]));
  }, [bumpKey]);

  return (
    <div>
      <h1 className="text-xl font-semibold text-stone-800 mb-2">Educational Pipelines</h1>
      <p className="text-sm text-stone-500 mb-6 max-w-3xl">
        Configure an automated pipeline per series. A pipeline picks the next
        unused candidate, generates a script via Claude, and renders a video
        with your chosen voice and format. Run on demand here or, when
        scheduling lands, on a recurring time.
      </p>

      {err && (
        <div className="mb-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          {err}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-6">
        <PipelineList
          pipelines={pipelines}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />
        <div className="min-w-0">
          {selectedId === 'new' ? (
            <PipelineEditor
              voices={voices}
              initial={null}
              onSaved={(p) => {
                setBumpKey((k) => k + 1);
                setSelectedId(p.id);
              }}
              onCancel={() => setSelectedId(null)}
            />
          ) : selectedId ? (
            <PipelineDetailView
              pipelineId={selectedId}
              voices={voices}
              onChanged={() => setBumpKey((k) => k + 1)}
              onDeleted={() => {
                setSelectedId(null);
                setBumpKey((k) => k + 1);
              }}
            />
          ) : (
            <EmptyHint />
          )}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Left rail — list of pipelines                                     */
/* ------------------------------------------------------------------ */

function PipelineList({
  pipelines,
  selectedId,
  onSelect,
}: {
  pipelines: EducationalPipeline[] | null;
  selectedId: number | 'new' | null;
  onSelect: (id: number | 'new') => void;
}) {
  return (
    <div>
      <button
        onClick={() => onSelect('new')}
        className={`w-full mb-3 px-3 py-2 rounded-lg text-sm font-medium border transition-colors cursor-pointer ${
          selectedId === 'new'
            ? 'bg-stone-800 text-white border-stone-800'
            : 'bg-white text-stone-700 border-stone-300 hover:border-stone-400'
        }`}
      >
        + New pipeline
      </button>

      {pipelines === null ? (
        <div className="text-sm text-stone-400">Loading…</div>
      ) : pipelines.length === 0 ? (
        <div className="text-sm text-stone-400 px-2">No pipelines yet.</div>
      ) : (
        <ul className="space-y-1">
          {pipelines.map((p) => (
            <li key={p.id}>
              <button
                onClick={() => onSelect(p.id)}
                className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors cursor-pointer ${
                  selectedId === p.id
                    ? 'bg-white border border-stone-800'
                    : 'bg-white border border-stone-200 hover:border-stone-400'
                }`}
              >
                <div className="font-medium text-stone-800 truncate">{p.name}</div>
                <div className="text-[11px] text-stone-500 mt-0.5">
                  {TYPE_LABEL[p.type]} · {p.format === 'short' ? 'Short' : 'Long'}
                  {!p.enabled && <span className="ml-1 text-amber-600">· disabled</span>}
                </div>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function EmptyHint() {
  return (
    <div className="rounded-lg border border-dashed border-stone-300 bg-stone-50/40 p-8 text-sm text-stone-500">
      <p className="mb-2 font-medium text-stone-700">Pick a pipeline or create one.</p>
      <p>
        A pipeline bundles a series choice (Word Origins, Translation Hides,
        Grammar Insights), a voice, and a format together so you can
        generate consistent content without re-entering settings.
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Detail view — read-only summary + Run-now + edit toggle           */
/* ------------------------------------------------------------------ */

function PipelineDetailView({
  pipelineId,
  voices,
  onChanged,
  onDeleted,
}: {
  pipelineId: number;
  voices: Voice[];
  onChanged: () => void;
  onDeleted: () => void;
}) {
  const [detail, setDetail] = useState<EducationalPipelineDetail | null>(null);
  const [editing, setEditing] = useState(false);
  const [running, setRunning] = useState(false);
  const [err, setErr] = useState('');
  const [reloadKey, setReloadKey] = useState(0);
  const { confirm, dialog } = useConfirm();

  useEffect(() => {
    let cancelled = false;
    setDetail(null);
    setErr('');
    getEducationalPipeline(pipelineId)
      .then((d) => { if (!cancelled) setDetail(d); })
      .catch((e) => { if (!cancelled) setErr(String(e)); });
    return () => { cancelled = true; };
  }, [pipelineId, reloadKey]);

  // Auto-poll while any video from this pipeline is in motion
  // (candidate / script_ready when we want to see the next status flip).
  const hasInFlight = useMemo(
    () => !!detail?.videos.some((v) =>
      v.status === 'candidate' || v.status === 'rendering' || v.status === 'script_ready'
    ),
    [detail],
  );
  useEffect(() => {
    if (!hasInFlight) return;
    const t = setInterval(() => setReloadKey((k) => k + 1), 4000);
    return () => clearInterval(t);
  }, [hasInFlight]);

  if (err) {
    return <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{err}</div>;
  }
  if (!detail) return <div className="text-sm text-stone-400">Loading…</div>;

  if (editing) {
    return (
      <PipelineEditor
        voices={voices}
        initial={detail}
        onSaved={() => {
          setEditing(false);
          setReloadKey((k) => k + 1);
          onChanged();
        }}
        onCancel={() => setEditing(false)}
      />
    );
  }

  async function handleRun() {
    setRunning(true);
    setErr('');
    try {
      await runEducationalPipeline(pipelineId);
      setReloadKey((k) => k + 1);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }

  async function handleDelete() {
    const ok = await confirm({
      title: 'Delete pipeline?',
      message: `Remove the "${detail!.name}" pipeline? Videos already produced are kept; only the pipeline configuration is deleted.`,
      confirmLabel: 'Delete',
      tone: 'danger',
    });
    if (!ok) return;
    try {
      await deleteEducationalPipeline(pipelineId);
      onDeleted();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  // Delete a single produced video (mp4 + DB row). Uses the same
  // useConfirm dialog instance the pipeline-delete uses, so there's
  // only one Confirm overlay rendered for the whole panel.
  async function handleDeleteVideo(v: EducationalVideo) {
    const label = `Quran ${v.chapter}:${v.verse}`
      + (v.format ? ` (${v.format})` : '');
    const ok = await confirm({
      title: 'Delete this video?',
      message: `Remove ${label}? The mp4 file and all its metadata are deleted permanently. This cannot be undone.`,
      confirmLabel: 'Delete',
      tone: 'danger',
    });
    if (!ok) return;
    try {
      await deleteEducationalVideo(v.id);
      setReloadKey((k) => k + 1);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  const voiceName = voices.find((v) => v.voice_id === detail.voice_id)?.name;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-baseline gap-2">
            <h2 className="text-lg font-semibold text-stone-800">{detail.name}</h2>
            {!detail.enabled && (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-amber-100 text-amber-700">
                Disabled
              </span>
            )}
          </div>
          <p className="text-sm text-stone-500 mt-0.5">
            {TYPE_LABEL[detail.type]} · {FORMAT_LABEL[detail.format]}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={handleRun}
            disabled={running || !detail.enabled}
            className="px-3 py-1.5 rounded-md bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 disabled:opacity-50 cursor-pointer"
            title={!detail.enabled ? 'Enable the pipeline to run it' : 'Pick a candidate and generate a video'}
          >
            {running ? 'Starting…' : 'Run now'}
          </button>
          <button
            onClick={() => setEditing(true)}
            className="px-3 py-1.5 rounded-md border border-stone-300 text-stone-700 text-sm font-medium hover:bg-stone-50 cursor-pointer"
          >
            Edit
          </button>
          <button
            onClick={handleDelete}
            className="px-3 py-1.5 rounded-md border border-red-300 text-red-700 text-sm font-medium hover:bg-red-50 cursor-pointer"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Config summary — music omitted because the renderer doesn't
          consume it yet; it'll come back when render-layer music
          overlay lands. */}
      <div className="rounded-lg border border-stone-200 bg-white p-4 grid grid-cols-3 gap-3 text-sm">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-stone-400 mb-0.5">Voice</div>
          <div className="text-stone-700">{voiceName || <span className="font-mono text-stone-400">{detail.voice_id}</span>}</div>
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-wider text-stone-400 mb-0.5">Format</div>
          <div className="text-stone-700">{FORMAT_LABEL[detail.format]}</div>
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-wider text-stone-400 mb-0.5">Background dim</div>
          <div className="text-stone-700">{detail.show_dim_background ? 'On' : 'Off'}</div>
        </div>
      </div>

      {/* Outro audio — optional sound bite played over the al-nuqta
          splash card at the end of every video this pipeline produces. */}
      <OutroAudioPanel
        pipelineId={pipelineId}
        currentFilename={detail.outro_audio_filename ?? null}
        onChanged={() => setReloadKey((k) => k + 1)}
      />

      {/* Schedule moved to /admin/scheduler so recitation + educational
          schedules live in one place. Keep a quiet pointer here so
          operators editing this pipeline find the new location. */}
      <div className="rounded-lg border border-stone-200 bg-stone-50 px-4 py-3 text-sm text-stone-600 flex items-center justify-between gap-3 flex-wrap">
        <span>
          <strong className="text-stone-700">Schedule:</strong> firing times,
          daily cap, and grace window are managed in{' '}
          <a href="/admin/scheduler#educational" className="underline decoration-dotted underline-offset-2 hover:text-stone-800">
            Scheduler → Educational
          </a>
          {' '}alongside recitation pipelines and the YouTube upload schedule.
        </span>
        <a
          href="/admin/scheduler#educational"
          className="px-3 py-1.5 rounded-md border border-stone-300 bg-white text-stone-700 text-xs font-medium hover:bg-stone-100"
        >
          Open Scheduler →
        </a>
      </div>

      {/* Videos produced */}
      <div>
        <div className="flex items-baseline justify-between mb-3">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-stone-400">
            Videos from this pipeline
          </h3>
          <span className="text-xs text-stone-400">{detail.videos.length}</span>
        </div>
        {detail.videos.length === 0 ? (
          <div className="rounded-lg border border-dashed border-stone-300 bg-stone-50/40 p-6 text-sm text-stone-500 text-center">
            None yet — click <strong>Run now</strong> to generate the first one.
          </div>
        ) : (
          <div className="border border-stone-200 rounded-lg overflow-hidden bg-white">
            {detail.videos.map((v) => (
              <PipelineVideoRow
                key={v.id}
                video={v}
                onDelete={() => handleDeleteVideo(v)}
                onUploaded={() => setReloadKey((k) => k + 1)}
              />
            ))}
          </div>
        )}
      </div>

      {dialog}
    </div>
  );
}

function PipelineVideoRow({
  video: v,
  onDelete,
  onUploaded,
}: {
  video: EducationalVideo;
  onDelete: () => void;
  onUploaded: () => void;
}) {
  const tone = statusTone(v.status);
  const [expanded, setExpanded] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadErr, setUploadErr] = useState('');
  // Playlist outcome from the most recent upload or retry. ok=null
  // means we haven't attempted yet (don't render anything).
  const [playlistResult, setPlaylistResult] = useState<{
    ok: boolean | null;
    message: string;
  }>({ ok: null, message: '' });
  const [retryingPlaylist, setRetryingPlaylist] = useState(false);
  // Live YouTube stats fetched on demand. null = never fetched.
  const [stats, setStats] = useState<{
    views: number; likes: number; comments: number;
  } | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);
  const [statsErr, setStatsErr] = useState('');
  const hasMeta = !!(v.youtube_title || v.youtube_description);
  // 'rendering' rows are blocked server-side from deletion to avoid
  // yanking a file out from under ffmpeg; reflect that in the button.
  const cannotDelete = v.status === 'rendering';
  const isUploaded = !!v.youtube_video_id;
  const canUpload = v.status === 'rendered' && !!v.filename && !isUploaded;

  async function handleUpload() {
    setUploading(true);
    setUploadErr('');
    setPlaylistResult({ ok: null, message: '' });
    try {
      const r = await uploadEducationalVideoToYouTube(v.id);
      // Surface the playlist outcome — the upload publishes the
      // video regardless, but the operator needs to know whether
      // the playlist add landed.
      if (r.playlist_note) {
        const ok = /added/i.test(r.playlist_note);
        setPlaylistResult({ ok, message: r.playlist_note });
      } else {
        // No playlist configured for this series; flag it so the
        // operator knows nothing was attempted.
        setPlaylistResult({
          ok: false,
          message: "No playlist configured for this series — set one in "
            + "Admin → Settings → YouTube Playlists, then click Retry playlist.",
        });
      }
      onUploaded();
    } catch (e) {
      setUploadErr(e instanceof Error ? e.message : String(e));
    } finally {
      setUploading(false);
    }
  }

  async function handleRetryPlaylist() {
    setRetryingPlaylist(true);
    try {
      const r = await retryEducationalPlaylistAdd(v.id);
      setPlaylistResult({ ok: r.ok, message: r.message });
    } catch (e) {
      setPlaylistResult({
        ok: false,
        message: e instanceof Error ? e.message : String(e),
      });
    } finally {
      setRetryingPlaylist(false);
    }
  }

  async function handleFetchStats() {
    setStatsLoading(true);
    setStatsErr('');
    try {
      const r = await getEducationalYouTubeStats(v.id);
      setStats({ views: r.views, likes: r.likes, comments: r.comments });
    } catch (e) {
      setStatsErr(e instanceof Error ? e.message : String(e));
    } finally {
      setStatsLoading(false);
    }
  }
  let parsedTags: string[] = [];
  try {
    parsedTags = v.youtube_tags ? (JSON.parse(v.youtube_tags) as string[]) : [];
  } catch {
    parsedTags = [];
  }
  return (
    <div className="border-b border-stone-100 last:border-b-0">
      <div className="px-3 py-2 flex items-center gap-3 text-sm">
        <span className="font-mono text-stone-700 w-20 flex-shrink-0">
          {v.chapter}:{v.verse}
        </span>
        <span className="text-stone-500 font-mono text-xs w-20 flex-shrink-0 truncate">
          {v.format ?? '—'}
        </span>
        <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${tone}`}>
          {v.status}
        </span>
        <span className="flex-1 text-stone-400 text-xs truncate">
          {v.error_message || formatDate(v.created_at)}
        </span>
        {hasMeta && (
          <button
            onClick={() => setExpanded((e) => !e)}
            className="px-2 py-0.5 rounded text-xs text-stone-500 hover:text-stone-800 cursor-pointer"
          >
            {expanded ? 'Hide YT' : 'Show YT'}
          </button>
        )}
        {v.filename && (v.status === 'rendered' || v.status === 'uploaded') && (
          <a
            href={`/api/admin/educational/${v.id}/video?token=${encodeURIComponent(localStorage.getItem('admin_token') || '')}`}
            target="_blank"
            rel="noopener noreferrer"
            className="px-2.5 py-1 rounded-md border border-emerald-300 text-emerald-700 text-xs font-medium hover:bg-emerald-50 cursor-pointer"
          >
            Open mp4
          </a>
        )}
        {isUploaded && v.youtube_video_id && (
          <a
            href={`https://youtube.com/watch?v=${v.youtube_video_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="px-2.5 py-1 rounded-md border border-red-400 text-red-700 text-xs font-medium hover:bg-red-50 cursor-pointer"
            title="Open this video on YouTube"
          >
            On YouTube ↗
          </a>
        )}
        {isUploaded && (
          <button
            onClick={handleFetchStats}
            disabled={statsLoading}
            className="px-2.5 py-1 rounded-md border border-stone-300 text-stone-700 text-xs font-medium hover:bg-stone-50 disabled:opacity-60 cursor-pointer"
            title="Fetch live view/like/comment counts from YouTube Data API."
          >
            {statsLoading ? 'Loading…' : stats ? 'Refresh stats' : 'Stats'}
          </button>
        )}
        {canUpload && (
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="px-2.5 py-1 rounded-md bg-red-600 text-white text-xs font-medium hover:bg-red-700 disabled:opacity-60 cursor-pointer"
            title="Upload this video to YouTube and add it to the per-series playlist."
          >
            {uploading ? 'Uploading…' : 'Upload to YouTube'}
          </button>
        )}
        <button
          onClick={onDelete}
          disabled={cannotDelete}
          title={cannotDelete
            ? "Wait for the render to finish or fail before deleting."
            : "Permanently delete this video and its mp4 file."}
          className="px-2.5 py-1 rounded-md border border-red-300 text-red-700 text-xs font-medium hover:bg-red-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
        >
          Delete
        </button>
      </div>
      {uploadErr && (
        <div className="px-3 pb-2 text-xs text-red-700">
          Upload failed: {uploadErr}
        </div>
      )}
      {stats && (
        <div className="px-3 pb-2 text-xs text-stone-600 flex items-center gap-3">
          <span title="Views">👁 {stats.views.toLocaleString()}</span>
          <span title="Likes">👍 {stats.likes.toLocaleString()}</span>
          <span title="Comments">💬 {stats.comments.toLocaleString()}</span>
        </div>
      )}
      {statsErr && (
        <div className="px-3 pb-2 text-xs text-amber-700">
          Stats: {statsErr}
          {/insufficient.*scope|403/i.test(statsErr) && (
            <span className="text-stone-500">
              {' '}— regenerate the YouTube refresh token with the broad{' '}
              <code className="bg-stone-100 px-1 rounded">youtube</code> scope
              (Admin → Settings → YouTube).
            </span>
          )}
        </div>
      )}
      {/* Playlist outcome from the most recent upload OR retry. Stays
          visible (and lets the operator retry) until the row reloads. */}
      {playlistResult.ok !== null && (
        <div
          className={`px-3 pb-2 text-xs flex items-center gap-2 flex-wrap ${
            playlistResult.ok ? 'text-emerald-700' : 'text-amber-700'
          }`}
        >
          <span>{playlistResult.ok ? '✓' : '⚠'} Playlist: {playlistResult.message}</span>
          {!playlistResult.ok && isUploaded && (
            <button
              onClick={handleRetryPlaylist}
              disabled={retryingPlaylist}
              className="px-2 py-0.5 rounded border border-amber-400 text-amber-700 text-xs font-medium hover:bg-amber-50 disabled:opacity-60 cursor-pointer"
              title="Re-read the playlist preference and retry the playlistItems.insert call."
            >
              {retryingPlaylist ? 'Retrying…' : 'Retry playlist'}
            </button>
          )}
        </div>
      )}
      {/* Always-available retry for already-uploaded rows whose
          playlist was set after upload, or whose initial add failed
          and the operator dismissed the inline result. */}
      {isUploaded && playlistResult.ok === null && (
        <div className="px-3 pb-2 text-[11px] text-stone-500">
          <button
            onClick={handleRetryPlaylist}
            disabled={retryingPlaylist}
            className="underline hover:no-underline cursor-pointer disabled:opacity-60"
            title="Add this video to the configured per-series playlist."
          >
            {retryingPlaylist ? 'Adding to playlist…' : 'Add to playlist'}
          </button>
        </div>
      )}
      {expanded && hasMeta && (
        <div className="px-3 pb-3 pt-1 bg-stone-50/50 border-t border-stone-100 space-y-2">
          {v.youtube_title && (
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-wider text-stone-400 mb-0.5">
                Title
              </div>
              <div className="text-sm text-stone-700">{v.youtube_title}</div>
            </div>
          )}
          {v.youtube_description && (
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-wider text-stone-400 mb-0.5">
                Description
              </div>
              <pre className="whitespace-pre-wrap font-sans text-xs text-stone-700 leading-relaxed bg-white border border-stone-200 rounded-md p-2 max-h-64 overflow-auto">
                {v.youtube_description}
              </pre>
            </div>
          )}
          {parsedTags.length > 0 && (
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-wider text-stone-400 mb-0.5">
                Tags
              </div>
              <div className="flex flex-wrap gap-1">
                {parsedTags.map((t, i) => (
                  <span key={i} className="px-2 py-0.5 rounded-full bg-stone-200 text-stone-700 text-[11px]">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function statusTone(s: string): string {
  switch (s) {
    case 'failed': return 'bg-red-100 text-red-700';
    case 'uploaded': return 'bg-green-100 text-green-700';
    case 'rendered': return 'bg-emerald-100 text-emerald-700';
    case 'rendering': return 'bg-amber-100 text-amber-700';
    case 'script_ready': return 'bg-blue-100 text-blue-700';
    default: return 'bg-stone-100 text-stone-600';
  }
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return '';
  try {
    return new Date(iso.includes('T') ? iso : iso + 'Z').toLocaleString();
  } catch {
    return iso;
  }
}

/* ------------------------------------------------------------------ */
/*  Editor (create or update)                                         */
/* ------------------------------------------------------------------ */

function PipelineEditor({
  voices,
  initial,
  onSaved,
  onCancel,
}: {
  voices: Voice[];
  initial: EducationalPipeline | null;
  onSaved: (p: EducationalPipeline) => void;
  onCancel: () => void;
}) {
  const isEdit = !!initial;
  const [name, setName] = useState(initial?.name ?? '');
  const [type, setType] = useState<EducationalType>(initial?.type ?? 'word_origins');
  const [voiceId, setVoiceId] = useState(initial?.voice_id ?? voices[0]?.voice_id ?? '');
  const [format, setFormat] = useState<'short' | 'long'>(initial?.format ?? 'short');
  const [showDim, setShowDim] = useState<boolean>(
    initial ? !!initial.show_dim_background : true,
  );
  // Music isn't editable in the form yet (renderer doesn't consume
  // it). Preserve any existing value from `initial` so an edit-save
  // doesn't accidentally clear it; null for new pipelines.
  const preservedMusicId: number | null = initial?.music_id ?? null;
  const [enabled, setEnabled] = useState<boolean>(initial ? !!initial.enabled : true);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState('');

  // Default to the first voice once voices load if we don't have one
  // (creation path with no voices configured yet handled by guard below).
  useEffect(() => {
    if (!voiceId && voices.length > 0) setVoiceId(voices[0].voice_id);
  }, [voices, voiceId]);

  async function handleSave() {
    setSaving(true);
    setErr('');
    try {
      if (!name.trim()) throw new Error('Name is required');
      if (!voiceId) throw new Error('Pick a voice');
      const input: EducationalPipelineInput = {
        name: name.trim(),
        type,
        voice_id: voiceId,
        format,
        show_dim_background: showDim,
        music_id: preservedMusicId,
        enabled,
      };
      if (isEdit) {
        // type is immutable on update — server enforces this; we
        // also don't expose the type field as editable below.
        const { type: _t, ...patch } = input;
        void _t;
        const updated = await updateEducationalPipeline(initial!.id, patch);
        onSaved(updated);
      } else {
        const created = await createEducationalPipeline(input);
        onSaved(created);
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-5 max-w-xl">
      <h2 className="text-lg font-semibold text-stone-800">
        {isEdit ? `Edit "${initial!.name}"` : 'New pipeline'}
      </h2>

      {err && (
        <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          {err}
        </div>
      )}

      {voices.length === 0 && (
        <div className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
          No ElevenLabs voices configured. Add one in <a href="/admin/settings#elevenlabs" className="underline">Settings → ElevenLabs</a> first.
        </div>
      )}

      <Field label="Name" hint="e.g. Word Origins · Shorts">
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={120}
          className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400"
          placeholder="Word Origins · Shorts"
        />
      </Field>

      <Field label="Series type" hint={isEdit ? 'Immutable on existing pipelines.' : "Which educational series this pipeline produces."}>
        <select
          value={type}
          onChange={(e) => setType(e.target.value as EducationalType)}
          disabled={isEdit}
          className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm bg-white disabled:bg-stone-50 focus:outline-none focus:ring-2 focus:ring-stone-400"
        >
          <option value="word_origins">Word Origins</option>
          <option value="translation_hides">What Translators Hide</option>
          <option value="grammar_insights">Grammar Insights</option>
        </select>
      </Field>

      <Field label="AI voice" hint="ElevenLabs voice used for narration. Manage in Settings.">
        <select
          value={voiceId}
          onChange={(e) => setVoiceId(e.target.value)}
          className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-stone-400"
        >
          {voices.length === 0 && <option value="">(none configured)</option>}
          {voices.map((v) => (
            <option key={v.id} value={v.voice_id}>
              {v.name}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Format">
        <select
          value={format}
          onChange={(e) => setFormat(e.target.value as 'short' | 'long')}
          className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-stone-400"
        >
          <option value="short">Short Form (≤55s · YouTube Shorts / TikTok)</option>
          <option value="long">Long Form (~2 min · regular YouTube)</option>
        </select>
      </Field>

      {/* Background-music wiring isn't in the renderer yet — hide
          the dropdown rather than show a control that does nothing.
          The DB column stays so we don't need a migration when the
          render layer learns to overlay music. */}

      <label className="flex items-center gap-2 text-sm text-stone-700 cursor-pointer">
        <input
          type="checkbox"
          checked={showDim}
          onChange={(e) => setShowDim(e.target.checked)}
          className="h-4 w-4 rounded border-stone-300"
        />
        Show dark dim behind text
        <span className="text-xs text-stone-400 ml-1">— recommended over busy background videos.</span>
      </label>

      <label className="flex items-center gap-2 text-sm text-stone-700 cursor-pointer">
        <input
          type="checkbox"
          checked={enabled}
          onChange={(e) => setEnabled(e.target.checked)}
          className="h-4 w-4 rounded border-stone-300"
        />
        Enabled
        <span className="text-xs text-stone-400 ml-1">— disabled pipelines can't be run or scheduled.</span>
      </label>

      <div className="flex items-center gap-2 pt-2">
        <button
          onClick={handleSave}
          disabled={saving || voices.length === 0}
          className="px-4 py-2 rounded-lg bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 disabled:opacity-50 cursor-pointer"
        >
          {saving ? 'Saving…' : isEdit ? 'Save changes' : 'Create pipeline'}
        </button>
        <button
          onClick={onCancel}
          disabled={saving}
          className="px-3 py-2 rounded-lg text-stone-600 text-sm hover:bg-stone-100 disabled:opacity-50 cursor-pointer"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Outro audio panel — optional sound bite over the splash card      */
/* ------------------------------------------------------------------ */

function OutroAudioPanel({
  pipelineId,
  currentFilename,
  onChanged,
}: {
  pipelineId: number;
  currentFilename: string | null;
  onChanged: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [info, setInfo] = useState<{ size: number; duration: number } | null>(null);

  // Reset transient info when the underlying file changes (parent
  // refresh after upload/delete).
  useEffect(() => { setInfo(null); setErr(''); }, [currentFilename]);

  async function handleUpload(file: File) {
    setBusy(true);
    setErr('');
    try {
      const r = await uploadEducationalOutroAudio(pipelineId, file);
      setInfo({ size: r.size_bytes, duration: r.duration_seconds });
      onChanged();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    setBusy(true);
    setErr('');
    try {
      await deleteEducationalOutroAudio(pipelineId);
      onChanged();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <div className="flex items-baseline justify-between mb-3">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-stone-400">
          Outro audio
        </h3>
        {currentFilename && (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-100 text-emerald-700">
            Set
          </span>
        )}
      </div>

      <div className="rounded-lg border border-stone-200 bg-white p-4 max-w-2xl">
        <p className="text-sm text-stone-500 mb-3">
          Upload a short sound bite (e.g. "More details in the description" — typically 4–5s).
          When set, it plays over the al-nuqta splash at the end of every video. The splash
          window auto-extends so the audio finishes before the video does.
        </p>

        {err && (
          <div className="mb-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">
            {err}
          </div>
        )}

        {currentFilename ? (
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-sm text-stone-700 font-mono truncate max-w-[16rem]">
              {currentFilename}
            </span>
            {info && (
              <span className="text-xs text-stone-500">
                {info.duration.toFixed(1)}s · {Math.round(info.size / 1024)} KB
              </span>
            )}
            <audio
              controls
              preload="metadata"
              src={educationalOutroAudioUrl(pipelineId)}
              className="h-9 max-w-xs"
            />
            <label
              className="px-3 py-1.5 rounded-md border border-stone-300 text-stone-700 text-sm font-medium hover:bg-stone-50 cursor-pointer"
              title="Replace the current audio"
            >
              Replace
              <input
                type="file"
                accept=".mp3,.wav,.m4a,.ogg,.aac,audio/*"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handleUpload(f);
                  e.target.value = '';  // allow re-uploading the same file
                }}
                disabled={busy}
                className="sr-only"
              />
            </label>
            <button
              onClick={handleDelete}
              disabled={busy}
              className="px-3 py-1.5 rounded-md border border-red-300 text-red-700 text-sm font-medium hover:bg-red-50 disabled:opacity-50 cursor-pointer"
            >
              Remove
            </button>
          </div>
        ) : (
          <label
            className="inline-flex items-center px-3 py-1.5 rounded-md bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 cursor-pointer"
          >
            {busy ? 'Uploading…' : 'Upload audio'}
            <input
              type="file"
              accept=".mp3,.wav,.m4a,.ogg,.aac,audio/*"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleUpload(f);
                e.target.value = '';
              }}
              disabled={busy}
              className="sr-only"
            />
          </label>
        )}

        <p className="mt-3 text-[11px] text-stone-400">
          Accepts mp3, wav, m4a, ogg, aac. Max 10 MB or 30 seconds.
        </p>
      </div>
    </section>
  );
}



function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-stone-700 mb-1">{label}</label>
      {children}
      {hint && <p className="mt-1 text-[11px] text-stone-400">{hint}</p>}
    </div>
  );
}
