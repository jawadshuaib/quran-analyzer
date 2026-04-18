import { useState, useEffect, useCallback } from 'react';
import {
  getPipelines, createPipeline, updatePipeline, deletePipeline,
  generatePipelineVideo, getPipelineVideos, deletePipelineVideo,
  pipelineVideoDownloadUrl, getResources, getMusicTracks, getVoices, getToken,
} from '../../api/admin';
import type { Pipeline, PipelineVideo, Resource, MusicTrack, Voice } from '../../api/admin';

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function statusLabel(status: string): { text: string; color: string } {
  switch (status) {
    case 'pending': return { text: 'Pending', color: 'bg-stone-100 text-stone-600' };
    case 'selecting_verses': return { text: 'Selecting Verses', color: 'bg-blue-50 text-blue-600' };
    case 'polishing': return { text: 'Polishing', color: 'bg-violet-50 text-violet-600' };
    case 'generating_tts': return { text: 'Generating Audio', color: 'bg-amber-50 text-amber-600' };
    case 'rendering': return { text: 'Rendering', color: 'bg-indigo-50 text-indigo-600' };
    case 'generating_metadata': return { text: 'Generating Metadata', color: 'bg-teal-50 text-teal-600' };
    case 'complete': return { text: 'Complete', color: 'bg-emerald-50 text-emerald-600' };
    case 'failed': return { text: 'Failed', color: 'bg-red-50 text-red-600' };
    default: return { text: status, color: 'bg-stone-100 text-stone-600' };
  }
}

interface VerseEntry {
  chapter: number;
  verse: number;
  ref: string;
  original_translation: string;
  polished_text: string;
}

