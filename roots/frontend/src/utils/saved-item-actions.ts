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
  type SavedItem,
  type SavedItemType,
  type SavedItemRef,
} from './saved-items';
import { clearVerseHighlights, hasHighlights } from './verse-highlights';
import { getAllNotes, getItemNote, setItemNoteRaw, deleteItemNote } from './user-notes';
import { getSurahName } from './surah-names';

/**
 * Everything needed to auto-save an item when its note is first written.
 * Callers (pages/cards) build this so THIS coupling layer never has to import
 * word/root data fetchers — keeping the store→notes→actions graph one-way.
 */
export type NoteDescriptor = Omit<SavedItem, 'savedAt' | 'source' | 'folders'>;

function autoSaveItem(desc: NoteDescriptor): void {
  saveItem({ ...desc, source: 'note' });
}

/** Release an auto-saved item once nothing keeps it: not a manual save, not
 *  filed in any folder, no highlights left (verses only), no note left. */
function maybeReleaseAutoSavedItem(type: SavedItemType, key: string): void {
  const source = getSavedItemSource(type, key);
  if (source === undefined || source === 'manual') return;
  if (getItemFolderIds(type, key).length > 0) return;
  if (type === 'verse' && hasHighlights(key)) return;
  if (getItemNote(type, key)) return;
  removeSavedItem(type, key);
}

/**
 * THE note write path — every surface that saves/deletes a note goes through
 * here (verse reader gutter, research view, word/root pages, Saved page/panel),
 * so a note always lives under a saved item:
 *   - non-empty text → note stored + the item auto-saved (source 'note')
 *   - empty text     → note deleted + a pure note-save released
 */
export function setItemNote(desc: NoteDescriptor, text: string): void {
  if (text.trim()) {
    setItemNoteRaw(desc.type, desc.key, text);
    if (!isSaved(desc.type, desc.key)) autoSaveItem(desc);
  } else {
    deleteItemNote(desc.type, desc.key);
    maybeReleaseAutoSavedItem(desc.type, desc.key);
  }
}

/** Verse shim over setItemNote — builds the verse descriptor (label via
 *  getSurahName). Kept so every existing verse note caller stays unchanged. */
export function setVerseNote(surah: number, verse: number, text: string): void {
  const verseKey = `${surah}:${verse}`;
  setItemNote(
    {
      type: 'verse',
      key: verseKey,
      label: `${getSurahName(surah)} ${verseKey}`,
      href: `/verse/${verseKey}`,
      // arabic/translation omitted — SavedVerseContent lazily backfills them.
    },
    text,
  );
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
    // Only bare verse keys ("s:v"); namespaced word:/root: notes are born
    // coupled (their item is saved as the note is written) — nothing to migrate.
    if (!/^\d+:\d+$/.test(key)) continue;
    if (isSaved('verse', key)) continue;
    const [surah] = key.split(':').map(Number);
    autoSaveItem({
      type: 'verse',
      key,
      label: `${getSurahName(surah)} ${key}`,
      href: `/verse/${key}`,
    });
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
  if (type === 'verse') clearVerseHighlights(key);
  deleteItemNote(type, key);
  removeSavedItem(type, key);
}

/** Bulk variant used by the /saved page's selection bar. */
export function removeSavedItemsAndCleanup(refs: SavedItemRef[]): void {
  for (const ref of refs) removeSavedItemAndCleanup(ref.type, ref.key);
}
