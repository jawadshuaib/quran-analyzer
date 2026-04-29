import { useEffect, useState } from 'react';
import { fetchDefaultReciter, reciterAudioUrl, type DefaultReciter } from '../api/quran';
import {
  getVerseAudioStatus,
  toggleVerseAudio,
  subscribeVerseAudio,
} from '../utils/verse-audio';

interface Props {
  surah: number;
  ayah: number;
}

/**
 * Stand-alone play button for a single verse. Used on the research
 * page (/verse/<ref>) next to the save/note buttons. The reader's
 * surah view has its own gutter version inline in ReaderVerse — both
 * share the verse-audio coordinator so only one verse plays at a
 * time across the whole app.
 */
export default function VersePlayButton({ surah, ayah }: Props) {
  const verseKey = `${surah}:${ayah}`;
  const [reciter, setReciter] = useState<DefaultReciter | null>(null);
  const [status, setStatus] = useState(() => getVerseAudioStatus(verseKey));

  useEffect(() => {
    fetchDefaultReciter().then(setReciter).catch(() => { /* silently disable */ });
  }, []);

  useEffect(() => {
    const update = () => setStatus(getVerseAudioStatus(verseKey));
    update();
    return subscribeVerseAudio(update);
  }, [verseKey]);

  if (!reciter) return null;

  const label =
    status === 'playing'
      ? 'Stop recitation'
      : status === 'loading'
        ? 'Loading recitation…'
        : `Play recitation (${reciter.name})`;

  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation();
        toggleVerseAudio(verseKey, reciterAudioUrl(reciter, surah, ayah));
      }}
      aria-label={label}
      title={label}
      className={`flex items-center justify-center rounded-full w-7 h-7 transition-colors ${
        status !== 'idle'
          ? 'text-amber-600 hover:text-amber-700'
          : 'text-stone-400 hover:text-amber-600'
      }`}
    >
      {status === 'loading' ? (
        <svg viewBox="0 0 16 16" className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M8 2a6 6 0 016 6" strokeLinecap="round" />
        </svg>
      ) : status === 'playing' ? (
        <svg viewBox="0 0 16 16" className="w-4 h-4" fill="currentColor">
          <rect x="4" y="3" width="3" height="10" rx="0.5" />
          <rect x="9" y="3" width="3" height="10" rx="0.5" />
        </svg>
      ) : (
        <svg viewBox="0 0 16 16" className="w-4 h-4" fill="currentColor">
          <path d="M5 3.2v9.6a.5.5 0 00.76.43l8-4.8a.5.5 0 000-.86l-8-4.8A.5.5 0 005 3.2z" />
        </svg>
      )}
    </button>
  );
}
