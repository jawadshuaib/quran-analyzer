/**
 * The visible viewport box, for clamping floating UI (tooltips, popovers,
 * sheets) so it can never be placed off-screen.
 *
 * Deliberately `document.documentElement.client{Width,Height}` and NOT
 * `window.inner{Width,Height}`: horizontal overflow ANYWHERE on the page
 * inflates window.innerWidth to the wider layout viewport, so a clamp against
 * it puts the right-hand bound past what the reader can actually see and the
 * element still runs off the edge — most visibly on a phone, where the excess
 * is a large fraction of the screen. clientWidth/clientHeight report the real
 * visible box regardless of what overflows inside it.
 *
 * clientHeight is also steadier than innerHeight on mobile, where innerHeight
 * changes as the URL bar collapses.
 *
 * Use this for every viewport-clamped placement, so the next such component
 * doesn't reintroduce the bug.
 */
export function viewportSize(): { width: number; height: number } {
  const el = document.documentElement;
  return { width: el.clientWidth, height: el.clientHeight };
}
