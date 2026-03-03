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

export interface AITranslationData {
  surah: number;
  ayah: number;
  translation: string;
  departure_notes: string | null;
  config_name: string;
  model_name: string;
  created_at: string;
}

export interface LemmaInfo {
  lemma_arabic: string;
  lemma_buckwalter: string;
}

export interface RootSampleVerse {
  surah: number;
  ayah: number;
  text_uthmani: string;
  translation: string;
  matched_positions: number[];
}

export interface RootDetailData {
  root_arabic: string;
  root_buckwalter: string;
  total_occurrences: number;
  lemmas: LemmaInfo[];
  cognate: CognateData | null;
  sample_verses: RootSampleVerse[];
}

export interface WordMeaningBrief {
  meaning_short: string;
  has_detail: boolean;
  preferred_translation?: string;
  preferred_source?: 'conventional' | 'ai' | 'judge';
}

export interface WordMeaningsResponse {
  surah: number;
  ayah: number;
  meanings: Record<string, WordMeaningBrief>;
}

export interface WordOccurrence {
  surah: number;
  ayah: number;
  word_positions: number[];
  text_uthmani: string;
  translation: string;
  conventional_gloss: string;
  ai_meaning: string | null;
}

export interface WordAIMeaning {
  meaning_short: string;
  meaning_detailed: string;
  semantic_field: string | null;
  cross_ref_notes: string | null;
  cognate_notes: string | null;
  morphology_notes: string | null;
  departure_notes: string | null;
  config_name: string;
  model_name: string;
  created_at: string;
  preferred_translation?: string;
  preferred_source?: 'conventional' | 'ai' | 'judge';
}

export interface WordAnalysisData {
  surah: number;
  ayah: number;
  word_pos: number;
  text_uthmani: string;
  translation: string;
  segments: Segment[];
  conventional_gloss: string;
  root_arabic: string | null;
  root_buckwalter: string | null;
  lemma_arabic: string | null;
  lemma_buckwalter: string | null;
  cognate: CognateData | null;
  other_occurrences: WordOccurrence[];
  total_lemma_occurrences: number;
  ai_meaning: WordAIMeaning | null;
}
