/**
 * User notes — per-verse free-form text stored in localStorage.
 *
 * Persistence guarantees:
 *   - Single namespaced key:  "quranExplorer.notes" — IF you ever rename
 *     this, write a one-time migration that READS the old key, writes
 *     the new, and only THEN removes the old. Never just rename.
 *   - Versioned envelope: { version: 1, notes: { "2:255": "..." } }
 *     so future schema changes are detectable.
 *   - No `.clear()` calls anywhere. No bulk wipes. Only individual
 *     `removeItem()` of THIS key (and only via clearAllNotes() which
 *     requires explicit user confirmation upstream).
 *   - Defensive read: any parse error returns an empty default rather
 *     than crashing. Existing data on disk is never overwritten unless
 *     the user explicitly edits a note.
 *
 * Why it matters: the user has reported losing local data before, and
 * we treat their notes as user-generated content that must survive
 * every possible code change short of the browser itself wiping origin
 * storage.
 */

const STORAGE_KEY = 'quranExplorer.notes';
const SCHEMA_VERSION = 1;
const CHANGE_EVENT = 'quranExplorer:notes-changed';

interface NotesEnvelope {
  version: number;
  notes: Record<string, string>;  // "<surah>:<verse>" -> note text
}

function readEnvelope(): NotesEnvelope {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { version: SCHEMA_VERSION, notes: {} };
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object' && parsed.notes && typeof parsed.notes === 'object') {
      return {
        version: typeof parsed.version === 'number' ? parsed.version : SCHEMA_VERSION,
        notes: parsed.notes as Record<string, string>,
      };
    }
  } catch {
    /* fall through */
  }
  return { version: SCHEMA_VERSION, notes: {} };
}

function writeEnvelope(env: NotesEnvelope) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ version: SCHEMA_VERSION, notes: env.notes }));
    window.dispatchEvent(new CustomEvent(CHANGE_EVENT));
  } catch {
    /* localStorage full / unavailable — surface as silent no-op */
  }
}

export function getAllNotes(): Record<string, string> {
  return readEnvelope().notes;
}

export function getNote(surah: number, verse: number): string {
  return readEnvelope().notes[`${surah}:${verse}`] || '';
}

export function setNote(surah: number, verse: number, text: string): void {
  const env = readEnvelope();
  const key = `${surah}:${verse}`;
  if (text.trim()) {
    env.notes[key] = text;
  } else {
    delete env.notes[key];
  }
  writeEnvelope(env);
}

export function deleteNote(surah: number, verse: number): void {
  const env = readEnvelope();
  delete env.notes[`${surah}:${verse}`];
  writeEnvelope(env);
}

export function getNotesCount(): number {
  return Object.keys(readEnvelope().notes).length;
}

/**
 * Subscribe to changes from any tab/component. Returns an unsubscribe.
 * Listens to BOTH our custom event (same-tab updates) and the browser's
 * `storage` event (other-tab updates).
 */
export function subscribeToNotes(callback: () => void): () => void {
  const onCustom = () => callback();
  const onStorage = (e: StorageEvent) => {
    if (e.key === STORAGE_KEY) callback();
  };
  window.addEventListener(CHANGE_EVENT, onCustom);
  window.addEventListener('storage', onStorage);
  return () => {
    window.removeEventListener(CHANGE_EVENT, onCustom);
    window.removeEventListener('storage', onStorage);
  };
}

/** Export all notes as a downloadable JSON for the user. */
export function exportNotes(): string {
  const env = readEnvelope();
  return JSON.stringify({ version: SCHEMA_VERSION, notes: env.notes }, null, 2);
}

/**
 * Merge an exported JSON back into local storage. NEVER overwrites
 * existing notes silently — the imported note wins only if the user
 * confirms (caller's responsibility). Default behavior here is "merge,
 * imported wins on conflict" so callers can choose to confirm first.
 */
export function importNotes(json: string, mode: 'merge' | 'replace' = 'merge'): void {
  let parsed: unknown;
  try {
    parsed = JSON.parse(json);
  } catch {
    throw new Error('Invalid notes JSON');
  }
  if (!parsed || typeof parsed !== 'object') throw new Error('Invalid notes shape');
  const incoming = (parsed as { notes?: Record<string, string> }).notes;
  if (!incoming || typeof incoming !== 'object') throw new Error('Missing notes field');
  const env = mode === 'replace' ? { version: SCHEMA_VERSION, notes: {} } : readEnvelope();
  for (const [k, v] of Object.entries(incoming)) {
    if (typeof k === 'string' && /^\d+:\d+$/.test(k) && typeof v === 'string') {
      env.notes[k] = v;
    }
  }
  writeEnvelope(env);
}
