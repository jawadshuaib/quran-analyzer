/**
 * Cross-store saved-item actions.
 *
 * Lives outside saved-items.ts because it needs verse-highlights.ts and
 * user-notes.ts, which themselves import saved-items.ts (the auto-save
 * couplings) — putting this in the store would create import cycles.
 *
 * Import graph (all one-way):
 *   saved-items  ←  verse-highlights, user-notes, THIS FILE
 *   user-notes   ←  verse-highlights (note guard), THIS FILE
 *   verse-highlights ← THIS FILE
 */

import {
  saveItem,
  removeSavedItem,
  isSaved,
  getSavedItemSource,
  getItemFolderIds,
  type SavedItemType,
  type SavedItemRef,
} from './saved-items';
import { clearVerseHighlights, hasHighlights } from './verse-highlights';
import { getAllNotes, getNote, setNote, deleteNote } from './user-notes';
import { getSurahName } from './surah-names';

function verseNums(verseKey: string): [number, number] {
  const [s, v] = verseKey.split(':').map(Number);
  return [s, v];
}

function autoSaveVerse(verseKey: string, source: 'note'): void {
  const [surah] = verseNums(verseKey);
  saveItem({
    type: 'verse',
    key: verseKey,
    label: `${getSurahName(surah)} ${verseKey}`,
    href: `/verse/${verseKey}`,
    source,
    // arabic/translation omitted — SavedVerseContent lazily backfills them.
  });
}

/** Release an auto-saved verse once nothing keeps it: not a manual save, not
 *  filed in any folder, no highlights left, no note left. */
function maybeReleaseAutoSavedVerse(verseKey: string): void {
  const source = getSavedItemSource('verse', verseKey);
  if (source === undefined || source === 'manual') return;
  if (getItemFolderIds('verse', verseKey).length > 0) return;
  if (hasHighlights(verseKey)) return;
  const [s, v] = verseNums(verseKey);
  if (getNote(s, v)) return;
  removeSavedItem('verse', verseKey);
}

/**
 * THE note write path — every surface that saves/deletes a verse note goes
 * through here (reader gutter, research view, Saved page/panel), so a note
 * always lives under a saved verse:
 *   - non-empty text → note stored + the verse auto-saved (source 'note')
 *   - empty text     → note deleted + a pure note-save released
 */
export function setVerseNote(surah: number, verse: number, text: string): void {
  const verseKey = `${surah}:${verse}`;
  if (text.trim()) {
    setNote(surah, verse, text);
    if (!isSaved('verse', verseKey)) autoSaveVerse(verseKey, 'note');
  } else {
    deleteNote(surah, verse);
    maybeReleaseAutoSavedVerse(verseKey);
  }
}

/**
 * One-time migration: notes written before the note↔saved coupling existed
 * may sit on verses that aren't saved ("detached" notes). Auto-save those
 * verses once so every note has a verse card to live under. Flagged so a
 * user who later removes such a verse (deleting its note with it) doesn't
 * see it resurrect.
 */
const NOTES_LINKED_FLAG = 'quranExplorer.notesLinkedToSaved';

export function ensureNotedVersesSaved(): void {
  try {
    if (localStorage.getItem(NOTES_LINKED_FLAG) === '1') return;
  } catch {
    return; // storage unavailable — nothing to migrate anyway
  }
  for (const key of Object.keys(getAllNotes())) {
    if (!/^\d+:\d+$/.test(key)) continue;
    if (isSaved('verse', key)) continue;
    autoSaveVerse(key, 'note');
  }
  try {
    localStorage.setItem(NOTES_LINKED_FLAG, '1');
  } catch {
    /* ignore */
  }
}

/**
 * Remove an item from Saved entirely, keeping the invariants that a verse is
 * never left highlighted-but-unsaved, and that a note never floats without
 * its verse card (highlighting/noting auto-save; removing here is the user
 * saying "drop this verse and its marks and note" — UI confirms first when a
 * note exists).
 *
 * Ordering subtlety: clearVerseHighlights' own auto-unsave skips verses that
 * are filed or noted (curated), so the explicit removeSavedItem at the end is
 * what actually removes — exactly "remove entirely" semantics.
 */
export function removeSavedItemAndCleanup(type: SavedItemType, key: string): void {
  if (type === 'verse') {
    clearVerseHighlights(key);
    const [s, v] = verseNums(key);
    if (Number.isFinite(s) && Number.isFinite(v)) deleteNote(s, v);
  }
  removeSavedItem(type, key);
}

/** Bulk variant used by the /saved page's selection bar. */
export function removeSavedItemsAndCleanup(refs: SavedItemRef[]): void {
  for (const ref of refs) removeSavedItemAndCleanup(ref.type, ref.key);
}