export default function PipelineManager() {
  // Shared data
  const [resources, setResources] = useState<Resource[]>([]);
  const [musicTracks, setMusicTracks] = useState<MusicTrack[]>([]);
  const [voices, setVoices] = useState<Voice[]>([]);

  // Pipelines
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  // Create / edit form
  const [formName, setFormName] = useState('');
  const [formResourceId, setFormResourceId] = useState<number | ''>('');
  const [formVoiceId, setFormVoiceId] = useState('');
  const [formShowBands, setFormShowBands] = useState(true);
  const [formMusicId, setFormMusicId] = useState<number | ''>('');
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  // Videos
  const [videos, setVideos] = useState<PipelineVideo[]>([]);
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState('');

  const selected = pipelines.find((p) => p.id === selectedId) || null;

  // Load shared data
  useEffect(() => {
    Promise.all([
      getResources().catch(() => []),
      getMusicTracks().catch(() => []),
      getVoices().catch(() => []),
      getPipelines().catch(() => []),
    ]).then(([res, mus, voi, pipes]) => {
      setResources(res);
      setMusicTracks(mus);
      setVoices(voi);
      setPipelines(pipes);
      if (pipes.length > 0) setSelectedId(pipes[0].id);
      setLoading(false);
    });
  }, []);

  // Load videos when selection changes
  const loadVideos = useCallback(() => {
    if (!selectedId) return;
    getPipelineVideos(selectedId).then(setVideos).catch(() => {});
  }, [selectedId]);

  useEffect(() => {
    loadVideos();
  }, [loadVideos]);

  // Poll for active videos
  useEffect(() => {
    const hasActive = videos.some((v) =>
      ['pending', 'selecting_verses', 'polishing', 'generating_tts', 'rendering', 'generating_metadata'].includes(v.status)
    );
    if (!hasActive) return;
    const timer = setInterval(loadVideos, 3000);
    return () => clearInterval(timer);
  }, [videos, loadVideos]);

  function resetForm() {
    setFormName('');
    setFormResourceId('');
    setFormVoiceId('');
    setFormShowBands(true);
    setFormMusicId('');
    setFormError('');
  }

  const hasActiveVideo = videos.some((v) =>
    ['pending', 'selecting_verses', 'polishing', 'generating_tts', 'rendering', 'generating_metadata'].includes(v.status)
  );

  function validateForm(): boolean {
    if (!formName.trim()) { setFormError('Name is required'); return false; }
    if (!formResourceId) { setFormError('Background video is required'); return false; }
    if (!formVoiceId) { setFormError('Voice is required'); return false; }
    return true;
  }

  async function handleCreate() {
    if (!validateForm()) return;
    setSaving(true);
    setFormError('');
    try {
      const pipe = await createPipeline({
        name: formName.trim(),
        resource_id: formResourceId as number,
        voice_id: formVoiceId,
        show_bands: formShowBands,
        music_id: formMusicId ? (formMusicId as number) : null,
      });
      setPipelines((prev) => [pipe, ...prev]);
      setSelectedId(pipe.id);
      setShowCreate(false);
      resetForm();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create');
    } finally {
      setSaving(false);
    }
  }

  function handleEdit(pipe: Pipeline) {
    setEditingId(pipe.id);
    setFormName(pipe.name);
    setFormResourceId(pipe.resource_id);
    setFormVoiceId(pipe.voice_id);
    setFormShowBands(!!pipe.show_bands);
    setFormMusicId(pipe.music_id || '');
    setFormError('');
    setShowCreate(false);
  }

  async function handleSaveEdit() {
    if (!editingId || !validateForm()) return;
    setSaving(true);
    setFormError('');
    try {
      const updated = await updatePipeline(editingId, {
        name: formName.trim(),
        resource_id: formResourceId as number,
        voice_id: formVoiceId,
        show_bands: formShowBands,
        music_id: formMusicId ? (formMusicId as number) : null,
      });
      setPipelines((prev) => prev.map((p) => p.id === editingId ? { ...p, ...updated } : p));
      setEditingId(null);
      resetForm();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to update');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    try {
      await deletePipeline(id);
      setPipelines((prev) => {
        const remaining = prev.filter((p) => p.id !== id);
        if (selectedId === id) {
          setSelectedId(remaining.length > 0 ? remaining[0].id : null);
        }
        return remaining;
      });
    } catch { /* ignore */ }
  }

  async function handleGenerate() {
    if (!selectedId) return;
    setGenerating(true);
    setGenError('');
    try {
      await generatePipelineVideo(selectedId);
      loadVideos();
    } catch (err) {
      setGenError(err instanceof Error ? err.message : 'Generation failed');
    } finally {
      setGenerating(false);
    }
  }

  async function handleDeleteVideo(vid: number) {
    try {
      await deletePipelineVideo(vid);
      setVideos((prev) => prev.filter((v) => v.id !== vid));
    } catch { /* ignore */ }
  }

  async function handleDownload(vid: PipelineVideo) {
    const token = getToken();
    const res = await fetch(pipelineVideoDownloadUrl(vid.id), {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pipeline_${vid.id}.mp4`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-stone-300 border-t-stone-600" />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-stone-800">Pipelines</h1>
        <button
          onClick={() => { setShowCreate(true); resetForm(); }}
          className="px-4 py-2 rounded-lg bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 transition-colors cursor-pointer"
        >
          New Pipeline
        </button>
      </div>

      {/* Pipeline tabs */}
      {pipelines.length > 0 && (
        <div className="flex items-center gap-2 mb-6 flex-wrap">
          {pipelines.map((p) => (
            <button
              key={p.id}
              onClick={() => { setSelectedId(p.id); setShowCreate(false); }}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                selectedId === p.id
                  ? 'bg-stone-800 text-white'
                  : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
              }`}
            >
              {p.name}
              {p.video_count ? <span className="ml-1.5 text-xs opacity-60">({p.video_count})</span> : null}
            </button>
          ))}
        </div>
      )}

      {/* Create / Edit form */}
      {(showCreate || editingId) && (
        <div className="rounded-xl border border-stone-200 bg-white p-6 mb-8">
          <h2 className="font-semibold text-stone-800 mb-4">{editingId ? 'Edit Pipeline' : 'Create New Pipeline'}</h2>
          <div className="space-y-4 max-w-lg">
            <div>
              <label className="block text-sm font-medium text-stone-700 mb-1">Pipeline Name</label>
              <input
                type="text"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="e.g. English Shorts - Reflective"
                className="w-full rounded-lg border border-stone-200 px-3 py-2 text-sm focus:outline-none focus:border-stone-400"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-stone-700 mb-1">Background Video</label>
              <select
                value={formResourceId}
                onChange={(e) => setFormResourceId(e.target.value ? Number(e.target.value) : '')}
                className="w-full rounded-lg border border-stone-200 px-3 py-2 text-sm focus:outline-none focus:border-stone-400"
              >
                <option value="">Select...</option>
                {resources.map((r) => (
                  <option key={r.id} value={r.id}>{r.description || r.original_name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-stone-700 mb-1">Voice</label>
              <select
                value={formVoiceId}
                onChange={(e) => setFormVoiceId(e.target.value)}
                className="w-full rounded-lg border border-stone-200 px-3 py-2 text-sm focus:outline-none focus:border-stone-400"
              >
                <option value="">Select...</option>
                {voices.map((v) => (
                  <option key={v.id} value={v.voice_id}>{v.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-stone-700 mb-1">Background Music (optional)</label>
              <select
                value={formMusicId}
                onChange={(e) => setFormMusicId(e.target.value ? Number(e.target.value) : '')}
                className="w-full rounded-lg border border-stone-200 px-3 py-2 text-sm focus:outline-none focus:border-stone-400"
              >
                <option value="">None</option>
                {musicTracks.map((m) => (
                  <option key={m.id} value={m.id}>{m.description || m.original_name}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formShowBands}
                  onChange={(e) => setFormShowBands(e.target.checked)}
                  className="rounded border-stone-300"
                />
                <span className="text-sm text-stone-700">Show dark background behind text</span>
              </label>
            </div>
            {formError && (
              <p className="text-sm text-red-600">{formError}</p>
            )}
            <div className="flex gap-2">
              <button
                onClick={editingId ? handleSaveEdit : handleCreate}
                disabled={saving}
                className="px-5 py-2 rounded-lg bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 transition-colors cursor-pointer disabled:opacity-50"
              >
                {saving ? 'Saving...' : editingId ? 'Save Changes' : 'Create Pipeline'}
              </button>
              <button
                onClick={() => { setShowCreate(false); setEditingId(null); resetForm(); }}
                className="px-4 py-2 rounded-lg text-sm text-stone-500 hover:text-stone-700 cursor-pointer"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Selected pipeline details */}
      {selected && !showCreate && !editingId && (
        <div>
          {/* Config summary */}
          <div className="rounded-xl border border-stone-200 bg-white p-6 mb-6">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-semibold text-stone-800 text-lg">{selected.name}</h2>
                <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-stone-400">
                  <span>Video: {resources.find((r) => r.id === selected.resource_id)?.description || resources.find((r) => r.id === selected.resource_id)?.original_name || '?'}</span>
                  <span>Voice: {voices.find((v) => v.voice_id === selected.voice_id)?.name || selected.voice_id}</span>
                  {selected.music_id && <span>Music: {musicTracks.find((m) => m.id === selected.music_id)?.description || musicTracks.find((m) => m.id === selected.music_id)?.original_name || '?'}</span>}
                  <span>Bands: {selected.show_bands ? 'On' : 'Off'}</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => handleEdit(selected)}
                  className="text-xs text-stone-400 hover:text-stone-600 cursor-pointer"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDelete(selected.id)}
                  className="text-xs text-red-400 hover:text-red-600 cursor-pointer"
                >
                  Delete
                </button>
              </div>
            </div>

            {/* Generate button */}
            <div className="mt-6 flex items-center gap-4">
              <button
                onClick={handleGenerate}
                disabled={generating || hasActiveVideo}
                className="px-6 py-3 rounded-xl bg-emerald-600 text-white font-semibold text-sm hover:bg-emerald-700 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {generating ? 'Starting...' : hasActiveVideo ? 'Video in progress...' : 'Create Video for English Pipeline'}
              </button>
              {genError && <p className="text-sm text-red-600">{genError}</p>}
            </div>
          </div>

          {/* Generated videos */}
          <h2 className="text-sm font-semibold text-stone-600 mb-3">Generated Videos ({videos.length})</h2>

          {videos.length === 0 && (
            <p className="text-sm text-stone-400">No videos generated yet. Click the button above to create your first video.</p>
          )}

          <div className="space-y-3">
            {videos.map((v) => (
              <VideoCard
                key={v.id}
                video={v}
                onDelete={handleDeleteVideo}
                onDownload={handleDownload}
              />
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {pipelines.length === 0 && !showCreate && (
        <div className="text-center py-16">
          <p className="text-stone-400 mb-4">No pipelines created yet.</p>
          <button
            onClick={() => { setShowCreate(true); resetForm(); }}
            className="px-5 py-2.5 rounded-lg bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 transition-colors cursor-pointer"
          >
            Create Your First Pipeline
          </button>
        </div>
      )}
    </div>
  );
}

function CopyButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }

  return (
    <button
      onClick={handleCopy}
      className="text-[10px] text-stone-400 hover:text-stone-600 cursor-pointer flex-shrink-0"
      title={`Copy ${label}`}
    >
      {copied ? 'Copied!' : 'Copy'}
    </button>
  );
}

function VideoCard({
  video,
  onDelete,
  onDownload,
}: {
  video: PipelineVideo;
  onDelete: (id: number) => void;
  onDownload: (v: PipelineVideo) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const sl = statusLabel(video.status);
  const verses: VerseEntry[] = (() => {
    try { return JSON.parse(video.verse_data || '[]'); }
    catch { return []; }
  })();

  const isActive = ['pending', 'selecting_verses', 'polishing', 'generating_tts', 'rendering', 'generating_metadata'].includes(video.status);

  return (
    <div className="rounded-xl border border-stone-200 bg-white p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 min-w-0">
          <span className={`px-2.5 py-1 rounded-full text-[11px] font-medium ${sl.color}`}>
            {sl.text}
          </span>
          {isActive && video.progress && (
            <span className="text-xs text-stone-400 truncate">{video.progress}</span>
          )}
          {isActive && (
            <div className="h-3 w-3 animate-spin rounded-full border-2 border-stone-200 border-t-stone-500 flex-shrink-0" />
          )}
          {verses.length > 0 && (
            <span className="text-xs text-stone-400 truncate">
              {verses.map((v) => v.ref).join(' | ')}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 flex-shrink-0 ml-3">
          {video.status === 'complete' && video.file_size && (
            <span className="text-[11px] text-stone-400">{formatBytes(video.file_size)}</span>
          )}
          {video.status === 'complete' && (
            <button
              onClick={() => onDownload(video)}
              className="text-xs font-medium text-emerald-600 hover:text-emerald-700 cursor-pointer"
            >
              Download
            </button>
          )}
          {verses.length > 0 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-stone-400 hover:text-stone-600 cursor-pointer"
            >
              {expanded ? 'Hide' : 'Details'}
            </button>
          )}
          {!isActive && (
            <button
              onClick={() => onDelete(video.id)}
              className="text-xs text-red-400 hover:text-red-600 cursor-pointer"
            >
              Delete
            </button>
          )}
        </div>
      </div>

      {video.error_message && (
        <p className="mt-2 text-xs text-red-500 bg-red-50 rounded-lg px-3 py-2">{video.error_message}</p>
      )}

      {/* YouTube metadata */}
      {video.status === 'complete' && (video.youtube_title || video.youtube_description) && (
        <div className="mt-3 border-t border-stone-100 pt-3 space-y-2">
          {video.youtube_title && (
            <div className="flex items-start gap-2">
              <div className="flex-1 min-w-0">
                <span className="text-[10px] font-medium uppercase tracking-wider text-stone-400">Title</span>
                <p className="text-sm text-stone-700 mt-0.5">{video.youtube_title}</p>
              </div>
              <CopyButton text={video.youtube_title} label="title" />
            </div>
          )}
          {video.youtube_description && (
            <div className="flex items-start gap-2">
              <div className="flex-1 min-w-0">
                <span className="text-[10px] font-medium uppercase tracking-wider text-stone-400">Description</span>
                <p className="text-xs text-stone-500 mt-0.5 leading-relaxed">{video.youtube_description}</p>
              </div>
              <CopyButton text={video.youtube_description} label="description" />
            </div>
          )}
        </div>
      )}

      {expanded && verses.length > 0 && (
        <div className="mt-3 border-t border-stone-100 pt-3 space-y-2">
          {verses.map((v, i) => (
            <div key={i} className="text-xs">
              <span className="font-medium text-stone-600">{v.ref}</span>
              <p className="text-stone-400 mt-0.5">{v.polished_text || v.original_translation}</p>
            </div>
          ))}
        </div>
      )}

      <div className="mt-2 text-[10px] text-stone-300">
        {new Date(video.created_at).toLocaleString()}
      </div>
    </div>
  );
}
