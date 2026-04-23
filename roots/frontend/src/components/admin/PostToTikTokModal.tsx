import { useState, useEffect, useRef } from 'react';
import {
  pipelineVideoDownloadUrl,
  uploadPipelineVideoToTiktok,
  getToken,
} from '../../api/admin';
import type { PipelineVideo } from '../../api/admin';

interface Props {
  video: PipelineVideo;
  onClose: () => void;
  onUploaded: (tiktokVideoId: string | null, publishId: string) => void;
}

/**
 * Upload a completed pipeline video to TikTok via the Content Posting API.
 *
 * While the app is in TikTok's sandbox (pre-approval) the privacy level is
 * hard-locked to SELF_ONLY — TikTok rejects PUBLIC_TO_EVERYONE for unapproved
 * apps. Post-approval we can relax this.
 */
export default function PostToTikTokModal({ video, onClose, onUploaded }: Props) {
  // Seed caption from YouTube title + description if nothing TikTok-specific yet.
  const seedCaption = (() => {
    if (video.tiktok_caption) return video.tiktok_caption;
    const t = (video.youtube_title || '').trim();
    const d = (video.youtube_description || '').trim();
    return t ? (d ? `${t}\n\n${d}` : t) : d;
  })();
  const [caption, setCaption] = useState(seedCaption.slice(0, 2200));

  const [videoBlobUrl, setVideoBlobUrl] = useState<string | null>(null);
  const [loadingVideo, setLoadingVideo] = useState(true);

  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [done, setDone] = useState<{ tiktok_video_id: string | null; publish_id: string; note: string } | null>(null);
  const blobUrlRef = useRef<string | null>(null);

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
      .catch(() => {})
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

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape' && !uploading) onClose();
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [uploading, onClose]);

  async function handlePublish() {
    setUploading(true);
    setError('');
    try {
      const result = await uploadPipelineVideoToTiktok(video.id, {
        caption,
        privacy_level: 'SELF_ONLY',
      });
      setDone({
        tiktok_video_id: result.tiktok_video_id,
        publish_id: result.publish_id,
        note: result.note,
      });
      onUploaded(result.tiktok_video_id, result.publish_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  }

  const charCount = caption.length;
  const overLimit = charCount > 2200;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl bg-white shadow-xl">
        <div className="flex items-start justify-between border-b border-stone-200 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-stone-800">Post to TikTok</h2>
            <p className="text-xs text-stone-500 mt-0.5">
              Sandbox / unapproved apps post as <code className="px-1 bg-stone-100 rounded">SELF_ONLY</code> —
              video will be visible only to you on TikTok.
            </p>
          </div>
          <button
            onClick={onClose}
            disabled={uploading}
            className="text-stone-400 hover:text-stone-600 disabled:opacity-40 cursor-pointer"
          >
            ✕
          </button>
        </div>

        <div className="px-6 py-4 space-y-4">
          {/* Preview */}
          <div className="rounded-lg bg-stone-900 aspect-[9/16] max-h-64 mx-auto flex items-center justify-center overflow-hidden">
            {loadingVideo ? (
              <div className="text-stone-400 text-xs">Loading preview…</div>
            ) : videoBlobUrl ? (
              <video
                src={videoBlobUrl}
                controls
                className="h-full w-full object-contain"
              />
            ) : (
              <div className="text-stone-500 text-xs">(preview unavailable)</div>
            )}
          </div>

          {/* Caption */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm font-medium text-stone-700">Caption</label>
              <span className={`text-[10px] ${overLimit ? 'text-red-600' : 'text-stone-400'}`}>
                {charCount} / 2200
              </span>
            </div>
            <textarea
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              rows={5}
              disabled={uploading || !!done}
              className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400 disabled:bg-stone-50"
              placeholder="Caption shown on TikTok. Hashtags are parsed automatically."
            />
            <p className="mt-1 text-[11px] text-stone-400">
              TikTok captions support hashtags. Keep the first sentence strong — it's what viewers see in feed.
            </p>
          </div>

          {/* Error / Done */}
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs px-3 py-2">
              {error}
            </div>
          )}
          {done && (
            <div className="rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs px-3 py-2 space-y-1">
              <div className="font-medium">Published to TikTok ✓</div>
              <div><span className="text-emerald-600">Publish ID:</span> <code>{done.publish_id}</code></div>
              {done.tiktok_video_id && (
                <div><span className="text-emerald-600">Video ID:</span> <code>{done.tiktok_video_id}</code></div>
              )}
              <div className="text-emerald-700 italic">{done.note}</div>
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-2 border-t border-stone-200 px-6 py-3">
          <button
            onClick={onClose}
            disabled={uploading}
            className="px-4 py-2 rounded-lg text-sm text-stone-600 hover:bg-stone-100 disabled:opacity-50 cursor-pointer"
          >
            {done ? 'Close' : 'Cancel'}
          </button>
          {!done && (
            <button
              onClick={handlePublish}
              disabled={uploading || !caption.trim() || overLimit}
              className="px-4 py-2 rounded-lg bg-black text-white text-sm font-medium hover:bg-stone-800 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {uploading ? 'Uploading…' : 'Publish to TikTok'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
