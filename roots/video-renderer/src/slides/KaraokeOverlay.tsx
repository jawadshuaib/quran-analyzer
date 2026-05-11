import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import type { NarrationT } from '../types';
import { COLORS, SYSTEM_FONT } from './shared';
import { wrapArabicRuns } from './arabic-runs';

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

interface Chunk {
  words: WordSpan[];
  startMs: number;
  endMs: number;
}

// At ~84px font / 600 weight, the 1080px-wide canvas with our
// padding fits roughly 20 characters per line. Pack words into
// two-line chunks so each chunk lingers ~2× as long on screen as
// the previous single-line design — easier on the eye, more
// context visible at once. A single word longer than the per-line
// budget becomes its own chunk (graceful overflow rather than
// truncation).
const MAX_CHUNK_CHARS = 40;
const MAX_LINE_CHARS = 20;

// True when the words can be laid out as ≤2 lines, each within the
// MAX_LINE_CHARS visual budget. A single oversized word is always
// "OK" (graceful overflow rather than rejection — we'd rather show
// it truncated than not at all).
function canFitInTwoLines(words: WordSpan[]): boolean {
  const total =
    words.reduce((s, w) => s + w.display.length, 0) + (words.length - 1);
  if (total <= MAX_LINE_CHARS) return true; // fits on one line
  // Try every possible split point.
  for (let split = 1; split < words.length; split++) {
    const top =
      words.slice(0, split).reduce((s, w) => s + w.display.length, 0) +
      (split - 1);
    const bot =
      words.slice(split).reduce((s, w) => s + w.display.length, 0) +
      (words.length - split - 1);
    if (top <= MAX_LINE_CHARS && bot <= MAX_LINE_CHARS) return true;
  }
  return false;
}

function buildChunks(words: WordSpan[]): Chunk[] {
  const chunks: Chunk[] = [];
  let buf: WordSpan[] = [];
  let bufLen = 0;
  for (const w of words) {
    const proposed = bufLen + (buf.length > 0 ? 1 : 0) + w.display.length;
    // End the chunk before adding `w` if either:
    //   - total chars would exceed MAX_CHUNK_CHARS, or
    //   - adding `w` would make the chunk un-splittable into two
    //     lines that each fit MAX_LINE_CHARS (the second condition
    //     catches "long word + long word" pairs that fit under the
    //     40-char chunk cap but can't actually be laid out).
    if (
      buf.length > 0 &&
      (proposed > MAX_CHUNK_CHARS || !canFitInTwoLines([...buf, w]))
    ) {
      chunks.push({
        words: buf,
        startMs: buf[0].startMs,
        endMs: buf[buf.length - 1].endMs,
      });
      buf = [w];
      bufLen = w.display.length;
    } else {
      buf.push(w);
      bufLen = proposed;
    }
  }
  if (buf.length > 0) {
    chunks.push({
      words: buf,
      startMs: buf[0].startMs,
      endMs: buf[buf.length - 1].endMs,
    });
  }
  return chunks;
}

