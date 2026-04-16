import { useState, useEffect, useRef, useCallback } from 'react';
import { fetchSurahs } from '../../api/quran';
import {
  getReciters, getVoices, getPreferences, savePreferences,
  getRecitationPreview,
} from '../../api/admin';
import type { Reciter, Voice, PreviewVerse } from '../../api/admin';
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

  // Playback
  const [playState, setPlayState] = useState<PlayState>('idle');
  const [currentIdx, setCurrentIdx] = useState(-1);
  const [currentPhase, setCurrentPhase] = useState<'recitation' | 'translation'>('recitation');
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const playingRef = useRef(false); // tracks if we should keep playing

  // Load initial data
  useEffect(() => {
    fetchSurahs().then(setSurahs);
    getReciters().then(setReciters).catch(() => {});
    getVoices().then(setVoices).catch(() => {});
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
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
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

      // Phase 2: Translation (pause to show translation — TTS will go here later)
      setCurrentPhase('translation');
      // For now, wait 2 seconds per translation line (TTS placeholder)
      await new Promise((r) => setTimeout(r, Math.max(2000, verse.translation.length * 40)));
      if (!playingRef.current) break;
    }

    if (playingRef.current) {
      setPlayState('idle');
      setCurrentIdx(-1);
      playingRef.current = false;
    }
  }, [previewVerses, playAudio]);

  const togglePause = useCallback(() => {
    if (!audioRef.current) return;
    if (playState === 'playing') {
      audioRef.current.pause();
      setPlayState('paused');
    } else if (playState === 'paused') {
      audioRef.current.play();
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
    </div>
  );
}
