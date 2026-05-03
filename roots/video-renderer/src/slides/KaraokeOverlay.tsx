import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import type { NarrationT } from '../types';
import { COLORS, SYSTEM_FONT } from './shared';

// Karaoke overlay — bottom-anchored caption that highlights words
// as the narrator speaks them.
//
// Design:
//   - Anchored to the bottom 280px of the slide.
//   - Subtle dark gradient behind so the white caption reads on
//     light backgrounds (root page, verse card surround) without
//     overpowering them.
//   - Words rendered inline. Future words: 35% opacity. Past words:
//     full opacity. Currently-spoken word: full opacity + soft gold
//     accent + subtle scale-up so the eye latches on without
//     reading like a strobe.
//   - When `displayText` is provided on the narration, we render it
//     as the visible caption but use the alignment from `text`
//     (which is what the audio actually says). We approximate the
//     mapping by splitting both strings into words and aligning
//     them positionally. Imperfect for divergent texts, but the
//     pacing stays right: the highlight still tracks the audio.
//
// The slide passes its narration directly. The component computes
// the active word from useCurrentFrame() — Remotion handles the
// per-frame redraw, so the karaoke updates 30 times per second.

interface WordSpan {
  display: string;     // what we render
  startMs: number;
  endMs: number;
}

// Walk the alignment to produce per-word timing. `text` is the TTS
// input (must match alignment). `displayText` is what we render —
// if missing, we render `text`. We split both on whitespace and
// align positionally; if the word counts differ, the trailing
// display words get zero-width timing fillers and won't highlight,
// but they'll still appear at the end. (For v1 we keep text ===
// displayText so this fallback is rarely needed.)
function alignmentToWords(narration: NarrationT): WordSpan[] {
  const text = narration.text;
  const display = narration.displayText ?? text;
  const alignment = narration.alignment;
  if (!alignment) return [];

  const ttsWords: { start: number; end: number; startMs: number; endMs: number }[] = [];
  let i = 0;
  while (i < text.length) {
    while (i < text.length && /\s/.test(text[i])) i++;
    if (i >= text.length) break;
    const wStart = i;
    while (i < text.length && !/\s/.test(text[i])) i++;
    const wEnd = i;
    const startSec = alignment.starts[wStart] ?? 0;
    const endSec = alignment.ends[wEnd - 1] ?? startSec;
    ttsWords.push({
      start: wStart,
      end: wEnd,
      startMs: startSec * 1000,
      endMs: endSec * 1000,
    });
  }

  const displayWords = display.match(/\S+/g) ?? [];
  return displayWords.map((w, idx) => {
    const t = ttsWords[idx];
    if (!t) return { display: w, startMs: 0, endMs: 0 };
    return { display: w, startMs: t.startMs, endMs: t.endMs };
  });
}

export function KaraokeOverlay({
  narration,
  audioStartFrame,
}: {
  narration: NarrationT;
  audioStartFrame: number;
}) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const words = alignmentToWords(narration);
  if (words.length === 0) return null;

  // Time elapsed since audio start, in milliseconds. Frame 0 of the
  // slide (where the narration starts via <Audio>) is our zero.
  const elapsedMs = ((frame - audioStartFrame) / fps) * 1000;

  // Fade in over the first 8 frames so the overlay doesn't pop in
  // at slide start; fade out the last 8 frames so it doesn't get
  // cut mid-frame at slide end.
  const overlayOpacity = interpolate(
    frame - audioStartFrame,
    [0, 8],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' },
  );

  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        bottom: 0,
        // Tall enough to seat 2-3 lines of 104px text comfortably.
        // The OutroPage's "al-nuqta.com" is 130px; karaoke at 104
        // is ~80% of that — readable at arm's length on a phone
        // without dominating the slide.
        height: 560,
        // Subtle dark gradient so the caption is legible on any
        // bg without being a heavy bar.
        background:
          'linear-gradient(to top, rgba(0,0,0,0.82) 0%, rgba(0,0,0,0.55) 55%, rgba(0,0,0,0) 100%)',
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'center',
        padding: '0 60px 60px',
        opacity: overlayOpacity,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          fontFamily: SYSTEM_FONT,
          fontSize: 104,
          fontWeight: 600,
          color: '#FFFFFF',
          // Tight line height so multi-line captions don't sprawl.
          lineHeight: 1.18,
          letterSpacing: '-0.01em',
          textAlign: 'center',
          textShadow: '0 4px 14px rgba(0,0,0,0.6)',
          maxWidth: 960,
        }}
      >
        {words.map((w, i) => {
          const isPast = elapsedMs > w.endMs;
          const isCurrent = elapsedMs >= w.startMs - 30 && elapsedMs <= w.endMs + 30;
          const isFuture = elapsedMs < w.startMs - 30;

          // Future words sit at low opacity so the caption reads
          // like a "what's coming" hint. Past words are full
          // opacity. Current word gets a slight scale + gold
          // accent so the eye locks on.
          const opacity = isFuture ? 0.35 : 1;
          const color = isCurrent ? COLORS.highlight : '#FFFFFF';
          const scale = isCurrent ? 1.06 : 1;

          return (
            <span
              key={i}
              style={{
                display: 'inline-block',
                transformOrigin: 'center bottom',
                transform: `scale(${scale})`,
                color,
                opacity,
                marginRight: 22,
                transition: 'none',
                fontWeight: isCurrent ? 700 : isPast ? 600 : 500,
              }}
            >
              {w.display}
            </span>
          );
        })}
      </div>
    </div>
  );
}
