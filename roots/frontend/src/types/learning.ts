// ── Learning Curriculum Types ──

export interface LearningUnit {
  unit_number: number;
  unit_theme: string;
  roots: LearningRootSummary[];
}

export interface LearningRootSummary {
  root_buckwalter: string;
  root_arabic: string;
  frequency_rank: number;
  theological_importance: number;
  derivative_richness: number;
  anchor_verse: string; // "S:A"
  related_roots: string[];
  mnemonic_image_url: string | null;
  mnemonic_caption: string | null;
  top_derivatives: { lemma_arabic: string; meaning_gloss: string }[];
}

export interface CurriculumResponse {
  units: LearningUnit[];
}

export interface LearningWordData {
  pos: number;
  arabic: string;
  lemma_bw: string;
  lemma_ar: string;
  root_bw: string;
  tag: string;
  part_of_speech: string;
  gloss: string;
  is_target: boolean;
  ai_meaning?: {
    meaning_short: string;
    preferred_translation?: string;
    preferred_source?: string;
  };
}

export interface LearningVerseData {
  chapter: number;
  verse: number;
  text_uthmani: string;
  translation: string;
  surah_name: string;
  words: LearningWordData[];
}

export interface LearningDerivative {
  lemma_buckwalter: string;
  lemma_arabic: string;
  pos: string;
  verb_form: string | null;
  frequency: number;
  meaning_gloss: string;
  semantic_shift: string;
  display_order: number;
}

export interface LearningContextVerse {
  verse_ref: string;
  verse_data: LearningVerseData | null;
  target_lemma_buckwalter: string;
  verse_role: 'anchor' | 'contrast' | 'reinforcement';
  teaching_note: string;
}

export interface RelatedRootInfo {
  root_buckwalter: string;
  root_arabic: string;
  unit_number: number;
  unit_theme: string;
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

export interface LearningRootDetail {
  root_buckwalter: string;
  root_arabic: string;
  unit_number: number;
  unit_theme: string;
  theological_importance: number;
  root_story: string;
  teaching_notes: string;
  mnemonic_image_url: string | null;
  mnemonic_caption: string | null;
  anchor_verse: {
    verse_ref: string;
    verse_data: LearningVerseData | null;
  };
  derivatives: LearningDerivative[];
  context_verses: LearningContextVerse[];
  cognate: CognateData | null;
  related_roots: RelatedRootInfo[];
}

export interface ReviewVerseData {
  chapter: number;
  verse: number;
  surah_name: string;
  text_uthmani: string;
  translation: string;
  target_positions: number[];
  target_words: {
    pos: number;
    arabic: string;
    lemma_bw: string;
    lemma_ar: string;
    gloss: string;
  }[];
}

export interface ReviewVersesResponse {
  verses: ReviewVerseData[];
}

export interface AskResponse {
  answer: string;
  model: string;
  elapsed_ms: number;
}

// ── Progress / Session Types (localStorage) ──

export interface SM2State {
  interval: number;    // Days until next review
  repetition: number;  // Number of successful reviews
  easeFactor: number;  // SM-2 ease factor (starts at 2.5)
}

export interface RootProgress {
  status: 'unseen' | 'learning' | 'reviewing' | 'mastered';
  firstSeen: string;     // ISO timestamp
  lastReviewed: string;  // ISO timestamp
  versesExposed: string[]; // "S:A" of seen verses
  selfRating: number;    // Last self-assessment (0-5)
  sm2: SM2State;
}

export interface ReviewItem {
  rootBw: string;
  dueDate: string; // ISO date string (YYYY-MM-DD)
}

export interface LearningStats {
  totalRootsLearned: number;
  totalReviewsDone: number;
  currentStreak: number;
  lastActivityDate: string; // ISO date
}

export interface LearningProgress {
  version: 1;
  currentUnit: number;
  rootProgress: Record<string, RootProgress>;
  reviewQueue: ReviewItem[];
  stats: LearningStats;
}
