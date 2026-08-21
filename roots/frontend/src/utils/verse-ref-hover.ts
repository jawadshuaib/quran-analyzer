/**
 * Transient "which verse is the reader pointing at" state.
 *
 * A verse reference in prose (an exegesis note, an Ask-the-Quran answer, a
 * dictionary entry) already opens a hover preview of the verse it cites. But
 * when that verse is *also* on the page — reading Surah 2 and the answer cites
 * 2:255, or a note on a verse page citing the verse it belongs to — the more
 * useful answer to "which verse is that?" is the one already in front of the
 * reader. Hovering the reference lights it up where it sits.
 *
 * Same shape and reasoning as word-hover.ts (the citation → quoted-words
 * highlight): the prose and the verse are rendered by component trees with no
 * common ancestor, so the state lives in a module-level store both sides
 * subscribe to. Ephemeral pointer state — never persisted, cleared on
 * mouse-out. Distinct from verse-highlights.ts, which is the reader's own
 * saved highlights.
 */

interface Held {
  /** "2:255", "2:256", … — every verse the hovered reference covers, so a
   *  range ("2:255–257") lights all of its verses, not just the first. */
  keys: Set<string>;
  /** Which reference currently holds the highlight. Prose routinely cites the
   *  same verse twice, so several spans map to the same key set. */
  owner: string;
}

let current: Held | null = null;
const listeners = new Set<(keys: ReadonlySet<string> | null) => void>();

function notify() {
  listeners.forEach((fn) => fn(current ? current.keys : null));
}

function sameKeys(a: Set<string>, b: Set<string>): boolean {
  if (a.size !== b.size) return false;
  for (const k of a) if (!b.has(k)) return false;
  return true;
}

export function getVerseRefHover(): ReadonlySet<string> | null {
  return current ? current.keys : null;
}

export function setVerseRefHover(keys: string[], owner: string): void {
  const next = new Set(keys);
  const unchanged = !!current && sameKeys(current.keys, next);
  // Always take ownership, even when the keys are unchanged: pointer-enter on
  // the next reference fires before pointer-leave on the previous one, so the
  // span being left must not be able to clear a highlight already handed on.
  current = { keys: next, owner };
  // Only repaint when the set actually changed — repeated pointer events over
  // one reference shouldn't re-render every verse on the page.
  if (!unchanged) notify();
}

/** Release the highlight, but only if `owner` still holds it. */
export function clearVerseRefHover(owner: string): void {
  if (!current || current.owner !== owner) return;
  current = null;
  notify();
}

export function subscribeVerseRefHover(
  fn: (keys: ReadonlySet<string> | null) => void,
): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}
