/**
 * Whether an "Ask the Quran" panel is open — so the related-verses bar, which
 * sits under it at the bottom of the screen, can step aside meanwhile.
 */

const EVENT = 'quranExplorer:ask-panel-changed';
let openCount = 0;

export function isAskPanelOpen(): boolean {
  return openCount > 0;
}

/** Call with true when a panel opens and false when it closes (or unmounts). */
export function setAskPanelOpen(open: boolean): void {
  openCount = Math.max(0, openCount + (open ? 1 : -1));
  try {
    window.dispatchEvent(new CustomEvent(EVENT));
  } catch {
    /* SSR / no window */
  }
}

export function subscribeAskPanel(cb: () => void): () => void {
  window.addEventListener(EVENT, cb);
  return () => window.removeEventListener(EVENT, cb);
}
