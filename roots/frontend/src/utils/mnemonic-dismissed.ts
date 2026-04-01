/**
 * Shared helpers for the "dismissed roots" feature.
 * Roots dismissed on the Mnemonic Sheet are stored in localStorage
 * and shown grayed-out on the Learning Dashboard.
 */

const STORAGE_KEY = 'mnemonic-dismissed-roots';

export function loadDismissed(): Set<string> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? new Set(JSON.parse(raw)) : new Set();
  } catch {
    return new Set();
  }
}

export function saveDismissed(set: Set<string>): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(set)));
}

export function clearDismissed(): void {
  localStorage.removeItem(STORAGE_KEY);
}
