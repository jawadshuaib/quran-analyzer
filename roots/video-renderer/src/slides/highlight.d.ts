// Type declarations for highlight.mjs (the shared, plain-JS highlight
// resolver used by both VerseFlowPage.tsx and scripts/verify.mjs).

export interface VerseFlowHighlightFields {
  arabicText: string;
  translation: string;
  highlightWordIndex?: number;
  highlightWordIndices?: number[];
  highlightTranslationText?: string;
}

export interface EnglishSpan {
  start: number;
  end: number;
  phrase: string;
}

export interface VerseFlowHighlightDescription {
  wordCount: number;
  paintedIndices: number[];
  paintedTokens: string[];
  outOfRangeIndices: number[];
  englishFound: boolean;
  englishSpan: string | null;
}

export function splitArabicWords(arabicText: string): string[];
export function resolveHighlightSet(slide: VerseFlowHighlightFields): Set<number>;
export function findEnglishSpan(
  translation: string,
  highlightTranslationText?: string,
): EnglishSpan;
export function describeVerseFlowHighlight(
  slide: VerseFlowHighlightFields,
): VerseFlowHighlightDescription;
