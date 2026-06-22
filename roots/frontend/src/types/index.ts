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
  language_family?: string;
  date_from?: number | null;
  date_to?: number | null;
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

export interface VerseNavRef {
  surah: number;
  ayah: number;
}

export interface VerseData {
  surah: number;
  ayah: number;
  surah_name: string;
  text_uthmani: string;
  translation: string;
  words: Word[];
  roots_summary: RootSummary[];
  previous?: VerseNavRef | null;
  next?: VerseNavRef | null;
}

export interface SurahInfo {
  number: number;
  name: string;
  /** Arabic name (added 2026-04-26 — older API responses may omit this) */
  name_arabic?: string;
  /** Short English meaning, e.g. "The Opening" for Al-Fatihah */
  meaning?: string;
  verse_count: number;
}

/** Response from /api/surah/<n> — bulk fetch all verses of one surah
 *  for the reader page. Per-word data is omitted; the reader fetches it
 *  on demand via /api/verse/<ref> when word-by-word mode is on. */
export interface SurahData {
  surah: number;
  name: string;
  name_arabic: string;
  meaning: string;
  verse_count: number;
  verses: SurahVerse[];
}

export interface SurahVerse {
  verse: number;
  text_uthmani: string;
  translation: string;
  has_translation_note: boolean;
  has_grammar_note: boolean;
  /** True when an approved, non-hidden exegesis note exists for this verse. */
  has_exegesis?: boolean;
  /** Present when /api/surah/<n>?include=words was requested. */
  words?: SurahVerseWord[];
  /** Present when ?include=surveyed_roots was requested. Subset of roots
   *  in this verse that have a term_surveys row — used by the chip
   *  tooltip layer in reader translations. */
  surveyed_roots?: string[];
}

export interface SurahVerseWord {
  position: number;
  /** All morphology segments for this word position, ordered. The
   *  reader composes the visible Arabic by joining segment.form_arabic
   *  (or simply uses text_uthmani split-by-whitespace). The full
   *  segment list is what powers the hover-tooltip morphology + root
   *  information. Mirrors the shape of `Word.segments` on the verse
   *  page so WordTooltip can render it directly. */
  segments: SurahVerseWordSegment[];
  translation: string;
  /** Where the per-word translation came from:
   *    'word' — real per-word source (ai_word_meanings or word_glosses)
   *    'root' — fallback to the root's primary meaning (last resort,
   *             rendered with italics + parens to flag it's a hint,
   *             not a verb-form gloss)
   *    ''     — no gloss available
   */
  translation_source?: 'word' | 'root' | '';
}

