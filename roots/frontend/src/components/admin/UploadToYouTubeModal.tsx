import { useState, useEffect, useRef } from 'react';
import {
  pipelineVideoDownloadUrl,
  uploadPipelineVideoToYouTube,
  regeneratePipelineVideoMetadata,
  getToken,
} from '../../api/admin';
import type { PipelineVideo } from '../../api/admin';

interface Props {
  video: PipelineVideo;
  onClose: () => void;
  onUploaded: (youtubeVideoId: string) => void;
}

/**
 * Upload a completed pipeline video to YouTube.
 *
 * Shows a preview (rendered from a blob URL so auth headers work),
 * editable title/description/tags (seeded from the stored AI-generated
 * metadata), and a privacy selector. On Publish, POSTs to the backend
 * which does the actual YouTube Data API v3 upload.
 */
export default function UploadToYouTubeModal({ video, onClose, onUploaded }: Props) {
  const [title, setTitle] = useState(video.youtube_title || '');
  const [description, setDescription] = useState(video.youtube_description || '');
  const [tagsInput, setTagsInput] = useState(parseTagsToString(video.youtube_tags));
  const [privacy, setPrivacy] = useState<'public' | 'unlisted' | 'private'>('public');

  const [videoBlobUrl, setVideoBlobUrl] = useState<string | null>(null);
  const [loadingVideo, setLoadingVideo] = useState(true);

  const [uploading, setUploading] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [regenerateMsg, setRegenerateMsg] = useState('');
  const [error, setError] = useState('');
  const [done, setDone] = useState<{ youtube_video_id: string; youtube_url: string } | null>(null);
  const blobUrlRef = useRef<string | null>(null);

  // Fetch the video as a blob with the auth header, then hand the blob URL to
  // <video> so it plays inline. Revoke on unmount.
  useEffect(() => {
    let cancelled = false;
    const token = getToken();
    setLoadingVideo(true);
    fetch(pipelineVideoDownloadUrl(video.id), {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then(async (r) => {
        if (!r.ok) throw new Error('Failed to load video');
        return r.blob();
      })
      .then((blob) => {
        if (cancelled) return;
        const url = URL.createObjectURL(blob);
        blobUrlRef.current = url;
        setVideoBlobUrl(url);
      })
      .catch(() => {
        if (cancelled) return;
        // not fatal — upload still works even if preview fails
      })
      .finally(() => {
        if (!cancelled) setLoadingVideo(false);
      });

    return () => {
      cancelled = true;
      if (blobUrlRef.current) {
        URL.revokeObjectURL(blobUrlRef.current);
        blobUrlRef.current = null;
      }
    };
  }, [video.id]);

  // Close on Escape (unless uploading)
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape' && !uploading) onClose();
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [uploading, onClose]);

  async function handleRegenerate() {
    setError('');
    setRegenerateMsg('');
    setRegenerating(true);
    try {
      const result = await regeneratePipelineVideoMetadata(video.id, {
        onProgress: (seconds) => {
          setRegenerateMsg(`Thinking... ${seconds}s`);
        },
      });
      setTitle(result.title || '');
      setDescription(result.description || '');
      setTagsInput((result.tags || []).join(', '));
      setRegenerateMsg('Regenerated');
      setTimeout(() => setRegenerateMsg(''), 2500);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Metadata regeneration failed');
      setRegenerateMsg('');
    } finally {
      setRegenerating(false);
    }
  }

  async function handlePublish() {
    setError('');
    const tags = parseStringToTags(tagsInput);
    if (!title.trim()) { setError('Title is required'); return; }
    if (title.length > 100) { setError('Title must be under 100 characters'); return; }
    if (description.length > 5000) { setError('Description must be under 5000 characters'); return; }

    setUploading(true);
    try {
      const result = await uploadPipelineVideoToYouTube(video.id, {
        title: title.trim(),
        description: description.trim(),
        tags,
        privacy,
      });
      setDone({
        youtube_video_id: result.youtube_video_id,
        youtube_url: result.youtube_url,
      });
      onUploaded(result.youtube_video_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  }

  // Success view
  if (done) {
    return (
      <div
        className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-stone-900/60 backdrop-blur-sm"
        onClick={onClose}
      >
        <div
          className="w-full max-w-md rounded-2xl bg-white shadow-2xl border border-stone-200 p-6"
          onClick={(e) => e.stopPropagation()}
        >
          <h3 className="text-lg font-semibold text-stone-800 mb-2">Uploaded to YouTube</h3>
          <p className="text-sm text-stone-600 mb-4">
            Your video was uploaded successfully.
          </p>
          <a
            href={done.youtube_url}
            target="_blank"
            rel="noopener noreferrer"
            className="block text-sm text-red-600 hover:text-red-700 font-medium break-all mb-4"
          >
            {done.youtube_url}
          </a>
          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 cursor-pointer"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-stone-900/60 backdrop-blur-sm"
      onClick={() => !uploading && onClose()}
    >
      <div
        className="w-full max-w-3xl rounded-2xl bg-white shadow-2xl border border-stone-200 overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-stone-100">
          <h3 className="text-base font-semibold text-stone-800">
            Upload to YouTube
          </h3>
          <button
            onClick={onClose}
            disabled={uploading}
            className="text-stone-400 hover:text-stone-600 cursor-pointer text-xl leading-none disabled:cursor-not-allowed"
            title="Close"
          >×</button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 grid grid-cols-1 md:grid-cols-[auto_1fr] gap-5">
          {/* Video preview — fixed width, vertical aspect for Shorts */}
          <div className="md:w-56">
            <div className="aspect-[9/16] bg-stone-900 rounded-xl overflow-hidden">
              {loadingVideo ? (
                <div className="h-full flex items-center justify-center text-stone-400 text-xs">
                  Loading preview...
                </div>
              ) : videoBlobUrl ? (
                <video
                  src={videoBlobUrl}
                  controls
                  playsInline
                  className="w-full h-full object-contain"
                />
              ) : (
                <div className="h-full flex items-center justify-center text-stone-400 text-xs px-3 text-center">
                  Preview unavailable (upload still works)
                </div>
              )}
            </div>
          </div>

          {/* Form */}
          <div className="space-y-4">
            {/* Regenerate metadata — replaces title/description/tags with fresh AI output */}
            <div className="flex items-center justify-between gap-2 rounded-lg bg-stone-50 border border-stone-100 px-3 py-2">
              <span className="text-xs text-stone-500">
                Regenerate title, description, and tags with the AI metadata model.
              </span>
              <div className="flex items-center gap-2">
                {regenerateMsg && (
                  <span className="text-[10px] text-emerald-600">{regenerateMsg}</span>
                )}
                <button
                  type="button"
                  onClick={handleRegenerate}
                  disabled={regenerating || uploading}
                  className="px-3 py-1 rounded-md border border-stone-300 bg-white text-xs font-medium text-stone-700 hover:bg-stone-50 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                  {regenerating ? 'Regenerating...' : 'Regenerate Metadata'}
                </button>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-medium text-stone-600">Title</label>
                <span className={`text-[10px] ${title.length > 100 ? 'text-red-500' : 'text-stone-400'}`}>
                  {title.length} / 100
                </span>
              </div>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={uploading}
                className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400 disabled:bg-stone-50"
                placeholder="Video title"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-medium text-stone-600">Description</label>
                <span className={`text-[10px] ${description.length > 5000 ? 'text-red-500' : 'text-stone-400'}`}>
                  {description.length} / 5000
                </span>
              </div>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={uploading}
                rows={5}
                className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400 resize-y disabled:bg-stone-50"
                placeholder="Description"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">
                Tags <span className="font-normal text-stone-400">(comma-separated)</span>
              </label>
              <textarea
                value={tagsInput}
                onChange={(e) => setTagsInput(e.target.value)}
                disabled={uploading}
                rows={2}
                className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400 resize-y disabled:bg-stone-50"
                placeholder="Quran, reflection, 2:255, ..."
              />
              <div className="mt-1 flex flex-wrap gap-1.5">
                {parseStringToTags(tagsInput).map((tag, i) => (
                  <span
                    key={i}
                    className="inline-block rounded bg-stone-100 px-1.5 py-0.5 text-[10px] text-stone-600"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">Privacy</label>
              <div className="flex gap-2">
                {(['public', 'unlisted', 'private'] as const).map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPrivacy(p)}
                    disabled={uploading}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors cursor-pointer disabled:cursor-not-allowed ${
                      privacy === p
                        ? 'bg-stone-800 text-white border-stone-800'
                        : 'bg-white text-stone-600 border-stone-300 hover:bg-stone-50'
                    }`}
                  >
                    {p.charAt(0).toUpperCase() + p.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {error}
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 px-5 py-4 bg-stone-50 border-t border-stone-100">
          <button
            onClick={onClose}
            disabled={uploading}
            className="px-4 py-2 rounded-lg text-sm text-stone-600 hover:bg-stone-200 disabled:opacity-50 cursor-pointer"
          >
            Cancel
          </button>
          <button
            onClick={handlePublish}
            disabled={uploading || !title.trim()}
            className="px-5 py-2 rounded-lg bg-red-600 text-white text-sm font-semibold hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {uploading ? 'Publishing...' : 'Publish to YouTube'}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ----------------------------------------------------------------- */

function parseTagsToString(tagsJson: string | null): string {
  if (!tagsJson) return '';
  try {
    const arr = JSON.parse(tagsJson);
    return Array.isArray(arr) ? arr.join(', ') : '';
  } catch {
    return '';
  }
}

function parseStringToTags(s: string): string[] {
  return s
    .split(',')
    .map((t) => t.trim().replace(/^#/, ''))
    .filter(Boolean)
    .slice(0, 15);
}
