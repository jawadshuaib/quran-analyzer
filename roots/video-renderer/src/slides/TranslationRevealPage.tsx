import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from 'remotion';
import type { TranslationRevealSlideT } from '../types';
import { COLORS, ARABIC_FONT, SYSTEM_FONT, ENTRY_FRAMES } from './shared';
import { wrapArabicRuns } from './arabic-runs';

// What Translation Hides — opening reveal slide.
//
// Two stacked rows that frame the entire video premise:
//   - Top, muted stone:    "Most translations say"        — conventional rendering
//   - Bottom, saturated rose:    "The Arabic actually says"     — what the verse really conveys
//
// Visual identity: rose-700 accent + rose-100 pill background. The
// muted "conventional" row reads as washed-out / cliché; the
// saturated "actual" row pops and feels like the reveal.
//
// Sizing: every font / pill / gap is sized for the 1080×1920 vertical
// mobile composition. Earlier sizes were tuned for a 16:9 desktop
// render and disappeared on phone screens — operator pointed out that
// the slide looked nearly blank with a small label at the top. This
// version centers vertically and roughly doubles every font so the
// reveal fills the screen and reads at a glance on mobile.
//
// Animation timing (~7s slide):
//   - Conventional row fades in first (0-18f), establishing the baseline.
//   - The "but" connector lands at ~22-36f.
//   - Hidden row enters at 30f with a subtle scale-up (96% → 100%) so
//     the eye is pulled to the reveal even before the narration explains it.
//   - Optional tagline fades in last (~60f) so it doesn't compete with
//     the contrast itself.
//
// Parallels GrammarContrastPage's structure but English-first because
// the audience reads English; the contrast IS the hook.
export function TranslationRevealPage({ slide }: { slide: TranslationRevealSlideT }) {
  const frame = useCurrentFrame();

  const convOpacity = interpolate(frame, [0, ENTRY_FRAMES], [0, 1], { extrapolateRight: 'clamp' });
  const convTranslateY = interpolate(frame, [0, ENTRY_FRAMES], [-12, 0], { extrapolateRight: 'clamp' });

  const connectorOpacity = interpolate(frame, [22, 36], [0, 1], { extrapolateRight: 'clamp' });

  const hiddenOpacity = interpolate(frame, [30, 50], [0, 1], { extrapolateRight: 'clamp' });
  const hiddenTranslateY = interpolate(frame, [30, 50], [12, 0], { extrapolateRight: 'clamp' });
  const hiddenScale = interpolate(
    frame, [30, 50], [0.96, 1],
    { extrapolateRight: 'clamp', easing: Easing.out(Easing.ease) },
  );

  const taglineOpacity = interpolate(frame, [60, 78], [0, 1], { extrapolateRight: 'clamp' });

  // Auto-scale gloss font by length. Long conventional translations
  // shrink so they don't dominate the screen; punchy "Y" reveals
  // stay bigger to feel like the payoff.
  //
  // Sizes are for 1080×1920 mobile. The smallest tier (>=110 chars)
  // still lands at 56px — large enough to read at a glance on a phone.
  const fontFor = (text: string, big: number, mid: number, small: number) => {
    const n = (text || '').length;
    if (n <= 60) return big;
    if (n <= 110) return mid;
    return small;
  };
  const convFontSize = fontFor(slide.conventionalText, 72, 60, 52);
  const hiddenFontSize = fontFor(slide.hiddenText, 80, 66, 56);

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.appBg, fontFamily: SYSTEM_FONT }}>
      {/* Series mark — pinned near the top so it doesn't shift as the
          centered content scales. Was previously stacked with the rows
          which made the layout drift toward the top of the screen on
          mobile and left the bottom half empty. */}
      <div
        style={{
          position: 'absolute',
          top: 80,
          left: 0,
          right: 0,
          color: COLORS.translationAccent,
          fontSize: 44,
          fontWeight: 700,
          letterSpacing: 3,
          textTransform: 'uppercase',
          textAlign: 'center',
        }}
      >
        What Translation Hides
      </div>

      {/* Centered reveal stack — vertically centered so the contrast
          sits in the optical middle of the phone screen. Previously
          was flex-start which left the bottom half blank. */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          padding: '200px 60px 120px 60px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 44,
        }}
      >
        {/* Conventional row — muted */}
        <RevealRow
          label={slide.conventionalLabel}
          text={slide.conventionalText}
          bgColor={COLORS.translationConvBg}
          labelColor={COLORS.translationConvText}
          textColor={COLORS.textSoft}
          textSize={convFontSize}
          opacity={convOpacity}
          translateY={convTranslateY}
          scale={1}
        />

        {/* Connector — italic "but", a beat between the two rows */}
        <div
          style={{
            opacity: connectorOpacity,
            color: COLORS.translationConvText,
            fontSize: 52,
            fontStyle: 'italic',
            margin: '12px 0',
          }}
        >
          but
        </div>

        {/* Hidden row — saturated rose, slightly larger to win the comparison */}
        <RevealRow
          label={slide.hiddenLabel}
          text={slide.hiddenText}
          arabic={slide.arabic}
          bgColor={COLORS.translationAccentSoft}
          labelColor={COLORS.translationAccent}
          textColor={COLORS.text}
          textSize={hiddenFontSize}
          opacity={hiddenOpacity}
          translateY={hiddenTranslateY}
          scale={hiddenScale}
        />

        {/* Optional tagline — what does this reveal DO? */}
        {slide.tagline && (
          <div
            style={{
              marginTop: 36,
              opacity: taglineOpacity,
              fontSize: 40,
              color: COLORS.translationAccentDeep,
              fontStyle: 'italic',
              textAlign: 'center',
              maxWidth: 940,
              fontWeight: 500,
              lineHeight: 1.35,
            }}
          >
            {wrapArabicRuns(slide.tagline)}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
}

// One side of the reveal — label pill on top, gloss text below,
// optional Arabic form to the right of the gloss for legitimacy.
// Encapsulates the geometry so both rows render with consistent
// spacing and the entrance animation only has to drive a wrapper div.
function RevealRow({
  label, text, arabic,
  bgColor, labelColor, textColor,
  textSize,
  opacity, translateY, scale,
}: {
  label: string;
  text: string;
  arabic?: string;
  bgColor: string;
  labelColor: string;
  textColor: string;
  textSize: number;
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
        gap: 28, width: '100%', maxWidth: 980,
      }}
    >
      <div
        style={{
          background: bgColor,
          padding: '14px 36px',
          borderRadius: 999,
          color: labelColor,
          fontSize: 32,
          fontWeight: 700,
          letterSpacing: 1.2,
          textTransform: 'uppercase',
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: textSize,
          lineHeight: 1.3,
          color: textColor,
          textAlign: 'center',
          maxWidth: 960,
          fontWeight: 500,
          // "Hidden" rows often quote a short phrase — italic gives the
          // reveal a quotation-y feel that signals "this is the real
          // reading," vs the conventional row's plain stone.
          fontStyle: 'normal',
        }}
      >
        {wrapArabicRuns(text)}
      </div>
      {arabic && (
        <div
          dir="rtl"
          lang="ar"
          style={{
            fontFamily: ARABIC_FONT,
            fontSize: 88,
            lineHeight: 1.4,
            color: textColor,
            textAlign: 'center',
            marginTop: 10,
          }}
        >
          {arabic}
        </div>
      )}
    </div>
  );
}
