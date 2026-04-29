/**
 * Single shared <audio> element for the reader's per-verse play
 * buttons. Only one verse can play at a time; clicking a different
 * verse stops the current one. Components subscribe to know whether
 * they are the active verse and what state ('loading'/'playing') the
 * audio is in, so the play icon can render the right glyph.
 */

export type VerseAudioState = 'idle' | 'loading' | 'playing';

let audio: HTMLAudioElement | null = null;
let activeKey = '';
let state: VerseAudioState = 'idle';
const listeners = new Set<() => void>();

function notify() {
  for (const l of listeners) l();
}

function ensureAudio(): HTMLAudioElement {
  if (audio) return audio;
  audio = new Audio();
  audio.preload = 'none';
  audio.addEventListener('playing', () => {
    state = 'playing';
    notify();
  });
  audio.addEventListener('waiting', () => {
    state = 'loading';
    notify();
  });
  const stop = () => {
    activeKey = '';
    state = 'idle';
    notify();
  };
  audio.addEventListener('ended', stop);
  audio.addEventListener('error', stop);
  audio.addEventListener('pause', () => {
    if (state !== 'idle') {
      activeKey = '';
      state = 'idle';
      notify();
    }
  });
  return audio;
}

export function getVerseAudioStatus(key: string): VerseAudioState {
  return activeKey === key ? state : 'idle';
}

export function toggleVerseAudio(key: string, url: string) {
  const a = ensureAudio();
  if (activeKey === key && state !== 'idle') {
    a.pause();
    a.currentTime = 0;
    activeKey = '';
    state = 'idle';
    notify();
    return;
  }
  // Different verse (or restart). Reset, set new src, play.
  a.pause();
  a.src = url;
  activeKey = key;
  state = 'loading';
  notify();
  a.play().catch(() => {
    if (activeKey === key) {
      activeKey = '';
      state = 'idle';
      notify();
    }
  });
}

export function subscribeVerseAudio(fn: () => void): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}