// Split a chunk's words into two roughly-balanced lines.
//
// Algorithm: greedy pack the first line up to MAX_LINE_CHARS, then
// shift one word back to the second line if that would balance the
// totals better. The shift step matters for chunks like
// "this is a really long phrase here" — pure greedy would put
// "this is a really long" on line 1 and "phrase here" on line 2,
// which looks lopsided. Re-balancing yields "this is a really" /
// "long phrase here", roughly equal char counts.
//
// Returns a single line when the chunk is short enough that a
// second line would just have one or two words flopping under it.
function splitIntoLines(words: WordSpan[]): WordSpan[][] {
  if (words.length < 2) return [words];

  const totalChars =
    words.reduce((s, w) => s + w.display.length, 0) + (words.length - 1);

  // Short enough to fit on one line confidently — keep it there
  // (matches the old single-line behavior for very short chunks
  // like the closing "Why?" in a grammar slide).
  if (totalChars <= MAX_LINE_CHARS) return [words];

  // Greedy fill: walk words onto line 1 until adding the next would
  // exceed the per-line budget. Always leave at least one word for
  // line 2 (we don't want to "split" by putting everything on top).
  let split = 1;
  let acc = words[0].display.length;
  for (let i = 1; i < words.length - 1; i++) {
    const next = acc + 1 + words[i].display.length;
    if (next > MAX_LINE_CHARS) break;
    acc = next;
    split = i + 1;
  }

  // Re-balance: if shifting one word back to line 2 makes the line
  // lengths closer to equal, do it. Avoids "this is a really long" /
  // "phrase here" patterns.
  const lineLen = (slice: WordSpan[]) =>
    slice.reduce((s, w) => s + w.display.length, 0) + (slice.length - 1);
  while (split > 1) {
    const top = lineLen(words.slice(0, split));
    const bot = lineLen(words.slice(split));
    const topPrev = lineLen(words.slice(0, split - 1));
    const botPrev = lineLen(words.slice(split - 1));
    if (Math.abs(topPrev - botPrev) < Math.abs(top - bot)) {
      split -= 1;
    } else {
      break;
    }
  }

  return [words.slice(0, split), words.slice(split)];
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
  const chunks = buildChunks(words);
  if (chunks.length === 0) return null;

  // Time elapsed since audio start, in milliseconds. Frame 0 of the
  // slide (where the narration starts via <Audio>) is our zero.
  const elapsedMs = ((frame - audioStartFrame) / fps) * 1000;

  // Pick the active chunk — the one whose word range covers
  // elapsedMs. If we're between chunks (small gap of silence), we
  // bias to the previous chunk so it lingers rather than blanking
  // out. Before the first word starts, show the first chunk faded.
  let activeIdx = 0;
  for (let i = 0; i < chunks.length; i++) {
    if (elapsedMs >= chunks[i].startMs) activeIdx = i;
    else break;
  }
  const activeChunk = chunks[activeIdx];

  // Fade in over the first 8 frames so the overlay doesn't pop in
  // at slide start; fade out the last 8 frames so it doesn't get
  // cut mid-frame at slide end.
  const overlayOpacity = interpolate(
    frame - audioStartFrame,
    [0, 8],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' },
  );

  // Per-chunk soft fade-in. When a new chunk becomes active, ease
  // the whole chunk in over ~133ms (4 frames at 30fps) so the
  // transition reads as a "swap" rather than a snap. The previous
  // chunk just disappears under the fade — fine, since the audio
  // is already on the new chunk's words by then.
  const elapsedInChunkMs = elapsedMs - activeChunk.startMs;
  const chunkOpacity = Math.max(0, Math.min(1, elapsedInChunkMs / 133 + 0.3));

  // Split the active chunk into two balanced lines (or one, when
  // the chunk is short enough that splitting would be silly).
  const lines = splitIntoLines(activeChunk.words);

  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        bottom: 0,
        // Two-line chunks at 84px font + 1.18 line-height need ~200px
        // of vertical space; 360 keeps generous breathing room between
        // the caption and the bottom edge plus accommodates the
        // gradient fade up into the slide content.
        height: 360,
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
        // Keying on the chunk start time forces React to re-mount
        // the inner div when the chunk changes — the per-chunk
        // fade-in then runs from 0 instead of staying at 1. Since
        // we render only the active chunk, this is what produces
        // the "swap" feel between chunks.
        key={activeChunk.startMs}
        style={{
          fontFamily: SYSTEM_FONT,
          fontSize: 84,
          fontWeight: 600,
          color: '#FFFFFF',
          // Tight line height keeps two stacked lines compact and
          // avoids any visible gap that'd make them feel like
          // separate captions instead of a single phrase.
          lineHeight: 1.15,
          letterSpacing: '-0.01em',
          textAlign: 'center',
          textShadow: '0 4px 14px rgba(0,0,0,0.6)',
          maxWidth: 960,
          opacity: chunkOpacity,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 4,
        }}
      >
        {lines.map((lineWords, lineIdx) => (
          <div
            key={lineIdx}
            // Each line is its own non-wrapping flex row so words
            // stay together; only the chunk-level split decides how
            // they break.
            style={{
              display: 'flex',
              justifyContent: 'center',
              flexWrap: 'nowrap',
              whiteSpace: 'nowrap',
            }}
          >
            {lineWords.map((w, i) => {
              // Whole chunk is always fully visible — no popping in
              // or fading out word by word. The viewer reads the
              // phrase as a stable unit. Only the currently-spoken
              // word gets a color shift to gold so the eye tracks
              // the audio without the rest of the line redrawing
              // around it.
              const isCurrent =
                elapsedMs >= w.startMs - 30 && elapsedMs <= w.endMs + 30;
              // Use the saturated `highlightText` (gold), not the
              // pale `highlight` (which is designed as a background
              // pill — at this scale on the dark caption gradient
              // it reads as off-white and the highlight disappears).
              const color = isCurrent ? COLORS.highlightText : '#FFFFFF';

              return (
                <span
                  key={i}
                  style={{
                    display: 'inline-block',
                    color,
                    marginRight: 18,
                    transition: 'none',
                    // Uniform weight across the chunk so words don't
                    // visibly thicken when they pass through
                    // "current".
                    fontWeight: 600,
                  }}
                >
                  {wrapArabicRuns(w.display)}
                </span>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
