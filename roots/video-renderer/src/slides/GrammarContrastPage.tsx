import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from 'remotion';
import type { GrammarContrastSlideT } from '../types';
import { COLORS, ARABIC_FONT, SYSTEM_FONT, ENTRY_FRAMES } from './shared';
import { wrapArabicRuns } from './arabic-runs';

// Grammar Insights — counterfactual contrast slide.
//
// "It could have said X. It said Y."
//
// Layout (vertical 1080×1920):
//   - "Could have said" row at the top, faded/muted: stone-100
//     pill background, stone-500 label. Arabic on top, English
//     gloss right beneath.
//   - A small connector arrow / "but" between the two rows so the
//     viewer's eye knows these are alternatives, not a sequence.
//   - "It said" row at the bottom, saturated: teal-100 pill,
//     teal-700 label. Same Arabic-then-gloss structure but slightly
//     larger so it visually wins the comparison.
//   - Optional tagline pinned at the bottom that names the move
//     in plain English (e.g. "the past tense, treating the future
//     as already done").
//
// Animation:
//   - Alternative row fades in first (0–18f), establishes the baseline.
//   - "but" / connector lands at ~24f.
//   - Said row enters at 30f with a subtle scale-up to draw the eye.
//   - Tagline fades in last (~60f) so it doesn't compete with the
//     contrast itself.
export function GrammarContrastPage({ slide }: { slide: GrammarContrastSlideT }) {
  const frame = useCurrentFrame();

  const altOpacity = interpolate(frame, [0, ENTRY_FRAMES], [0, 1], { extrapolateRight: 'clamp' });
  const altTranslateY = interpolate(frame, [0, ENTRY_FRAMES], [-12, 0], { extrapolateRight: 'clamp' });

  const connectorOpacity = interpolate(frame, [22, 36], [0, 1], { extrapolateRight: 'clamp' });

  const saidOpacity = interpolate(frame, [30, 50], [0, 1], { extrapolateRight: 'clamp' });
  const saidTranslateY = interpolate(frame, [30, 50], [12, 0], { extrapolateRight: 'clamp' });
  const saidScale = interpolate(
    frame, [30, 50], [0.96, 1],
    { extrapolateRight: 'clamp', easing: Easing.out(Easing.ease) },
  );

  const taglineOpacity = interpolate(frame, [60, 78], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.appBg, fontFamily: SYSTEM_FONT }}>
      <div
        style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
          padding: '160px 60px 100px 60px',
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          gap: 24,
        }}
      >
        {/* Series mark — keeps continuity with the verse slides */}
        <div
          style={{
            color: COLORS.grammarAccent, fontSize: 22, fontWeight: 600,
            letterSpacing: 1.5, textTransform: 'uppercase',
            marginBottom: 12,
          }}
        >
          A Deliberate Choice
        </div>

        {/* "Could have said" — muted */}
        <ContrastRow
          label={slide.alternativeLabel}
          arabic={slide.alternativeArabic}
          gloss={slide.alternativeGloss}
          bgColor={COLORS.contrastAltBg}
          labelColor={COLORS.contrastAlt}
          glossColor={COLORS.textSoft}
          arabicSize={56}
          glossSize={26}
          opacity={altOpacity}
          translateY={altTranslateY}
          scale={1}
        />

        {/* Connector — small "but" pill in stone */}
        <div
          style={{
            opacity: connectorOpacity,
            color: COLORS.contrastAlt,
            fontSize: 28, fontStyle: 'italic',
            margin: '8px 0',
          }}
        >
          but
        </div>

        {/* "It said" — saturated, slightly larger */}
        <ContrastRow
          label={slide.saidLabel}
          arabic={slide.saidArabic}
          gloss={slide.saidGloss}
          bgColor={COLORS.contrastSaidBg}
          labelColor={COLORS.contrastSaid}
          glossColor={COLORS.text}
          arabicSize={64}
          glossSize={30}
          opacity={saidOpacity}
          translateY={saidTranslateY}
          scale={saidScale}
        />

        {/* Optional tagline — what does this choice DO? */}
        {slide.tagline && (
          <div
            style={{
              marginTop: 36, opacity: taglineOpacity,
              fontSize: 24, color: COLORS.grammarAccentDeep,
              fontStyle: 'italic', textAlign: 'center', maxWidth: 800,
              fontWeight: 500,
            }}
          >
            {wrapArabicRuns(slide.tagline)}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
}

// One side of the comparison. Encapsulates the label-pill / Arabic /
// gloss vertical stack so both rows render with consistent geometry.
function ContrastRow({
  label, arabic, gloss,
  bgColor, labelColor, glossColor,
  arabicSize, glossSize,
  opacity, translateY, scale,
}: {
  label: string;
  arabic: string;
  gloss: string;
  bgColor: string;
  labelColor: string;
  glossColor: string;
  arabicSize: number;
  glossSize: number;
  opacity: number;
  translateY: number;
  scale: number;
}) {
  return (
    <div
      style={{
        opacity,
        transform: `translateY(${translateY}px) scale(${scale})`,
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        gap: 12, width: '100%', maxWidth: 880,
      }}
    >
      <div
        style={{
          background: bgColor,
          padding: '6px 18px', borderRadius: 999,
          color: labelColor, fontSize: 18, fontWeight: 600,
          letterSpacing: 0.4, textTransform: 'uppercase',
        }}
      >
        {wrapArabicRuns(label)}
      </div>
      <div
        dir="rtl"
        style={{
          fontFamily: ARABIC_FONT, fontSize: arabicSize, lineHeight: 1.4,
          color: COLORS.text, textAlign: 'center',
        }}
      >
        {arabic}
      </div>
      <div
        style={{
          fontStyle: 'italic', fontSize: glossSize, lineHeight: 1.3,
          color: glossColor, textAlign: 'center',
          maxWidth: 760,
        }}
      >
        {wrapArabicRuns(gloss)}
      </div>
    </div>
  );
}
