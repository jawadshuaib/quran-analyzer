import { useState, useEffect, useCallback } from 'react';
import {
  getPipelines, createPipeline, updatePipeline, deletePipeline,
  generatePipelineVideo, getPipelineVideos, deletePipelineVideo,
  pipelineVideoDownloadUrl, getResources, getMusicTracks, getVoices, getReciters, getToken,
  setPipelineVideoUploaded,
} from '../../api/admin';
import type { Pipeline, PipelineVideo, Resource, MusicTrack, Voice, Reciter } from '../../api/admin';
import { useConfirm } from './shared/useConfirm';
import { safeFilename } from './shared/filename';
import UploadToYouTubeModal from './UploadToYouTubeModal';

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
  const [reciters, setReciters] = useState<Reciter[]>([]);

  // Pipelines
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  // Create / edit form
  const [formName, setFormName] = useState('');
  const [formLanguage, setFormLanguage] = useState<'english' | 'arabic'>('english');
  const [formResourceId, setFormResourceId] = useState<number | ''>('');
  const [formVoiceId, setFormVoiceId] = useState('');
  const [formReciterId, setFormReciterId] = useState<number | ''>('');
  const [formShowBands, setFormShowBands] = useState(true);
  const [formRandomResource, setFormRandomResource] = useState(false);
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
      getReciters().catch(() => []),
      getPipelines().catch(() => []),
    ]).then(([res, mus, voi, rec, pipes]) => {
      setResources(res);
      setMusicTracks(mus);
      setVoices(voi);
      setReciters(rec);
      setPipelines(pipes);

      // Preselect based on ?lang= query param (set by AdminMedia cards)
      const params = new URLSearchParams(window.location.search);
      const wantLang = params.get('lang');
      const isValidLang = wantLang === 'arabic' || wantLang === 'english';

      if (pipes.length > 0) {
        let preselect = pipes[0];
        if (isValidLang) {
          const match = pipes.find((p: Pipeline) => p.language === wantLang);
          if (match) {
            preselect = match;
          } else {
            // User asked for a language that has no pipelines yet — open the
            // create form pre-filled with that language.
            setShowCreate(true);
            setFormLanguage(wantLang);
          }
        }
        setSelectedId(preselect.id);
      } else if (isValidLang) {
        // No pipelines at all — open create form with requested language
        setShowCreate(true);
        setFormLanguage(wantLang);
      }
      setLoading(false);
    });
  }, []);

  // Load videos when selection changes
  const loadVideos = useCallback(() => {
    if (!selectedId) return;
    getPipelineVideos(selectedId)
      .then((fetched) => {
        // Defensive client-side filter — only keep videos that belong to the
        // currently selected pipeline. Guards against stale fetches and any
        // pipeline_id inconsistency on the server side.
        setVideos(fetched.filter((v) => v.pipeline_id === selectedId));
      })
      .catch(() => {});
  }, [selectedId]);

  // Clear videos immediately when switching pipelines so the previous
  // pipeline's list doesn't flash while the new fetch is in flight.
  useEffect(() => {
    setVideos([]);
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
    setFormLanguage('english');
    setFormResourceId('');
    setFormVoiceId('');
    setFormReciterId('');
    setFormShowBands(true);
    setFormRandomResource(false);
    setFormMusicId('');
    setFormError('');
  }

  const hasActiveVideo = videos.some((v) =>
    ['pending', 'selecting_verses', 'polishing', 'generating_tts', 'rendering', 'generating_metadata'].includes(v.status)
  );

  function validateForm(): boolean {
    if (!formName.trim()) { setFormError('Name is required'); return false; }
    if (!formResourceId) { setFormError('Background video is required'); return false; }
    if (formLanguage === 'english' && !formVoiceId) {
      setFormError('Voice is required for English pipelines');
      return false;
    }
    if (formLanguage === 'arabic' && !formReciterId) {
      setFormError('Reciter is required for Arabic pipelines');
      return false;
    }
    return true;
  }

  async function handleCreate() {
    if (!validateForm()) return;
    setSaving(true);
    setFormError('');
    try {
      const pipe = await createPipeline({
        name: formName.trim(),
        language: formLanguage,
        resource_id: formResourceId as number,
        voice_id: formLanguage === 'english' ? formVoiceId : undefined,
        reciter_id: formLanguage === 'arabic' ? (formReciterId as number) : null,
        show_bands: formShowBands,
        random_resource: formRandomResource,
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
    setFormLanguage(pipe.language === 'arabic' ? 'arabic' : 'english');
    setFormResourceId(pipe.resource_id);
    setFormVoiceId(pipe.voice_id || '');
    setFormReciterId(pipe.reciter_id || '');
    setFormShowBands(!!pipe.show_bands);
    setFormRandomResource(!!pipe.random_resource);
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
        voice_id: formLanguage === 'english' ? formVoiceId : undefined,
        reciter_id: formLanguage === 'arabic' ? (formReciterId as number) : null,
        show_bands: formShowBands,
        random_resource: formRandomResource,
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

  const { confirm, dialog: confirmDialog } = useConfirm();

  async function handleDelete(id: number) {
    const pipe = pipelines.find((p) => p.id === id);
    const ok = await confirm({
      title: 'Delete pipeline?',
      message: pipe
        ? `This will permanently delete "${pipe.name}" and all ${pipe.video_count || 0} of its generated videos. This cannot be undone.`
        : 'This will permanently delete the pipeline and all its generated videos. This cannot be undone.',
      confirmLabel: 'Delete pipeline',
      tone: 'danger',
    });
    if (!ok) return;
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

  // Manual generation form state
  const [showManualForm, setShowManualForm] = useState(false);
  const [manualRange, setManualRange] = useState('');
  const [manualTitle, setManualTitle] = useState('');
  const [manualDescription, setManualDescription] = useState('');
  const [manualError, setManualError] = useState('');

  function parseVerseRange(input: string): { chapter: number; ayah_start: number; ayah_end: number } | null {
    const trimmed = input.trim();
    const rangeMatch = trimmed.match(/^(\d+)\s*:\s*(\d+)\s*-\s*(\d+)$/);
    if (rangeMatch) {
      const chapter = parseInt(rangeMatch[1]);
      const start = parseInt(rangeMatch[2]);
      const end = parseInt(rangeMatch[3]);
      if (chapter >= 1 && chapter <= 114 && start >= 1 && end >= start) {
        return { chapter, ayah_start: start, ayah_end: end };
      }
      return null;
    }
    const singleMatch = trimmed.match(/^(\d+)\s*:\s*(\d+)$/);
    if (singleMatch) {
      const chapter = parseInt(singleMatch[1]);
      const ayah = parseInt(singleMatch[2]);
      if (chapter >= 1 && chapter <= 114 && ayah >= 1) {
        return { chapter, ayah_start: ayah, ayah_end: ayah };
      }
      return null;
    }
    return null;
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

  async function handleManualGenerate() {
    if (!selectedId) return;
    setManualError('');

    const parsed = parseVerseRange(manualRange);
    if (!parsed) {
      setManualError('Invalid verse range. Use format "102:1-8" or "102:3".');
      return;
    }
    if (!manualTitle.trim()) {
      setManualError('Title is required');
      return;
    }

    setGenerating(true);
    setGenError('');
    try {
      await generatePipelineVideo(selectedId, {
        chapter: parsed.chapter,
        ayah_start: parsed.ayah_start,
        ayah_end: parsed.ayah_end,
        youtube_title: manualTitle.trim(),
        youtube_description: manualDescription.trim(),
      });
      // Reset form
      setManualRange('');
      setManualTitle('');
      setManualDescription('');
      setShowManualForm(false);
      loadVideos();
    } catch (err) {
      setGenError(err instanceof Error ? err.message : 'Generation failed');
    } finally {
      setGenerating(false);
    }
  }

  async function handleDeleteVideo(vid: number) {
    const video = videos.find((v) => v.id === vid);
    const preview = video?.youtube_title
      ? `"${video.youtube_title}"`
      : video
      ? `video #${video.id}`
      : 'this video';
    const ok = await confirm({
      title: 'Delete generated video?',
      message: `This will permanently delete ${preview} and its associated audio files. This cannot be undone.`,
      confirmLabel: 'Delete video',
      tone: 'danger',
    });
    if (!ok) return;
    try {
      await deletePipelineVideo(vid);
      setVideos((prev) => prev.filter((v) => v.id !== vid));
    } catch { /* ignore */ }
  }

  async function handleToggleUploaded(vid: number, uploaded: boolean) {
    // Optimistic update — flip the checkbox instantly, roll back on failure
    setVideos((prev) => prev.map((v) =>
      v.id === vid ? { ...v, uploaded_to_youtube: uploaded ? 1 : 0 } : v,
    ));
    try {
      await setPipelineVideoUploaded(vid, uploaded);
    } catch {
      setVideos((prev) => prev.map((v) =>
        v.id === vid ? { ...v, uploaded_to_youtube: uploaded ? 0 : 1 } : v,
      ));
    }
  }

  async function handleDownload(vid: PipelineVideo) {
    const token = getToken();
    const res = await fetch(pipelineVideoDownloadUrl(vid.id), {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);

    // Build a human-readable filename. Prefer the YouTube title; if absent,
    // use the verse reference; finally fall back to pipeline_<id>.
    let base: string;
    if (vid.youtube_title) {
      base = safeFilename(vid.youtube_title);
    } else {
      let verseRef = '';
      try {
        const verses = JSON.parse(vid.verse_data || '[]');
        if (verses.length > 0 && verses[0].ref) verseRef = verses[0].ref;
      } catch { /* ignore */ }
      base = verseRef ? safeFilename(verseRef) : `pipeline_${vid.id}`;
    }

    const a = document.createElement('a');
    a.href = url;
    a.download = `${base}.mp4`;
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
          {pipelines.map((p) => {
            const langBadge = p.language === 'arabic' ? 'AR' : 'EN';
            const isSelected = selectedId === p.id;
            return (
              <button
                key={p.id}
                onClick={() => { setSelectedId(p.id); setShowCreate(false); }}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                  isSelected
                    ? 'bg-stone-800 text-white'
                    : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
                }`}
              >
                <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                  isSelected ? 'bg-white/20' : 'bg-stone-200 text-stone-500'
                }`}>
                  #{p.id}
                </span>
                <span className={`text-[9px] font-semibold px-1 py-0.5 rounded ${
                  p.language === 'arabic'
                    ? (isSelected ? 'bg-amber-200/30 text-amber-100' : 'bg-amber-100 text-amber-700')
                    : (isSelected ? 'bg-emerald-200/30 text-emerald-100' : 'bg-emerald-100 text-emerald-700')
                }`}>
                  {langBadge}
                </span>
                <span>{p.name}</span>
                {p.video_count ? <span className="text-xs opacity-60">({p.video_count})</span> : null}
              </button>
            );
          })}
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
                placeholder={formLanguage === 'arabic' ? 'e.g. Arabic Shorts - Juz Amma' : 'e.g. English Shorts - Reflective'}
                className="w-full rounded-lg border border-stone-200 px-3 py-2 text-sm focus:outline-none focus:border-stone-400"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-stone-700 mb-1">Language</label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setFormLanguage('english')}
                  disabled={!!editingId}
                  className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors cursor-pointer disabled:cursor-not-allowed ${
                    formLanguage === 'english'
                      ? 'bg-stone-800 text-white border-stone-800'
                      : 'bg-white text-stone-600 border-stone-300 hover:bg-stone-50'
                  }`}
                >
                  English (TTS)
                </button>
                <button
                  type="button"
                  onClick={() => setFormLanguage('arabic')}
                  disabled={!!editingId}
                  className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors cursor-pointer disabled:cursor-not-allowed ${
                    formLanguage === 'arabic'
                      ? 'bg-stone-800 text-white border-stone-800'
                      : 'bg-white text-stone-600 border-stone-300 hover:bg-stone-50'
                  }`}
                >
                  Arabic (Recitation)
                </button>
              </div>
              {editingId && (
                <p className="text-xs text-stone-400 mt-1">Language cannot be changed after creation.</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-stone-700 mb-1">
                Background Video {formRandomResource && <span className="font-normal text-stone-400">(overridden by random per run)</span>}
              </label>
              <select
                value={formResourceId}
                onChange={(e) => setFormResourceId(e.target.value ? Number(e.target.value) : '')}
                className={`w-full rounded-lg border border-stone-200 px-3 py-2 text-sm focus:outline-none focus:border-stone-400 ${
                  formRandomResource ? 'opacity-60' : ''
                }`}
              >
                <option value="">Select...</option>
                {resources.map((r) => (
                  <option key={r.id} value={r.id}>{r.description || r.original_name}</option>
                ))}
              </select>
              <label className="flex items-center gap-2 cursor-pointer mt-2">
                <input
                  type="checkbox"
                  checked={formRandomResource}
                  onChange={(e) => setFormRandomResource(e.target.checked)}
                  className="rounded border-stone-300"
                />
                <span className="text-sm text-stone-700">Pick a random background video for each generated video</span>
              </label>
            </div>
            {formLanguage === 'english' ? (
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
            ) : (
              <div>
                <label className="block text-sm font-medium text-stone-700 mb-1">Reciter</label>
                <select
                  value={formReciterId}
                  onChange={(e) => setFormReciterId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full rounded-lg border border-stone-200 px-3 py-2 text-sm focus:outline-none focus:border-stone-400"
                >
                  <option value="">Select...</option>
                  {reciters.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.reciter_name}{r.style ? ` — ${r.style}` : ''}
                    </option>
                  ))}
                </select>
              </div>
            )}
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
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-mono text-stone-400 bg-stone-100 px-2 py-0.5 rounded">
                    #{selected.id}
                  </span>
                  <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
                    selected.language === 'arabic' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'
                  }`}>
                    {selected.language === 'arabic' ? 'Arabic · Recitation' : 'English · TTS'}
                  </span>
                  <h2 className="font-semibold text-stone-800 text-lg">{selected.name}</h2>
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-stone-400">
                  <span>
                    Video: {selected.random_resource
                      ? <span className="italic text-stone-500">Random per run</span>
                      : (resources.find((r) => r.id === selected.resource_id)?.description
                          || resources.find((r) => r.id === selected.resource_id)?.original_name
                          || '?')}
                  </span>
                  {selected.language === 'arabic' ? (
                    <span>Reciter: {(() => {
                      const rec = reciters.find((r) => r.id === selected.reciter_id);
                      if (!rec) return selected.reciter_id ? `#${selected.reciter_id}` : '?';
                      return `${rec.reciter_name}${rec.style ? ` (${rec.style})` : ''}`;
                    })()}</span>
                  ) : (
                    <span>Voice: {voices.find((v) => v.voice_id === selected.voice_id)?.name || selected.voice_id}</span>
                  )}
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

            {/* Generate buttons */}
            <div className="mt-6 space-y-3">
              <div className="flex flex-wrap items-center gap-3">
                <button
                  onClick={handleGenerate}
                  disabled={generating || hasActiveVideo || showManualForm}
                  className="px-6 py-3 rounded-xl bg-emerald-600 text-white font-semibold text-sm hover:bg-emerald-700 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {generating && !showManualForm
                    ? 'Starting...'
                    : hasActiveVideo
                    ? 'Video in progress...'
                    : `Auto Pick Verses for ${selected?.language === 'arabic' ? 'Arabic' : 'English'} Pipeline`}
                </button>
                <button
                  onClick={() => { setShowManualForm(!showManualForm); setManualError(''); }}
                  disabled={generating || hasActiveVideo}
                  className="px-6 py-3 rounded-xl border border-stone-300 bg-white text-stone-700 font-semibold text-sm hover:bg-stone-50 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {showManualForm ? 'Cancel Manual Selection' : 'Manually Pick Verses for Pipeline'}
                </button>
                {genError && <p className="text-sm text-red-600">{genError}</p>}
              </div>

              {showManualForm && (
                <div className="mt-2 rounded-xl border border-stone-200 bg-stone-50 p-4 space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-stone-600 mb-1">Verse range</label>
                    <input
                      type="text"
                      value={manualRange}
                      onChange={(e) => setManualRange(e.target.value)}
                      placeholder="e.g. 102:1-8"
                      className="w-full max-w-xs px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-emerald-400"
                    />
                    <p className="mt-1 text-xs text-stone-400">Format: <code>surah:start-end</code> or <code>surah:ayah</code> for a single verse.</p>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-stone-600 mb-1">YouTube title</label>
                    <input
                      type="text"
                      value={manualTitle}
                      onChange={(e) => setManualTitle(e.target.value)}
                      placeholder="e.g. 102:1-8 | The Rivalry That Destroys You"
                      className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-stone-600 mb-1">YouTube description</label>
                    <textarea
                      value={manualDescription}
                      onChange={(e) => setManualDescription(e.target.value)}
                      placeholder="Brief, thoughtful description..."
                      rows={3}
                      className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 resize-y"
                    />
                  </div>
                  {manualError && (
                    <p className="text-sm text-red-600">{manualError}</p>
                  )}
                  <div className="flex items-center gap-3 pt-1">
                    <button
                      onClick={handleManualGenerate}
                      disabled={generating || hasActiveVideo}
                      className="px-5 py-2.5 rounded-xl bg-emerald-600 text-white font-semibold text-sm hover:bg-emerald-700 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {generating ? 'Starting...' : 'Generate Video'}
                    </button>
                  </div>
                </div>
              )}
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
                onUploadedToggle={handleToggleUploaded}
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

      {confirmDialog}
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
  onUploadedToggle,
}: {
  video: PipelineVideo;
  onDelete: (id: number) => void;
  onDownload: (v: PipelineVideo) => void;
  onUploadedToggle: (id: number, uploaded: boolean) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const sl = statusLabel(video.status);
  const verses: VerseEntry[] = (() => {
    try { return JSON.parse(video.verse_data || '[]'); }
    catch { return []; }
  })();

  const [showUploadModal, setShowUploadModal] = useState(false);
  const isActive = ['pending', 'selecting_verses', 'polishing', 'generating_tts', 'rendering', 'generating_metadata'].includes(video.status);
  const bySchedule = video.triggered_by === 'scheduler';
  const uploaded = !!video.uploaded_to_youtube;

  return (
    <div className="rounded-xl border border-stone-200 bg-white p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0 flex-wrap">
          <span className={`px-2.5 py-1 rounded-full text-[11px] font-medium ${sl.color}`}>
            {sl.text}
          </span>
          {bySchedule && (
            <span
              className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-indigo-50 text-indigo-700 border border-indigo-100"
              title="This video was generated automatically by the scheduler"
            >
              Generated by Scheduler
            </span>
          )}
          {video.status === 'complete' && (
            <label
              className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium bg-stone-50 border border-stone-200 text-stone-600 cursor-pointer hover:bg-stone-100"
              title="Mark as uploaded to YouTube"
            >
              <input
                type="checkbox"
                checked={uploaded}
                onChange={(e) => onUploadedToggle(video.id, e.target.checked)}
                className="h-3 w-3 rounded border-stone-300 cursor-pointer"
              />
              {uploaded ? 'Uploaded to YouTube' : 'Not uploaded'}
            </label>
          )}
          {isActive && video.progress && (
            <span className="text-xs text-stone-400 truncate">{video.progress}</span>
          )}
          {isActive && (
            <div className="h-3 w-3 animate-spin rounded-full border-2 border-stone-200 border-t-stone-500 flex-shrink-0" />
          )}
          {verses.length > 0 && (
            <span className="text-xs text-stone-400 truncate">
              {Array.from(new Set(verses.map((v) => v.ref))).join(' | ')}
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
          {video.status === 'complete' && (
            <button
              onClick={() => setShowUploadModal(true)}
              className="text-xs font-medium text-red-600 hover:text-red-700 cursor-pointer"
              title={uploaded ? 'Already uploaded — upload again' : 'Upload this video to YouTube'}
            >
              {uploaded ? 'Re-upload to YouTube' : 'Upload to YouTube'}
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

      {expanded && verses.length > 0 && (() => {
        const uniqueRefs = Array.from(new Set(verses.map((v) => v.ref)));
        const passageMode = uniqueRefs.length === 1;
        return (
          <div className="mt-3 border-t border-stone-100 pt-3 space-y-2">
            {passageMode && (
              <div className="text-xs font-medium text-stone-600">{uniqueRefs[0]}</div>
            )}
            {verses.map((v, i) => (
              <div key={i} className="text-xs">
                {passageMode ? (
                  <span className="font-medium text-stone-500">v{v.verse}</span>
                ) : (
                  <span className="font-medium text-stone-600">{v.ref}</span>
                )}
                <p className="text-stone-400 mt-0.5">{v.polished_text || v.original_translation}</p>
              </div>
            ))}
          </div>
        );
      })()}

      <div className="mt-2 text-[10px] text-stone-300 flex items-center gap-2">
        <span>{new Date(video.created_at).toLocaleString()}</span>
        {video.youtube_video_id && (
          <a
            href={`https://youtube.com/watch?v=${video.youtube_video_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-red-500 hover:text-red-600 font-medium"
            title="Open on YouTube"
          >
            ▶ youtube.com/watch?v={video.youtube_video_id}
          </a>
        )}
      </div>

      {showUploadModal && (
        <UploadToYouTubeModal
          video={video}
          onClose={() => setShowUploadModal(false)}
          onUploaded={(ytId) => {
            // The server already updated uploaded_to_youtube + youtube_video_id
            // — nothing more to do here. The parent's next poll will refresh.
            void ytId;
          }}
        />
      )}
    </div>
  );
}
