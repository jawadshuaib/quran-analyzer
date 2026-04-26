import { useState, useEffect, useRef, useCallback } from 'react';
import {
  getExplanations, getExplanation, getResources, getMusicTracks,
  startExplanationVideoGeneration, getGeneratedVideos, deleteGeneratedVideo,
  generatedVideoDownloadUrl, getToken,
} from '../../api/admin';
import type { ExplanationListItem, Explanation, Resource, MusicTrack, GeneratedVideo } from '../../api/admin';
import { useConfirm } from './shared/useConfirm';

function formatBytes(bytes: number): string {
  if (!bytes) return '--';
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function GenerateExplanationVideo() {
  const [explanations, setExplanations] = useState<ExplanationListItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [preview, setPreview] = useState<Explanation | null>(null);
  const [resources, setResources] = useState<Resource[]>([]);
  const [resourceId, setResourceId] = useState<number | null>(null);
  const [musicTracks, setMusicTracks] = useState<MusicTrack[]>([]);
  const [musicId, setMusicId] = useState<number | null>(null);
  const [format, setFormat] = useState<'short' | 'regular'>('short');

  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState('');
  const [videos, setVideos] = useState<GeneratedVideo[]>([]);
  const pollRef = useRef<number | null>(null);
  const { confirm, dialog: confirmDialog } = useConfirm();

  useEffect(() => {
    getExplanations().then(setExplanations).catch(() => {});
    getResources().then((r) => { setResources(r); if (r.length > 0) setResourceId(r[0].id); }).catch(() => {});
    getMusicTracks().then(setMusicTracks).catch(() => {});
    getGeneratedVideos().then(setVideos).catch(() => {});
  }, []);

  // Load preview when selection changes
  useEffect(() => {
    if (!selectedId) { setPreview(null); return; }
    getExplanation(selectedId).then(setPreview).catch(() => setPreview(null));
  }, [selectedId]);

  // Polling for active jobs
  const startPolling = useCallback(() => {
    if (pollRef.current) return;
    pollRef.current = window.setInterval(async () => {
      try {
        const vids = await getGeneratedVideos();
        setVideos(vids);
        const hasActive = vids.some((v) => v.status === 'pending' || v.status === 'processing');
        if (!hasActive && pollRef.current) {
          clearInterval(pollRef.current);
          pollRef.current = null;
        }
      } catch { /* ignore */ }
    }, 3000);
  }, []);

  useEffect(() => {
    const hasActive = videos.some((v) => v.status === 'pending' || v.status === 'processing');
    if (hasActive) startPolling();
    return () => { if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; } };
  }, [videos, startPolling]);

  async function handleGenerate() {
    if (!selectedId || !resourceId) return;
    const ok = await confirm({
      title: 'Generate explanation video?',
      message: 'Renders this explanation into a video. Uses any pre-generated TTS plus video render time and disk space; may take several minutes.',
      confirmLabel: 'Generate',
    });
    if (!ok) return;
    setGenError('');
    setGenerating(true);
    try {
      await startExplanationVideoGeneration({
        explanation_id: selectedId,
        format,
        resource_id: resourceId,
        music_id: musicId || undefined,
      });
      const vids = await getGeneratedVideos();
      setVideos(vids);
      startPolling();
    } catch (err) {
      setGenError(err instanceof Error ? err.message : 'Generation failed');
    } finally {
      setGenerating(false);
    }
  }

  async function handleDownloadVideo(v: GeneratedVideo) {
    try {
      const token = getToken();
      const res = await fetch(generatedVideoDownloadUrl(v.id), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`Download failed (${res.status})`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const safeName = v.title.replace(/[^\w\s.-]/g, '').trim() || 'video';
      a.download = `${safeName}.mp4`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setGenError(err instanceof Error ? err.message : 'Download failed');
    }
  }

  async function handleDeleteVideo(id: number) {
    const video = videos.find((v) => v.id === id);
    const ok = await confirm({
      title: 'Delete generated video?',
      message: video
        ? `Permanently delete "${video.title || `video #${video.id}`}" and its files from disk? This cannot be undone.`
        : 'Permanently delete this video and its files from disk? This cannot be undone.',
      confirmLabel: 'Delete',
      tone: 'danger',
    });
    if (!ok) return;
    try {
      await deleteGeneratedVideo(id);
      setVideos((prev) => prev.filter((v) => v.id !== id));
    } catch (err) {
      setGenError(err instanceof Error ? err.message : 'Delete failed');
    }
  }

  const readyExplanations = explanations.filter((e) => e.status === 'ready');

  return (
    <div>
      <h1 className="text-xl font-semibold text-stone-800 mb-6">Generate Explanation Video</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Left: Config */}
        <div className="space-y-5">
          {/* Explanation selector */}
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1">Explanation</label>
            {readyExplanations.length === 0 ? (
              <p className="text-sm text-stone-400">
                No ready explanations. <a href="/admin/media/explanations" className="text-blue-500 hover:underline">Create one</a>.
              </p>
            ) : (
              <select
                value={selectedId ?? ''}
                onChange={(e) => setSelectedId(e.target.value ? Number(e.target.value) : null)}
                className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-stone-400"
              >
                <option value="">Select an explanation...</option>
                {readyExplanations.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.title} ({e.verse_count} verse groups)
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Format */}
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-2">Format</label>
            <div className="flex gap-3">
              {(['short', 'regular'] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFormat(f)}
                  className={`flex-1 px-4 py-3 rounded-lg border text-sm font-medium transition-colors cursor-pointer ${
                    format === f
                      ? 'border-stone-800 bg-stone-800 text-white'
                      : 'border-stone-300 bg-white text-stone-600 hover:border-stone-400'
                  }`}
                >
                  {f === 'short' ? 'Short (9:16)' : 'Regular (16:9)'}
                  <span className="block text-xs font-normal mt-0.5 opacity-70">
                    {f === 'short' ? 'YouTube Shorts / TikTok' : 'YouTube / Standard'}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Background Video */}
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1">Background Video</label>
            {resources.length === 0 ? (
              <p className="text-sm text-stone-400">
                No videos uploaded. <a href="/admin/media/resources" className="text-blue-500 hover:underline">Upload one</a>.
              </p>
            ) : (
              <select
                value={resourceId ?? ''}
                onChange={(e) => setResourceId(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-stone-400"
              >
                {resources.map((r) => (
                  <option key={r.id} value={r.id}>{r.original_name}</option>
                ))}
              </select>
            )}
          </div>

          {/* Background Music */}
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1">Background Music</label>
            {musicTracks.length === 0 ? (
              <p className="text-sm text-stone-400">
                No tracks uploaded. <a href="/admin/media/music" className="text-blue-500 hover:underline">Upload one</a>.
              </p>
            ) : (
              <select
                value={musicId ?? ''}
                onChange={(e) => setMusicId(e.target.value ? Number(e.target.value) : null)}
                className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-stone-400"
              >
                <option value="">None</option>
                {musicTracks.map((t) => (
                  <option key={t.id} value={t.id}>{t.original_name}</option>
                ))}
              </select>
            )}
          </div>

          {/* Generate button */}
          <button
            onClick={handleGenerate}
            disabled={generating || !selectedId || !resourceId}
            className="w-full py-3 rounded-lg bg-stone-800 text-white text-sm font-semibold hover:bg-stone-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
          >
            {generating ? 'Starting...' : 'Generate Video'}
          </button>

          {genError && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
              {genError}
            </div>
          )}
        </div>

        {/* Right: Preview */}
        <div>
          <h2 className="text-sm font-medium text-stone-700 mb-3">Segment Preview</h2>
          {!preview ? (
            <p className="text-sm text-stone-400">Select an explanation to preview its segments.</p>
          ) : (
            <div className="space-y-2 max-h-[60vh] overflow-y-auto">
              {preview.segments.map((seg, i) => (
                <div
                  key={i}
                  className={`rounded-lg border p-3 text-sm ${
                    seg.type === 'transition'
                      ? 'border-amber-200 bg-amber-50'
                      : seg.type === 'closing'
                      ? 'border-violet-200 bg-violet-50'
                      : 'border-stone-200 bg-white'
                  }`}
                >
                  <span className="text-xs font-medium uppercase tracking-wider text-stone-400 mb-1 block">
                    {seg.type}
                  </span>
                  {seg.type === 'verses' && (
                    <>
                      <p className="text-xs text-stone-500 mb-1">{seg.ref}</p>
                      <p className="text-stone-700">{seg.translation}</p>
                    </>
                  )}
                  {seg.type === 'transition' && (
                    <p className="text-amber-800 italic">{seg.text}</p>
                  )}
                  {seg.type === 'closing' && (
                    <p className="text-violet-800">{seg.text}</p>
                  )}
                  {seg.tts_filename && (
                    <span className="inline-block mt-1 text-xs text-green-600">TTS ready</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Generated Videos */}
      {videos.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-stone-700 mb-3">Generated Videos</h2>
          <div className="border border-stone-200 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-stone-50 text-left text-stone-500 text-xs">
                <tr>
                  <th className="px-4 py-2 font-medium">Title</th>
                  <th className="px-4 py-2 font-medium">Format</th>
                  <th className="px-4 py-2 font-medium">Status</th>
                  <th className="px-4 py-2 font-medium">Size</th>
                  <th className="px-4 py-2 font-medium">Created</th>
                  <th className="px-4 py-2 font-medium"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {videos.map((v) => (
                  <tr key={v.id} className="hover:bg-stone-50">
                    <td className="px-4 py-2 text-stone-800">{v.title}</td>
                    <td className="px-4 py-2 text-stone-500">{v.format}</td>
                    <td className="px-4 py-2">
                      <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                        v.status === 'complete' ? 'bg-green-100 text-green-700' :
                        v.status === 'error' ? 'bg-red-100 text-red-700' :
                        'bg-amber-100 text-amber-700'
                      }`}>
                        {v.status === 'processing' ? v.progress || 'processing' : v.status}
                      </span>
                      {v.error_message && (
                        <p className="text-xs text-red-500 mt-1">{v.error_message}</p>
                      )}
                    </td>
                    <td className="px-4 py-2 text-stone-500">{formatBytes(v.file_size ?? 0)}</td>
                    <td className="px-4 py-2 text-stone-400 text-xs">
                      {new Date(v.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-2 text-right space-x-2">
                      {v.status === 'complete' && v.filename && (
                        <button
                          onClick={() => handleDownloadVideo(v)}
                          className="text-xs text-blue-600 hover:underline cursor-pointer"
                        >
                          Download
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteVideo(v.id)}
                        className="text-xs text-red-500 hover:text-red-700 cursor-pointer"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {confirmDialog}
    </div>
  );
}
