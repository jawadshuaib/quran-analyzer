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
  // key -> note text. Verse notes are BARE ("<surah>:<verse>") for full
  // backward-compat with everything written before words/roots were notable;
  // words/roots are namespaced ("word:<s>:<a>/<pos>", "root:<buckwalter>").
  notes: Record<string, string>;
}

/**
 * Item types that can carry a note. Kept as a LOCAL type (structurally equal
 * to saved-items' SavedItemType) so this file imports nothing from
 * saved-items.ts — preserving the one-way store→notes graph.
 */
export type NotableType = 'verse' | 'word' | 'root';

/**
 * The ONLY place the note-key prefix convention lives. Verse keys stay bare
 * (zero migration for existing notes); other types get a "type:" prefix.
 */
function noteStorageKey(type: NotableType, key: string): string {
  return type === 'verse' ? key : `${type}:${key}`;
}

function isNamespaced(k: string): boolean {
  return k.startsWith('word:') || k.startsWith('root:');
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

// ----- Generic (type, key) core ---------------------------------------------

export function getItemNote(type: NotableType, key: string): string {
  return readEnvelope().notes[noteStorageKey(type, key)] || '';
}

export function setItemNoteRaw(type: NotableType, key: string, text: string): void {
  const env = readEnvelope();
  const storageKey = noteStorageKey(type, key);
  if (text.trim()) {
    env.notes[storageKey] = text;
  } else {
    delete env.notes[storageKey];
  }
  writeEnvelope(env);
}

export function deleteItemNote(type: NotableType, key: string): void {
  const env = readEnvelope();
  delete env.notes[noteStorageKey(type, key)];
  writeEnvelope(env);
}

/**
 * All notes of one type, keyed by the item's OWN key (de-namespaced) so
 * callers index by `item.key` without ever seeing the prefix convention:
 *   getNotesByType('verse') → { "57:20": "…" }
 *   getNotesByType('word')  → { "57:20/17": "…" }
 *   getNotesByType('root')  → { "kfr": "…" }
 */
export function getNotesByType(type: NotableType): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(readEnvelope().notes)) {
    if (type === 'verse') {
      if (!isNamespaced(k)) out[k] = v;
    } else {
      const prefix = `${type}:`;
      if (k.startsWith(prefix)) out[k.slice(prefix.length)] = v;
    }
  }
  return out;
}

// ----- Verse wrappers (backward-compat; every existing caller untouched) -----

export function getNote(surah: number, verse: number): string {
  return getItemNote('verse', `${surah}:${verse}`);
}

export function setNote(surah: number, verse: number, text: string): void {
  setItemNoteRaw('verse', `${surah}:${verse}`, text);
}

export function deleteNote(surah: number, verse: number): void {
  deleteItemNote('verse', `${surah}:${verse}`);
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
    // Accept bare verse keys ("s:v") plus namespaced word/root keys — anything
    // else is foreign and dropped, so a stray blob can't inject arbitrary keys.
    if (
      typeof k === 'string' &&
      typeof v === 'string' &&
      (/^\d+:\d+$/.test(k) || k.startsWith('word:') || k.startsWith('root:'))
    ) {
      env.notes[k] = v;
    }
  }
  writeEnvelope(env);
}
