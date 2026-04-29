import { useEffect, useRef, useState } from 'react';
import {
  getReciters,
  getRecitationPreview,
  getPreferences,
  savePreferences,
  type Reciter,
} from '../../api/admin';

/**
 * Admin route that picks the default reciter used by the public
 * reader's per-verse play button (/read/<surah>). The same reciter
 * list comes from quran.com via /api/admin/reciters that the
 * Recitations media page uses.
 *
 * Persisted as `default_reciter_id` in admin_preferences. The public
 * `/api/reciter/default` endpoint reads that value to build the
 * per-verse audio URL on the reader.
 */
export default function VerseSettings() {
  const [reciters, setReciters] = useState<Reciter[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [savedId, setSavedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Preview state — plays the configured reciter's recitation for a
  // sample verse so the admin can hear the choice before committing.
  const [previewRef, setPreviewRef] = useState('1:1');
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    Promise.all([getReciters(), getPreferences()])
      .then(([rs, prefs]) => {
        setReciters(rs);
        const raw = prefs.default_reciter_id;
        const id = raw ? parseInt(raw, 10) : 7;
        const valid = rs.find((r) => r.id === id) ? id : (rs[0]?.id ?? null);
        setSelectedId(valid);
        setSavedId(valid);
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load reciters'))
      .finally(() => setLoading(false));
    return () => {
      audioRef.current?.pause();
    };
  }, []);

  async function handleSave() {
    if (selectedId == null) return;
    setSaving(true);
    setSaved(false);
    try {
      await savePreferences({ default_reciter_id: String(selectedId) });
      setSavedId(selectedId);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  }

  function handlePreview() {
    if (selectedId == null) return;
    if (playing) {
      audioRef.current?.pause();
      audioRef.current = null;
      setPlaying(false);
      return;
    }
    const m = previewRef.match(/^\s*(\d+)\s*:\s*(\d+)\s*$/);
    if (!m) {
      setError('Use the format surah:ayah, e.g. 1:1');
      return;
    }
    const surah = parseInt(m[1], 10);
    const ayah = parseInt(m[2], 10);
    setError('');
    // Reuse the admin recitation-preview endpoint — it returns audio
    // URLs for arbitrary reciter_id, so the admin can preview the
    // currently-selected reciter even before saving.
    getRecitationPreview({
      reciter_id: selectedId,
      from_surah: surah,
      from_ayah: ayah,
      to_surah: surah,
      to_ayah: ayah,
    })
      .then((verses) => {
        const url = verses[0]?.audio_url;
        if (!url) throw new Error('No audio for that verse');
        const audio = new Audio(url);
        audioRef.current = audio;
        audio.addEventListener('ended', () => setPlaying(false));
        audio.addEventListener('error', () => {
          setError('Failed to load audio for that verse');
          setPlaying(false);
        });
        audio.play().then(() => setPlaying(true)).catch(() => setPlaying(false));
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Preview failed'));
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-stone-500">
        <span className="h-3 w-3 animate-spin rounded-full border-2 border-stone-300 border-t-stone-600" />
        Loading reciters…
      </div>
    );
  }

  const dirty = selectedId !== savedId;

  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-semibold text-stone-800 mb-1">Verse Settings</h1>
      <p className="text-sm text-stone-500 mb-6">
        Reader-wide settings that affect what end-users see and hear on{' '}
        <code className="text-xs bg-stone-100 px-1 py-0.5 rounded">/read/&lt;surah&gt;</code>.
      </p>

      <div className="rounded-xl border border-stone-200 bg-white p-5">
        <h2 className="text-sm font-semibold text-stone-800 mb-1">Default reciter</h2>
        <p className="text-xs text-stone-500 mb-4">
          Selected reciter is used by the per-verse play button on every public
          reader page. Changes apply immediately after saving.
        </p>

        <label className="block text-xs font-medium text-stone-600 mb-1">Reciter</label>
        <select
          value={selectedId ?? ''}
          onChange={(e) => setSelectedId(parseInt(e.target.value, 10))}
          className="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm bg-white"
        >
          {reciters.map((r) => (
            <option key={r.id} value={r.id}>
              {r.reciter_name}
              {r.style ? ` (${r.style})` : ''}
              {r.translated_name?.name && r.translated_name.name !== r.reciter_name
                ? ` — ${r.translated_name.name}`
                : ''}
            </option>
          ))}
        </select>

        <div className="mt-4 flex items-end gap-3">
          <div>
            <label className="block text-xs font-medium text-stone-600 mb-1">Preview verse</label>
            <input
              type="text"
              value={previewRef}
              onChange={(e) => setPreviewRef(e.target.value)}
              placeholder="1:1"
              className="w-32 rounded-lg border border-stone-300 px-3 py-2 text-sm bg-white"
            />
          </div>
          <button
            type="button"
            onClick={handlePreview}
            disabled={selectedId == null}
            className="px-3 py-2 rounded-lg text-sm bg-stone-100 hover:bg-stone-200 text-stone-800 cursor-pointer disabled:opacity-50"
          >
            {playing ? 'Stop preview' : 'Preview'}
          </button>
        </div>

        <div className="mt-5 flex items-center gap-3">
          <button
            type="button"
            onClick={handleSave}
            disabled={!dirty || saving}
            className="px-4 py-2 rounded-lg text-sm bg-stone-800 text-white hover:bg-stone-700 cursor-pointer disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Save as default'}
          </button>
          {saved && <span className="text-xs text-emerald-700">Saved.</span>}
        </div>
      </div>

      {error && (
        <p className="mt-4 text-xs text-red-700">{error}</p>
      )}
    </div>
  );
}
