import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import type { RootSlideT } from '../types';
import { COLORS, ARABIC_FONT, SYSTEM_FONT, ENTRY_FRAMES } from './shared';

// Slide A — root word reveal.
// Layout (1080x1920 vertical):
//   - Top third: large RTL Arabic root letters with generous spacing
//   - Middle: "Root: <buckwalter>" Latin label
//   - Lower-middle: "Meaning" eyebrow + meaning sentence
//   - Cream-warm background (#F4F2EA) matches mockup A.html exactly.
//
// Animation: root letters fade up + scale in via spring; the meaning
// block fades in 8 frames behind the letters so the eye lands on
// Arabic first, then drifts down to the gloss.
export function RootPage({ slide }: { slide: RootSlideT }) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Root letters: spring-based reveal so they feel weighty rather
  // than mechanical. damping=200 gives a gentle settle without
  // bouncing.
  const rootSpring = spring({
    frame,
    fps,
    config: { damping: 200, stiffness: 90 },
  });
  const rootOpacity = interpolate(frame, [0, ENTRY_FRAMES], [0, 1], { extrapolateRight: 'clamp' });
  const rootScale = interpolate(rootSpring, [0, 1], [0.92, 1]);

  // Meaning block follows ~8 frames behind so it doesn't compete
  // for attention on entry.
  const meaningOpacity = interpolate(frame, [10, 10 + ENTRY_FRAMES], [0, 1], { extrapolateRight: 'clamp' });
  const meaningTranslateY = interpolate(frame, [10, 10 + ENTRY_FRAMES], [12, 0], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.pageBg }}>
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '120px 80px',
          textAlign: 'center',
        }}
      >
        {/* Root Arabic — biggest visual weight on the slide.
            marginBottom is generous (was 16, now 56) because tall
            Arabic letters like ع / ل / ك have visual descenders
            that touched the "Root: ..." label below at the smaller
            gap. Doesn't push the meaning block down materially —
            the parent flexbox is justify-center'd so spacing
            redistributes evenly. */}
        <div
          style={{
            fontFamily: ARABIC_FONT,
            fontSize: 240,
            fontWeight: 400,
            lineHeight: 1,
            direction: 'rtl',
            letterSpacing: '0.18em',
            color: COLORS.text,
            marginBottom: 56,
            opacity: rootOpacity,
            transform: `scale(${rootScale})`,
          }}
        >
          {slide.rootArabic}
        </div>

        <div
          style={{
            fontFamily: SYSTEM_FONT,
            fontSize: 96,
            fontWeight: 400,
            color: COLORS.text,
            letterSpacing: '-0.005em',
            marginBottom: 240,
            opacity: rootOpacity,
          }}
        >
          {slide.rootLabel}
        </div>

        {/* Meaning block — eyebrow + body text */}
        <div
          style={{
            opacity: meaningOpacity,
            transform: `translateY(${meaningTranslateY}px)`,
          }}
        >
          <div
            style={{
              fontFamily: SYSTEM_FONT,
              fontSize: 56,
              fontWeight: 700,
              color: COLORS.text,
              letterSpacing: '-0.01em',
              marginBottom: 20,
            }}
          >
            {slide.meaningTitle || 'Meaning'}
          </div>
          <div
            style={{
              fontFamily: SYSTEM_FONT,
              fontSize: 56,
              fontWeight: 400,
              color: COLORS.text,
              letterSpacing: '-0.005em',
              maxWidth: 920,
              lineHeight: 1.3,
            }}
          >
            {slide.meaning}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
}
