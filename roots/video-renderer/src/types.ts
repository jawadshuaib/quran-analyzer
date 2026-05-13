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
  // 1-indexed positions of multiple Arabic words to highlight as a
  // contiguous (or near-contiguous) phrase. Translation Hides uses
  // this when the hidden nuance is phrase-level: the corresponding
  // English span ("what struck them will be striking her") maps to
  // 2-4 Arabic words, and highlighting only one would leave the
  // viewer wondering which Arabic part they're meant to be looking
  // at. When both `highlightWordIndex` and `highlightWordIndices`
  // are present, indices is the source of truth; the singular field
  // stays for backward compatibility with payloads that predate the
  // multi-word highlight.
  highlightWordIndices: z.array(z.number().int().positive()).optional(),
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
  // — overriding the per-highlight `translationSubstring` glosses.
  //
  // Each emphasis is either a bare string (uses the first Arabic
  // highlight's marker color) or an object with its own marker so
  // parallel clauses can render in different colors. The backend
  // groups Arabic highlights into chunks (e.g. parallel-clause
  // pairs split on a وَ) and assigns one marker per chunk, then
  // pairs each english emphasis with its chunk's color so the
  // viewer immediately sees the parallel structure as distinct
  // pieces — e.g. for 1:5: ["You alone we serve" (blue),
  // "You alone we seek help from" (amber)].
  englishEmphases: z.array(
    z.union([
      z.string(),
      z.object({
        phrase: z.string(),
        marker: z.enum(['tense', 'pronoun', 'fronted', 'agent', 'default']).optional(),
      }),
    ]),
  ).optional(),
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

// ---------------------------------------------------------------------------
// What Translation Hides series slides
//
// The series reveals nuance that the conventional English translation
// flattens. Two bespoke slides + reuse of verse-flow + outro give the
// series its visual identity (rose accent) and keep engineering small.
// ---------------------------------------------------------------------------

// Opening hook. Two stacked rows: top "Most translations say X" in
// muted stone, bottom "The Arabic actually says Y" in saturated rose.
// Mirrors GrammarContrastSlide's geometry but English-first because
// the audience reads English; the contrast IS the hook.
//
// Either `arabic` is set (preferred — shows the Arabic form next to
// the AI gloss for legitimacy) or it's omitted (when the nuance is
// verse-level rather than tied to a specific word). The "Translation
// vs Quran" framing is universal regardless.
export const TranslationRevealSlide = z.object({
  type: z.literal('translation-reveal'),
  // Bumped to 10s from 7s so the new four-beat choreography
  // (hook → artifact → conventional → reveal) has room to breathe.
  // Earlier 7s collapsed all four beats into ~2.5s — viewers got
  // the contrast before any context, which read as "He's aware of
  // their tails" with no idea what verse or word was being talked
  // about. YouTube-marketer principle: hook + context first,
  // payoff earned.
  durationSec: z.number().positive().default(10),
  // Optional verse reference shown during the context beat
  // ("Quran 25:58" or "Sura al-Furqan • 25:58"). Renderer builds
  // a default from chapter:verse when this is omitted but the
  // chapter+verse fields below are set.
  verseRef: z.string().optional(),
  chapter: z.number().int().positive().optional(),
  verse: z.number().int().positive().optional(),
  // Optional hook line — the catch-the-thumb-scroll line that
  // opens the slide. "There's a word in this verse that doesn't
  // mean what you think." If omitted, the renderer uses a sensible
  // default phrased around the verse reference so the viewer always
  // gets a context-setting beat before the contrast lands.
  hookLine: z.string().optional(),
  // Optional transliteration of `arabic` — shown small under the
  // big Arabic word during the artifact beat. Useful when the
  // hook word is a content word the AI judge picked out.
  transliteration: z.string().optional(),
  // Top row — what most viewers think the verse says.
  conventionalLabel: z.string().default('Most translations say'),
  conventionalText: z.string(),
  // Bottom row — what the Arabic actually conveys. When `arabic` is
  // present, it renders alongside the gloss (smaller, RTL).
  hiddenLabel: z.string().default('The Arabic actually says'),
  hiddenText: z.string(),
  arabic: z.string().optional(),
  // Optional one-line tagline below both rows (e.g. "and that changes
  // everything"). Kept short — narration carries depth.
  tagline: z.string().optional(),
  narration: Narration.optional(),
});

// Word Lens slide — the payoff frame. Large Arabic word centered,
// conventional gloss above (muted, with strikethrough), AI gloss
// below (saturated rose), optional one-line evidence chip naming the
// lens kind ("morphology: passive, agent omitted", "lexical: root
// means X across Semitic", "context: same word used differently in
// Y:Z"). When no single word is the focus, the renderer can elide
// the strikethrough and instead use this slide for a phrase-lens.
export const WordLensSlide = z.object({
  type: z.literal('word-lens'),
  durationSec: z.number().positive().default(10),
  // Large Arabic surface form in the center. Required.
  arabic: z.string(),
  // 1-based word position on the source verse (for the operator's
  // reference; the renderer doesn't strictly need it but keeping it
  // on the schema makes the payload self-documenting).
  wordPos: z.number().int().positive().optional(),
  // Optional transliteration shown beneath the Arabic (small, italic).
  transliteration: z.string().optional(),
  // Conventional gloss row (top, muted, strikethrough by default).
  conventionalGloss: z.string(),
  // AI / "hidden" gloss row (bottom, saturated rose).
  hiddenGloss: z.string(),
  // Optional evidence chip — one short phrase naming WHY the AI gloss
  // is preferred. E.g. "morphology: passive voice", "lexical: root
  // sense across Semitic", "context: contrasts 2:155 usage".
  evidenceChip: z.string().optional(),
  // Strike the conventional gloss visually. Default true; false when
  // both renderings are valid and the AI version is a refinement,
  // not a correction.
  strikeConventional: z.boolean().default(true),
  narration: Narration.optional(),
});

export const Slide = z.discriminatedUnion('type', [
  RootSlide,
  VerseFlowSlide,
  WordToWordSlide,
  GrammarVerseSlide,
  GrammarContrastSlide,
  TranslationRevealSlide,
  WordLensSlide,
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
export type TranslationRevealSlideT = z.infer<typeof TranslationRevealSlide>;
export type WordLensSlideT = z.infer<typeof WordLensSlide>;
export type SlideT = z.infer<typeof Slide>;
export type PayloadT = z.infer<typeof Payload>;
export type NarrationT = z.infer<typeof Narration>;
