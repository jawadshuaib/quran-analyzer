/**
 * Verse highlights — localStorage-backed user highlighting of Qurʾān verses.
 *
 * A highlight is anchored to a CONTIGUOUS RANGE OF ARABIC WORD POSITIONS
 * within one verse — NOT to character offsets. Every surface renders the
 * Arabic from `text_uthmani.split(/\s+/)`, 1-indexed by token (reader plain,
 * reader word-by-word, and the research view all agree on these positions),
 * so a `{startPos, endPos}` range is:
 *   - deterministic from the verse data → survives reloads,
 *   - independent of layout → survives the word-by-word toggle,
 *   - portable → a highlight made in the reader shows in /verse/<ref> too,
 *   - robust to English being caught in a drag-selection → we only ever look
 *     at which Arabic word tokens a selection covers and ignore the rest.
 *
 * Highlighting a verse also AUTO-SAVES it (source 'highlight'); clearing the
 * verse's last highlight auto-removes that save — but only if it was a
 * highlight save, never a manual one. See saved-items `toggleManualSave`.
 */

import {
  saveItem,
  removeSavedItem,
  isSaved,
  getSavedItemSource,
} from './saved-items';
import { getSurahName } from './surah-names';
import { notifySavedItemsChanged } from '../components/SavedItemsPanel';

// ----- Colors --------------------------------------------------------------

/** Palette, in assignment order. The FIRST highlight in any verse is yellow
 *  (the default); each additional disjoint highlight takes the next unused
 *  color, cycling once all are in use. */
export const HIGHLIGHT_COLORS = ['yellow', 'orange', 'green', 'sky', 'pink'] as const;
export type HighlightColor = (typeof HIGHLIGHT_COLORS)[number];

/** Background applied to highlighted word tokens. Written as literal class
 *  strings so the Tailwind scanner keeps them. */
export const HIGHLIGHT_BG: Record<HighlightColor, string> = {
  yellow: 'bg-yellow-200',
  orange: 'bg-orange-200',
  green: 'bg-green-200',
  sky: 'bg-sky-200',
  pink: 'bg-pink-200',
};

/** Solid swatch used in the color-picker popover. */
export const HIGHLIGHT_SWATCH: Record<HighlightColor, string> = {
  yellow: 'bg-yellow-300',
  orange: 'bg-orange-300',
  green: 'bg-green-400',
  sky: 'bg-sky-400',
  pink: 'bg-pink-400',
};

export const HIGHLIGHT_LABEL: Record<HighlightColor, string> = {
  yellow: 'Yellow',
  orange: 'Orange',
  green: 'Green',
  sky: 'Blue',
  pink: 'Pink',
};

/** True on touch-first devices (no hover). On these the delete-× is shown on
 *  highlights unconditionally, since there's no hover to reveal it. */
export function isCoarsePointer(): boolean {
  try {
    return (
      typeof window !== 'undefined' &&
      !!window.matchMedia &&
      window.matchMedia('(pointer: coarse)').matches
    );
  } catch {
    return false;
  }
}

// ----- Model ---------------------------------------------------------------

export interface Highlight {
  /** Stable id, unique within the verse. */
  id: string;
  /** First Arabic word position covered (1-indexed, inclusive). */
  startPos: number;
  /** Last Arabic word position covered (inclusive). */
  endPos: number;
  color: HighlightColor;
  /** Epoch ms when created. */
  createdAt: number;
}

interface HighlightStore {
  version: 1;
  /** Keyed by verseKey "surah:ayah". */
  byVerse: Record<string, Highlight[]>;
}

const STORAGE_KEY = 'quranExplorer.verseHighlights';
export const VERSE_HIGHLIGHTS_CHANGED = 'verse-highlights-changed';

function isValidHighlight(h: unknown): h is Highlight {
  if (!h || typeof h !== 'object') return false;
  const x = h as Record<string, unknown>;
  return (
    typeof x.id === 'string' &&
    typeof x.startPos === 'number' && Number.isFinite(x.startPos) &&
    typeof x.endPos === 'number' && Number.isFinite(x.endPos) &&
    (HIGHLIGHT_COLORS as readonly string[]).includes(x.color as string)
  );
}

function load(): HighlightStore {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { version: 1, byVerse: {} };
    const parsed = JSON.parse(raw) as HighlightStore;
    if (parsed.version !== 1 || typeof parsed.byVerse !== 'object' || !parsed.byVerse) {
      return { version: 1, byVerse: {} };
    }
    // Sanitize: drop any non-array verse entry or malformed highlight so callers
    // can trust the shape (the spread+sort in getHighlights would otherwise throw
    // on externally-corrupted storage and crash the verse render on reload).
    const byVerse: Record<string, Highlight[]> = {};
    for (const [vk, list] of Object.entries(parsed.byVerse)) {
      if (!Array.isArray(list)) continue;
      const valid = list.filter(isValidHighlight);
      if (valid.length) byVerse[vk] = valid;
    }
    return { version: 1, byVerse };
  } catch {
    return { version: 1, byVerse: {} };
  }
}

function persist(store: HighlightStore): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
  } catch {
    // quota exceeded / disabled — silently no-op
  }
}

function notify(): void {
  try {
    window.dispatchEvent(new CustomEvent(VERSE_HIGHLIGHTS_CHANGED));
  } catch {
    /* SSR / no window */
  }
}

