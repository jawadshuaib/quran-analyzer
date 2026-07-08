import { AbsoluteFill, useCurrentFrame, interpolate } from 'remotion';
import type { PoetrySlideT } from '../types';
import { COLORS, ARABIC_FONT, SYSTEM_FONT, ENTRY_FRAMES } from './shared';
import { wrapArabicRuns } from './arabic-runs';

// Q&A bank — a pre-Islamic bayt on its own slide.
//
// Deliberately DISTINCT from every Qur'an-verse slide: warm parchment
// card, amber accent, and an explicit "PRE-ISLAMIC POETRY" eyebrow, so a
// viewer can never mistake a poet's line for scripture (the same
// visual-separation doctrine the site's poetry pages follow). The bayt
// itself is corpus-verified upstream by the compile gate.
export function PoetryPage({ slide }: { slide: PoetrySlideT }) {
  const frame = useCurrentFrame();

  const cardOpacity = interpolate(frame, [0, ENTRY_FRAMES], [0, 1], { extrapolateRight: 'clamp' });
  const cardTranslateY = interpolate(frame, [0, ENTRY_FRAMES], [16, 0], { extrapolateRight: 'clamp' });
  // English fades in a beat after the Arabic, mirroring the reading order.
  const englishOpacity = interpolate(frame, [ENTRY_FRAMES + 6, ENTRY_FRAMES + 24], [0, 1], {
    extrapolateRight: 'clamp',
    extrapolateLeft: 'clamp',
  });

  const baytLen = slide.bayt.length;
  const baytFontSize = baytLen <= 60 ? 64 : baytLen <= 110 ? 54 : 46;

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.appBg, justifyContent: 'center', alignItems: 'center' }}>
      <div
        style={{
          width: '86%',
          borderRadius: 28,
          // Parchment: warmer + darker than the cream verse cards.
          background: 'linear-gradient(175deg, #F6EBD9 0%, #EFE0C4 100%)',
          border: '1px solid rgba(146, 100, 21, 0.35)',
          boxShadow: '0 18px 60px rgba(99, 56, 6, 0.18)',
          padding: '64px 56px',
          opacity: cardOpacity,
          transform: `translateY(${cardTranslateY}px)`,
        }}
      >
        <div
          style={{
            fontFamily: SYSTEM_FONT,
            fontSize: 24,
            fontWeight: 700,
            letterSpacing: '0.18em',
            color: '#92650F',
            marginBottom: 40,
            display: 'flex',
            alignItems: 'center',
            gap: 16,
          }}
        >
          <span style={{ flex: 1, height: 1, background: 'rgba(146,100,21,0.35)' }} />
          PRE-ISLAMIC POETRY
          <span style={{ flex: 1, height: 1, background: 'rgba(146,100,21,0.35)' }} />
        </div>

        <div
          dir="rtl"
          lang="ar"
          style={{
            fontFamily: ARABIC_FONT,
            fontSize: baytFontSize,
            lineHeight: 2.05,
            color: '#3A2E1B',
            textAlign: 'center',
          }}
        >
          {slide.bayt}
        </div>

        {slide.english && (
          <div
            style={{
              fontFamily: SYSTEM_FONT,
              fontSize: 34,
              lineHeight: 1.55,
              fontStyle: 'italic',
              color: '#6B5836',
              textAlign: 'center',
              marginTop: 36,
              opacity: englishOpacity,
            }}
          >
            {wrapArabicRuns(slide.english)}
          </div>
        )}

        {slide.poet && (
          <div
            style={{
              fontFamily: SYSTEM_FONT,
              fontSize: 26,
              color: '#92650F',
              textAlign: 'center',
              marginTop: 32,
              opacity: englishOpacity,
            }}
          >
            — {wrapArabicRuns(slide.poet)}
          </div>
        )}

        <div
          style={{
            fontFamily: SYSTEM_FONT,
            fontSize: 20,
            color: 'rgba(107, 88, 54, 0.7)',
            textAlign: 'center',
            marginTop: 40,
          }}
        >
          a poet's line from before the Qur'an — not scripture
        </div>
      </div>
    </AbsoluteFill>
  );
}
