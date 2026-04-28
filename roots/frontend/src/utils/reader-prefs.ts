/**
 * Reader-mode preferences. Currently just the word-by-word toggle.
 *
 * Same defensive persistence rules as user-notes / last-read:
 *   - Stable namespaced key (we keep the EXISTING quranExplorer.wordToWord
 *     Enabled key that VerseDisplay used so we don't orphan anyone's
 *     existing setting)
 *   - "1" / "0" string values (back-compatible with the old code)
 *   - Cross-tab sync via a custom event + the storage event
 *   - Never wiped except via explicit user action
 */

const WORD_TO_WORD_KEY = 'quranExplorer.wordToWordEnabled';
const CHANGE_EVENT = 'quranExplorer:reader-prefs-changed';

export function isWordByWordEnabled(): boolean {
  try {
    return localStorage.getItem(WORD_TO_WORD_KEY) === '1';
  } catch {
    return false;
  }
}

export function setWordByWordEnabled(enabled: boolean): void {
  try {
    localStorage.setItem(WORD_TO_WORD_KEY, enabled ? '1' : '0');
    window.dispatchEvent(new CustomEvent(CHANGE_EVENT));
  } catch {
    /* silent */
  }
}

export function subscribeToReaderPrefs(cb: () => void): () => void {
  const onCustom = () => cb();
  const onStorage = (e: StorageEvent) => {
    if (e.key === WORD_TO_WORD_KEY) cb();
  };
  window.addEventListener(CHANGE_EVENT, onCustom);
  window.addEventListener('storage', onStorage);
  return () => {
    window.removeEventListener(CHANGE_EVENT, onCustom);
    window.removeEventListener('storage', onStorage);
  };
}
