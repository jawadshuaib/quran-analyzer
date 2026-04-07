/**
 * LocalStorage helpers for the "Ask the Quran" assistant.
 * Stores the user's Claude API key, session ID, and model preference.
 */

const API_KEY_KEY = 'quranExplorer.claudeApiKey';
const SESSION_KEY = 'quranExplorer.sessionId';
const MODEL_KEY = 'quranExplorer.claudeModel';

export const DEFAULT_MODEL = 'claude-sonnet-4-20250514';
export const AVAILABLE_MODELS = [
  { id: 'claude-sonnet-4-20250514', label: 'Claude Sonnet 4 (recommended)' },
  { id: 'claude-opus-4-20250514', label: 'Claude Opus 4 (strongest, more expensive)' },
];

export function getApiKey(): string | null {
  try {
    return localStorage.getItem(API_KEY_KEY);
  } catch {
    return null;
  }
}

export function setApiKey(key: string): void {
  try {
    localStorage.setItem(API_KEY_KEY, key.trim());
  } catch {
    // localStorage may be blocked
  }
}

export function removeApiKey(): void {
  try {
    localStorage.removeItem(API_KEY_KEY);
  } catch {
    // ignore
  }
}

export function getSessionId(): string {
  try {
    let id = localStorage.getItem(SESSION_KEY);
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem(SESSION_KEY, id);
    }
    return id;
  } catch {
    return 'anonymous';
  }
}

export function getModel(): string {
  try {
    return localStorage.getItem(MODEL_KEY) || DEFAULT_MODEL;
  } catch {
    return DEFAULT_MODEL;
  }
}

export function setModel(model: string): void {
  try {
    localStorage.setItem(MODEL_KEY, model);
  } catch {
    // ignore
  }
}
