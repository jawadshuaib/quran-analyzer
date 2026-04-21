import { useState, useEffect, useRef } from 'react';
import { getResources, uploadResource, deleteResource, updateResource, resourceThumbnailUrl, getToken } from '../../api/admin';
import type { Resource } from '../../api/admin';
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

export default function AdminResources() {
  const [resources, setResources] = useState<Resource[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [deleteError, setDeleteError] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);
  const { confirm, dialog: confirmDialog } = useConfirm();

  useEffect(() => {
    getResources().then(setResources).catch(() => {});
  }, []);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadError('');
    setUploading(true);
    try {
      const resource = await uploadResource(file);
      setResources((prev) => [resource, ...prev]);
      // Only clear file input on success so user can retry on failure
      if (fileRef.current) fileRef.current.value = '';
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(id: number) {
    const resource = resources.find((r) => r.id === id);
    const ok = await confirm({
      title: 'Delete background video?',
      message: resource
        ? `Permanently delete "${resource.description || resource.original_name}"? This cannot be undone. Pipelines that use this video will need a new one selected.`
        : 'Permanently delete this background video? This cannot be undone.',
      confirmLabel: 'Delete',
      tone: 'danger',
    });
    if (!ok) return;
    setDeleteError('');
    try {
      await deleteResource(id);
      setResources((prev) => prev.filter((r) => r.id !== id));
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Delete failed');
    }
  }

  return (
    <div>
      <h1 className="text-xl font-semibold text-stone-800 mb-6">Background Videos</h1>

      {/* Upload */}
      <div className="mb-8">
        <label className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 transition-colors cursor-pointer">
          {uploading ? 'Uploading...' : 'Upload Video'}
          <input
            ref={fileRef}
            type="file"
            accept=".mp4,.mov,.webm"
            onChange={handleUpload}
            disabled={uploading}
            className="hidden"
          />
        </label>
        <span className="text-xs text-stone-400 ml-3">MP4, MOV, or WebM (max 500MB)</span>
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

      {/* Resource grid */}
      {resources.length === 0 && !uploading && (
        <p className="text-sm text-stone-400">No background videos uploaded yet.</p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {resources.map((r) => (
          <ResourceCard key={r.id} resource={r} onDelete={handleDelete} onUpdate={(updated) => setResources((prev) => prev.map((p) => p.id === updated.id ? updated : p))} />
        ))}
      </div>
      {confirmDialog}
    </div>
  );
}

function ResourceCard({ resource, onDelete, onUpdate }: { resource: Resource; onDelete: (id: number) => void; onUpdate: (r: Resource) => void }) {
  const [thumbSrc, setThumbSrc] = useState<string | null>(null);
  const [thumbError, setThumbError] = useState(false);
  const [desc, setDesc] = useState(resource.description || '');
  const [saving, setSaving] = useState(false);
  const dirty = desc !== (resource.description || '');

  useEffect(() => {
    let revoke: string | null = null;
    const token = getToken();
    fetch(resourceThumbnailUrl(resource.id), {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((res) => {
        if (!res.ok) throw new Error('Failed');
        return res.blob();
      })
      .then((blob) => {
        revoke = URL.createObjectURL(blob);
        setThumbSrc(revoke);
      })
      .catch(() => setThumbError(true));

    return () => {
      if (revoke) URL.revokeObjectURL(revoke);
    };
  }, [resource.id]);

  async function handleSaveDesc() {
    setSaving(true);
    try {
      const updated = await updateResource(resource.id, desc);
      onUpdate(updated);
    } catch { /* ignore */ }
    finally { setSaving(false); }
  }

  return (
    <div className="rounded-xl border border-stone-200 bg-white overflow-hidden">
      {/* Thumbnail */}
      <div className="aspect-video bg-stone-100 flex items-center justify-center">
        {thumbSrc ? (
          <img src={thumbSrc} alt={resource.original_name} className="w-full h-full object-cover" />
        ) : thumbError ? (
          <span className="text-xs text-stone-400">No preview</span>
        ) : (
          <span className="text-xs text-stone-300">Loading...</span>
        )}
      </div>
      {/* Info */}
      <div className="p-3">
        <p className="text-sm font-medium text-stone-800 truncate" title={resource.original_name}>
          {resource.original_name}
        </p>
        <div className="flex items-center gap-3 mt-1 text-xs text-stone-400">
          <span>{formatDuration(resource.duration_seconds)}</span>
          {resource.width && resource.height && <span>{resource.width}x{resource.height}</span>}
          <span>{formatBytes(resource.file_size)}</span>
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
        <button
          onClick={() => onDelete(resource.id)}
          className="mt-2 text-xs text-red-400 hover:text-red-600 cursor-pointer"
        >
          Delete
        </button>
      </div>
    </div>
  );
}
