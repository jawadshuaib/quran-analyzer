import { useEffect, useMemo, useState } from 'react';
import {
  getEducationalPipelines,
  getEducationalPipeline,
  createEducationalPipeline,
  updateEducationalPipeline,
  deleteEducationalPipeline,
  runEducationalPipeline,
  getEducationalSchedule,
  upsertEducationalSchedule,
  getEducationalScheduleRuns,
  getVoices,
  type EducationalPipeline,
  type EducationalPipelineDetail,
  type EducationalPipelineInput,
  type EducationalType,
  type EducationalSchedule,
  type EducationalScheduleRun,
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

      {/* Schedule */}
      <SchedulePanel pipelineId={pipelineId} pipelineEnabled={!!detail.enabled} />

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
  const [expanded, setExpanded] = useState(false);
  const hasMeta = !!(v.youtube_title || v.youtube_description);
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
      </div>
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
/*  Schedule panel — auto-fire times, daily cap, grace, audit log     */
/* ------------------------------------------------------------------ */

const STATUS_TONE: Record<EducationalScheduleRun['status'], string> = {
  fired: 'bg-emerald-100 text-emerald-700',
  skipped_grace: 'bg-stone-100 text-stone-600',
  skipped_cap: 'bg-stone-100 text-stone-600',
  skipped_active: 'bg-amber-100 text-amber-700',
  error: 'bg-red-100 text-red-700',
};

const STATUS_LABEL: Record<EducationalScheduleRun['status'], string> = {
  fired: 'fired',
  skipped_grace: 'past grace',
  skipped_cap: 'cap reached',
  skipped_active: 'busy',
  error: 'error',
};

function SchedulePanel({
  pipelineId,
  pipelineEnabled,
}: {
  pipelineId: number;
  pipelineEnabled: boolean;
}) {
  const [schedule, setSchedule] = useState<EducationalSchedule | null>(null);
  const [runs, setRuns] = useState<EducationalScheduleRun[]>([]);
  const [err, setErr] = useState('');
  const [saving, setSaving] = useState(false);

  // Form state — diverges from server state during edits.
  const [timesText, setTimesText] = useState('');     // chip-builder is overkill; comma-separated input is enough
  const [maxRuns, setMaxRuns] = useState(2);
  const [enabled, setEnabled] = useState(false);
  const [graceMinutes, setGraceMinutes] = useState(30);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      getEducationalSchedule(pipelineId),
      getEducationalScheduleRuns(pipelineId, 25),
    ])
      .then(([s, r]) => {
        if (cancelled) return;
        setSchedule(s);
        setTimesText(s.times.join(', '));
        setMaxRuns(s.max_runs_per_day);
        setEnabled(s.enabled);
        setGraceMinutes(s.grace_minutes);
        setRuns(r);
      })
      .catch((e) => { if (!cancelled) setErr(String(e)); });
    return () => { cancelled = true; };
  }, [pipelineId]);

  async function handleSave() {
    setSaving(true);
    setErr('');
    try {
      const times = timesText
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean);
      const updated = await upsertEducationalSchedule(pipelineId, {
        times,
        max_runs_per_day: Math.max(1, Math.min(24, maxRuns)),
        enabled,
        grace_minutes: Math.max(0, Math.min(240, graceMinutes)),
      });
      setSchedule(updated);
      // Backend canonicalizes (sorted, deduped, HH:MM zero-padded).
      // Sync the input text so subsequent edits diff cleanly.
      setTimesText(updated.times.join(', '));
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  if (!schedule) {
    return (
      <section>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-stone-400 mb-3">
          Schedule
        </h3>
        {err
          ? <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{err}</div>
          : <div className="text-sm text-stone-400">Loading…</div>
        }
      </section>
    );
  }

  return (
    <section>
      <div className="flex items-baseline justify-between mb-3">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-stone-400">
          Schedule
        </h3>
        {schedule.enabled && (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-100 text-emerald-700">
            Auto-firing
          </span>
        )}
      </div>

      {!pipelineEnabled && (
        <div className="mb-3 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-md px-3 py-2">
          Pipeline is disabled — even with the schedule on, no runs will fire.
          Re-enable the pipeline at the top of this page.
        </div>
      )}
      {err && (
        <div className="mb-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          {err}
        </div>
      )}

      <div className="rounded-lg border border-stone-200 bg-white p-4 grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl">
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-stone-700 mb-1">Run times</label>
          <input
            type="text"
            value={timesText}
            onChange={(e) => setTimesText(e.target.value)}
            placeholder="09:30, 14:00, 18:30"
            className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
          />
          <p className="mt-1 text-[11px] text-stone-400">
            Comma-separated 24-hour HH:MM values. Server time. Saved canonical (sorted, deduped, zero-padded).
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">Max runs per day</label>
          <input
            type="number"
            min={1}
            max={24}
            value={maxRuns}
            onChange={(e) => setMaxRuns(Number(e.target.value) || 1)}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400"
          />
          <p className="mt-1 text-[11px] text-stone-400">
            Skipped slots don't count. Above-cap slots record as cap-reached.
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">Grace window (minutes)</label>
          <input
            type="number"
            min={0}
            max={240}
            value={graceMinutes}
            onChange={(e) => setGraceMinutes(Number(e.target.value) || 0)}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400"
          />
          <p className="mt-1 text-[11px] text-stone-400">
            How long after a slot's time it can still fire (e.g. after a deploy).
          </p>
        </div>

        <label className="md:col-span-2 flex items-center gap-2 text-sm text-stone-700 cursor-pointer">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
            className="h-4 w-4 rounded border-stone-300"
          />
          Enabled
          <span className="text-xs text-stone-400 ml-1">
            — when off, the schedule is preserved but no runs fire.
          </span>
        </label>

        <div className="md:col-span-2 flex items-center gap-2">
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-3 py-1.5 rounded-md bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 disabled:opacity-50 cursor-pointer"
          >
            {saving ? 'Saving…' : 'Save schedule'}
          </button>
          {schedule.updated_at && (
            <span className="text-[11px] text-stone-400">
              Last saved: {formatDate(schedule.updated_at)}
            </span>
          )}
        </div>
      </div>

      {/* Recent runs audit log */}
      <div className="mt-5">
        <div className="flex items-baseline justify-between mb-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-stone-400">
            Recent fires
          </h4>
          <span className="text-[11px] text-stone-400">{runs.length}</span>
        </div>
        {runs.length === 0 ? (
          <div className="text-sm text-stone-400 px-1">
            No scheduled runs yet — set times above and the daemon will start firing.
          </div>
        ) : (
          <div className="border border-stone-200 rounded-lg overflow-hidden bg-white">
            {runs.map((r) => (
              <div
                key={r.id}
                className="border-b border-stone-100 last:border-b-0 px-3 py-2 flex items-center gap-3 text-sm"
              >
                <span className="font-mono text-stone-700 w-40 flex-shrink-0">
                  {r.scheduled_time}
                </span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${STATUS_TONE[r.status]}`}>
                  {STATUS_LABEL[r.status]}
                </span>
                <span className="flex-1 text-stone-500 text-xs truncate">
                  {r.note || (r.video_id ? `→ video #${r.video_id}` : '')}
                </span>
                <span className="text-[11px] text-stone-400 flex-shrink-0">
                  {formatDate(r.fired_at)}
                </span>
              </div>
            ))}
          </div>
        )}
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
