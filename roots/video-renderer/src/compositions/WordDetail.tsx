import { AbsoluteFill, Sequence, Audio, staticFile } from 'remotion';
import type { PayloadT, SlideT } from '../types';
import { FPS } from '../slides/shared';
import { RootPage } from '../slides/RootPage';
import { VerseFlowPage } from '../slides/VerseFlowPage';
import { WordToWordPage } from '../slides/WordToWordPage';
import { OutroPage } from '../slides/OutroPage';
import { GrammarVersePage } from '../slides/GrammarVersePage';
import { GrammarContrastPage } from '../slides/GrammarContrastPage';
import { TranslationRevealPage } from '../slides/TranslationRevealPage';
import { WordLensPage } from '../slides/WordLensPage';
import { KaraokeOverlay } from '../slides/KaraokeOverlay';

// Top-level composition for word-detail videos.
//
// Layout per slide:
//   - The slide itself (RootPage / VerseFlowPage / etc.) fills the frame.
//   - If the slide has narration: an <Audio> tag plays the per-slide
//     narration mp3, AND a KaraokeOverlay anchored to the bottom
//     280px shows the caption with the active word highlighted.
//
// The composition's total duration is the sum of slide durations
// (computed by totalFrames). Each slide's duration was bumped by
// scripts/narration.mjs to be at least audio_length + 0.4s, so the
// audio never gets cut.
//
// Audio for separate slides is layered at non-overlapping <Sequence>
// offsets so they don't cross-talk. Optional payload-level
// `audioFile` (e.g. background music) plays globally.

export function WordDetailComposition({ payload }: { payload: PayloadT }) {
  let cursor = 0;
  const sequences = payload.slides.map((slide, i) => {
    const durationFrames = Math.max(1, Math.round(slide.durationSec * FPS));
    const seq = (
      <Sequence key={i} from={cursor} durationInFrames={durationFrames}>
        <SlideWithNarration slide={slide} />
      </Sequence>
    );
    cursor += durationFrames;
    return seq;
  });

  return (
    <AbsoluteFill>
      {sequences}
      {payload.audioFile && (
        <Audio src={staticFile(payload.audioFile)} />
      )}
    </AbsoluteFill>
  );
}

// Renders the slide visual + (when present) the audio track + the
// karaoke overlay. Karaoke uses audioStartFrame=0 because we're
// inside the slide's <Sequence>, which already resets useCurrentFrame.
function SlideWithNarration({ slide }: { slide: SlideT }) {
  const hasNarration = 'narration' in slide && !!slide.narration;
  return (
    <>
      <SlideRenderer slide={slide} />
      {hasNarration && slide.narration?.audioFile && (
        <Audio src={staticFile(slide.narration.audioFile)} />
      )}
      {hasNarration && slide.narration?.alignment && (
        <KaraokeOverlay
          narration={slide.narration}
          audioStartFrame={0}
        />
      )}
    </>
  );
}

function SlideRenderer({ slide }: { slide: SlideT }) {
  switch (slide.type) {
    case 'root':
      return <RootPage slide={slide} />;
    case 'verse-flow':
      return <VerseFlowPage slide={slide} />;
    case 'word-to-word':
      return <WordToWordPage slide={slide} />;
    case 'grammar-verse':
      return <GrammarVersePage slide={slide} />;
    case 'grammar-contrast':
      return <GrammarContrastPage slide={slide} />;
    case 'translation-reveal':
      return <TranslationRevealPage slide={slide} />;
    case 'word-lens':
      return <WordLensPage slide={slide} />;
    case 'outro':
      return <OutroPage slide={slide} />;
    default: {
      const _exhaustive: never = slide;
      return _exhaustive;
    }
  }
}

export function totalFrames(payload: PayloadT): number {
  return payload.slides.reduce(
    (acc, s) => acc + Math.max(1, Math.round(s.durationSec * FPS)),
    0,
  );
}
