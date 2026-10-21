/**
 * The DOM side of note highlights (store + anchoring: note-highlights.ts).
 *
 * A highlightable note renders inside an element carrying
 *   data-note-hl="<kind>"  data-note-verse="<surah:ayah>"  data-note-src="<hash>"
 * (see NoteHighlightable). This module reads such an element's text the same
 * way every time — so a passage quoted from it on one surface is found again on
 * another — and converts between live DOM Ranges and offsets into that text.
 */

import {
  addNoteHighlight,
  getNoteHighlights,
  resolveNoteHighlight,
  type NoteKind,
} from './note-highlights';

export interface NoteTextModel {
  /** The note's readable text. Paragraph-like blocks are joined by "\n". */
  text: string;
  /** Each text node and the offset in `text` where it begins. */
  nodes: { node: Text; start: number }[];
}

const BLOCK_SELECTOR = 'p, div, li, h1, h2, h3, h4, h5, h6';

/** Text that isn't part of the note: hover tooltips rendered inline (the
 *  poetry quote's), and anything marked as UI chrome. */
const SKIP_SELECTOR = '[role="tooltip"], [data-nh-ignore]';

/** Letters (incl. transliteration marks like ʿ and Arabic diacritics) and digits. */
const WORD_CHAR = /[\p{L}\p{M}\p{N}]/u;

export function readNoteText(root: HTMLElement): NoteTextModel {
  const walker = root.ownerDocument.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode: (n) =>
      n.parentElement?.closest(SKIP_SELECTOR) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT,
  });
  let text = '';
  const nodes: NoteTextModel['nodes'] = [];
  let lastBlock: Element | null = null;
  for (let n = walker.nextNode() as Text | null; n; n = walker.nextNode() as Text | null) {
    // A virtual newline between paragraphs, so a passage spanning two of them
    // reads naturally when quoted back (on the Saved page) instead of running
    // the sentences together. It belongs to no node.
    const block = n.parentElement?.closest(BLOCK_SELECTOR) ?? root;
    if (lastBlock && block !== lastBlock && text && !text.endsWith('\n')) text += '\n';
    lastBlock = block;
    nodes.push({ node: n, start: text.length });
    text += n.data;
  }
  return { text, nodes };
}

/** The [start, end) offsets a Range covers within the model, or null when it
 *  covers none of its text. */
export function rangeToOffsets(model: NoteTextModel, range: Range): { start: number; end: number } | null {
  let start = -1;
  let end = -1;
  for (const { node, start: at } of model.nodes) {
    if (!range.intersectsNode(node)) continue;
    const from = node === range.startContainer ? range.startOffset : 0;
    const to = node === range.endContainer ? range.endOffset : node.length;
    // intersectsNode is also true for a boundary that merely touches the node.
    if (to <= from) continue;
    if (start < 0) start = at + from;
    end = at + to;
  }
  return start >= 0 && end > start ? { start, end } : null;
}

/** A live Range over text[start, end), or null if the offsets fall outside. */
export function offsetsToRange(model: NoteTextModel, start: number, end: number): Range | null {
  const { nodes } = model;
  if (!nodes.length) return null;
  // Start in the node that holds `start` — or, when `start` is a virtual
  // newline, at the beginning of the node after it.
  const s = nodes.find((n) => start < n.start + n.node.length);
  // End in the node that holds the char before `end`.
  let e: (typeof nodes)[number] | undefined;
  for (const n of nodes) {
    if (n.start < end) e = n;
    else break;
  }
  if (!s || !e) return null;
  const range = s.node.ownerDocument.createRange();
  range.setStart(s.node, Math.max(0, start - s.start));
  range.setEnd(e.node, Math.min(e.node.length, end - e.start));
  return range.collapsed ? null : range;
}

/** Verse text for the auto-saved item, read off the verse on the page (the
 *  same attributes HighlightController uses). */
function verseMetaFromPage(verseKey: string): { arabic?: string; translation?: string } {
  const region = document.querySelector(
    `[data-arabic-region][data-verse-key="${CSS.escape(verseKey)}"]`,
  );
  return {
    arabic: region?.getAttribute('data-verse-text') || undefined,
    translation: region?.getAttribute('data-verse-translation') || undefined,
  };
}

/**
 * Turn whatever part of the current selection falls inside highlightable notes
 * into note highlights — one per note touched. The selection itself is left
 * alone, so the passage can still be copied.
 */
export function captureNoteSelection(sel: Selection): void {
  if (sel.isCollapsed || sel.rangeCount === 0) return;
  const roots = document.querySelectorAll<HTMLElement>('[data-note-hl][data-note-verse]');
  roots.forEach((root) => {
    const note = root.getAttribute('data-note-hl') as NoteKind;
    const verseKey = root.getAttribute('data-note-verse') || '';
    const srcHash = root.getAttribute('data-note-src') || '';
    let model: NoteTextModel | null = null;
    for (let i = 0; i < sel.rangeCount; i++) {
      const range = sel.getRangeAt(i);
      if (!range.intersectsNode(root)) continue;
      model ??= readNoteText(root);
      const hit = rangeToOffsets(model, range);
      if (!hit) continue;
      let { start, end } = hit;
      const { text } = model;
      // Drop the stray whitespace a drag tends to pick up at either end.
      while (start < end && /\s/.test(text[start])) start++;
      while (end > start && /\s/.test(text[end - 1])) end--;
      if (end - start < 2) continue; // a stray click-drag, not a passage
      // Snap out to whole words, as a verse highlight snaps to whole tokens —
      // a drag that starts or stops mid-word means the word.
      while (start > 0 && WORD_CHAR.test(text[start - 1]) && WORD_CHAR.test(text[start])) start--;
      while (end < text.length && WORD_CHAR.test(text[end]) && WORD_CHAR.test(text[end - 1])) end++;

      // Fold in any highlight this one overlaps or touches.
      const mergeIds: string[] = [];
      for (const h of getNoteHighlights(verseKey)) {
        if (h.note !== note) continue;
        const r = resolveNoteHighlight(text, h);
        if (r && r.start <= end && r.end >= start) {
          mergeIds.push(h.id);
          start = Math.min(start, r.start);
          end = Math.max(end, r.end);
        }
      }
      addNoteHighlight(verseKey, note, text, start, end, srcHash, mergeIds, verseMetaFromPage(verseKey));
    }
  });
}
