import { lazy as reactLazy, type ComponentType } from 'react';

/**
 * React.lazy, but a chunk that fails to load reloads the page once.
 *
 * Each deploy ships new hashed chunk names and removes the old ones, so a tab
 * opened before a deploy would 404 on its next lazy import and render
 * nothing. A reload fetches the new index.html and its chunk names. The
 * sessionStorage flag stops a genuinely broken chunk from reload-looping.
 */
const FLAG = 'chunk-reload-at';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function lazy<T extends ComponentType<any>>(load: () => Promise<{ default: T }>) {
  return reactLazy(() =>
    load().then(
      (mod) => {
        try { sessionStorage.removeItem(FLAG); } catch { /* storage blocked */ }
        return mod;
      },
      (err) => {
        let last = 0;
        try { last = Number(sessionStorage.getItem(FLAG)) || 0; } catch { /* storage blocked */ }
        if (Date.now() - last > 10_000) {
          try { sessionStorage.setItem(FLAG, String(Date.now())); } catch { /* storage blocked */ }
          window.location.reload();
          return new Promise<{ default: T }>(() => {}); // wait for the reload
        }
        throw err;
      },
    ),
  );
}
