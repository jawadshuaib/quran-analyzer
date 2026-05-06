import { z } from 'zod';

// Per-slide narration. Text is what we send to ElevenLabs TTS.
// displayText overrides the karaoke caption when our TTS input
// uses phonetic spellings (e.g. "noon-zay-lam") but we want to
// display proper transliteration ("nūn-zāy-lām") to viewers. When
// displayText is omitted, the caption uses `text` directly.
//
// audioFile + alignment are FILLED IN by scripts/narration.mjs
// after the ElevenLabs call. Operators don't write these by hand:
//   - audioFile is a relative filename in public/, e.g. "narr-abc123.mp3"
//   - alignment is the character-level timing data ElevenLabs
//     returns from the with-timestamps endpoint, used to drive the
//     karaoke per-word highlight.
export const NarrationAlignment = z.object({
  // Each char + its [start, end] in seconds, indexed against `text`.
  // We don't try to remap to displayText — that'd require Ollama
  // alignment work. For v1, we accept that displayText with a
  // different word count won't be perfectly synced; the per-word
  // approximation is close enough.
  characters: z.array(z.string()),
  starts: z.array(z.number()),
  ends: z.array(z.number()),
});

export const Narration = z.object({
  text: z.string(),
  displayText: z.string().optional(),
  audioFile: z.string().optional(),
  alignment: NarrationAlignment.optional(),
  // Total audio duration in seconds. Computed from alignment after
  // generation. Used by the renderer to extend slide.durationSec
  // when the spoken narration runs longer than the visual dwell.
  durationSec: z.number().optional(),
});

// Each slide is a self-contained "scene" the renderer knows how to
// draw. Backend assembles a list of these and ships the JSON to
// scripts/render.mjs. Adding a new slide type means: add a variant
// here, create a corresponding component under src/slides/, and wire
// it into the renderer in src/compositions/WordDetail.tsx.

export const RootSlide = z.object({
  type: z.literal('root'),
  durationSec: z.number().positive().default(5),
  rootArabic: z.string(),       // e.g. "ن ز ل" with spaces between letters
  rootLabel: z.string(),         // e.g. "Root: nzl"
  meaningTitle: z.string().default('Meaning'),
  meaning: z.string(),           // e.g. "Descend/send down (from above)"
  narration: Narration.optional(),
});

export const VerseFlowSlide = z.object({
  type: z.literal('verse-flow'),
  durationSec: z.number().positive().default(6),
  surah: z.number().int().positive(),
  ayah: z.number().int().positive(),
  arabicText: z.string(),
  translation: z.string(),
  // 1-indexed position of the target word in the arabic text (split
  // on whitespace). Highlighted on screen so the viewer can match
  // the spoken word to the visible word.
  highlightWordIndex: z.number().int().positive().optional(),
  // Optional substring of `translation` to highlight. When present,
  // the renderer finds it (case-insensitively) and gives it the
  // same yellow pill treatment so the viewer can see the
  // Arabic→English correspondence at a glance.
  highlightTranslationText: z.string().optional(),
  narration: Narration.optional(),
});

export const Word = z.object({
  ar: z.string(),
  en: z.string(),
  highlight: z.boolean().optional(),
});

export const WordToWordSlide = z.object({
  type: z.literal('word-to-word'),
  durationSec: z.number().positive().default(6),
  surah: z.number().int().positive(),
  ayah: z.number().int().positive(),
  // Words in Quranic order — renderer arranges them RTL.
  words: z.array(Word),
  translation: z.string(),
  narration: Narration.optional(),
});

// Closing card — al-nuqta brand splash. Mirrors the outro the
// existing ffmpeg pipeline produces (warm-charcoal bg, site name +
// tagline) so videos rendered through Remotion close consistently
// with the rest of the channel.
//
// outroAudioFile: optional sound bite played over the splash —
// matches the existing pipeline's outro_audio_filename feature.
// File must already be staged in public/ by the caller (the
// Python orchestrator copies it from data/educational_outro_audio/
// before invoking the renderer).
export const OutroSlide = z.object({
  type: z.literal('outro'),
  durationSec: z.number().positive().default(5),
  siteName: z.string().default('al-nuqta.com'),
  tagline: z.string().default('A Root Based Translation of the Quran'),
  outroAudioFile: z.string().optional(),
  narration: Narration.optional(),
});

// ---------------------------------------------------------------------------
// Grammar Insights series slides
//
// These are bespoke for the grammatical-insights pipeline. They mirror
// the visual language of the existing Word Origins slides (same fonts,
// same card geometry) but use the amber accent palette so the Grammar
// Insights series is visually distinct on the channel.
// ---------------------------------------------------------------------------

