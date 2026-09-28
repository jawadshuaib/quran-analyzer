/**
 * A thin progress bar across the top of the screen from the moment a link
 * that leaves the page is tapped until the next page replaces this one.
 *
 * Most links on the site are plain <a href>s that do a full page load, so on
 * a slow phone connection a tap otherwise looks like it did nothing. Links
 * that are handled in-page (their click handler called preventDefault, e.g.
 * SPA navigation) never trigger it, nor do new-tab, download, hash-only and
 * off-site links.
 */

const BAR_ID = 'nav-progress';

function ensureBar(): HTMLDivElement {
  let bar = document.getElementById(BAR_ID) as HTMLDivElement | null;
  if (bar) return bar;
  const style = document.createElement('style');
  style.textContent = `
#${BAR_ID} { position: fixed; top: 0; left: 0; height: 3px; width: 0; z-index: 9999;
  background: #BA7517; box-shadow: 0 0 6px rgba(186,117,23,.5); opacity: 0;
  pointer-events: none; transition: width 8s cubic-bezier(.1,.7,.2,1), opacity .2s; }
#${BAR_ID}.on { opacity: 1; width: 85%; }
#${BAR_ID}.start { transition: none; width: 12%; opacity: 1; }
@media (prefers-reduced-motion: reduce) { #${BAR_ID} { transition: opacity .2s; } }`;
  document.head.appendChild(style);
  bar = document.createElement('div');
  bar.id = BAR_ID;
  bar.setAttribute('role', 'progressbar');
  bar.setAttribute('aria-label', 'Loading page');
  document.body.appendChild(bar);
  return bar;
}

function start() {
  const bar = ensureBar();
  // jump to a visible sliver at once, then creep toward 85% while we wait
  bar.className = 'start';
  void bar.offsetWidth;
  bar.className = 'on';
}

function stop() {
  const bar = document.getElementById(BAR_ID);
  if (bar) bar.className = '';
}

export function initNavProgress() {
  document.addEventListener('click', (e) => {
    if (e.defaultPrevented || e.button !== 0) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const a = (e.target as Element | null)?.closest?.('a');
    if (!a || !a.href) return;
    if (a.target && a.target !== '_self') return;
    if (a.hasAttribute('download')) return;
    const url = new URL(a.href, window.location.href);
    if (url.origin !== window.location.origin) return;
    // same page, only the hash differs: the browser just scrolls
    if (url.pathname === window.location.pathname && url.search === window.location.search && url.hash) return;
    start();
  });
  // Back/forward cache restores this page with the bar still showing.
  window.addEventListener('pageshow', stop);
  // If the navigation turned out to be a download or was cancelled, don't
  // leave the bar stuck on screen.
  window.addEventListener('focus', () => window.setTimeout(stop, 1500));
}