export interface SurahVerseWordSegment {
  form_arabic: string;
  form_buckwalter: string;
  tag: string;
  pos: string;
  root_arabic: string;
  root_buckwalter: string;
  lemma_arabic: string;
  lemma_buckwalter: string;
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

export interface ThematicVerseRef {
  surah: number;
  ayah: number;
  text_uthmani: string;
  translation: string;
}

export interface ThematicLink {
  theme: string;
  summary: string;
  confidence: number;
  verses: ThematicVerseRef[];
}

export interface VerseThematicContext {
  passage: {
    start_ayah: number | null;
    end_ayah: number | null;
    theme: string;
    confidence: number;
  };
  surah_role: {
    summary: string;
    confidence: number;
  };
  neighbor_surahs: {
    summary: string;
    confidence: number;
  };
  quran_wide_links: ThematicLink[];
  evidence: Record<string, unknown>;
  model: {
    config_name: string;
    model_name: string;
    prompt_version: string;
    created_at: string;
  };
}

export interface ThematicContextResponse {
  query: { surah: number; ayah: number };
  thematic_context: VerseThematicContext;
}

export interface SurahContextKeyVerse {
  surah: number;
  ayah: number;
  why: string;
  text_uthmani: string;
  translation: string;
}

export interface VerseSurahContext {
  summary_so_far: string;
  current_verse_focus: string;
  key_verses: SurahContextKeyVerse[];
  summary_points: Array<{ text: string; refs: string[] }>;
  lexical_continuity: Array<{
    root_buckwalter: string;
    root_arabic: string;
    occurrences_before: number;
    example_refs: string[];
  }>;
  signal_score: number;
  verifier: Record<string, unknown>;
  evidence: Record<string, unknown>;
  model: {
    config_name: string;
    model_name: string;
    prompt_version: string;
    created_at: string;
  };
}

export interface SurahContextResponse {
  query: { surah: number; ayah: number };
  surah_context: VerseSurahContext;
}

export interface GrammarInsightItem {
  title: string;
  insight: string;
  refs: string[];
  kind?: 'investigative' | 'educational';
  educational_note?: string;
  category?:
    | 'perspective_shift'
    | 'person_mixture'
    | 'royal_we_vs_i'
    | 'gender_nuance'
    | 'sound_communication'
    | 'time_perspective'
    | 'oath_structure'
    | 'exception_scope'
    | 'conditional_structure'
    | 'cognate_accusative'
    | 'demonstrative_distance'
    | 'plural_type'
    | 'educational'
    | 'other_grammar';
  confidence?: number;
  morph_evidence?: Array<{ type: string; value: string }>;
}

export interface V7GrammarInsight {
  id: string;
  kind: 'investigative' | 'educational';
  category: string;
  title: string;
  claim: {
    observation: string;
    scope: 'word' | 'phrase' | 'clause' | 'verse';
    strength: 'direct' | 'probable' | 'tentative';
  };
  counterfactual: {
    present: boolean;
    type: 'explicit_alternative' | 'suppressed_alternative' | 'none';
    text: string | null;
    safety: 'high' | 'medium' | 'low' | null;
  };
  meaning_payoff: {
    text: string;
    type: string;
    strength: 'strong' | 'moderate' | 'light';
  };
  educational_note: {
    text: string;
    reading_level: 'basic' | 'intermediate';
  };
  evidence_trace: Array<{
    token_ref: string;
    surface_ar: string;
    buckwalter: string;
    root: string;
    feature_type: string;
    feature_value: string;
    role: 'primary_support' | 'secondary_support' | 'contrast_anchor';
  }>;
  quality: {
    model_confidence_raw: number;
    evidence_sufficiency: number;
    linguistic_correctness: number;
    interpretive_value: number;
    novelty: number;
    clarity: number;
    risk: number;
    overall_confidence: number;
  };
  display: {
    tier: 'primary' | 'secondary' | 'suppressed';
    eligible: boolean;
    reason_codes: string[];
  };
}

export interface VerseGrammarInsights {
  overview: string;
  insights: GrammarInsightItem[];
  signal_score: number;
  generation_version?: string;
  insights_v7?: V7GrammarInsight[];
  quality?: Record<string, unknown>;
  overall_confidence?: number;
  model_confidence_raw?: number;
  display?: Record<string, unknown>;
  verifier: Record<string, unknown>;
  evidence: Record<string, unknown>;
  model: {
    config_name: string;
    model_name: string;
    prompt_version: string;
    created_at: string;
  };
}

export interface GrammarInsightsResponse {
  query: { surah: number; ayah: number };
  grammar_insights: VerseGrammarInsights;
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

export interface VerseExegesisData {
  surah: number;
  ayah: number;
  exegesis_markdown: string;
  source_scores: number[] | null;
  created_at: string;
  edited_at: string | null;
}

/** One authenticated pre-Islamic poetry line quoted in a comparison. */
export interface PoetryQuotedLine {
  line_root_id: number;
  poet?: string;
  /** 'A' (Muʿallaqāt) | 'B' (major poets) | 'C' (broad scrape, illustration). */
  auth_tier?: string;
  arabic?: string;
  surface_word?: string;
  english?: string;
  translit?: string;
  note?: string;
}

/** Root-level comparison shown in the "In Pre-Islamic Poetry" section. */
export interface RootPoetryComparison {
  root_buckwalter: string;
  root_arabic: string;
  /** continuity | narrowing | widening | elevation | theologization |
   *  moralization | referential_transfer | reassignment */
  shift_type: string;
  comparison_markdown: string;
  quran_usage_summary?: string | null;
  poetry_usage_summary?: string | null;
  quoted_lines: PoetryQuotedLine[];
  collocations?: { quran?: string[]; poetry?: string[] } | null;
  /** True when the verdict is agreement, not contrast. */
  continuity: boolean;
  confidence?: number | null;
  auth_tier_max?: string | null;
  created_at?: string | null;
}

/** One line (bayt) of a pre-Islamic poem on the poem page. */
export interface PoemLine {
  line_no: number;
  arabic: string;
  english?: string | null;
  /** True when one of our comparisons quotes this line (highlighted). */
  quoted: boolean;
}

/** A full pre-Islamic poem (the /poem/<id> page). */
export interface PoemData {
  id: number;
  poet: string;
  poet_latin?: string | null;
  title?: string | null;
  meter?: string | null;
  rhyme?: string | null;
  era?: string | null;
  line_count: number;
  translated_count: number;
  lines: PoemLine[];
}

/** A row in the /poems library index. */
export interface PoemSummary {
  id: number;
  poet: string;
  poet_latin?: string | null;
  title?: string | null;
  meter?: string | null;
  era?: string | null;
  line_count: number;
  translated_count: number;
}

/** Verse-level poetry note shown below the exegesis. */
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
  // Keyed by lowercased term_english so lookups from [[markers]] are robust
  terms: Record<string, GrammarTerm>;
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
  primary_meaning?: string;
  detailed_meaning?: string;
  semantic_field?: string;
}

export interface WordMeaningBrief {
  meaning_short: string;
  has_detail: boolean;
  meaning_excerpt?: string | null;
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
  verse_root_buckwalters?: string[];
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
  preferred_source?: string;
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
  verse_root_buckwalters?: string[];
}
