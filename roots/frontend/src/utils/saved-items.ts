/**
 * Saved Items — localStorage-backed favorites system.
 *
 * Supports saving verses, words, and roots with flexible metadata, and
 * organizing saved items into user-named FOLDERS (many-to-many: one item
 * can live in several folders; a folder holds any item type). Uses a
 * versioned JSON blob stored under a single key.
 *
 * v1 → v2: added `folders` (list of Folder) to the envelope and
 * `folders?: string[]` (folder ids) to each item. Migration is lazy and
 * lossless: a v1 blob is upgraded in memory on read and only persisted in
 * the v2 shape by the next mutation, so a code rollback before the user's
 * first mutation leaves the original blob untouched.
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
   *   - 'note'      — auto-saved because the user wrote a note on the verse
   *                   (a note lives UNDER its verse in the Saved UI); released
   *                   when the note is deleted, unless something else keeps it
   * Absent on items saved before this field existed → treated as 'manual'.
   */
  source?: 'manual' | 'highlight' | 'note';
  /** The Arabic to render in the Saved surfaces without a network round-trip:
   *  verse → the Uthmani text (highlights drawn over its word tokens);
   *  word  → the HOST verse's Uthmani text (for the one-line context snippet);
   *  root  → the Arabic root glyph. */
  arabic?: string;
  /** The gloss/meaning line: verse → English translation; word/root can also
   *  carry their meaning here (or in `subtitle`). */
  translation?: string;
  /** Extra structured fields for rich display of word/root cards (see
   *  SavedItemMeta). Optional + additive — no migration. */
  meta?: SavedItemMeta;
  /** Ids of folders this item belongs to. Absent or empty = unfiled. */
  folders?: string[];
}

/**
 * Structured extras that let a saved WORD render as a vocabulary flashcard and
 * a saved ROOT as a mini dictionary entry, without refetching. All optional;
 * lazily backfilled for items saved before this existed.
 */
export interface SavedItemMeta {
  /** Word: the word's own Arabic form (the flashcard headline glyph). */
  wordArabic?: string;
  /** Word/root: the Arabic root glyph (e.g. the spaced root). */
  rootArabic?: string;
  /** Word/root: the Buckwalter root — powers the /root/<bw> chip link. */
  rootBuckwalter?: string;
  /** Word: the lemma's Arabic. */
  lemmaArabic?: string;
  /** Word/root: comma-separated semantic-field tags (first shown, rest in title). */
  semanticField?: string;
  /** Root: total occurrences across the Qur'an. */
  occurrences?: number;
  /** Root: number of distinct lemmas. */
  lemmaCount?: number;
}

export type SavedItemSource = NonNullable<SavedItem['source']>;

/** A user-named collection of saved items (e.g. "dhikr"). Membership lives
 *  on the items (`SavedItem.folders`), so deleting a folder can never orphan
 *  an item — it just unfiles it. */
export interface Folder {
  id: string;
  name: string;
  createdAt: string;
}

export const FOLDER_NAME_MAX = 48;

/** Minimal identity of a saved item, for bulk operations. */
export interface SavedItemRef {
  type: SavedItemType;
  key: string;
}

interface SavedItemsStore {
  version: 2;
  items: SavedItem[];
  /** Array order IS display order. */
  folders: Folder[];
}

const STORAGE_KEY = 'quranExplorer.savedItems';

// ----- Change events ---------------------------------------------------------

/** Global event name fired whenever the saved-items store changes. */
export const SAVED_ITEMS_CHANGED = 'saved-items-changed';

/** Notify listeners that saved items changed. Fired automatically by every
 *  store mutation; only needed manually for exotic cases. */
export function notifySavedItemsChanged(): void {
  try {
    window.dispatchEvent(new CustomEvent(SAVED_ITEMS_CHANGED));
  } catch {
    /* SSR / no window */
  }
}

/** Subscribe to any saved-items change (this tab via custom event, other tabs
 *  via the storage event). Returns an unsubscribe function. */
export function subscribeToSavedItems(cb: () => void): () => void {
  const onCustom = () => cb();
  const onStorage = (e: StorageEvent) => {
    if (e.key === STORAGE_KEY) cb();
  };
  window.addEventListener(SAVED_ITEMS_CHANGED, onCustom);
  window.addEventListener('storage', onStorage);
  return () => {
    window.removeEventListener(SAVED_ITEMS_CHANGED, onCustom);
    window.removeEventListener('storage', onStorage);
  };
}

// ----- Persistence -----------------------------------------------------------

function emptyStore(): SavedItemsStore {
  return { version: 2, items: [], folders: [] };
}

