import { useState, useEffect, useRef } from 'react';
import { getMusicTracks, uploadMusicTrack, deleteMusicTrack, updateMusicTrack, musicAudioUrl, getToken } from '../../api/admin';
import type { MusicTrack } from '../../api/admin';
import { useConfirm } from './shared/useConfirm';

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDuration(seconds: number | null): string {
  if (!seconds) return '--';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export default function AdminMusic() {
  const [tracks, setTracks] = useState<MusicTrack[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [deleteError, setDeleteError] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);
  const { confirm, dialog: confirmDialog } = useConfirm();

  useEffect(() => {
    getMusicTracks().then(setTracks).catch(() => {});
  }, []);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadError('');
    setUploading(true);
    try {
      const track = await uploadMusicTrack(file);
      setTracks((prev) => [track, ...prev]);
      if (fileRef.current) fileRef.current.value = '';
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(id: number) {
    const track = tracks.find((t) => t.id === id);
    const ok = await confirm({
      title: 'Delete music track?',
      message: track
        ? `Permanently delete "${track.description || track.original_name}"? This cannot be undone. Pipelines that use this track will need a new one selected.`
        : 'Permanently delete this music track? This cannot be undone.',
      confirmLabel: 'Delete',
      tone: 'danger',
    });
    if (!ok) return;
    setDeleteError('');
    try {
      await deleteMusicTrack(id);
      setTracks((prev) => prev.filter((t) => t.id !== id));
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Delete failed');
    }
  }

  return (
    <div>
      <h1 className="text-xl font-semibold text-stone-800 mb-6">Background Music</h1>

      {/* Upload */}
      <div className="mb-8">
        <label className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 transition-colors cursor-pointer">
          {uploading ? 'Uploading...' : 'Upload Track'}
          <input
            ref={fileRef}
            type="file"
            accept=".mp3,.wav,.m4a,.aac,.ogg,.flac"
            onChange={handleUpload}
            disabled={uploading}
            className="hidden"
          />
        </label>
        <span className="text-xs text-stone-400 ml-3">MP3, WAV, M4A, AAC, OGG, or FLAC</span>
        {uploadError && (
          <div className="mt-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 max-w-md">
            {uploadError}
          </div>
        )}
        {deleteError && (
          <div className="mt-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 max-w-md">
            {deleteError}
          </div>
        )}
      </div>

      {/* Track list */}
      {tracks.length === 0 && !uploading && (
        <p className="text-sm text-stone-400">No background music uploaded yet.</p>
      )}

      <div className="space-y-3 max-w-2xl">
        {tracks.map((t) => (
          <MusicCard key={t.id} track={t} onDelete={handleDelete} onUpdate={(updated) => setTracks((prev) => prev.map((p) => p.id === updated.id ? updated : p))} />
        ))}
      </div>
      {confirmDialog}
    </div>
  );
}

function MusicCard({ track, onDelete, onUpdate }: { track: MusicTrack; onDelete: (id: number) => void; onUpdate: (t: MusicTrack) => void }) {
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [desc, setDesc] = useState(track.description || '');
  const [saving, setSaving] = useState(false);
  const dirty = desc !== (track.description || '');

  function handlePlay() {
    if (audioUrl) {
      setAudioUrl(null);
      return;
    }
    const token = getToken();
    fetch(musicAudioUrl(track.id), {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((res) => {
        if (!res.ok) throw new Error('Failed');
        return res.blob();
      })
      .then((blob) => setAudioUrl(URL.createObjectURL(blob)))
      .catch(() => {});
  }

  async function handleSaveDesc() {
    setSaving(true);
    try {
      const updated = await updateMusicTrack(track.id, desc);
      onUpdate(updated);
    } catch { /* ignore */ }
    finally { setSaving(false); }
  }

  return (
    <div className="rounded-xl border border-stone-200 bg-white p-4">
      <div className="flex items-center gap-4">
        <button
          onClick={handlePlay}
          className="flex-shrink-0 w-10 h-10 rounded-full bg-stone-100 hover:bg-stone-200 flex items-center justify-center text-stone-600 transition-colors cursor-pointer"
          title={audioUrl ? 'Stop' : 'Preview'}
        >
          {audioUrl ? (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>
          ) : (
            <svg className="w-4 h-4 ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          )}
        </button>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-stone-800 truncate" title={track.original_name}>
            {track.original_name}
          </p>
          <div className="flex items-center gap-3 mt-0.5 text-xs text-stone-400">
            <span>{formatDuration(track.duration_seconds)}</span>
            <span>{formatBytes(track.file_size)}</span>
          </div>
        </div>
        <button
          onClick={() => onDelete(track.id)}
          className="text-xs text-red-400 hover:text-red-600 cursor-pointer flex-shrink-0"
        >
          Delete
        </button>
        {audioUrl && (
          <audio src={audioUrl} autoPlay onEnded={() => setAudioUrl(null)} className="hidden" />
        )}
      </div>
      {/* Description */}
      <div className="mt-2">
        <input
          type="text"
          value={desc}
          onChange={(e) => setDesc(e.target.value)}
          onBlur={() => { if (dirty) handleSaveDesc(); }}
          onKeyDown={(e) => { if (e.key === 'Enter' && dirty) handleSaveDesc(); }}
          placeholder="Add a description..."
          maxLength={500}
          className="w-full text-xs text-stone-600 border border-stone-200 rounded-md px-2 py-1.5 focus:outline-none focus:border-stone-400 placeholder:text-stone-300"
        />
        {saving && <span className="text-[10px] text-stone-400 mt-0.5 block">Saving...</span>}
      </div>
    </div>
  );
}
