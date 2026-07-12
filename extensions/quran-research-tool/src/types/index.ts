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

export interface GrammarTerm {
  term_english: string;
  term_arabic: string | null;
  plain_explanation: string;
  example_sentence: string | null;
  example_translation: string | null;
}

export interface GrammarNotesData {
  surah: number;
  ayah: number;
  notes_markdown: string;
  terms: Record<string, GrammarTerm>;
  config_name: string;
  model_name: string;
  created_at: string;
}

export interface VerseExegesisData {
  surah: number;
  ayah: number;
  exegesis_markdown: string;
  source_scores: number[] | null;
  created_at: string;
  edited_at: string | null;
}

/** One authenticated pre-Islamic poetry line quoted in a verse note. */
export interface PoetryQuotedLine {
  line_root_id: number;
  poet?: string;
  arabic?: string;
  surface_word?: string;
  english?: string;
  translit?: string;
  note?: string;
  /** Where this line lives in the poem library — lets an inline quote link to
   *  the website's /poem/<poem_id>#line-<line_no>. */
  poem_id?: number;
  line_no?: number;
}

/** Verse-level pre-Islamic poetry note shown below the exegesis. */
export interface VersePoetryNote {
  surah: number;
  ayah: number;
  focus_root_buckwalter?: string | null;
  note_markdown: string;
  quoted_lines: PoetryQuotedLine[];
  continuity: boolean;
  confidence?: number | null;
  auth_tier_max?: string | null;
  created_at?: string | null;
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
