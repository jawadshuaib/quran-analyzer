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
export const OutroSlide = z.object({
  type: z.literal('outro'),
  durationSec: z.number().positive().default(5),
  siteName: z.string().default('al-nuqta.com'),
  tagline: z.string().default('A Root Based Translation of the Quran'),
});

export const Slide = z.discriminatedUnion('type', [
  RootSlide,
  VerseFlowSlide,
  WordToWordSlide,
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
export type SlideT = z.infer<typeof Slide>;
export type PayloadT = z.infer<typeof Payload>;
export type NarrationT = z.infer<typeof Narration>;
