/**
 * Transient "which words is the reader pointing at" state.
 *
 * Hovering a citation inside an exegesis note (e.g. *inna l-ḥasanāti yudhhibna
 * l-sayyiʾāt*, or the Arabic طَرَفَىِ ٱلنَّهَارِ) highlights the words of the verse
 * that the citation quotes. The prose and the Arabic are rendered by different
 * component trees with no common ancestor holding this state, so it lives in a
 * module-level store both sides subscribe to.
 *
 * Deliberately NOT part of verse-highlights.ts: those are the reader's own
 * saved highlights, persisted to localStorage. This is ephemeral pointer
 * state — never stored, cleared on mouse-out.
 */

export interface WordHover {
  /** "11:114" — scopes the highlight so only the right verse reacts. */
  verseKey: string;
  /** 1-indexed, inclusive, matching the word positions the reader renders. */
  start: number;
  end: number;
}

interface Held extends WordHover {
  /** Which citation currently owns the highlight. A note often cites the same
   *  phrase more than once, so several spans map to the same word range. */
  owner: string;
}

let current: Held | null = null;
const listeners = new Set<(h: WordHover | null) => void>();

function notify() {
  listeners.forEach((fn) => fn(current));
}

export function getWordHover(): WordHover | null {
  return current;
}

export function setWordHover(hover: WordHover, owner: string): void {
  const sameRange =
    !!current &&
    current.verseKey === hover.verseKey &&
    current.start === hover.start &&
    current.end === hover.end;
  // Always take ownership, even when the range is unchanged: moving between two
  // citations of the same phrase must transfer the claim, or the span being
  // left will clear a highlight the span being entered still wants.
  current = { ...hover, owner };
  // Only repaint when the range actually changed — repeated pointer events over
  // one citation shouldn't re-render every word in the verse.
  if (!sameRange) notify();
}

/** Release the highlight, but only if `owner` still holds it. Pointer enter on
 *  the next citation fires before leave on the previous one, so an unguarded
 *  clear would wipe a highlight that has already been handed on. */
export function clearWordHover(owner: string): void {
  if (!current || current.owner !== owner) return;
  current = null;
  notify();
}

export function subscribeWordHover(fn: (h: WordHover | null) => void): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

/** True when `pos` falls inside the active hover for `verseKey`. */
export function isWordHovered(
  hover: WordHover | null,
  verseKey: string,
  pos: number,
): boolean {
  return !!hover && hover.verseKey === verseKey && pos >= hover.start && pos <= hover.end;
}