function newId(): string {
  try {
    const c = (globalThis as { crypto?: { randomUUID?: () => string } }).crypto;
    if (c?.randomUUID) return c.randomUUID();
  } catch {
    /* fall through */
  }
  return `h_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

// ----- Reads ---------------------------------------------------------------

/** All highlights for a verse, ascending by start position. */
export function getHighlights(verseKey: string): Highlight[] {
  const list = load().byVerse[verseKey] ?? [];
  return [...list].sort((a, b) => a.startPos - b.startPos || a.createdAt - b.createdAt);
}

export function hasHighlights(verseKey: string): boolean {
  return (load().byVerse[verseKey]?.length ?? 0) > 0;
}

// ----- Color assignment ----------------------------------------------------

function nextColor(existing: Highlight[]): HighlightColor {
  const used = new Set(existing.map((h) => h.color));
  const free = HIGHLIGHT_COLORS.find((c) => !used.has(c));
  return free ?? HIGHLIGHT_COLORS[existing.length % HIGHLIGHT_COLORS.length];
}

// ----- Auto-save coupling --------------------------------------------------

/** Verse display text carried alongside a highlight so the auto-saved item can
 *  show the verse (Arabic + translation) in the Saved panel. */
export interface VerseMeta {
  arabic?: string;
  translation?: string;
}

function ensureSavedForHighlight(verseKey: string, meta?: VerseMeta): void {
  if (isSaved('verse', verseKey)) return;
  const [s] = verseKey.split(':');
  const surah = parseInt(s, 10);
  saveItem({
    type: 'verse',
    key: verseKey,
    label: `${getSurahName(surah)} ${verseKey}`,
    href: `/verse/${verseKey}`,
    source: 'highlight',
    arabic: meta?.arabic,
    translation: meta?.translation,
  });
  notifySavedItemsChanged();
}

function maybeUnsaveAfterClear(verseKey: string): void {
  if (hasHighlights(verseKey)) return;
  if (getSavedItemSource('verse', verseKey) === 'highlight') {
    removeSavedItem('verse', verseKey);
    notifySavedItemsChanged();
  }
}

// ----- Writes --------------------------------------------------------------

/**
 * Add a highlight covering word positions [startPos, endPos] in `verseKey`.
 * If the new range overlaps or is adjacent to existing highlight(s), they all
 * MERGE into one (keeping the earliest one's id + color → dragging extends a
 * highlight rather than stacking). Otherwise a new highlight is created with
 * the next unused color. Returns the resulting (possibly merged) highlight.
 */
export function addHighlight(
  verseKey: string,
  startPos: number,
  endPos: number,
  meta?: VerseMeta,
): Highlight {
  const start = Math.min(startPos, endPos);
  const end = Math.max(startPos, endPos);

  const store = load();
  const list = store.byVerse[verseKey] ?? [];

  // Touching/overlapping = within one position of each other.
  const touching = list.filter((h) => h.startPos <= end + 1 && h.endPos >= start - 1);
  const rest = list.filter((h) => !touching.includes(h));

  let result: Highlight;
  if (touching.length > 0) {
    const anchor = touching.reduce((a, b) => (a.createdAt <= b.createdAt ? a : b));
    result = {
      ...anchor,
      startPos: Math.min(start, ...touching.map((h) => h.startPos)),
      endPos: Math.max(end, ...touching.map((h) => h.endPos)),
    };
  } else {
    result = {
      id: newId(),
      startPos: start,
      endPos: end,
      color: nextColor(list),
      createdAt: Date.now(),
    };
  }

  store.byVerse[verseKey] = [...rest, result];
  persist(store);
  ensureSavedForHighlight(verseKey, meta);
  notify();
  return result;
}

/** Recolor an existing highlight (no-op if not found). */
export function setHighlightColor(
  verseKey: string,
  id: string,
  color: HighlightColor,
): void {
  const store = load();
  const list = store.byVerse[verseKey];
  if (!list) return;
  const h = list.find((x) => x.id === id);
  if (!h || h.color === color) return;
  h.color = color;
  persist(store);
  notify();
}

/** Remove one highlight; auto-unsaves the verse if it was a highlight save
 *  and no highlights remain. */
export function removeHighlight(verseKey: string, id: string): void {
  const store = load();
  const list = store.byVerse[verseKey];
  if (!list) return;
  const next = list.filter((h) => h.id !== id);
  if (next.length === list.length) return; // nothing removed
  if (next.length === 0) delete store.byVerse[verseKey];
  else store.byVerse[verseKey] = next;
  persist(store);
  maybeUnsaveAfterClear(verseKey);
  notify();
}

/** Remove every highlight on a verse (also auto-unsaves per the rule). */
export function clearVerseHighlights(verseKey: string): void {
  const store = load();
  if (!store.byVerse[verseKey]) return;
  delete store.byVerse[verseKey];
  persist(store);
  maybeUnsaveAfterClear(verseKey);
  notify();
}

// ----- Subscription --------------------------------------------------------

/** Subscribe to any highlight change (this tab via custom event, other tabs
 *  via the storage event). Returns an unsubscribe function. */
export function subscribeToHighlights(cb: () => void): () => void {
  const onCustom = () => cb();
  const onStorage = (e: StorageEvent) => {
    if (e.key === STORAGE_KEY) cb();
  };
  window.addEventListener(VERSE_HIGHLIGHTS_CHANGED, onCustom);
  window.addEventListener('storage', onStorage);
  return () => {
    window.removeEventListener(VERSE_HIGHLIGHTS_CHANGED, onCustom);
    window.removeEventListener('storage', onStorage);
  };
}
