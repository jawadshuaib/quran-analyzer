import { useState, useEffect, useRef, useCallback } from 'react';
import {
  getResources, getReciters, getTTSCache,
  startVideoGeneration, getGeneratedVideos, deleteGeneratedVideo,
  generatedVideoDownloadUrl, getToken, generateDescription,
} from '../../api/admin';
import type { Resource, Reciter, TTSCacheEntry, GeneratedVideo } from '../../api/admin';

function formatBytes(bytes: number): string {
  if (!bytes) return '--';
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function GenerateVideo() {
  // Options
  const [format, setFormat] = useState<'short' | 'regular'>('short');
  const [resources, setResources] = useState<Resource[]>([]);
  const [resourceId, setResourceId] = useState<number | null>(null);
  const [reciters, setReciters] = useState<Reciter[]>([]);
  const [reciterId, setReciterId] = useState(7);
  const [ttsEntries, setTtsEntries] = useState<TTSCacheEntry[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [title, setTitle] = useState('');
  const [titleManuallyEdited, setTitleManuallyEdited] = useState(false);
  const [englishOnly, setEnglishOnly] = useState(false);

  // Generation
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState('');
  const [videos, setVideos] = useState<GeneratedVideo[]>([]);
  const pollRef = useRef<number | null>(null);

  // Description
  const [description, setDescription] = useState('');
  const [generatingDesc, setGeneratingDesc] = useState(false);

  // Load data
  useEffect(() => {
    getResources().then((r) => { setResources(r); if (r.length > 0) setResourceId(r[0].id); }).catch(() => {});
    getReciters().then(setReciters).catch(() => {});
    getTTSCache().then(setTtsEntries).catch(() => {});
    getGeneratedVideos().then(setVideos).catch(() => {});
  }, []);

  // Poll for active jobs
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
      } catch {
        // ignore
      }
    }, 3000);
  }, []);

  useEffect(() => {
    const hasActive = videos.some((v) => v.status === 'pending' || v.status === 'processing');
    if (hasActive) startPolling();
    return () => { if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; } };
  }, [videos, startPolling]);

  // Toggle verse selection
  function toggleVerse(id: number) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function selectAll() {
    setSelectedIds(new Set(ttsEntries.map((e) => e.id)));
  }

  function selectNone() {
    setSelectedIds(new Set());
  }

  // Auto-generate title from selection (only if not manually edited)
  useEffect(() => {
    if (titleManuallyEdited) return;
    if (selectedIds.size === 0) { setTitle(''); return; }
    const selected = ttsEntries.filter((e) => selectedIds.has(e.id)).sort((a, b) =>
      a.chapter !== b.chapter ? a.chapter - b.chapter : a.verse - b.verse
    );
    if (selected.length === 0) return;
    const first = selected[0];
    const last = selected[selected.length - 1];
    if (first.chapter === last.chapter && first.verse === last.verse) {
      setTitle(`${first.surah_name} ${first.chapter}:${first.verse}`);
    } else if (first.chapter === last.chapter) {
      setTitle(`${first.surah_name} ${first.chapter}:${first.verse}-${last.verse}`);
    } else {
      setTitle(`${first.surah_name} ${first.chapter}:${first.verse} - ${last.surah_name} ${last.chapter}:${last.verse}`);
    }
  }, [selectedIds, ttsEntries, titleManuallyEdited]);

  async function handleGenerate() {
    if (!resourceId || selectedIds.size === 0) return;
    setGenError('');
    setGenerating(true);
    try {
      const verses = ttsEntries
        .filter((e) => selectedIds.has(e.id))
        .sort((a, b) => a.chapter !== b.chapter ? a.chapter - b.chapter : a.verse - b.verse)
        .map((e) => ({ chapter: e.chapter, verse: e.verse, tts_cache_id: e.id }));
      await startVideoGeneration({
        title: title || 'Untitled',
        format,
        resource_id: resourceId,
        reciter_id: reciterId,
        verses,
        english_only: englishOnly || undefined,
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

  async function handleDeleteVideo(id: number) {
    try {
      await deleteGeneratedVideo(id);
      setVideos((prev) => prev.filter((v) => v.id !== id));
    } catch (err) {
      setGenError(err instanceof Error ? err.message : 'Delete failed');
    }
  }

  async function handleGenerateDescription() {
    if (selectedIds.size === 0) return;
    setGeneratingDesc(true);
    setGenError('');
    try {
      const verses = ttsEntries
        .filter((e) => selectedIds.has(e.id))
        .sort((a, b) => a.chapter !== b.chapter ? a.chapter - b.chapter : a.verse - b.verse)
        .map((e) => ({ chapter: e.chapter, verse: e.verse }));
      const desc = await generateDescription(verses);
      setDescription(desc);
    } catch (err) {
      setGenError(err instanceof Error ? err.message : 'Failed to generate description');
    } finally {
      setGeneratingDesc(false);
    }
  }

  // Group TTS entries by surah
  const grouped = ttsEntries.reduce<Record<string, TTSCacheEntry[]>>((acc, e) => {
    const key = `${e.chapter}. ${e.surah_name}`;
    (acc[key] ??= []).push(e);
    return acc;
  }, {});

  const reciterLabel = (r: Reciter) =>
    r.style ? `${r.reciter_name} (${r.style})` : r.reciter_name;

  return (
    <div>
      <h1 className="text-xl font-semibold text-stone-800 mb-6">Generate Video</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Left: Config */}
        <div className="space-y-5">
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

          {/* English Only */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={englishOnly}
              onChange={(e) => setEnglishOnly(e.target.checked)}
              className="rounded border-stone-300"
            />
            <span className="text-sm text-stone-700">English only</span>
            <span className="text-xs text-stone-400">(no Arabic recitation or text)</span>
          </label>

          {/* Background */}
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

          {/* Reciter */}
          {!englishOnly && (
            <div>
              <label className="block text-sm font-medium text-stone-700 mb-1">Reciter</label>
              <select
                value={reciterId}
                onChange={(e) => setReciterId(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-stone-400"
              >
                {reciters.map((r) => (
                  <option key={r.id} value={r.id}>{reciterLabel(r)}</option>
                ))}
              </select>
            </div>
          )}

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => { setTitle(e.target.value); setTitleManuallyEdited(true); }}
              placeholder="Auto-generated from selection..."
              className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400"
            />
            {titleManuallyEdited && (
              <button
                onClick={() => { setTitleManuallyEdited(false); }}
                className="text-xs text-blue-500 hover:underline mt-1 cursor-pointer"
              >
                Reset to auto-title
              </button>
            )}
          </div>

          {/* Description */}
          {selectedIds.size > 0 && (
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-sm font-medium text-stone-700">YouTube Description</label>
                <button
                  onClick={handleGenerateDescription}
                  disabled={generatingDesc}
                  className="text-xs text-indigo-600 hover:text-indigo-800 disabled:opacity-50 cursor-pointer"
                >
                  {generatingDesc ? 'Generating...' : description ? 'Regenerate' : 'Generate with AI'}
                </button>
              </div>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Click 'Generate with AI' to create a description from the selected verses..."
                rows={6}
                className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-stone-400 resize-y"
              />
              {description && (
                <button
                  onClick={() => { navigator.clipboard.writeText(description); }}
                  className="text-xs text-stone-400 hover:text-stone-600 mt-1 cursor-pointer"
                >
                  Copy to clipboard
                </button>
              )}
            </div>
          )}

          {/* Generate */}
          <button
            onClick={handleGenerate}
            disabled={generating || !resourceId || selectedIds.size === 0}
            className="px-5 py-2.5 rounded-lg bg-emerald-700 text-white text-sm font-medium hover:bg-emerald-600 disabled:opacity-50 transition-colors cursor-pointer"
          >
            {generating ? 'Starting...' : `Generate Video (${selectedIds.size} verses)`}
          </button>

          {genError && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {genError}
            </div>
          )}
        </div>

        {/* Right: Verse selector */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-stone-700">
              Select Verses ({selectedIds.size} selected)
            </label>
            <div className="flex gap-2">
              <button onClick={selectAll} className="text-xs text-blue-500 hover:underline cursor-pointer">All</button>
              <button onClick={selectNone} className="text-xs text-stone-400 hover:underline cursor-pointer">None</button>
            </div>
          </div>

          {ttsEntries.length === 0 ? (
            <p className="text-sm text-stone-400">
              No cached translations. <a href="/admin/media/recitations" className="text-blue-500 hover:underline">Generate some first</a>.
            </p>
          ) : (
            <div className="border border-stone-200 rounded-lg max-h-96 overflow-y-auto">
              {Object.entries(grouped).map(([surah, entries]) => (
                <div key={surah}>
                  <div className="sticky top-0 bg-stone-50 px-3 py-1.5 text-xs font-semibold text-stone-500 border-b border-stone-100">
                    {surah}
                  </div>
                  {entries.sort((a, b) => a.verse - b.verse).map((entry) => (
                    <label
                      key={entry.id}
                      className={`flex items-start gap-2 px-3 py-2 cursor-pointer hover:bg-stone-50 border-b border-stone-50 ${
                        selectedIds.has(entry.id) ? 'bg-emerald-50/50' : ''
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedIds.has(entry.id)}
                        onChange={() => toggleVerse(entry.id)}
                        className="mt-0.5"
                      />
                      <div className="flex-1 min-w-0">
                        <span className="text-sm text-stone-800">
                          {entry.chapter}:{entry.verse}
                        </span>
                        <p className="text-xs text-stone-400 truncate">
                          {entry.translation_text}
                        </p>
                      </div>
                      <span className="text-xs text-stone-300 whitespace-nowrap">
                        {entry.voice_name || 'voice'}
                      </span>
                    </label>
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Generated videos */}
      {videos.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-stone-800 mb-3">Generated Videos</h2>
          <div className="border border-stone-200 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-stone-50 text-stone-500 text-xs">
                <tr>
                  <th className="text-left px-3 py-2 font-medium">Title</th>
                  <th className="text-left px-3 py-2 font-medium">Format</th>
                  <th className="text-left px-3 py-2 font-medium">Status</th>
                  <th className="text-left px-3 py-2 font-medium">Size</th>
                  <th className="px-3 py-2 font-medium w-32">Actions</th>
                </tr>
              </thead>
              <tbody>
                {videos.map((v) => (
                  <VideoRow key={v.id} video={v} onDelete={handleDeleteVideo} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function VideoRow({ video, onDelete }: { video: GeneratedVideo; onDelete: (id: number) => void }) {
  const [downloadError, setDownloadError] = useState('');

  async function handleDownload() {
    setDownloadError('');
    try {
      const token = getToken();
      const res = await fetch(generatedVideoDownloadUrl(video.id), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`Download failed (${res.status})`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      // Sanitize title for filename
      const safeName = video.title.replace(/[^\w\s.-]/g, '').trim() || 'video';
      a.download = `${safeName}.mp4`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setDownloadError(err instanceof Error ? err.message : 'Download failed');
    }
  }

  const statusColor = {
    pending: 'text-amber-600',
    processing: 'text-blue-600',
    complete: 'text-emerald-600',
    failed: 'text-red-600',
  }[video.status] || 'text-stone-500';

  return (
    <tr className="border-t border-stone-100">
      <td className="px-3 py-2 text-stone-800">{video.title}</td>
      <td className="px-3 py-2 text-stone-500">{video.format === 'short' ? '9:16' : '16:9'}</td>
      <td className={`px-3 py-2 ${statusColor}`}>
        {video.status === 'processing' ? video.progress || 'Processing...' : video.status}
        {video.status === 'failed' && video.error_message && (
          <span className="block text-xs text-red-400 mt-0.5 max-w-xs truncate" title={video.error_message}>
            {video.error_message}
          </span>
        )}
        {downloadError && (
          <span className="block text-xs text-red-400 mt-0.5">{downloadError}</span>
        )}
      </td>
      <td className="px-3 py-2 text-stone-400">{video.file_size ? formatBytes(video.file_size) : '--'}</td>
      <td className="px-3 py-2 text-right whitespace-nowrap">
        {video.status === 'complete' && (
          <button
            onClick={handleDownload}
            className="text-xs text-blue-500 hover:text-blue-700 mr-2 cursor-pointer"
          >
            Download
          </button>
        )}
        <button
          onClick={() => onDelete(video.id)}
          className="text-xs text-red-400 hover:text-red-600 cursor-pointer"
        >
          Delete
        </button>
      </td>
    </tr>
  );
}
