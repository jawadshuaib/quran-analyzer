/**
 * Generic Quran text scanner — detects Quranic verses on any webpage
 * by matching normalized Arabic word trigrams against a pre-built index.
 */

import { normalizeArabic, hasArabic } from './normalize';

// ── Types ──────────────────────────────────────────────────────────────

interface TrigramIndex {
  trigrams: Record<string, number[][]>; // trigram → [[surah, ayah, startPos], ...]
  verses: Record<string, string[]>;     // "surah:ayah" → [normalized words]
}

export interface MatchedWord {
  node: Text;
  wordStart: number;  // char offset within the text node
  wordEnd: number;
  surah: number;
  ayah: number;
  position: number;   // 1-indexed word position in the verse
}

// ── State ──────────────────────────────────────────────────────────────

let index: TrigramIndex | null = null;
let indexLoading = false;
const SCANNED_ATTR = 'data-qrt-scanned';

// ── Index loading ──────────────────────────────────────────────────────

async function loadIndex(): Promise<TrigramIndex | null> {
  if (index) return index;
  if (indexLoading) {
    // Wait for the in-flight load
    while (indexLoading) {
      await new Promise((r) => setTimeout(r, 50));
    }
    return index;
  }

  indexLoading = true;
  try {
    const url = chrome.runtime.getURL('quran-index.json');
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to load index: ${res.status}`);
    index = await res.json() as TrigramIndex;
    return index;
  } catch (e) {
    console.warn('[QRT] Failed to load trigram index:', e);
    return null;
  } finally {
    indexLoading = false;
  }
}

// ── Text node collection ───────────────────────────────────────────────

function collectArabicTextNodes(root: Node): Text[] {
  const nodes: Text[] = [];
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      // Skip nodes inside our own tooltips
      const parent = node.parentElement;
      if (!parent) return NodeFilter.FILTER_REJECT;
      if (parent.closest('.qrt-tooltip, [data-qrt-bound]')) return NodeFilter.FILTER_REJECT;
      // Skip script/style/input elements
      const tag = parent.tagName;
      if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'TEXTAREA' || tag === 'INPUT' || tag === 'CODE' || tag === 'PRE') {
        return NodeFilter.FILTER_REJECT;
      }
      // Only accept nodes with Arabic text
      if (node.textContent && hasArabic(node.textContent)) {
        return NodeFilter.FILTER_ACCEPT;
      }
      return NodeFilter.FILTER_REJECT;
    },
  });

  let node: Text | null;
  while ((node = walker.nextNode() as Text | null)) {
    nodes.push(node);
  }
  return nodes;
}

// ── Matching ───────────────────────────────────────────────────────────

interface WordSpan {
  start: number; // char offset in text node
  end: number;
  normalized: string;
}

function findWordSpans(text: string): WordSpan[] {
  const spans: WordSpan[] = [];
  // Match runs of Arabic characters (including diacritics, small marks, tatweel)
  const re = /[\u0621-\u065F\u0670\u0671\u06D6-\u06ED\u0640\u06E0-\u06E9\u0610-\u061A]+/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    const norm = normalizeArabic(m[0]);
    if (norm.length > 0) {
      spans.push({ start: m.index, end: m.index + m[0].length, normalized: norm });
    }
  }
  return spans;
}

/**
 * Given a list of matches from trigrams, try to extend each match by checking
 * additional words against the verse's normalized word list.
 */
function extendMatch(
  spans: WordSpan[],
  startIdx: number,
  surah: number,
  ayah: number,
  startPos: number,
  idx: TrigramIndex,
): { endIdx: number; endPos: number } {
  const verseKey = `${surah}:${ayah}`;
  const verseWords = idx.verses[verseKey];
  if (!verseWords) return { endIdx: startIdx + 2, endPos: startPos + 2 };

  let wordIdx = startIdx + 3; // next word after the trigram
  let pos = startPos + 3;     // next verse position (1-indexed)

  while (wordIdx < spans.length && pos <= verseWords.length) {
    if (spans[wordIdx].normalized === verseWords[pos - 1]) {
      wordIdx++;
      pos++;
    } else {
      break;
    }
  }

  return { endIdx: wordIdx - 1, endPos: pos - 1 };
}

// Also try extending backward
function extendMatchBackward(
  spans: WordSpan[],
  startIdx: number,
  surah: number,
  ayah: number,
  startPos: number,
  idx: TrigramIndex,
): { newStartIdx: number; newStartPos: number } {
  const verseKey = `${surah}:${ayah}`;
  const verseWords = idx.verses[verseKey];
  if (!verseWords) return { newStartIdx: startIdx, newStartPos: startPos };

  let wordIdx = startIdx - 1;
  let pos = startPos - 1;

  while (wordIdx >= 0 && pos >= 1) {
    if (spans[wordIdx].normalized === verseWords[pos - 1]) {
      wordIdx--;
      pos--;
    } else {
      break;
    }
  }

  return { newStartIdx: wordIdx + 1, newStartPos: pos + 1 };
}

function matchSpans(spans: WordSpan[], idx: TrigramIndex): MatchedWord[] {
  const matches: MatchedWord[] = [];
  const matched = new Set<number>(); // track which span indices are already matched

  for (let i = 0; i <= spans.length - 3; i++) {
    if (matched.has(i)) continue;

    const tri = `${spans[i].normalized} ${spans[i + 1].normalized} ${spans[i + 2].normalized}`;
    const locations = idx.trigrams[tri];
    if (!locations || locations.length === 0) continue;

    // Pick the best matching location by extending the match
    let bestLoc = locations[0];
    let bestLen = 3;

    for (const loc of locations) {
      const [s, a, p] = loc;

      // Extend backward
      const { newStartIdx, newStartPos } = extendMatchBackward(spans, i, s, a, p, idx);
      // Extend forward
      const { endIdx: extEndIdx } = extendMatch(spans, newStartIdx, s, a, newStartPos, idx);

      const len = extEndIdx - newStartIdx + 1;
      if (len > bestLen) {
        bestLen = len;
        bestLoc = [s, a, newStartPos];
      }
    }

    const [surah, ayah, startPos] = bestLoc;
    // Re-extend with best location
    const { newStartIdx, newStartPos } = extendMatchBackward(spans, i, surah, ayah, startPos, idx);
    const { endIdx } = extendMatch(spans, newStartIdx, surah, ayah, newStartPos, idx);

    for (let j = newStartIdx; j <= endIdx; j++) {
      if (matched.has(j)) continue;
      matched.add(j);
      // We'll fill in the node reference later — just store offsets for now
      matches.push({
        node: null as unknown as Text,
        wordStart: spans[j].start,
        wordEnd: spans[j].end,
        surah,
        ayah,
        position: newStartPos + (j - newStartIdx),
      });
    }

    // Skip past this match
    i = endIdx;
  }

  return matches;
}

// ── DOM annotation ─────────────────────────────────────────────────────

function annotateTextNode(textNode: Text, matches: MatchedWord[]): void {
  if (matches.length === 0) return;

  const text = textNode.textContent!;
  const parent = textNode.parentNode;
  if (!parent) return;

  // Sort matches by position in the text
  matches.sort((a, b) => a.wordStart - b.wordStart);

  const frag = document.createDocumentFragment();
  let lastEnd = 0;

  for (const m of matches) {
    // Text before this word
    if (m.wordStart > lastEnd) {
      frag.appendChild(document.createTextNode(text.slice(lastEnd, m.wordStart)));
    }

    // Wrapped word
    const span = document.createElement('span');
    span.textContent = text.slice(m.wordStart, m.wordEnd);
    span.setAttribute('data-word-location', `${m.surah}:${m.ayah}:${m.position}`);
    span.setAttribute('data-qrt-scanned', '1');
    frag.appendChild(span);

    lastEnd = m.wordEnd;
  }

  // Remaining text
  if (lastEnd < text.length) {
    frag.appendChild(document.createTextNode(text.slice(lastEnd)));
  }

  parent.replaceChild(frag, textNode);
}

// ── Public API ─────────────────────────────────────────────────────────

/**
 * Scan the page (or a subtree) for Arabic text, match against the Quran
 * trigram index, and wrap detected Quranic words with annotated spans.
 * Returns true if any annotations were added.
 */
export async function scanForQuranText(root: Node = document.body): Promise<boolean> {
  const idx = await loadIndex();
  if (!idx) return false;

  const textNodes = collectArabicTextNodes(root);
  if (textNodes.length === 0) return false;

  let annotated = false;

  for (const textNode of textNodes) {
    const text = textNode.textContent;
    if (!text || !hasArabic(text)) continue;

    // Skip already-scanned ancestors
    const parent = textNode.parentElement;
    if (parent?.hasAttribute(SCANNED_ATTR)) continue;

    const spans = findWordSpans(text);
    if (spans.length < 3) continue; // Need at least 3 words for a trigram

    const matches = matchSpans(spans, idx);
    if (matches.length === 0) continue;

    // Set node reference
    for (const m of matches) {
      m.node = textNode;
    }

    annotateTextNode(textNode, matches);
    annotated = true;
  }

  return annotated;
}

/**
 * Quick check: does this page have enough Arabic content to warrant scanning?
 */
export function pageHasArabic(): boolean {
  const sample = document.body?.textContent?.slice(0, 50000) ?? '';
  return hasArabic(sample);
}
