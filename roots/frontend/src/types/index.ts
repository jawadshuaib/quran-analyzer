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

export interface RootSummary {
  root_arabic: string;
  root_buckwalter: string;
  occurrences: number;
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
