import { AbsoluteFill, useCurrentFrame, interpolate } from 'remotion';
import type { VerseFlowSlideT } from '../types';
import { COLORS, ARABIC_FONT, SYSTEM_FONT, ENTRY_FRAMES } from './shared';

// Slide B — full verse with the target word highlighted in soft yellow.
// Layout (1080x1920 vertical):
//   - Outer cream-warm bg (#E9E7DF)
//   - Cream verse-card centered, fills most of the frame
//   - Card header: "‹ Surah X, Ayah Y ›" + "Word-to-Word [toggle off]"
//   - Card body: flowing RTL Arabic with target word highlighted
//   - Card footer: italic English translation, separated by hairline
//
// Animation: card fades + slides up on entry; the highlight pulse
// scales in 6 frames behind the verse so the eye lands on the
// passage first, then settles on the target word.
export function VerseFlowPage({ slide }: { slide: VerseFlowSlideT }) {
  const frame = useCurrentFrame();

  const cardOpacity = interpolate(frame, [0, ENTRY_FRAMES], [0, 1], { extrapolateRight: 'clamp' });
  const cardTranslateY = interpolate(frame, [0, ENTRY_FRAMES], [16, 0], { extrapolateRight: 'clamp' });

  // Highlight enters slightly delayed so it reads as a deliberate
  // emphasis, not a static design element.
  const highlightOpacity = interpolate(
    frame,
    [6, 6 + ENTRY_FRAMES],
    [0, 1],
    { extrapolateRight: 'clamp' },
  );

  // Build the verse with the highlight applied in-place. Splits on
  // whitespace, wraps the 1-indexed target word in a styled span.
  const words = slide.arabicText.split(/\s+/);
  const targetIdx = (slide.highlightWordIndex ?? 0) - 1;

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.appBg }}>
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '90px 50px',
        }}
      >
        <div
          style={{
            backgroundColor: COLORS.cardBg,
            borderRadius: 36,
            padding: '60px 64px 70px',
            width: '100%',
            maxWidth: 980,
            boxShadow: '0 2px 0 rgba(0,0,0,0.02), 0 16px 48px -32px rgba(60,55,40,0.18)',
            opacity: cardOpacity,
            transform: `translateY(${cardTranslateY}px)`,
          }}
        >
          {/* Card header — surah/ayah nav + word-to-word toggle (off) */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 24,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 24,
                fontFamily: SYSTEM_FONT,
                fontSize: 32,
                fontWeight: 600,
                color: COLORS.text,
                letterSpacing: '-0.01em',
              }}
            >
              <span style={{ color: COLORS.chev, fontSize: 36, lineHeight: 1 }}>‹</span>
              <span>Surah {slide.surah}, Ayah {slide.ayah}</span>
              <span style={{ color: COLORS.chev, fontSize: 36, lineHeight: 1 }}>›</span>
            </div>
            <ToggleOff label="Word-to-Word" />
          </div>

          {/* Verse flow */}
          <div
            style={{
              direction: 'rtl',
              fontFamily: ARABIC_FONT,
              fontSize: 64,
              lineHeight: 2.0,
              textAlign: 'justify',
              textAlignLast: 'center',
              margin: '40px 0 50px',
              color: COLORS.text,
            }}
          >
            {words.map((w, i) => {
              const isTarget = i === targetIdx;
              return (
                <span key={i}>
                  {isTarget ? (
                    <span
                      style={{
                        backgroundColor: COLORS.highlight,
                        padding: '4px 16px 8px',
                        borderRadius: 16,
                        opacity: highlightOpacity,
                      }}
                    >
                      {w}
                    </span>
                  ) : (
                    w
                  )}
                  {i < words.length - 1 ? ' ' : ''}
                </span>
              );
            })}
          </div>

          {/* English translation */}
          <p
            style={{
              fontFamily: SYSTEM_FONT,
              fontSize: 30,
              fontStyle: 'italic',
              lineHeight: 1.55,
              color: COLORS.textSoft,
              borderTop: `1px solid ${COLORS.hairline}`,
              paddingTop: 32,
              marginTop: 8,
            }}
          >
            {slide.translation}
          </p>
        </div>
      </div>
    </AbsoluteFill>
  );
}

// Word-to-Word toggle in the OFF state — used on the verse-flow
// slide so the slide reads as the "before" state of the toggle.
// The on-state toggle lives in WordToWordPage.
function ToggleOff({ label }: { label: string }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 18,
        fontFamily: SYSTEM_FONT,
        fontSize: 26,
        color: COLORS.text,
      }}
    >
      <span>{label}</span>
      <div
        style={{
          width: 84,
          height: 50,
          borderRadius: 26,
          backgroundColor: COLORS.toggleOff,
          position: 'relative',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: 4,
            left: 4,
            width: 42,
            height: 42,
            background: '#fff',
            borderRadius: '50%',
            boxShadow: '0 1px 3px rgba(0,0,0,0.18), 0 1px 1px rgba(0,0,0,0.06)',
          }}
        />
      </div>
    </div>
  );
}
