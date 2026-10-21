/**
 * Note highlights — localStorage-backed user highlighting of passages inside
 * the notes under a verse (exegesis, translation notes, grammar notes,
 * pre-Islamic poetry).
 *
 * Verse highlights can anchor to Arabic word positions because the verse text
 * never changes. Note prose does — notes get revised — so a note highlight is
 * anchored by QUOTING it instead (the W3C Web Annotation "text quote" idea):
 * the exact passage plus a little of the text either side of it. Resolving a
 * highlight means finding that passage in the note as it reads today, using
 * the context (and the old offset, as a last tiebreak) to choose between
 * repeats. A revision that leaves the passage alone keeps the highlight; one
 * that rewrites it drops the highlight cleanly (see `srcHash`).
 *
 * The text a highlight is quoted from is the note's RENDERED text — what the
 * reader actually selected — read by note-highlight-dom.ts. Both the research
 * view and the reader render each note through the same components, so a
 * highlight made in one resolves in the other.
 *
 * One colour only (yellow) — unlike verse highlights there is no picker.
 *
 * Highlighting a note also auto-saves its verse (source 'highlight'), with the
 * same auto-unsave rule as verse highlights: see verse-highlights.ts.
 */

import {
  ensureSavedForHighlight,
  maybeUnsaveAfterClear,
  VERSE_HIGHLIGHTS_CHANGED,
  type VerseMeta,
} from './verse-highlights';

export const NOTE_KINDS = ['exegesis', 'translation', 'grammar', 'poetry'] as const;
export type NoteKind = (typeof NOTE_KINDS)[number];

export const NOTE_KIND_LABEL: Record<NoteKind, string> = {
  exegesis: 'Exegesis',
  translation: 'Translation Notes',
  grammar: 'Grammar Notes',
  poetry: 'In Pre-Islamic Poetry',
};

/** Matches the yellow verse-highlight background (bg-yellow-200). */
export const NOTE_HIGHLIGHT_HEX = '#fef08a';

/** How much text either side of a passage is kept to tell repeats apart. */
export const CONTEXT_CHARS = 32;

export interface NoteHighlight {
  id: string;
  note: NoteKind;
  /** The highlighted passage, verbatim from the rendered note. */
  exact: string;
  /** Up to CONTEXT_CHARS of text just before / after the passage. */
  prefix: string;
  suffix: string;
  /** Character offset of the passage when it was made — a tiebreak only. */
  start: number;
  /** Hash of the note's source text when the highlight was made. If the
   *  passage can't be found AND the note's source has changed since, the note
   *  was edited out from under it and the highlight is pruned. If the source
   *  is unchanged, a miss is a transient render and the highlight is kept. */
  srcHash: string;
  createdAt: number;
}

interface NoteHighlightStore {
  version: 1;
  /** Keyed by verseKey "surah:ayah". */
  byVerse: Record<string, NoteHighlight[]>;
}

const STORAGE_KEY = 'quranExplorer.noteHighlights';

function isValid(h: unknown): h is NoteHighlight {
  if (!h || typeof h !== 'object') return false;
  const x = h as Record<string, unknown>;
  return (
    typeof x.id === 'string' &&
    (NOTE_KINDS as readonly string[]).includes(x.note as string) &&
    typeof x.exact === 'string' && x.exact.length > 0 &&
    typeof x.prefix === 'string' &&
    typeof x.suffix === 'string' &&
    typeof x.start === 'number' && Number.isFinite(x.start) &&
    typeof x.srcHash === 'string'
  );
}

function load(): NoteHighlightStore {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { version: 1, byVerse: {} };
    const parsed = JSON.parse(raw) as NoteHighlightStore;
    if (parsed.version !== 1 || typeof parsed.byVerse !== 'object' || !parsed.byVerse) {
      return { version: 1, byVerse: {} };
    }
    // Same sanitising as the verse store — never let corrupted storage crash
    // a note render.
    const byVerse: Record<string, NoteHighlight[]> = {};
    for (const [vk, list] of Object.entries(parsed.byVerse)) {
      if (!Array.isArray(list)) continue;
      const valid = list.filter(isValid);
      if (valid.length) byVerse[vk] = valid;
    }
    return { version: 1, byVerse };
  } catch {
    return { version: 1, byVerse: {} };
  }
}

function persist(store: NoteHighlightStore): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
  } catch {
    // quota exceeded / disabled — silently no-op
  }
}

