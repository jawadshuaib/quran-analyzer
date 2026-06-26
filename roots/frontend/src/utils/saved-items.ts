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
  /**
   * How this item entered the saved list:
   *   - 'manual'    — the user pressed Save (sticky; never auto-removed)
   *   - 'highlight' — auto-saved because the user highlighted part of the
   *                   verse; auto-removed when the verse's last highlight is
   *                   cleared (unless promoted to 'manual' in the meantime)
   * Absent on items saved before this field existed → treated as 'manual'.
   */
  source?: 'manual' | 'highlight';
  /** Verse-only: the Uthmani Arabic text, so the Saved panel can show the
   *  verse itself (and render highlights over its word tokens) without a
   *  network round-trip. */
  arabic?: string;
  /** Verse-only: the English translation shown under the Arabic in the panel. */
  translation?: string;
}

export type SavedItemSource = NonNullable<SavedItem['source']>;

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

/** How a saved item entered the list. Returns undefined if it isn't saved.
 *  Items stored before the `source` field existed report 'manual'. */
export function getSavedItemSource(
  type: SavedItemType,
  key: string,
): SavedItemSource | undefined {
  const item = load().items.find((i) => i.type === type && i.key === key);
  if (!item) return undefined;
  return item.source ?? 'manual';
}

/** Mark an already-saved item as a sticky 'manual' save (no-op if not saved).
 *  Used to promote a highlight-auto-saved verse so clearing its highlights
 *  later won't remove it. Optionally refreshes the display metadata so the
 *  promoted item matches a directly-pressed manual save (richer label /
 *  subtitle) instead of keeping the terser highlight-era metadata. */
export function promoteSavedItemToManual(
  type: SavedItemType,
  key: string,
  patch?: Pick<SavedItem, 'label' | 'href' | 'subtitle' | 'arabic' | 'translation'>,
): void {
  const store = load();
  const item = store.items.find((i) => i.type === type && i.key === key);
  if (!item) return;
  item.source = 'manual';
  if (patch) {
    if (patch.label) item.label = patch.label;
    if (patch.href) item.href = patch.href;
    if (patch.subtitle !== undefined) item.subtitle = patch.subtitle;
    if (patch.arabic) item.arabic = patch.arabic;
    if (patch.translation) item.translation = patch.translation;
  }
  save(store);
}

/** Backfill the verse text/translation on an already-saved item (no-op if not
 *  saved or unchanged). Used to upgrade items saved before these fields existed
 *  once the panel has fetched the verse. */
export function updateSavedItemContent(
  type: SavedItemType,
  key: string,
  content: { arabic?: string; translation?: string },
): void {
  const store = load();
  const item = store.items.find((i) => i.type === type && i.key === key);
  if (!item) return;
  let changed = false;
  if (content.arabic && item.arabic !== content.arabic) { item.arabic = content.arabic; changed = true; }
  if (content.translation && item.translation !== content.translation) { item.translation = content.translation; changed = true; }
  if (changed) save(store);
}

/**
 * Verse-aware Save toggle that understands the highlight coupling:
 *   - not saved         → save as a sticky 'manual' item        → true
 *   - saved 'highlight' → PROMOTE to 'manual' (stays saved)     → true
 *   - saved 'manual'    → remove                                → false
 * The middle case means pressing Save on a verse that was auto-saved by a
 * highlight makes the save sticky instead of paradoxically unsaving it.
 */
export function toggleManualSave(item: Omit<SavedItem, 'savedAt' | 'source'>): boolean {
  const source = getSavedItemSource(item.type, item.key);
  if (source === undefined) {
    saveItem({ ...item, source: 'manual' });
    return true;
  }
  if (source === 'highlight') {
    promoteSavedItemToManual(item.type, item.key, {
      label: item.label,
      href: item.href,
      subtitle: item.subtitle,
      arabic: item.arabic,
      translation: item.translation,
    });
    return true;
  }
  removeSavedItem(item.type, item.key);
  return false;
}
