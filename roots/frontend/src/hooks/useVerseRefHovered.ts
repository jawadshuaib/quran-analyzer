import { useCallback, useSyncExternalStore } from 'react';
import { getVerseRefHover, subscribeVerseRefHover } from '../utils/verse-ref-hover';

/**
 * True while the reader is hovering a prose reference to this verse — see
 * utils/verse-ref-hover.ts. Rendered verses use it to light themselves up, so
 * a citation of "2:255" points at the actual verse when it happens to be on
 * the page (the reader, or the verse's own page) rather than only opening a
 * preview of it.
 */
export function useVerseRefHovered(verseKey: string): boolean {
  const subscribe = useCallback(
    (onChange: () => void) => subscribeVerseRefHover(() => onChange()),
    [],
  );
  const getSnapshot = useCallback(
    () => !!getVerseRefHover()?.has(verseKey),
    [verseKey],
  );
  // useSyncExternalStore, not subscribe-into-useState: the value is derived
  // from a store outside React, and this reads it during render instead of
  // painting once unhighlighted and then correcting itself.
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}
