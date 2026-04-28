/**
 * Last-read position — used by the homepage's "Continue reading" card.
 *
 * Same defensive persistence rules as user-notes.ts:
 *   - Stable namespaced key: "quranExplorer.lastRead"
 *   - Versioned envelope
 *   - Never wiped except via explicit user clear
 *   - Multi-tab sync via the storage event + custom event
 */

const STORAGE_KEY = 'quranExplorer.lastRead';
const SCHEMA_VERSION = 1;
const CHANGE_EVENT = 'quranExplorer:lastRead-changed';

export interface LastRead {
  surah: number;
  verse: number;
  /** ISO timestamp of when this position was last seen. */
  savedAt: string;
}

interface Envelope {
  version: number;
  lastRead: LastRead | null;
}

function read(): Envelope {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { version: SCHEMA_VERSION, lastRead: null };
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object' && parsed.lastRead) {
      const lr = parsed.lastRead;
      if (
        typeof lr.surah === 'number' && lr.surah >= 1 && lr.surah <= 114 &&
        typeof lr.verse === 'number' && lr.verse >= 1 &&
        typeof lr.savedAt === 'string'
      ) {
        return { version: SCHEMA_VERSION, lastRead: lr };
      }
    }
  } catch {
    /* fall through */
  }
  return { version: SCHEMA_VERSION, lastRead: null };
}

function write(env: Envelope) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      version: SCHEMA_VERSION,
      lastRead: env.lastRead,
    }));
    window.dispatchEvent(new CustomEvent(CHANGE_EVENT));
  } catch {
    /* silent */
  }
}

export function getLastRead(): LastRead | null {
  return read().lastRead;
}

export function setLastRead(surah: number, verse: number): void {
  if (surah < 1 || surah > 114 || verse < 1) return;
  write({ version: SCHEMA_VERSION, lastRead: { surah, verse, savedAt: new Date().toISOString() } });
}

export function clearLastRead(): void {
  write({ version: SCHEMA_VERSION, lastRead: null });
}

export function subscribeToLastRead(cb: () => void): () => void {
  const onCustom = () => cb();
  const onStorage = (e: StorageEvent) => {
    if (e.key === STORAGE_KEY) cb();
  };
  window.addEventListener(CHANGE_EVENT, onCustom);
  window.addEventListener('storage', onStorage);
  return () => {
    window.removeEventListener(CHANGE_EVENT, onCustom);
    window.removeEventListener('storage', onStorage);
  };
}