function notify(): void {
  // The verse-highlight event, so anything already listening for highlight
  // changes (the Saved panel) refreshes for note highlights too.
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
  return `n_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

/** Short stable hash (FNV-1a) of a note's source text. */
export function hashNoteSource(src: string): string {
  let h = 0x811c9dc5;
  for (let i = 0; i < src.length; i++) {
    h ^= src.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return (h >>> 0).toString(36);
}

// ----- Reads ---------------------------------------------------------------

/** All of a verse's note highlights, in note order then reading order. */
export function getNoteHighlights(verseKey: string): NoteHighlight[] {
  const list = load().byVerse[verseKey] ?? [];
  return [...list].sort(
    (a, b) =>
      NOTE_KINDS.indexOf(a.note) - NOTE_KINDS.indexOf(b.note) ||
      a.start - b.start ||
      a.createdAt - b.createdAt,
  );
}

export function hasNoteHighlights(verseKey: string): boolean {
  return (load().byVerse[verseKey]?.length ?? 0) > 0;
}

// ----- Anchoring -----------------------------------------------------------

/** Length of the common run at the END of a and b. */
function commonSuffixLen(a: string, b: string): number {
  let n = 0;
  while (n < a.length && n < b.length && a[a.length - 1 - n] === b[b.length - 1 - n]) n++;
  return n;
}

/** Length of the common run at the START of a and b. */
function commonPrefixLen(a: string, b: string): number {
  let n = 0;
  while (n < a.length && n < b.length && a[n] === b[n]) n++;
  return n;
}

/**
 * Where `h` sits in `text` today, or null when its passage no longer occurs.
 * Every occurrence of the passage is scored by how much of the stored context
 * still surrounds it; the original offset only breaks ties.
 */
export function resolveNoteHighlight(
  text: string,
  h: Pick<NoteHighlight, 'exact' | 'prefix' | 'suffix' | 'start'>,
): { start: number; end: number } | null {
  let best: { start: number; score: number; dist: number } | null = null;
  for (let at = text.indexOf(h.exact); at >= 0; at = text.indexOf(h.exact, at + 1)) {
    const before = text.slice(Math.max(0, at - h.prefix.length), at);
    const after = text.slice(at + h.exact.length, at + h.exact.length + h.suffix.length);
    const score = commonSuffixLen(before, h.prefix) + commonPrefixLen(after, h.suffix);
    const dist = Math.abs(at - h.start);
    if (!best || score > best.score || (score === best.score && dist < best.dist)) {
      best = { start: at, score, dist };
    }
  }
  return best ? { start: best.start, end: best.start + h.exact.length } : null;
}

// ----- Writes --------------------------------------------------------------

/**
 * Save the passage text[start, end) of one note as a highlight. Highlights it
 * overlaps or touches (`mergeIds`, resolved by the caller against the same
 * text) are folded into it, so extending a selection grows a highlight rather
 * than stacking a second one on top.
 */
export function addNoteHighlight(
  verseKey: string,
  note: NoteKind,
  text: string,
  start: number,
  end: number,
  srcHash: string,
  mergeIds: string[] = [],
  meta?: VerseMeta,
): void {
  const store = load();
  const list = store.byVerse[verseKey] ?? [];
  const merged = list.filter((h) => mergeIds.includes(h.id));
  const rest = list.filter((h) => !mergeIds.includes(h.id));
  const anchor = merged.length
    ? merged.reduce((a, b) => (a.createdAt <= b.createdAt ? a : b))
    : null;
  const next: NoteHighlight = {
    id: anchor?.id ?? newId(),
    note,
    exact: text.slice(start, end),
    prefix: text.slice(Math.max(0, start - CONTEXT_CHARS), start),
    suffix: text.slice(end, end + CONTEXT_CHARS),
    start,
    srcHash,
    createdAt: anchor?.createdAt ?? Date.now(),
  };
  store.byVerse[verseKey] = [...rest, next];
  persist(store);
  ensureSavedForHighlight(verseKey, meta);
  notify();
}

/** Remove note highlights by id; auto-unsaves the verse per the usual rule
 *  once nothing (verse or note highlight) is left on it. */
export function removeNoteHighlights(verseKey: string, ids: string[]): void {
  const store = load();
  const list = store.byVerse[verseKey];
  if (!list) return;
  const next = list.filter((h) => !ids.includes(h.id));
  if (next.length === list.length) return;
  if (next.length === 0) delete store.byVerse[verseKey];
  else store.byVerse[verseKey] = next;
  persist(store);
  maybeUnsaveAfterClear(verseKey);
  notify();
}

export function removeNoteHighlight(verseKey: string, id: string): void {
  removeNoteHighlights(verseKey, [id]);
}

// ----- Subscription --------------------------------------------------------

/** Subscribe to note-highlight changes in this tab and others. */
export function subscribeToNoteHighlights(cb: () => void): () => void {
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