function isValidFolder(f: unknown): f is Folder {
  if (!f || typeof f !== 'object') return false;
  const x = f as Record<string, unknown>;
  return typeof x.id === 'string' && typeof x.name === 'string';
}

function load(): SavedItemsStore {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return emptyStore();
    const parsed = JSON.parse(raw) as { version?: unknown; items?: unknown; folders?: unknown };
    if (parsed?.version === 1) {
      // v1 → v2: items carry over untouched (no folders field = unfiled).
      // In-memory only; persisted by the next mutation's save().
      return {
        version: 2,
        items: Array.isArray(parsed.items) ? (parsed.items as SavedItem[]) : [],
        folders: [],
      };
    }
    if (parsed?.version === 2) {
      return {
        version: 2,
        items: Array.isArray(parsed.items) ? (parsed.items as SavedItem[]) : [],
        folders: Array.isArray(parsed.folders)
          ? (parsed.folders as unknown[]).filter(isValidFolder)
          : [],
      };
    }
    // Unknown/future version: read as empty, never overwrite on read.
    return emptyStore();
  } catch {
    return emptyStore();
  }
}

function save(store: SavedItemsStore): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
  } catch {
    // localStorage full or disabled
  }
  notifySavedItemsChanged();
}

function newId(): string {
  try {
    const c = (globalThis as { crypto?: { randomUUID?: () => string } }).crypto;
    if (c?.randomUUID) return c.randomUUID();
  } catch {
    /* fall through */
  }
  return `f_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

function findItem(store: SavedItemsStore, type: SavedItemType, key: string): SavedItem | undefined {
  return store.items.find((i) => i.type === type && i.key === key);
}

// ----- Item reads ------------------------------------------------------------

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

// ----- Item writes -----------------------------------------------------------

/** Save an item (no-op if already saved). */
export function saveItem(item: Omit<SavedItem, 'savedAt'>): void {
  const store = load();
  if (findItem(store, item.type, item.key)) return;
  store.items.unshift({ ...item, savedAt: new Date().toISOString() });
  save(store);
}

/** Remove a saved item entirely (all folder memberships go with it). */
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
  patch?: Pick<SavedItem, 'label' | 'href' | 'subtitle' | 'arabic' | 'translation' | 'meta'>,
): void {
  const store = load();
  const item = findItem(store, type, key);
  if (!item) return;
  item.source = 'manual';
  if (patch) {
    if (patch.label) item.label = patch.label;
    if (patch.href) item.href = patch.href;
    if (patch.subtitle !== undefined) item.subtitle = patch.subtitle;
    if (patch.arabic) item.arabic = patch.arabic;
    if (patch.translation) item.translation = patch.translation;
    if (patch.meta) item.meta = { ...item.meta, ...patch.meta };
  }
  save(store);
}

/** Backfill the verse text/translation on an already-saved item (no-op if not
 *  saved or unchanged). Used to upgrade items saved before these fields existed
 *  once the panel has fetched the verse. */
export function updateSavedItemContent(
  type: SavedItemType,
  key: string,
  content: { arabic?: string; translation?: string; subtitle?: string; meta?: SavedItemMeta },
): void {
  const store = load();
  const item = findItem(store, type, key);
  if (!item) return;
  let changed = false;
  if (content.arabic && item.arabic !== content.arabic) { item.arabic = content.arabic; changed = true; }
  if (content.translation && item.translation !== content.translation) { item.translation = content.translation; changed = true; }
  if (content.subtitle && item.subtitle !== content.subtitle) { item.subtitle = content.subtitle; changed = true; }
  if (content.meta) {
    const next = { ...item.meta };
    let metaChanged = false;
    for (const [k, v] of Object.entries(content.meta) as [keyof SavedItemMeta, unknown][]) {
      if (v !== undefined && v !== null && (next as Record<string, unknown>)[k] !== v) {
        (next as Record<string, unknown>)[k] = v;
        metaChanged = true;
      }
    }
    if (metaChanged) { item.meta = next; changed = true; }
  }
  if (changed) save(store);
}

/**
 * Verse-aware Save toggle that understands the auto-save couplings:
 *   - not saved              → save as a sticky 'manual' item   → true
 *   - saved 'highlight'/'note' → PROMOTE to 'manual' (stays)    → true
 *   - saved 'manual'         → remove                           → false
 * The middle case means pressing Save on a verse that was auto-saved by a
 * highlight or a note makes the save sticky instead of paradoxically
 * unsaving it.
 */
export function toggleManualSave(item: Omit<SavedItem, 'savedAt' | 'source'>): boolean {
  const source = getSavedItemSource(item.type, item.key);
  if (source === undefined) {
    saveItem({ ...item, source: 'manual' });
    return true;
  }
  if (source === 'highlight' || source === 'note') {
    promoteSavedItemToManual(item.type, item.key, {
      label: item.label,
      href: item.href,
      subtitle: item.subtitle,
      arabic: item.arabic,
      translation: item.translation,
      meta: item.meta,
    });
    return true;
  }
  removeSavedItem(item.type, item.key);
  return false;
}

// ----- Folder CRUD -----------------------------------------------------------

function normalizeName(name: string): string {
  return name.trim().toLowerCase();
}

function validFolderName(name: string): string | null {
  const trimmed = name.trim();
  if (!trimmed || trimmed.length > FOLDER_NAME_MAX) return null;
  return trimmed;
}

/** All folders, in display order. */
export function getFolders(): Folder[] {
  return load().folders;
}

export function getFolder(id: string): Folder | undefined {
  return load().folders.find((f) => f.id === id);
}

/** Create a folder. Idempotent on name: if a folder with the same normalized
 *  name exists, returns it instead of creating a duplicate (the right
 *  behavior for inline creation in the save popover). Returns null for an
 *  empty or over-long name. */
export function createFolder(name: string): Folder | null {
  const trimmed = validFolderName(name);
  if (!trimmed) return null;
  const store = load();
  const existing = store.folders.find((f) => normalizeName(f.name) === normalizeName(trimmed));
  if (existing) return existing;
  const folder: Folder = { id: newId(), name: trimmed, createdAt: new Date().toISOString() };
  store.folders.push(folder);
  save(store);
  return folder;
}

/** Rename a folder. Returns false if the folder is missing, the name is
 *  invalid, or another folder already uses it. */
export function renameFolder(id: string, name: string): boolean {
  const trimmed = validFolderName(name);
  if (!trimmed) return false;
  const store = load();
  const folder = store.folders.find((f) => f.id === id);
  if (!folder) return false;
  const collision = store.folders.some(
    (f) => f.id !== id && normalizeName(f.name) === normalizeName(trimmed),
  );
  if (collision) return false;
  folder.name = trimmed;
  save(store);
  return true;
}

/** Delete a folder. Items stay saved — they are only unfiled from it. */
export function deleteFolder(id: string): void {
  const store = load();
  const before = store.folders.length;
  store.folders = store.folders.filter((f) => f.id !== id);
  if (store.folders.length === before) return;
  for (const item of store.items) {
    if (item.folders?.includes(id)) {
      item.folders = item.folders.filter((fid) => fid !== id);
    }
  }
  save(store);
}

/** Reorder folders to match `orderedIds`. Unknown ids are ignored; folders
 *  missing from the list keep their relative order at the end. */
export function reorderFolders(orderedIds: string[]): void {
  const store = load();
  const byId = new Map(store.folders.map((f) => [f.id, f]));
  const next: Folder[] = [];
  for (const id of orderedIds) {
    const f = byId.get(id);
    if (f) {
      next.push(f);
      byId.delete(id);
    }
  }
  for (const f of store.folders) {
    if (byId.has(f.id)) next.push(f);
  }
  store.folders = next;
  save(store);
}

// ----- Folder membership -----------------------------------------------------

/** Folder ids an item belongs to ([] if unsaved or unfiled). */
export function getItemFolderIds(type: SavedItemType, key: string): string[] {
  return load().items.find((i) => i.type === type && i.key === key)?.folders ?? [];
}

/** Known folder ids only, deduped. */
function sanitizeFolderIds(store: SavedItemsStore, ids: string[]): string[] {
  const known = new Set(store.folders.map((f) => f.id));
  return [...new Set(ids)].filter((id) => known.has(id));
}

/** File an item into a folder. Filing is curation, so the item's source is
 *  promoted to 'manual' (a filed verse must never be auto-unsaved by the
 *  highlight coupling). No-op if unsaved, folder unknown, or already filed. */
export function addItemToFolder(type: SavedItemType, key: string, folderId: string): void {
  const store = load();
  const item = findItem(store, type, key);
  if (!item) return;
  if (!store.folders.some((f) => f.id === folderId)) return;
  const current = item.folders ?? [];
  if (current.includes(folderId)) return;
  item.folders = [...current, folderId];
  item.source = 'manual';
  save(store);
}

/** Unfile an item from one folder. The item stays saved. */
export function removeItemFromFolder(type: SavedItemType, key: string, folderId: string): void {
  const store = load();
  const item = findItem(store, type, key);
  if (!item?.folders?.includes(folderId)) return;
  item.folders = item.folders.filter((id) => id !== folderId);
  save(store);
}

/** Replace an item's full folder set (the popover-checklist primitive).
 *  Dedups, drops unknown ids; a non-empty set promotes source to 'manual'. */
export function setItemFolders(type: SavedItemType, key: string, folderIds: string[]): void {
  const store = load();
  const item = findItem(store, type, key);
  if (!item) return;
  const next = sanitizeFolderIds(store, folderIds);
  item.folders = next;
  if (next.length > 0) item.source = 'manual';
  save(store);
}

/** One-gesture save + file: saves as manual (or promotes a highlight save,
 *  keeping richer metadata), then unions `folderIds` into its membership.
 *  Single load/save → single change notification. */
export function saveItemToFolders(
  item: Omit<SavedItem, 'savedAt' | 'source'>,
  folderIds: string[],
): void {
  const store = load();
  let existing = findItem(store, item.type, item.key);
  if (!existing) {
    existing = { ...item, savedAt: new Date().toISOString(), source: 'manual' };
    store.items.unshift(existing);
  } else {
    existing.source = 'manual';
    if (item.label) existing.label = item.label;
    if (item.href) existing.href = item.href;
    if (item.subtitle !== undefined) existing.subtitle = item.subtitle;
    if (item.arabic) existing.arabic = item.arabic;
    if (item.translation) existing.translation = item.translation;
  }
  const union = [...(existing.folders ?? []), ...folderIds];
  existing.folders = sanitizeFolderIds(store, union);
  save(store);
}

// ----- Folder queries (for the /saved page) -----------------------------------

/** Item count per folder id, in one pass. */
export function getFolderCounts(): Record<string, number> {
  const store = load();
  const known = new Set(store.folders.map((f) => f.id));
  const counts: Record<string, number> = {};
  for (const f of store.folders) counts[f.id] = 0;
  for (const item of store.items) {
    for (const id of item.folders ?? []) {
      if (known.has(id)) counts[id]++;
    }
  }
  return counts;
}

/** Items filed in a folder, newest-saved first. */
export function getItemsInFolder(folderId: string): SavedItem[] {
  return load().items.filter((i) => i.folders?.includes(folderId));
}

/** Items not filed in any folder. */
export function getUnfiledItems(): SavedItem[] {
  return load().items.filter((i) => !i.folders?.length);
}

// ----- Bulk operations (each = one load/save/notify) ---------------------------

/** File several items into a folder (promotes each to manual). */
export function addItemsToFolder(refs: SavedItemRef[], folderId: string): void {
  const store = load();
  if (!store.folders.some((f) => f.id === folderId)) return;
  let changed = false;
  for (const ref of refs) {
    const item = findItem(store, ref.type, ref.key);
    if (!item) continue;
    const current = item.folders ?? [];
    if (current.includes(folderId)) continue;
    item.folders = [...current, folderId];
    item.source = 'manual';
    changed = true;
  }
  if (changed) save(store);
}

/** Unfile several items from a folder (items stay saved). */
export function removeItemsFromFolder(refs: SavedItemRef[], folderId: string): void {
  const store = load();
  let changed = false;
  for (const ref of refs) {
    const item = findItem(store, ref.type, ref.key);
    if (!item?.folders?.includes(folderId)) continue;
    item.folders = item.folders.filter((id) => id !== folderId);
    changed = true;
  }
  if (changed) save(store);
}

/** Move several items between folders. `fromFolderId` null = the items were
 *  viewed unfiled/all (nothing to remove). Promotes each to manual. */
export function moveItemsToFolder(
  refs: SavedItemRef[],
  fromFolderId: string | null,
  toFolderId: string,
): void {
  const store = load();
  if (!store.folders.some((f) => f.id === toFolderId)) return;
  let changed = false;
  for (const ref of refs) {
    const item = findItem(store, ref.type, ref.key);
    if (!item) continue;
    let next = item.folders ?? [];
    if (fromFolderId) next = next.filter((id) => id !== fromFolderId);
    if (!next.includes(toFolderId)) next = [...next, toFolderId];
    item.folders = next;
    item.source = 'manual';
    changed = true;
  }
  if (changed) save(store);
}

/** Remove several items from Saved entirely. NOTE: for verses the caller must
 *  clear highlights per verse first (see utils/saved-item-actions.ts) — that
 *  coupling lives outside this module to avoid an import cycle with
 *  verse-highlights.ts. */
export function removeSavedItems(refs: SavedItemRef[]): void {
  const store = load();
  const keys = new Set(refs.map((r) => `${r.type} ${r.key}`));
  const next = store.items.filter((i) => !keys.has(`${i.type} ${i.key}`));
  if (next.length === store.items.length) return;
  store.items = next;
  save(store);
}
