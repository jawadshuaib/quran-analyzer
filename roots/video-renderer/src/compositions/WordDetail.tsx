import { AbsoluteFill, Sequence, Audio, staticFile } from 'remotion';
import type { PayloadT, SlideT } from '../types';
import { FPS } from '../slides/shared';
import { RootPage } from '../slides/RootPage';
import { VerseFlowPage } from '../slides/VerseFlowPage';
import { WordToWordPage } from '../slides/WordToWordPage';
import { OutroPage } from '../slides/OutroPage';

// Top-level composition for word-detail videos. The Composition's
// duration is computed from the sum of slide durations (or set to
// the audio length, whichever is longer — see Root.tsx). Each slide
// is wrapped in a <Sequence> so its useCurrentFrame() resets at the
// slide's start, which is what makes the entry animations feel
// natural per slide.

export function WordDetailComposition({ payload }: { payload: PayloadT }) {
  let cursor = 0;
  const sequences = payload.slides.map((slide, i) => {
    const durationFrames = Math.max(1, Math.round(slide.durationSec * FPS));
    const seq = (
      <Sequence key={i} from={cursor} durationInFrames={durationFrames}>
        <SlideRenderer slide={slide} />
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

// Discriminator on slide.type — adding a new slide kind means adding
// a case here plus a component under src/slides/. Keeping the
// switch explicit (rather than a lookup table) so TypeScript can
// narrow each branch via the discriminated union in types.ts.
function SlideRenderer({ slide }: { slide: SlideT }) {
  switch (slide.type) {
    case 'root':
      return <RootPage slide={slide} />;
    case 'verse-flow':
      return <VerseFlowPage slide={slide} />;
    case 'word-to-word':
      return <WordToWordPage slide={slide} />;
    case 'outro':
      return <OutroPage slide={slide} />;
    default: {
      // Exhaustiveness guard — TS errors if a new variant is added
      // to the union but not handled above.
      const _exhaustive: never = slide;
      return _exhaustive;
    }
  }
}

// Sum slide durations to compute the composition length in frames.
// render.mjs and Root.tsx both need this so they declare the same
// duration to Remotion.
export function totalFrames(payload: PayloadT): number {
  return payload.slides.reduce(
    (acc, s) => acc + Math.max(1, Math.round(s.durationSec * FPS)),
    0,
  );
}
