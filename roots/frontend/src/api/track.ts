// Lightweight visitor-tracker — fires POST /api/track/pageview on every
// SPA route change. The backend handles privacy (hashes the IP with a
// server-side salt), exclusion of admin IPs, and silent-drops for /admin
// or /api paths. We still skip /admin client-side to avoid the round-trip
// noise during admin browsing.
//
// Single source of truth: this module patches window.history once on
// import and emits "trackpage" custom events. Call `initPageTracking()`
// once from the App entry point to wire up the listener.

let installed = false;
let lastFiredPath = '';
let lastFiredAt = 0;

function patchHistory() {
  if (installed) return;
  installed = true;

  const dispatch = () => window.dispatchEvent(new Event('trackpage'));

  // pushState / replaceState don't fire popstate, so wrap them.
  const origPush = window.history.pushState;
  const origReplace = window.history.replaceState;
  window.history.pushState = function (...args) {
    const ret = origPush.apply(this, args as Parameters<typeof origPush>);
    dispatch();
    return ret;
  };
  window.history.replaceState = function (...args) {
    const ret = origReplace.apply(this, args as Parameters<typeof origReplace>);
    dispatch();
    return ret;
  };
  window.addEventListener('popstate', dispatch);
}

async function postPageview(path: string, referrer: string) {
  try {
    await fetch('/api/track/pageview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      // keepalive lets the request survive page unload (e.g. when the user
      // clicks a real <a> link to leave the site).
      keepalive: true,
      body: JSON.stringify({ path, referrer }),
    });
  } catch {
    // Tracking is best-effort. Swallow network errors so they never
    // surface to the user — the page must keep working even if /api is
    // down or the user is offline.
  }
}

function fireForCurrentRoute() {
  const path = window.location.pathname;
  if (path.startsWith('/admin') || path.startsWith('/api/')) return;

  // Dedupe: don't double-fire when several frameworks dispatch
  // overlapping route events within the same paint.
  const now = Date.now();
  if (path === lastFiredPath && now - lastFiredAt < 1500) return;
  lastFiredPath = path;
  lastFiredAt = now;

  // Use document.referrer only on the very first load. SPA navigations
  // get their referrer from the previous page within the app.
  const referrer = document.referrer || '';
  postPageview(path, referrer);
}

export function initPageTracking() {
  patchHistory();
  window.addEventListener('trackpage', fireForCurrentRoute);
  // Fire once for the initial load.
  fireForCurrentRoute();
}
