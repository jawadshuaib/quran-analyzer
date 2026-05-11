import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from 'remotion';
import type { WordToWordSlideT } from '../types';
import { COLORS, ARABIC_FONT, SYSTEM_FONT, ENTRY_FRAMES } from './shared';
import { wrapArabicRuns } from './arabic-runs';

// Cells per row — vertical 1080-wide canvas can't fit 6 cells per
// row like the desktop mockup (C.html) without making the Arabic
// font tiny. 3 per row gives each cell ~280px which holds Arabic
// at a readable size.
const CELLS_PER_ROW = 3;

// Slide C — word-to-word breakdown of the same verse from slide B.
// Layout (1080x1920 vertical):
//   - Same outer cream-warm bg + cream verse card as Slide B, so the
//     transition from B → C reads as "the toggle just flipped on".
//   - Card header: surah/ayah nav + toggle in the ON state (green).
//   - Card body: RTL grid of (Arabic word, English gloss) cells.
//     3 cells per row — adapted down from the desktop mockup's 6 to
//     keep the Arabic at video-readable size on a 1080-wide canvas.
//   - Card footer: same italic English translation under hairline.
//
// Animation: cells stagger in row-by-row. Row N starts ~3 frames
// after row N-1 so the slide builds rather than flashing in. Once
// the grid is fully loaded the slide just dwells.
export function WordToWordPage({ slide }: { slide: WordToWordSlideT }) {
  const frame = useCurrentFrame();

  const cardOpacity = interpolate(frame, [0, ENTRY_FRAMES], [0, 1], { extrapolateRight: 'clamp' });

  // Chunk words into rows. RTL display means we do NOT pre-reverse
  // the array — we lay the cells out in source order and rely on
  // direction:rtl to flip the visual order per row.
  const rows: typeof slide.words[] = [];
  for (let i = 0; i < slide.words.length; i += CELLS_PER_ROW) {
    rows.push(slide.words.slice(i, i + CELLS_PER_ROW));
  }

  // After all rows have finished landing, the highlighted cell does
  // a single subtle scale-pulse (1 → 1.06 → 1) over 18 frames so
  // the eye is drawn to the target word once the grid is stable.
  // Computed off the LAST row's land time so the pulse never
  // overlaps the entrance animation.
  const allRowsLanded = 4 + (rows.length - 1) * 3 + ENTRY_FRAMES;
  const pulseStart = allRowsLanded + 6;       // beat after settle
  const pulsePeak = pulseStart + 9;
  const pulseEnd = pulsePeak + 9;
  const pulseScale = interpolate(
    frame,
    [pulseStart, pulsePeak, pulseEnd],
    [1, 1.06, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.ease) },
  );

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
          padding: '60px 40px',
        }}
      >
        <div
          style={{
            backgroundColor: COLORS.cardBg,
            borderRadius: 36,
            padding: '60px 50px 60px',
            width: '100%',
            maxWidth: 1000,
            boxShadow: '0 2px 0 rgba(0,0,0,0.02), 0 16px 48px -32px rgba(60,55,40,0.18)',
            opacity: cardOpacity,
          }}
        >
          {/* Card header — same shape as VerseFlowPage but toggle is ON */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 16,
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
            <ToggleOn label="Word-to-Word" />
          </div>

          {/* Word-to-word grid */}
          <div
            style={{
              direction: 'rtl',
              display: 'flex',
              flexDirection: 'column',
              gap: 36,
              margin: '38px 0 38px',
            }}
          >
            {rows.map((row, rowIdx) => {
              // Each row's contents fade in starting at this frame
              // so rows stagger top→down.
              const rowStart = 4 + rowIdx * 3;
              const rowOpacity = interpolate(
                frame,
                [rowStart, rowStart + ENTRY_FRAMES],
                [0, 1],
                { extrapolateRight: 'clamp' },
              );
              const isPartial = row.length < CELLS_PER_ROW;
              return (
                <div
                  key={rowIdx}
                  style={{
                    display: 'flex',
                    flexDirection: 'row',
                    justifyContent: isPartial ? 'flex-start' : 'space-between',
                    alignItems: 'flex-start',
                    gap: isPartial ? 56 : 16,
                    opacity: rowOpacity,
                  }}
                >
                  {row.map((w, i) => (
                    <Cell
                      key={i}
                      ar={w.ar}
                      en={w.en}
                      highlight={!!w.highlight}
                      pulseScale={w.highlight ? pulseScale : 1}
                    />
                  ))}
                </div>
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
            {wrapArabicRuns(slide.translation)}
          </p>
        </div>
      </div>
    </AbsoluteFill>
  );
}

// One Arabic-word + English-gloss cell. Highlight wraps the Arabic
// word in a soft-yellow pill so the grid version of the highlight
// matches the verse-flow slide. `pulseScale` drives the
// post-entrance attention pulse on the highlighted cell.
function Cell({ ar, en, highlight, pulseScale }: { ar: string; en: string; highlight: boolean; pulseScale: number }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 16,
        minWidth: 0,
      }}
    >
      <div
        style={{
          fontFamily: ARABIC_FONT,
          fontSize: 60,
          lineHeight: 1.3,
          whiteSpace: 'nowrap',
          color: COLORS.text,
          // transformOrigin keeps the pulse centered on the cell,
          // not anchored to a corner.
          transformOrigin: 'center center',
          transform: `scale(${pulseScale})`,
          ...(highlight
            ? {
                backgroundColor: COLORS.highlight,
                padding: '4px 18px 8px',
                borderRadius: 14,
              }
            : {}),
        }}
      >
        {ar}
      </div>
      <div
        style={{
          fontFamily: SYSTEM_FONT,
          fontSize: 24,
          fontWeight: 400,
          color: COLORS.textMuted,
          direction: 'ltr',
          whiteSpace: 'nowrap',
        }}
      >
        {wrapArabicRuns(en)}
      </div>
    </div>
  );
}

// Word-to-Word toggle in the ON state — green pill with the dot
// nudged to the right. Mirrors the off-state toggle in
// VerseFlowPage.tsx so the two slides feel like a continuous "user
// flipped the switch" moment.
function ToggleOn({ label }: { label: string }) {
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
          backgroundColor: COLORS.toggleOn,
          position: 'relative',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: 4,
            left: 38,
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
