/**
 * Cross-store saved-item actions.
 *
 * Lives outside saved-items.ts because it needs verse-highlights.ts, which
 * itself imports saved-items.ts (the auto-save coupling) — putting this in
 * the store would create an import cycle.
 */

import { removeSavedItem, type SavedItemType, type SavedItemRef } from './saved-items';
import { clearVerseHighlights } from './verse-highlights';

/**
 * Remove an item from Saved entirely, keeping the invariant that a verse is
 * never left highlighted-but-unsaved (highlighting auto-saves; removing here
 * is the user saying "drop this verse and its marks").
 *
 * Note the ordering subtlety: clearVerseHighlights' own auto-unsave skips
 * verses that are filed in folders (curated), so the explicit removeSavedItem
 * after it is what actually removes — exactly "remove entirely" semantics.
 */
export function removeSavedItemAndCleanup(type: SavedItemType, key: string): void {
  if (type === 'verse') clearVerseHighlights(key);
  removeSavedItem(type, key);
}

/** Bulk variant used by the /saved page's selection bar. */
export function removeSavedItemsAndCleanup(refs: SavedItemRef[]): void {
  for (const ref of refs) removeSavedItemAndCleanup(ref.type, ref.key);
}
