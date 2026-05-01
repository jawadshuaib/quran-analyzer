import { useEffect, useMemo, useState } from 'react';
import {
  getEducationalPipelines,
  getEducationalPipeline,
  createEducationalPipeline,
  updateEducationalPipeline,
  deleteEducationalPipeline,
  runEducationalPipeline,
  getVoices,
  getMusicTracks,
  type EducationalPipeline,
  type EducationalPipelineDetail,
  type EducationalPipelineInput,
  type EducationalType,
  type Voice,
  type MusicTrack,
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
  const [music, setMusic] = useState<MusicTrack[]>([]);
  const [selectedId, setSelectedId] = useState<number | 'new' | null>(null);
  const [bumpKey, setBumpKey] = useState(0);
  const [err, setErr] = useState('');

  useEffect(() => {
    getEducationalPipelines().then(setPipelines).catch((e) => setErr(String(e)));
    getVoices().then(setVoices).catch(() => setVoices([]));
    getMusicTracks().then(setMusic).catch(() => setMusic([]));
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
              music={music}
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
              music={music}
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
  music,
  onChanged,
  onDeleted,
}: {
  pipelineId: number;
  voices: Voice[];
  music: MusicTrack[];
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
        music={music}
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

  const voiceName = voices.find((v) => v.voice_id === detail.voice_id)?.name;
  const musicName = music.find((m) => m.id === detail.music_id)?.original_name;

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

      {/* Config summary */}
      <div className="rounded-lg border border-stone-200 bg-white p-4 grid grid-cols-2 gap-3 text-sm">
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
        <div>
          <div className="text-[10px] uppercase tracking-wider text-stone-400 mb-0.5">Background music</div>
          <div className="text-stone-700">{musicName || <span className="text-stone-400">—</span>}</div>
        </div>
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
              <PipelineVideoRow key={v.id} video={v} />
            ))}
          </div>
        )}
      </div>

      {dialog}
    </div>
  );
}

function PipelineVideoRow({ video: v }: { video: EducationalVideo }) {
  const tone = statusTone(v.status);
  return (
    <div className="border-b border-stone-100 last:border-b-0 px-3 py-2 flex items-center gap-3 text-sm">
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
      {v.filename && v.status === 'rendered' && (
        <a
          href={`/api/admin/educational/${v.id}/video?token=${encodeURIComponent(localStorage.getItem('admin_token') || '')}`}
          target="_blank"
          rel="noopener noreferrer"
          className="px-2.5 py-1 rounded-md border border-emerald-300 text-emerald-700 text-xs font-medium hover:bg-emerald-50 cursor-pointer"
        >
          Open mp4
        </a>
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
  music,
  initial,
  onSaved,
  onCancel,
}: {
  voices: Voice[];
  music: MusicTrack[];
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
  const [musicId, setMusicId] = useState<number | ''>(
    initial?.music_id ?? '',
  );
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
        music_id: musicId === '' ? null : Number(musicId),
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

      <Field label="Background music" hint="Optional ambient track behind the narration.">
        <select
          value={musicId === null ? '' : musicId}
          onChange={(e) => setMusicId(e.target.value === '' ? '' : Number(e.target.value))}
          className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-stone-400"
        >
          <option value="">— None —</option>
          {music.map((m) => (
            <option key={m.id} value={m.id}>
              {m.description || m.original_name}
            </option>
          ))}
        </select>
      </Field>

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
