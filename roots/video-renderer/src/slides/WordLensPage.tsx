import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig, Easing } from 'remotion';
import type { WordLensSlideT } from '../types';
import { COLORS, ARABIC_FONT, SYSTEM_FONT, ENTRY_FRAMES } from './shared';
import { wrapArabicRuns } from './arabic-runs';

// What Translation Hides — Word Lens slide. The payoff frame.
//
// One Arabic word centered, BIG. Above: the conventional English
// gloss with a strikethrough (when strikeConventional=true) — the
// rendering the viewer probably already knows. Below: the AI gloss in
// saturated rose — what the word actually means in this verse.
// Optional evidence chip names WHY the AI gloss is preferred
// (morphology, lexical sense, context, cognate).
//
// Layout (vertical 1080×1920):
//   - Top quarter: conventional gloss row (muted, with strikethrough)
//   - Middle (visual anchor): big Arabic form + optional transliteration
//   - Below the Arabic: AI gloss in rose with optional evidence chip
//
// Animation:
//   - Arabic word springs in (0-18f, scale 0.92→1) so it lands with
//     weight, like a Mushaf page being turned.
//   - Conventional row fades in at 8f (slightly behind the Arabic, so
//     the eye lands on Arabic first).
//   - Strikethrough draws across at 30-50f if enabled — visually
//     "crossing out" the conventional reading.
//   - AI gloss row enters at 38f with a translateY-from-below, like
//     a curtain pulling back to reveal what was hidden.
//   - Evidence chip lands last (~70f) so it doesn't compete with
//     the reveal.
//
// Mirrors RootPage's visual weight on Arabic while adding the
// contrast geometry that gives Translation Hides its identity.
export function WordLensPage({ slide }: { slide: WordLensSlideT }) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Arabic spring — weighty settle, no bounce.
  const arabicSpring = spring({
    frame, fps,
    config: { damping: 200, stiffness: 90 },
  });
  const arabicOpacity = interpolate(frame, [0, ENTRY_FRAMES], [0, 1], { extrapolateRight: 'clamp' });
  const arabicScale = interpolate(arabicSpring, [0, 1], [0.92, 1]);

  const transliterationOpacity = interpolate(
    frame, [10, 10 + ENTRY_FRAMES], [0, 1],
    { extrapolateRight: 'clamp' },
  );

  // Conventional row — lands shortly behind the Arabic.
  const convOpacity = interpolate(
    frame, [8, 8 + ENTRY_FRAMES], [0, 1],
    { extrapolateRight: 'clamp' },
  );

  // Strikethrough sweep — draws across the conventional gloss to
  // visually retire the old reading. Only renders when enabled.
  const strikeProgress = interpolate(
    frame, [30, 50], [0, 1],
    { extrapolateRight: 'clamp', easing: Easing.out(Easing.ease) },
  );

  // AI gloss — curtain-pull from below.
  const aiOpacity = interpolate(frame, [38, 58], [0, 1], { extrapolateRight: 'clamp' });
  const aiTranslateY = interpolate(frame, [38, 58], [20, 0], { extrapolateRight: 'clamp' });

  const chipOpacity = interpolate(frame, [70, 88], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.appBg, fontFamily: SYSTEM_FONT }}>
      <div
        style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
          // Symmetric vertical padding now that the "THE WORD" series
          // mark is gone — gives the Arabic visual anchor more room
          // to breathe at the optical center.
          padding: '100px 80px 80px 80px',
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center',
          // Larger inter-block gap so the conventional gloss row,
          // the giant Arabic word, and the AI-gloss row don't crash
          // into each other on mobile (where the slide is viewed
          // upright at ~6" — the previous 32px collapsed visually).
          gap: 64,
        }}
      >

        {/* Conventional gloss — muted, with optional strikethrough */}
        <div
          style={{
            opacity: convOpacity,
            display: 'flex', flexDirection: 'column', alignItems: 'center',
            gap: 16,
          }}
        >
          <div
            style={{
              // Bumped from 22 → 32 — mobile-readable label
              // ("TRANSLATED AS"). At 22px these all-caps labels were
              // dense on a small screen.
              fontSize: 32, color: COLORS.translationConvText,
              letterSpacing: 1.2, textTransform: 'uppercase', fontWeight: 700,
            }}
          >
            Translated as
          </div>
          <div
            style={{
              position: 'relative', display: 'inline-block',
              // Bumped from 44 → 64 — the conventional gloss is the
              // viewer's anchor for "what I think this means". On a
              // phone the previous size disappeared next to the 200px
              // Arabic; the contrast row needs visual weight.
              fontSize: 64, color: COLORS.textSoft, lineHeight: 1.25,
              fontStyle: 'italic', textAlign: 'center',
              maxWidth: 880,
              padding: '0 12px',
            }}
          >
            {wrapArabicRuns(slide.conventionalGloss)}
            {slide.strikeConventional && (
              <span
                style={{
                  position: 'absolute',
                  left: 12,
                  right: 12,
                  // Sit on the x-height roughly, not the baseline; looks
                  // like a deliberate strike rather than an underscore.
                  top: '52%',
                  height: 4,
                  background: COLORS.translationAccent,
                  transformOrigin: 'left center',
                  transform: `scaleX(${strikeProgress})`,
                  borderRadius: 2,
                }}
              />
            )}
          </div>
        </div>

        {/* Arabic word — visual anchor.
            lineHeight bumped from 1 → 1.4 so the Arabic diacritics
            (which sit ABOVE the baseline) don't intrude into the
            conventional-gloss row above. With lineHeight 1 + a 200px
            font, the kasra/fatha marks on فَرْجَهَا were rendering
            right under "her chastity" — operator feedback. The extra
            margin gives a clean band of empty space on both sides. */}
        <div
          dir="rtl"
          lang="ar"
          style={{
            fontFamily: ARABIC_FONT,
            fontSize: 200,
            fontWeight: 400,
            lineHeight: 1.4,
            color: COLORS.text,
            letterSpacing: '0.04em',
            opacity: arabicOpacity,
            transform: `scale(${arabicScale})`,
            margin: '40px 0',
          }}
        >
          {slide.arabic}
        </div>

        {/* Transliteration — small, italic, beneath the Arabic */}
        {slide.transliteration && (
          <div
            style={{
              fontSize: 32, color: COLORS.textSoft,
              fontStyle: 'italic',
              opacity: transliterationOpacity,
              marginTop: -16,
              letterSpacing: 0.4,
            }}
          >
            {slide.transliteration}
          </div>
        )}

        {/* AI gloss — saturated rose, curtain-pulls from below */}
        <div
          style={{
            opacity: aiOpacity,
            transform: `translateY(${aiTranslateY}px)`,
            display: 'flex', flexDirection: 'column', alignItems: 'center',
            gap: 16,
          }}
        >
          <div
            style={{
              // Mirrors the bumped "TRANSLATED AS" label above.
              fontSize: 32, color: COLORS.translationAccent,
              letterSpacing: 1.2, textTransform: 'uppercase', fontWeight: 700,
            }}
          >
            Actually means
          </div>
          <div
            style={{
              // Bumped from 54 → 76 — this is the payoff line; it
              // should be the LARGEST English on the slide so the
              // viewer's eye lands here last and longest. Previous
              // size let the conventional gloss (post-bump) compete
              // for weight, which dulled the reveal.
              fontSize: 76, color: COLORS.translationAccentDeep,
              fontWeight: 700, lineHeight: 1.2,
              textAlign: 'center', maxWidth: 880,
              letterSpacing: '-0.01em',
            }}
          >
            {wrapArabicRuns(slide.hiddenGloss)}
          </div>
        </div>

        {/* Evidence chip — one-line provenance for the AI gloss */}
        {slide.evidenceChip && (
          <div
            style={{
              opacity: chipOpacity,
              display: 'inline-block',
              padding: '12px 26px',
              borderRadius: 999,
              background: COLORS.translationAccentSoft,
              border: `1px solid ${COLORS.translationAccent}33`,
              color: COLORS.translationAccentDeep,
              fontSize: 28, fontWeight: 600,
              letterSpacing: 0.3,
              marginTop: 8,
            }}
          >
            {wrapArabicRuns(slide.evidenceChip)}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
}
