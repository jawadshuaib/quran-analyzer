/**
 * Copy context — the transient "a verse is selected, offer to copy it" state,
 * plus the remembered copy preferences.
 *
 * When the user selects text in a verse, the selection controller snapshots the
 * covered Arabic word range (+ the verse's text/translation/surah name, read
 * from the region's data-* attributes) into the in-memory active context. That
 * drives the pop-in copy icon (per verse) and the copy modal. It is a SNAPSHOT,
 * not the live browser selection, so it survives the selection being collapsed
 * (which the highlight controller does) and a click on the copy icon.
 *
 * Only one verse can be the active context at a time. Deselecting (click away /
 * Escape / a new selection / closing the modal) clears it.
 */

export type CopyFormat = 'selected' | 'full' | 'translation' | 'highlighted';

export interface CopyContext {
  /** "surah:ayah", e.g. "94:1". */
  verseKey: string;
  /** Covered Arabic word positions (1-indexed, inclusive). */
  startPos: number;
  endPos: number;
  /** Full Uthmani text + translation, for the copy formats. */
  arabic: string;
  translation: string;
  /** Surah display name, for the reference line. */
  surahName: string;
}

const CHANGE_EVENT = 'quranExplorer:copy-context-changed';

let active: CopyContext | null = null;
let modalOpen = false;

function notify(): void {
  try {
    window.dispatchEvent(new CustomEvent(CHANGE_EVENT));
  } catch {
    /* SSR / no window */
  }
}

export function getCopyContext(): CopyContext | null {
  return active;
}

export function isCopyModalOpen(): boolean {
  return modalOpen;
}

/** Set (or replace) the active copy context — drives the per-verse copy icon. */
export function setCopyContext(ctx: CopyContext): void {
  active = ctx;
  notify();
}

/** Clear the active context (deselect). Also closes the modal. */
export function clearCopyContext(): void {
  if (!active && !modalOpen) return;
  active = null;
  modalOpen = false;
  notify();
}

export function openCopyModal(): void {
  if (!active) return;
  modalOpen = true;
  notify();
}

/** Close just the modal (keeps no context — the action is done). */
export function closeCopyModal(): void {
  if (!modalOpen) return;
  modalOpen = false;
  notify();
}

export function subscribeCopyContext(cb: () => void): () => void {
  const handler = () => cb();
  window.addEventListener(CHANGE_EVENT, handler);
  return () => window.removeEventListener(CHANGE_EVENT, handler);
}

// ----- Remembered preferences (localStorage) -------------------------------

export interface CopyPrefs {
  lastFormat: CopyFormat;
  includeReference: boolean;
}

const PREFS_KEY = 'quranExplorer.copyPrefs';
const DEFAULT_PREFS: CopyPrefs = { lastFormat: 'selected', includeReference: true };

export function getCopyPrefs(): CopyPrefs {
  try {
    const raw = localStorage.getItem(PREFS_KEY);
    if (!raw) return { ...DEFAULT_PREFS };
    const parsed = JSON.parse(raw) as Partial<CopyPrefs>;
    return {
      lastFormat: parsed.lastFormat ?? DEFAULT_PREFS.lastFormat,
      includeReference: typeof parsed.includeReference === 'boolean'
        ? parsed.includeReference
        : DEFAULT_PREFS.includeReference,
    };
  } catch {
    return { ...DEFAULT_PREFS };
  }
}

export function setCopyPrefs(patch: Partial<CopyPrefs>): void {
  try {
    localStorage.setItem(PREFS_KEY, JSON.stringify({ ...getCopyPrefs(), ...patch }));
  } catch {
    /* quota / disabled — non-fatal */
  }
}
