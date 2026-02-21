export interface MorphFeatures {
  gender?: string;
  number?: string;
  person?: string;
  case?: string;
  voice?: string;
  mood?: string;
  verb_form?: string;
  state?: string;
  [key: string]: string | undefined;
}

export interface Segment {
  form_arabic: string;
  form_buckwalter: string;
  tag: string;
  pos: string;
  root_arabic: string;
  root_buckwalter: string;
  lemma_arabic: string;
  lemma_buckwalter: string;
  features: MorphFeatures;
  features_raw: string;
}

export interface Word {
  position: number;
  segments: Segment[];
  translation?: string;
}

export interface CognateDerivative {
  language: string;
  word: string;
  displayed_text: string;
  concept: string;
  meaning: string;
}

export interface CognateData {
  semitic_root_id: number;
  transliteration: string;
  concept: string;
  derivatives: CognateDerivative[];
}

export interface RootSummary {
  root_arabic: string;
  root_buckwalter: string;
  occurrences: number;
  cognate?: CognateData | null;
}

export interface VerseData {
  surah: number;
  ayah: number;
  text_uthmani: string;
  translation: string;
  words: Word[];
  roots_summary: RootSummary[];
}

export interface SurahInfo {
  number: number;
  name: string;
  verse_count: number;
}

export interface SharedRoot {
  root_arabic: string;
  root_buckwalter: string;
  idf: number;
}

export interface RelatedVerse {
  surah: number;
  ayah: number;
  text_uthmani: string;
  translation: string;
  similarity_score: number;
  shared_roots: SharedRoot[];
}

export interface RelatedVersesResponse {
  query: { surah: number; ayah: number };
  related: RelatedVerse[];
  meta: { query_root_count: number };
}

export interface ContextVerse {
  surah: number;
  ayah: number;
  text_uthmani: string;
  translation: string;
}

export interface ContextResponse {
  query: { surah: number; ayah: number };
  context: ContextVerse[];
  surah_total: number;
}

export interface SearchTerm {
  lemma_bw: string | null;
  root_bw: string | null;
  form_bw: string | null;
  display_arabic: string;
}

export interface ResolvedTerm {
  display_arabic: string;
  search_type: 'lemma' | 'root' | 'form';
  search_key: string;
}

export interface WordSearchResult {
  surah: number;
  ayah: number;
  text_uthmani: string;
  translation: string;
  score: number;
  matched_terms: ResolvedTerm[];
  matched_positions: number[];
}

export interface WordSearchResponse {
  terms_used: ResolvedTerm[];
  results: WordSearchResult[];
  total_found: number;
}
