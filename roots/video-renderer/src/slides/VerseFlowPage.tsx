import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from 'remotion';
import type { VerseFlowSlideT } from '../types';
import { COLORS, ARABIC_FONT, SYSTEM_FONT, ENTRY_FRAMES } from './shared';
import { wrapArabicRuns } from './arabic-runs';

// Slide B — full verse with the target word highlighted in soft yellow.
//
// Visual upgrades over the prototype:
//   - Highlight SWEEPS in (scaleX 0→1, transform-origin: right for
//     RTL) so the yellow pill grows from the trailing edge of the
//     word, like a marker stroke. Fades + slides at the same time
//     for a layered feel.
//   - Matching English phrase in the translation also highlights —
//     same yellow pill, same sweep animation but LTR, fired ~6
//     frames after the Arabic so the eye has time to register the
//     correspondence (Arabic → English).
//   - Translation font auto-scales by length: short translations
//     feel BIGGER and more deliberate; long translations stay
//     compact so they don't dominate.
export function VerseFlowPage({ slide }: { slide: VerseFlowSlideT }) {
  const frame = useCurrentFrame();

  const cardOpacity = interpolate(frame, [0, ENTRY_FRAMES], [0, 1], { extrapolateRight: 'clamp' });
  const cardTranslateY = interpolate(frame, [0, ENTRY_FRAMES], [16, 0], { extrapolateRight: 'clamp' });

  // Highlight sweep — 24-frame ease-out so it lands smoothly. The
  // yellow grows from 0 → 1 width while the text stays fully
  // visible on top.
  const arabicHighlightStart = 8;
  const arabicHighlightEnd = arabicHighlightStart + 24;
  const arabicSweep = interpolate(
    frame,
    [arabicHighlightStart, arabicHighlightEnd],
    [0, 1],
    { extrapolateRight: 'clamp', easing: Easing.out(Easing.ease) },
  );

  // English highlight follows ~6 frames behind so the viewer's eye
  // has a beat to register the Arabic before being directed to the
  // matching gloss. Same 24-frame sweep duration.
  const enHighlightStart = arabicHighlightStart + 6;
  const enHighlightEnd = enHighlightStart + 24;
  const enSweep = interpolate(
    frame,
    [enHighlightStart, enHighlightEnd],
    [0, 1],
    { extrapolateRight: 'clamp', easing: Easing.out(Easing.ease) },
  );

  // Build the verse with the highlight applied in-place.
  const words = slide.arabicText.split(/\s+/);
  const targetIdx = (slide.highlightWordIndex ?? 0) - 1;

  // Find the highlighted English phrase (case-insensitive).
  const englishHighlight = slide.highlightTranslationText?.trim() ?? '';
  const translationLower = slide.translation.toLowerCase();
  const enMatchStart = englishHighlight
    ? translationLower.indexOf(englishHighlight.toLowerCase())
    : -1;
  const enMatchEnd = enMatchStart >= 0 ? enMatchStart + englishHighlight.length : -1;

  // Auto-scale the translation font by length. Short, punchy
  // translations get bigger so they feel like the payoff line; long
  // multi-clause translations shrink to fit without overflowing the
  // card.
  const translationLen = slide.translation.length;
  const translationFontSize =
    translationLen <= 80 ? 40 :
    translationLen <= 140 ? 34 :
    translationLen <= 200 ? 30 :
    26;

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

          {/* Verse flow — RTL, target word wrapped in a sweeping
              highlight pill */}
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
                    <SweepHighlight progress={arabicSweep} originSide="right">
                      {w}
                    </SweepHighlight>
                  ) : (
                    w
                  )}
                  {i < words.length - 1 ? ' ' : ''}
                </span>
              );
            })}
          </div>

          {/* English translation — italic, with the matching phrase
              wrapped in its own (LTR) sweep highlight when present */}
          <p
            style={{
              fontFamily: SYSTEM_FONT,
              fontSize: translationFontSize,
              fontStyle: 'italic',
              lineHeight: 1.55,
              color: COLORS.textSoft,
              borderTop: `1px solid ${COLORS.hairline}`,
              paddingTop: 32,
              marginTop: 8,
            }}
          >
            {enMatchStart >= 0 ? (
              <>
                {wrapArabicRuns(slide.translation.slice(0, enMatchStart))}
                <SweepHighlight progress={enSweep} originSide="left">
                  {wrapArabicRuns(slide.translation.slice(enMatchStart, enMatchEnd))}
                </SweepHighlight>
                {wrapArabicRuns(slide.translation.slice(enMatchEnd))}
              </>
            ) : (
              wrapArabicRuns(slide.translation)
            )}
          </p>
        </div>
      </div>
    </AbsoluteFill>
  );
}

// Sweep highlight — yellow pill that grows from one edge to the
// other while the text on top stays fully visible. RTL slides set
// originSide="right" so the highlight enters from the trailing
// edge of the word; LTR (English translation) uses "left".
//
// Layered structure: outer span is `inline-block` and relatively
// positioned so the absolute background tracks its bounds. Text
// stacks above via z-index so it's never obscured by the bg.
function SweepHighlight({
  children,
  progress,
  originSide,
}: {
  children: React.ReactNode;
  progress: number;
  originSide: 'left' | 'right';
}) {
  return (
    <span
      style={{
        position: 'relative',
        display: 'inline-block',
        padding: '4px 16px 8px',
      }}
    >
      <span
        style={{
          position: 'absolute',
          inset: 0,
          backgroundColor: COLORS.highlight,
          borderRadius: 16,
          transformOrigin: `${originSide} center`,
          transform: `scaleX(${progress})`,
          zIndex: 0,
        }}
      />
      <span style={{ position: 'relative', zIndex: 1 }}>{children}</span>
    </span>
  );
}

// Word-to-Word toggle in the OFF state.
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