// One highlight on the verse — a word index (1-based) plus optional
// metadata so the renderer can color-code by what kind of grammatical
// move is being shown. Multiple highlights coexist on the same verse,
// each in its own pastel color, so a viewer can see at a glance how
// many moves are at play.
export const GrammarHighlight = z.object({
  // 1-indexed within the Arabic words split on whitespace.
  wordIndex: z.number().int().positive(),
  // Optional: the corresponding English token to highlight in parallel.
  // Renderer searches the translation case-insensitively.
  translationSubstring: z.string().optional(),
  // Semantic color hint. Renderer maps to a pastel pill background.
  // 'tense'    → amber  (e.g. perfective for future)
  // 'pronoun'  → blue   (e.g. iltifat: He → We)
  // 'fronted'  → rose   (taqdim: object brought to the front)
  // 'agent'    → green  (passive voice / agent omission)
  // 'default'  → amber  (when no semantic hint is provided)
  marker: z.enum(['tense', 'pronoun', 'fronted', 'agent', 'default']).default('default'),
});

// The workhorse slide for the Grammar Insights series. Shows the verse
// with one or more highlights and an optional small annotation pinned
// below the card explaining what the highlight is doing — e.g.
// "the past-tense form" or "the speaker is no longer 'He' but 'We'".
export const GrammarVerseSlide = z.object({
  type: z.literal('grammar-verse'),
  durationSec: z.number().positive().default(7),
  surah: z.number().int().positive(),
  ayah: z.number().int().positive(),
  arabicText: z.string(),
  translation: z.string(),
  highlights: z.array(GrammarHighlight).default([]),
  // Optional: phrase-level English emphases the script writer
  // explicitly chose for this slide. When present, the renderer
  // highlights every occurrence of each phrase in the translation
  // — overriding the per-highlight `translationSubstring` glosses,
  // which are richer than single-word gloss matches and let the
  // LLM frame the grammatical move with its surrounding context
  // (e.g. ["You alone we serve", "You alone we seek help from"]
  // for a person-mixture slide on 1:5).
  englishEmphases: z.array(z.string()).optional(),
  // Small annotation pinned below the verse card. Deprecated; the
  // renderer no longer draws this. Kept on the schema so legacy
  // payloads still parse.
  annotation: z.string().optional(),
  narration: Narration.optional(),
});

// Counterfactual contrast slide: "It could have said X. It said Y."
// Renders two stacked rows — the alternative on top in muted stone,
// the chosen form below in saturated teal. Each row has its Arabic
// form and a plain-English gloss right beside it.
export const GrammarContrastSlide = z.object({
  type: z.literal('grammar-contrast'),
  durationSec: z.number().positive().default(8),
  // Top (muted) row — the natural alternative the verse did NOT use.
  alternativeArabic: z.string(),
  alternativeGloss: z.string(),
  alternativeLabel: z.string().default('Could have said'),
  // Bottom (accented) row — what the verse actually says.
  saidArabic: z.string(),
  saidGloss: z.string(),
  saidLabel: z.string().default('It said'),
  // Optional one-line tagline below both rows that names the move
  // in plain English (e.g. "the past tense, treating the future as
  // already done"). Kept short — narration handles depth.
  tagline: z.string().optional(),
  narration: Narration.optional(),
});

export const Slide = z.discriminatedUnion('type', [
  RootSlide,
  VerseFlowSlide,
  WordToWordSlide,
  GrammarVerseSlide,
  GrammarContrastSlide,
  OutroSlide,
]);

export const Payload = z.object({
  slides: z.array(Slide).min(1),
  // Optional narration audio. File should be in public/ and
  // referenced relative (e.g. "narration.mp3"). When present, the
  // composition stretches to cover audio duration so the audio
  // never gets cut.
  audioFile: z.string().optional(),
  // Optional metadata for output naming / debugging only.
  videoId: z.string().optional(),
  title: z.string().optional(),
});

export type RootSlideT = z.infer<typeof RootSlide>;
export type VerseFlowSlideT = z.infer<typeof VerseFlowSlide>;
export type WordToWordSlideT = z.infer<typeof WordToWordSlide>;
export type OutroSlideT = z.infer<typeof OutroSlide>;
export type GrammarVerseSlideT = z.infer<typeof GrammarVerseSlide>;
export type GrammarContrastSlideT = z.infer<typeof GrammarContrastSlide>;
export type GrammarHighlightT = z.infer<typeof GrammarHighlight>;
export type SlideT = z.infer<typeof Slide>;
export type PayloadT = z.infer<typeof Payload>;
export type NarrationT = z.infer<typeof Narration>;
