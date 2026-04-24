import { useState, useEffect, useRef } from 'react';
import { pipelineVideoDownloadUrl, getToken } from '../../api/admin';

/**
 * Lazy-loading preview player for a pipeline video.
 *
 * Shows a small play-button poster by default; on click, fetches the
 * video bytes with the admin auth header, wraps them as a blob URL, and
 * hands that to a standard <video controls> element. Blob gets revoked
 * on unmount so long pipeline pages don't leak memory.
 *
 * We can't use a plain <video src="/api/admin/..."> because the download
 * endpoint requires an Authorization: Bearer header, and <video> elements
 * don't send custom headers on media fetches. Blob is the workaround.
 */
export default function InlineVideoPreview({ videoId }: { videoId: number }) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const blobRef = useRef<string | null>(null);

  useEffect(() => {
    return () => {
      if (blobRef.current) {
        URL.revokeObjectURL(blobRef.current);
        blobRef.current = null;
      }
    };
  }, []);

  async function handleLoad() {
    if (blobUrl || loading) return;
    setLoading(true);
    setError('');
    try {
      const token = getToken();
      const res = await fetch(pipelineVideoDownloadUrl(videoId), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`Failed (${res.status})`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      blobRef.current = url;
      setBlobUrl(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }

  // 9:16 aspect ratio placeholder sized to match card height
  const baseClasses =
    'flex-shrink-0 w-20 sm:w-24 aspect-[9/16] rounded-md overflow-hidden bg-stone-900 relative';

  if (blobUrl) {
    return (
      <div className={baseClasses}>
        <video
          src={blobUrl}
          controls
          autoPlay
          playsInline
          className="h-full w-full object-contain bg-black"
        />
      </div>
    );
  }

  return (
    <button
      type="button"
      onClick={handleLoad}
      disabled={loading}
      aria-label="Load preview"
      title={error ? `Error: ${error}` : 'Click to preview'}
      className={`${baseClasses} flex items-center justify-center cursor-pointer group transition-colors ${
        error ? 'bg-red-900/30 hover:bg-red-900/50' : 'hover:bg-stone-800'
      }`}
    >
      {loading ? (
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-stone-500 border-t-stone-200" />
      ) : (
        <svg
          className={`h-7 w-7 transition-transform group-hover:scale-110 ${
            error ? 'text-red-300' : 'text-stone-400 group-hover:text-stone-200'
          }`}
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          <path d="M8 5v14l11-7z" />
        </svg>
      )}
    </button>
  );
}
