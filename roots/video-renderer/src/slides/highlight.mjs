// Single source of truth for verse-word highlight resolution.
//
// BOTH the React slide (VerseFlowPage.tsx) AND the offline verifier
// (scripts/verify.mjs) import these functions, so the "which words
// does the renderer light up?" answer can never drift between what
// actually renders and what the Q&A match-gate validates.
//
// Plain .mjs (not .tsx) on purpose: Node can import it directly for
// the verifier, and esbuild resolves it from the .tsx at bundle time.
// Types live in highlight.d.ts for the TypeScript side.

/**
 * Split a verse's Arabic into the SAME token list the renderer draws.
 * Must match VerseFlowPage's `slide.arabicText.split(/\s+/)` EXACTLY,
 * including its handling of leading/trailing whitespace (no trim), so
 * 1-based indices line up byte-for-byte.
 */
export function splitArabicWords(arabicText) {
  return String(arabicText ?? '').split(/\s+/);
}

/**
 * Resolve the set of 0-based word positions the renderer will paint,
 * from a verse-flow slide's highlight fields. `highlightWordIndices`
 * (1-based array) is the source of truth; the legacy singular
 * `highlightWordIndex` folds in as a single element. Mirrors the
 * exact union logic in VerseFlowPage.
 */
export function resolveHighlightSet(slide) {
  const set = new Set();
  if (Array.isArray(slide.highlightWordIndices)) {
    for (const i of slide.highlightWordIndices) {
      if (Number.isInteger(i) && i > 0) set.add(i - 1);
    }
  }
  if (Number.isInteger(slide.highlightWordIndex) && (slide.highlightWordIndex ?? 0) > 0) {
    set.add(slide.highlightWordIndex - 1);
  }
  return set;
}

/**
 * Find the English phrase span the renderer will highlight — the same
 * case-insensitive indexOf VerseFlowPage uses. Returns { start, end }
 * with start === -1 when the phrase is absent (the silent-no-op case
 * the match-gate must treat as a hard failure).
 */
export function findEnglishSpan(translation, highlightTranslationText) {
  const en = String(highlightTranslationText ?? '').trim();
  if (!en) return { start: -1, end: -1, phrase: '' };
  const start = String(translation ?? '').toLowerCase().indexOf(en.toLowerCase());
  if (start < 0) return { start: -1, end: -1, phrase: en };
  return { start, end: start + en.length, phrase: en };
}

/**
 * Full report of what the renderer would paint for a verse-flow slide:
 * the token list, the painted 0-based indices (in range), any
 * out-of-range indices (bugs), the painted token strings, and the
 * English span. This is exactly the renderer's "truth" that the
 * Python match-gate diffs against the script's intent.
 */
export function describeVerseFlowHighlight(slide) {
  const words = splitArabicWords(slide.arabicText);
  const set = resolveHighlightSet(slide);
  const inRange = [];
  const outOfRange = [];
  for (const i of set) {
    if (i >= 0 && i < words.length) inRange.push(i);
    else outOfRange.push(i);
  }
  inRange.sort((a, b) => a - b);
  outOfRange.sort((a, b) => a - b);
  const en = findEnglishSpan(slide.translation, slide.highlightTranslationText);
  return {
    wordCount: words.length,
    // 1-based to match the payload's indexing convention.
    paintedIndices: inRange.map((i) => i + 1),
    paintedTokens: inRange.map((i) => words[i]),
    outOfRangeIndices: outOfRange.map((i) => i + 1),
    englishFound: en.start >= 0,
    englishSpan: en.start >= 0 ? slide.translation.slice(en.start, en.end) : null,
  };
}
