import { useState, useEffect, useRef, useCallback } from 'react';
import { fetchSurahs } from '../../api/quran';
import {
  getReciters, getVoices, getPreferences, savePreferences,
  getRecitationPreview, generateTTS,
  getTTSCache, deleteTTSCache, ttsCacheAudioUrl, getToken,
} from '../../api/admin';
import type { Reciter, Voice, PreviewVerse, TTSCacheEntry } from '../../api/admin';
import type { SurahInfo } from '../../types';

type PlayState = 'idle' | 'playing' | 'paused';

export default function VerseRecitations() {
  // Data lists
  const [surahs, setSurahs] = useState<SurahInfo[]>([]);
  const [reciters, setReciters] = useState<Reciter[]>([]);
  const [voices, setVoices] = useState<Voice[]>([]);

  // Selections
  const [reciterId, setReciterId] = useState(7); // Mishari default
  const [voiceId, setVoiceId] = useState<number | null>(null);
  const [fromSurah, setFromSurah] = useState(1);
  const [fromAyah, setFromAyah] = useState(1);
  const [toSurah, setToSurah] = useState(1);
  const [toAyah, setToAyah] = useState(1);

  // Preview
  const [previewVerses, setPreviewVerses] = useState<PreviewVerse[]>([]);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [previewError, setPreviewError] = useState('');

  // TTS cache & batch generation
  const [ttsCache, setTtsCache] = useState<TTSCacheEntry[]>([]);
  const [generating, setGenerating] = useState(false);
  const [genProgress, setGenProgress] = useState('');

  // Playback
  const [playState, setPlayState] = useState<PlayState>('idle');
  const [currentIdx, setCurrentIdx] = useState(-1);
  const [currentPhase, setCurrentPhase] = useState<'recitation' | 'translation'>('recitation');
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const playingRef = useRef(false); // tracks if we should keep playing
  const pausedRef = useRef(false);  // tracks pause state for translation phase
  const translationTimerRef = useRef<number | null>(null); // cancellable translation delay

  // Load initial data
  const refreshCache = useCallback(() => {
    getTTSCache().then(setTtsCache).catch(() => {});
  }, []);

  useEffect(() => {
    fetchSurahs().then(setSurahs);
    getReciters().then(setReciters).catch(() => {});
    getVoices().then(setVoices).catch(() => {});
    refreshCache();
    getPreferences().then((prefs) => {
      if (prefs.last_reciter_id) setReciterId(Number(prefs.last_reciter_id));
      if (prefs.last_voice_id) setVoiceId(Number(prefs.last_voice_id));
    }).catch(() => {});
  }, []);

  // Verse count for selected surah
  const fromMaxAyah = surahs.find((s) => s.number === fromSurah)?.verse_count ?? 1;
  const toMaxAyah = surahs.find((s) => s.number === toSurah)?.verse_count ?? 1;

  // Clamp ayah when surah changes
  useEffect(() => { if (fromAyah > fromMaxAyah) setFromAyah(1); }, [fromSurah, fromMaxAyah]);
  useEffect(() => { if (toAyah > toMaxAyah) setToAyah(1); }, [toSurah, toMaxAyah]);

  // Sync "to" with "from" if to < from
  useEffect(() => {
    if (toSurah < fromSurah || (toSurah === fromSurah && toAyah < fromAyah)) {
      setToSurah(fromSurah);
      setToAyah(fromAyah);
    }
  }, [fromSurah, fromAyah]);

  // Save reciter preference
  function handleReciterChange(id: number) {
    setReciterId(id);
    savePreferences({ last_reciter_id: String(id) }).catch(() => {});
  }

  // Save voice preference
  function handleVoiceChange(id: number) {
    setVoiceId(id);
    savePreferences({ last_voice_id: String(id) }).catch(() => {});
  }

  // Load preview
  async function loadPreview() {
    setPreviewError('');
    setLoadingPreview(true);
    stopPlayback();
    try {
      const verses = await getRecitationPreview({
        reciter_id: reciterId,
        from_surah: fromSurah,
        from_ayah: fromAyah,
        to_surah: toSurah,
        to_ayah: toAyah,
      });
      setPreviewVerses(verses);
    } catch (err) {
      setPreviewError(err instanceof Error ? err.message : 'Failed to load preview');
    } finally {
      setLoadingPreview(false);
    }
  }

  // Playback controls
  const stopPlayback = useCallback(() => {
    playingRef.current = false;
    pausedRef.current = false;
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if (translationTimerRef.current) {
      clearTimeout(translationTimerRef.current);
      translationTimerRef.current = null;
    }
    setPlayState('idle');
    setCurrentIdx(-1);
    setCurrentPhase('recitation');
  }, []);

  const playAudio = useCallback((url: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => resolve();
      audio.onerror = () => reject(new Error('Audio failed'));
      audio.play().catch(reject);
    });
  }, []);

  // Get the ElevenLabs voice_id string for the selected voice
  const selectedVoiceElId = voices.find((v) => v.id === voiceId)?.voice_id ?? null;

  // Batch-generate TTS for all preview verses without playing
  async function generateAll() {
    if (!selectedVoiceElId || previewVerses.length === 0) return;
    setGenerating(true);
    setPreviewError('');
    for (let i = 0; i < previewVerses.length; i++) {
      const verse = previewVerses[i];
      if (!verse.translation) continue;
      setGenProgress(`Generating ${i + 1} of ${previewVerses.length}...`);
      try {
        const url = await generateTTS(verse.translation, selectedVoiceElId, verse.surah, verse.ayah);
        URL.revokeObjectURL(url); // we just wanted to cache it server-side
      } catch (err) {
        setPreviewError(`Failed on ${verse.surah}:${verse.ayah}: ${err instanceof Error ? err.message : 'TTS error'}`);
        break;
      }
    }
    setGenerating(false);
    setGenProgress('');
    refreshCache();
  }

  const startPlayback = useCallback(async () => {
    if (previewVerses.length === 0) return;
    playingRef.current = true;
    setPlayState('playing');

    for (let i = 0; i < previewVerses.length; i++) {
      if (!playingRef.current) break;
      const verse = previewVerses[i];

      // Phase 1: Recitation
      setCurrentIdx(i);
      setCurrentPhase('recitation');
      try {
        await playAudio(verse.audio_url);
      } catch {
        // Skip on error
      }
      if (!playingRef.current) break;

      // Phase 2: Translation — speak via ElevenLabs TTS or fall back to timed delay
      setCurrentPhase('translation');
      if (selectedVoiceElId && verse.translation) {
        try {
          const ttsUrl = await generateTTS(verse.translation, selectedVoiceElId, verse.surah, verse.ayah);
          if (!playingRef.current) break;
          await playAudio(ttsUrl);
          URL.revokeObjectURL(ttsUrl);
          refreshCache();
        } catch {
          // TTS failed — fall back to timed delay
          const totalMs = Math.max(2000, verse.translation.length * 40);
          let elapsed = 0;
          const tick = 100;
          while (elapsed < totalMs && playingRef.current) {
            if (!pausedRef.current) elapsed += tick;
            await new Promise((r) => { translationTimerRef.current = window.setTimeout(r, tick); });
            translationTimerRef.current = null;
          }
        }
      } else {
        // No voice selected — timed delay
        const totalMs = Math.max(2000, verse.translation.length * 40);
        let elapsed = 0;
        const tick = 100;
        while (elapsed < totalMs && playingRef.current) {
          if (!pausedRef.current) elapsed += tick;
          await new Promise((r) => { translationTimerRef.current = window.setTimeout(r, tick); });
          translationTimerRef.current = null;
        }
      }
      if (!playingRef.current) break;
    }

    if (playingRef.current) {
      setPlayState('idle');
      setCurrentIdx(-1);
      playingRef.current = false;
    }
  }, [previewVerses, playAudio, selectedVoiceElId, refreshCache]);

  const togglePause = useCallback(() => {
    if (playState === 'playing') {
      pausedRef.current = true;
      if (audioRef.current) audioRef.current.pause();
      setPlayState('paused');
    } else if (playState === 'paused') {
      pausedRef.current = false;
      if (audioRef.current) audioRef.current.play();
      setPlayState('playing');
    }
  }, [playState]);

  const reciterLabel = (r: Reciter) =>
    r.style ? `${r.reciter_name} (${r.style})` : r.reciter_name;

  return (
    <div>
      <h1 className="text-xl font-semibold text-stone-800 mb-6">Verse Recitations</h1>

      {/* Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* Left column: Reciter + Voice */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1">Reciter</label>
            <select
              value={reciterId}
              onChange={(e) => handleReciterChange(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-stone-400"
            >
              {reciters.map((r) => (
                <option key={r.id} value={r.id}>{reciterLabel(r)}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1">
              Translation Voice
              {voices.length === 0 && (
                <a href="/admin/settings" className="text-xs text-blue-500 ml-2 hover:underline">
                  Add voices in Settings
                </a>
              )}
            </label>
            <select
              value={voiceId ?? ''}
              onChange={(e) => handleVoiceChange(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-stone-400"
              disabled={voices.length === 0}
            >
              <option value="">Select a voice...</option>
              {voices.map((v) => (
                <option key={v.id} value={v.id}>{v.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Right column: Verse range */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1">From</label>
            <div className="flex gap-2">
              <select
                value={fromSurah}
                onChange={(e) => { setFromSurah(Number(e.target.value)); setFromAyah(1); }}
                className="flex-1 px-3 py-2 rounded-lg border border-stone-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-stone-400"
              >
                {surahs.map((s) => (
                  <option key={s.number} value={s.number}>
                    {s.number}. {s.name}
                  </option>
                ))}
              </select>
              <select
                value={fromAyah}
                onChange={(e) => setFromAyah(Number(e.target.value))}
                className="w-24 px-3 py-2 rounded-lg border border-stone-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-stone-400"
              >
                {Array.from({ length: fromMaxAyah }, (_, i) => i + 1).map((a) => (
                  <option key={a} value={a}>Ayah {a}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1">To</label>
            <div className="flex gap-2">
              <select
                value={toSurah}
                onChange={(e) => { setToSurah(Number(e.target.value)); setToAyah(1); }}
                className="flex-1 px-3 py-2 rounded-lg border border-stone-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-stone-400"
              >
                {surahs.map((s) => (
                  <option key={s.number} value={s.number}>
                    {s.number}. {s.name}
                  </option>
                ))}
              </select>
              <select
                value={toAyah}
                onChange={(e) => setToAyah(Number(e.target.value))}
                className="w-24 px-3 py-2 rounded-lg border border-stone-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-stone-400"
              >
                {Array.from({ length: toMaxAyah }, (_, i) => i + 1).map((a) => (
                  <option key={a} value={a}>Ayah {a}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Load button */}
      <div className="flex gap-3 mb-8">
        <button
          onClick={loadPreview}
          disabled={loadingPreview}
          className="px-5 py-2.5 rounded-lg bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 disabled:opacity-50 transition-colors cursor-pointer"
        >
          {loadingPreview ? 'Loading...' : 'Load Preview'}
        </button>

        {previewVerses.length > 0 && (
          <>
            {playState === 'idle' ? (
              <button
                onClick={startPlayback}
                className="px-5 py-2.5 rounded-lg bg-emerald-700 text-white text-sm font-medium hover:bg-emerald-600 transition-colors cursor-pointer"
              >
                Play All
              </button>
            ) : (
              <>
                <button
                  onClick={togglePause}
                  className="px-5 py-2.5 rounded-lg bg-amber-600 text-white text-sm font-medium hover:bg-amber-500 transition-colors cursor-pointer"
                >
                  {playState === 'playing' ? 'Pause' : 'Resume'}
                </button>
                <button
                  onClick={stopPlayback}
                  className="px-5 py-2.5 rounded-lg bg-red-600 text-white text-sm font-medium hover:bg-red-500 transition-colors cursor-pointer"
                >
                  Stop
                </button>
              </>
            )}
          </>
        )}

        {previewVerses.length > 0 && selectedVoiceElId && playState === 'idle' && (
          <button
            onClick={generateAll}
            disabled={generating}
            className="px-5 py-2.5 rounded-lg bg-blue-700 text-white text-sm font-medium hover:bg-blue-600 disabled:opacity-50 transition-colors cursor-pointer"
          >
            {generating ? genProgress || 'Generating...' : 'Generate Translations'}
          </button>
        )}
      </div>

      {previewError && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-4">
          {previewError}
        </div>
      )}

      {/* Preview cards */}
      {previewVerses.length > 0 && (
        <div className="space-y-4">
          {previewVerses.map((verse, i) => {
            const isActive = i === currentIdx;
            const showTranslation = isActive && currentPhase === 'translation';

            return (
              <div
                key={`${verse.surah}:${verse.ayah}`}
                className={`
                  rounded-xl border p-5 transition-all duration-300
                  ${isActive
                    ? 'border-emerald-400 bg-emerald-50/50 shadow-sm'
                    : i < currentIdx
                      ? 'border-stone-200 bg-stone-50 opacity-60'
                      : 'border-stone-200 bg-white'
                  }
                `}
              >
                {/* Verse ref */}
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-medium text-stone-400">
                    {verse.surah_name} {verse.surah}:{verse.ayah}
                  </span>
                  {isActive && (
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                      currentPhase === 'recitation'
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'bg-blue-100 text-blue-700'
                    }`}>
                      {currentPhase === 'recitation' ? 'Reciting...' : 'Translation'}
                    </span>
                  )}
                </div>

                {/* Arabic text */}
                <p
                  dir="rtl"
                  lang="ar"
                  className={`text-2xl leading-loose font-serif text-stone-800 mb-3 transition-opacity duration-300 ${
                    isActive && currentPhase === 'recitation' ? 'opacity-100' : 'opacity-80'
                  }`}
                >
                  {verse.arabic_text}
                </p>

                {/* Translation */}
                <p
                  className={`text-sm leading-relaxed transition-all duration-500 ${
                    showTranslation
                      ? 'text-blue-800 font-medium opacity-100'
                      : 'text-stone-500 opacity-70'
                  }`}
                >
                  {verse.translation}
                </p>
              </div>
            );
          })}
        </div>
      )}

      {/* Cached TTS table */}
      {ttsCache.length > 0 && (
        <div className="mt-10">
          <h2 className="text-lg font-semibold text-stone-800 mb-3">Generated Translations</h2>
          <p className="text-xs text-stone-400 mb-4">
            {ttsCache.length} cached — these will be reused on playback instead of calling ElevenLabs again.
          </p>
          <div className="border border-stone-200 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-stone-50 text-stone-500 text-xs">
                <tr>
                  <th className="text-left px-3 py-2 font-medium">Verse</th>
                  <th className="text-left px-3 py-2 font-medium">Translation</th>
                  <th className="text-left px-3 py-2 font-medium">Voice</th>
                  <th className="px-3 py-2 font-medium w-24">Actions</th>
                </tr>
              </thead>
              <tbody>
                {ttsCache.map((entry) => (
                  <TTSCacheRow key={entry.id} entry={entry} onDelete={(id) => {
                    deleteTTSCache(id).then(refreshCache).catch(() => {});
                  }} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function TTSCacheRow({ entry, onDelete }: { entry: TTSCacheEntry; onDelete: (id: number) => void }) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const blobUrlRef = useRef<string | null>(null);
  const [playing, setPlaying] = useState(false);

  // Clean up audio on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
      if (blobUrlRef.current) { URL.revokeObjectURL(blobUrlRef.current); blobUrlRef.current = null; }
    };
  }, []);

  function togglePlay() {
    if (playing && audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      if (blobUrlRef.current) { URL.revokeObjectURL(blobUrlRef.current); blobUrlRef.current = null; }
      setPlaying(false);
      return;
    }
    const token = getToken();
    fetch(ttsCacheAudioUrl(entry.id), {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((res) => res.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        blobUrlRef.current = url;
        const a = new Audio(url);
        audioRef.current = a;
        a.onended = () => { setPlaying(false); URL.revokeObjectURL(url); blobUrlRef.current = null; };
        a.play();
        setPlaying(true);
      })
      .catch(() => setPlaying(false));
  }

  const truncated = entry.translation_text.length > 80
    ? entry.translation_text.slice(0, 80) + '...'
    : entry.translation_text;

  return (
    <tr className="border-t border-stone-100">
      <td className="px-3 py-2 text-stone-800 whitespace-nowrap">
        {entry.surah_name} {entry.chapter}:{entry.verse}
      </td>
      <td className="px-3 py-2 text-stone-600 max-w-xs" title={entry.translation_text}>
        {truncated}
      </td>
      <td className="px-3 py-2 text-stone-500 whitespace-nowrap">
        {entry.voice_name || entry.voice_id.slice(0, 8)}
      </td>
      <td className="px-3 py-2 text-right whitespace-nowrap">
        <button
          onClick={togglePlay}
          className="text-xs text-blue-500 hover:text-blue-700 mr-2 cursor-pointer"
        >
          {playing ? 'Stop' : 'Play'}
        </button>
        <button
          onClick={() => onDelete(entry.id)}
          className="text-xs text-red-400 hover:text-red-600 cursor-pointer"
        >
          Delete
        </button>
      </td>
    </tr>
  );
}
