/**
 * Saved Items — localStorage-backed favorites system.
 *
 * Supports saving verses, words, and roots with flexible metadata.
 * Uses a versioned JSON blob stored under a single key.
 */

export type SavedItemType = 'verse' | 'word' | 'root';

export interface SavedItem {
  /** Discriminator: what kind of item is saved */
  type: SavedItemType;
  /** Unique key within its type, e.g. "2:255", "2:255/4", "rHm" */
  key: string;
  /** Human-readable label shown in the list */
  label: string;
  /** URL path to navigate to */
  href: string;
  /** Optional secondary text (surah name, meaning, etc.) */
  subtitle?: string;
  /** ISO timestamp when the item was saved */
  savedAt: string;
}

interface SavedItemsStore {
  version: 1;
  items: SavedItem[];
}

const STORAGE_KEY = 'quranExplorer.savedItems';

function load(): SavedItemsStore {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { version: 1, items: [] };
    const parsed = JSON.parse(raw) as SavedItemsStore;
    if (parsed.version !== 1) return { version: 1, items: [] };
    return parsed;
  } catch {
    return { version: 1, items: [] };
  }
}

function save(store: SavedItemsStore): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
  } catch {
    // localStorage full or disabled
  }
}

/** Get all saved items, newest first. */
export function getSavedItems(): SavedItem[] {
  return load().items;
}

/** Get saved items of a specific type. */
export function getSavedItemsByType(type: SavedItemType): SavedItem[] {
  return load().items.filter((item) => item.type === type);
}

/** Check whether a specific item is saved. */
export function isSaved(type: SavedItemType, key: string): boolean {
  return load().items.some((item) => item.type === type && item.key === key);
}

/** Get total count of saved items. */
export function getSavedCount(): number {
  return load().items.length;
}

/** Save an item (no-op if already saved). */
export function saveItem(item: Omit<SavedItem, 'savedAt'>): void {
  const store = load();
  const exists = store.items.some(
    (existing) => existing.type === item.type && existing.key === item.key,
  );
  if (exists) return;
  store.items.unshift({ ...item, savedAt: new Date().toISOString() });
  save(store);
}

/** Remove a saved item. */
export function removeSavedItem(type: SavedItemType, key: string): void {
  const store = load();
  store.items = store.items.filter(
    (item) => !(item.type === type && item.key === key),
  );
  save(store);
}

/** Toggle an item: save if missing, remove if present. Returns new saved state. */
export function toggleSavedItem(item: Omit<SavedItem, 'savedAt'>): boolean {
  if (isSaved(item.type, item.key)) {
    removeSavedItem(item.type, item.key);
    return false;
  }
  saveItem(item);
  return true;
}
