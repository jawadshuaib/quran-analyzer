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
  // Animated with transform only (never width): iOS Safari stops painting
  // the page you're leaving once navigation starts, but keeps running
  // compositor animations, so a width transition froze in place. The grow
  // is front-loaded so the first second shows clear movement, and a
  // highlight sweeps along the bar for as long as it's up.
  const style = document.createElement('style');
  style.textContent = `
#${BAR_ID} { position: fixed; top: 0; left: 0; right: 0; height: 3px; z-index: 9999;
  overflow: hidden; pointer-events: none; opacity: 0; transition: opacity .2s; }
#${BAR_ID} > i { position: absolute; inset: 0; background: #BA7517; transform-origin: 0 50%;
  transform: scaleX(0); will-change: transform; }
#${BAR_ID} > b { position: absolute; top: 0; bottom: 0; left: 0; width: 40%; will-change: transform;
  background: linear-gradient(90deg, transparent, rgba(255,235,190,.9), transparent);
  transform: translateX(-100%); }
#${BAR_ID}.on { opacity: 1; }
#${BAR_ID}.on > i { animation: np-grow 12s cubic-bezier(.2,.6,.3,1) forwards; }
#${BAR_ID}.on > b { animation: np-sweep 1.1s linear infinite; }
@keyframes np-grow { 0% { transform: scaleX(0); } 3% { transform: scaleX(.3); }
  12% { transform: scaleX(.55); } 35% { transform: scaleX(.75); } 100% { transform: scaleX(.93); } }
@keyframes np-sweep { from { transform: translateX(-100%); } to { transform: translateX(250%); } }
@media (prefers-reduced-motion: reduce) { #${BAR_ID}.on > i { animation: none; transform: scaleX(.6); } }`;
  document.head.appendChild(style);
  bar = document.createElement('div');
  bar.id = BAR_ID;
  bar.innerHTML = '<i></i><b></b>';
  bar.setAttribute('role', 'progressbar');
  bar.setAttribute('aria-label', 'Loading page');
  document.body.appendChild(bar);
  return bar;
}

function start() {
  const bar = ensureBar();
  // restart the animations if a second link is tapped mid-load
  bar.className = '';
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
