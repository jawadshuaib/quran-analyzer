import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from 'remotion';
import type { VerseContrastSlideT, ContrastVerseT } from '../types';
import { COLORS, ARABIC_FONT, SYSTEM_FONT, ENTRY_FRAMES } from './shared';
import { wrapArabicRuns } from './arabic-runs';
import { splitArabicWords, resolveHighlightSet, findEnglishSpan } from './highlight.mjs';

// Q&A bank — two verses on screen AT ONCE, each with its own highlight.
// For insights built on a mirror ("the same word marks rescue there and
// ruin here"): the viewer sees both halves of the contrast side by side
// instead of having to remember the first verse. The bottom panel enters
// a beat after the top so the eye reads them in order.
//
// Highlight painting reuses the SAME shared resolver (highlight.mjs) as
// VerseFlowPage and the match-gate's verifier — no drift between
// validation and pixels.
export function VerseContrastPage({ slide }: { slide: VerseContrastSlideT }) {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.appBg, justifyContent: 'center', alignItems: 'center' }}>
      <div style={{ width: '88%', display: 'flex', flexDirection: 'column', gap: 28 }}>
        <ContrastPanel verse={slide.top} frame={frame} delay={0} />
        <div
          style={{
            alignSelf: 'center',
            fontFamily: SYSTEM_FONT,
            fontSize: 26,
            color: 'rgba(60, 56, 48, 0.45)',
            letterSpacing: '0.25em',
            opacity: interpolate(frame, [ENTRY_FRAMES + 6, ENTRY_FRAMES + 20], [0, 1], {
              extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
            }),
          }}
        >
          ⟷
        </div>
        <ContrastPanel verse={slide.bottom} frame={frame} delay={ENTRY_FRAMES + 10} />
      </div>
    </AbsoluteFill>
  );
}

function ContrastPanel({
  verse,
  frame,
  delay,
}: {
  verse: ContrastVerseT;
  frame: number;
  delay: number;
}) {
  const opacity = interpolate(frame, [delay, delay + ENTRY_FRAMES], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const translateY = interpolate(frame, [delay, delay + ENTRY_FRAMES], [14, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  // Highlight sweep, staggered after the panel entry (RTL: grows from the
  // right, like a marker stroke — same feel as VerseFlowPage).
  const sweep = interpolate(
    frame,
    [delay + ENTRY_FRAMES, delay + ENTRY_FRAMES + 22],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.ease) },
  );

  const words = splitArabicWords(verse.arabicText);
  const highlightSet = resolveHighlightSet(verse);
  const enSpan = findEnglishSpan(verse.translation, verse.highlightTranslationText);

  const arabicFontSize = words.length <= 8 ? 52 : words.length <= 16 ? 44 : 38;
  const translationFontSize = verse.translation.length <= 90 ? 28 : 24;

  return (
    <div
      style={{
        borderRadius: 24,
        background: COLORS.cardBg,
        border: `1px solid ${COLORS.hairline}`,
        boxShadow: '0 12px 44px rgba(44, 44, 42, 0.10)',
        padding: '36px 40px',
        opacity,
        transform: `translateY(${translateY}px)`,
      }}
    >
      <div
        style={{
          fontFamily: SYSTEM_FONT,
          fontSize: 22,
          fontWeight: 600,
          color: COLORS.textMuted,
          marginBottom: 18,
        }}
      >
        Surah {verse.surah}, Ayah {verse.ayah}
      </div>

      <div
        dir="rtl"
        lang="ar"
        style={{
          fontFamily: ARABIC_FONT,
          fontSize: arabicFontSize,
          lineHeight: 1.95,
          color: COLORS.text,
          textAlign: 'center',
        }}
      >
        {words.map((w: string, i: number) => {
          const hl = highlightSet.has(i); // resolveHighlightSet is 0-indexed
          return (
            <span key={i} style={{ position: 'relative', display: 'inline-block', padding: '0 4px' }}>
              {hl && (
                <span
                  style={{
                    position: 'absolute',
                    inset: '6% 0',
                    background: COLORS.highlight,
                    borderRadius: 8,
                    transform: `scaleX(${sweep})`,
                    transformOrigin: 'right',
                  }}
                />
              )}
              <span style={{ position: 'relative' }}>{w}</span>
              {i < words.length - 1 ? ' ' : ''}
            </span>
          );
        })}
      </div>

      <div
        style={{
          fontFamily: SYSTEM_FONT,
          fontSize: translationFontSize,
          lineHeight: 1.5,
          color: COLORS.textSoft,
          textAlign: 'center',
          marginTop: 18,
        }}
      >
        {enSpan.start >= 0 ? (
          <>
            {wrapArabicRuns(verse.translation.slice(0, enSpan.start))}
            <span
              style={{
                position: 'relative',
                display: 'inline-block',
                padding: '0 4px',
              }}
            >
              <span
                style={{
                  position: 'absolute',
                  inset: '4% 0',
                  background: COLORS.highlight,
                  borderRadius: 6,
                  transform: `scaleX(${sweep})`,
                  transformOrigin: 'left',
                }}
              />
              <span style={{ position: 'relative' }}>
                {wrapArabicRuns(verse.translation.slice(enSpan.start, enSpan.end))}
              </span>
            </span>
            {wrapArabicRuns(verse.translation.slice(enSpan.end))}
          </>
        ) : (
          wrapArabicRuns(verse.translation)
        )}
      </div>
    </div>
  );
}
