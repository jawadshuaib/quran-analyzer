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

// --- Types for verse card / word tooltips ---

export interface Segment {
  form_arabic: string;
  form_buckwalter: string;
  tag: string;
  pos: string;
  root_arabic: string;
  root_buckwalter: string;
  lemma_arabic: string;
  lemma_buckwalter: string;
}

export interface Word {
  position: number;
  segments: Segment[];
  translation?: string;
}

export interface RootSummary {
  root_arabic: string;
  root_buckwalter: string;
  occurrences: number;
}

export interface VerseData {
  surah: number;
  ayah: number;
  surah_name: string;
  text_uthmani: string;
  translation: string;
  words: Word[];
  roots_summary: RootSummary[];
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
