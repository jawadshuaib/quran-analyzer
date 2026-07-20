/**
 * Recent search queries — the empty-state history shown in the search dropdown.
 *
 * Same defensive persistence rules as user-notes.ts / last-read.ts:
 *   - Stable namespaced key: "quranExplorer.recentSearches"
 *   - Versioned envelope
 *   - Never wiped except via an explicit user "Clear"
 *   - Multi-tab sync via the storage event + a custom event
 *
 * Local-only, like every other user-data store on the site — no query text
 * ever leaves the browser.
 */

const STORAGE_KEY = 'quranExplorer.recentSearches';
const SCHEMA_VERSION = 1;
const CHANGE_EVENT = 'quranExplorer:recentSearches-changed';
const MAX_ITEMS = 10;

interface Envelope {
  version: number;
  items: string[]; // newest first
}

function read(): Envelope {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { version: SCHEMA_VERSION, items: [] };
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object' && Array.isArray(parsed.items)) {
      const items = parsed.items.filter((s: unknown) => typeof s === 'string' && s.trim());
      return { version: SCHEMA_VERSION, items: items.slice(0, MAX_ITEMS) };
    }
  } catch {
    /* fall through */
  }
  return { version: SCHEMA_VERSION, items: [] };
}

function write(items: string[]) {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ version: SCHEMA_VERSION, items: items.slice(0, MAX_ITEMS) }),
    );
    window.dispatchEvent(new CustomEvent(CHANGE_EVENT));
  } catch {
    /* localStorage full / unavailable — silent no-op */
  }
}

export function getRecentSearches(): string[] {
  return read().items;
}

/** Record a query at the front of the list, de-duplicated case-insensitively. */
export function addRecentSearch(query: string): void {
  const q = query.trim();
  if (!q) return;
  const lower = q.toLowerCase();
  const items = read().items.filter((s) => s.toLowerCase() !== lower);
  items.unshift(q);
  write(items);
}

export function removeRecentSearch(query: string): void {
  const lower = query.trim().toLowerCase();
  write(read().items.filter((s) => s.toLowerCase() !== lower));
}

export function clearRecentSearches(): void {
  write([]);
}

export function subscribeToRecentSearches(cb: () => void): () => void {
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

/** Curated concept queries shown alongside recents in the empty dropdown and on
 *  the empty results page. Rotated so the same 4 aren't always first. */
export const SUGGESTED_QUERIES: string[] = [
  'mercy and forgiveness',
  'patience in hardship',
  'the creation of Adam',
  'gratitude',
  'light and darkness',
  'the Day of Judgement',
  'charity to the poor',
  'seeking knowledge',
  'trust in God',
  'the story of Moses',
  'repentance',
  'paradise',
];
