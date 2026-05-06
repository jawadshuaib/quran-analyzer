import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from 'remotion';
import type { GrammarVerseSlideT, GrammarHighlightT } from '../types';
import { COLORS, ARABIC_FONT, SYSTEM_FONT, ENTRY_FRAMES } from './shared';

// Grammar Insights — verse slide.
//
// Mirrors VerseFlowPage's structure (card + Arabic + translation +
// chapter:verse badge), but:
//   - Supports MULTIPLE highlights, each in its own semantic color.
//     A verse can show e.g. a tense marker (amber) AND a pronoun
//     shift (blue) at the same time. The pastel pill colors stay
//     legible-under-dark-text so the verse text never disappears.
//   - Pinned amber accent strip down the left edge of the card
//     visually identifies the series — viewers learn "amber edge =
//     grammar series" the same way they learn "yellow card = word
//     origins".
//   - English highlights mirror the Arabic ones — when a highlight
//     has translationSubstring, the renderer finds the substring in
//     the translation and applies the same pill color so the
//     viewer can see the Arabic→English correspondence.
//
// Note: an earlier version rendered a small italic annotation line
// below the card (a truncated paraphrase of the V7 payoff). It read
// poorly — too small, too easy to clip, and competed with the
// karaoke caption for attention. Removed; the spoken narration now
// carries the entire payoff. The `annotation` field on the slide
// type is kept for backward compatibility with older payloads but
// is no longer rendered.
//
// Sweep timing: each Arabic highlight enters with a 24-frame
// scaleX-0-to-1 sweep (RTL: from right edge), staggered by 12
// frames between adjacent highlights so they land in sequence
// rather than all at once. The matching English pill follows ~6
// frames behind its Arabic counterpart.
export function GrammarVersePage({ slide }: { slide: GrammarVerseSlideT }) {
  const frame = useCurrentFrame();

  const cardOpacity = interpolate(frame, [0, ENTRY_FRAMES], [0, 1], { extrapolateRight: 'clamp' });
  const cardTranslateY = interpolate(frame, [0, ENTRY_FRAMES], [16, 0], { extrapolateRight: 'clamp' });

  const words = slide.arabicText.split(/\s+/);
  const baseHighlightStart = 8;
  const sweepDur = 24;
  const stagger = 12;

  // Auto-scale translation font by length (matches VerseFlowPage).
  const translationLen = slide.translation.length;
  const translationFontSize =
    translationLen <= 80 ? 38 :
    translationLen <= 140 ? 32 :
    translationLen <= 200 ? 28 :
    24;

  // Map each highlight's marker to the pastel pill bg color.
  const markerColor = (m: GrammarHighlightT['marker']) => {
    switch (m) {
      case 'tense':   return COLORS.grammarMarkerTense;
      case 'pronoun': return COLORS.grammarMarkerPronoun;
      case 'fronted': return COLORS.grammarMarkerFronted;
      case 'agent':   return COLORS.grammarMarkerAgent;
      default:        return COLORS.grammarMarkerTense;
    }
  };

  // Pre-compute sweep progress for each Arabic highlight, staggered.
  const arabicSweeps = slide.highlights.map((_, i) => {
    const start = baseHighlightStart + i * stagger;
    return interpolate(
      frame, [start, start + sweepDur], [0, 1],
      { extrapolateRight: 'clamp', easing: Easing.out(Easing.ease) },
    );
  });

  // English sweeps follow ~6f behind their Arabic counterparts so
  // the eye sees Arabic first, English second.
  const enSweeps = slide.highlights.map((_, i) => {
    const start = baseHighlightStart + i * stagger + 6;
    return interpolate(
      frame, [start, start + sweepDur], [0, 1],
      { extrapolateRight: 'clamp', easing: Easing.out(Easing.ease) },
    );
  });

  // Build a map from word-index → highlight (for O(1) lookup during render).
  const highlightByIdx = new Map<number, { hl: GrammarHighlightT; sweep: number }>();
  slide.highlights.forEach((hl, i) => {
    highlightByIdx.set(hl.wordIndex - 1, { hl, sweep: arabicSweeps[i] });
  });

  // Pre-find each English highlight's match position in the translation.
  // Sequential search; ok for ≤4 highlights.
  const enMatches = slide.highlights.map((hl, i) => {
    if (!hl.translationSubstring) return null;
    const lower = slide.translation.toLowerCase();
    const idx = lower.indexOf(hl.translationSubstring.toLowerCase());
    if (idx < 0) return null;
    return {
      start: idx,
      end: idx + hl.translationSubstring.length,
      color: markerColor(hl.marker),
      sweep: enSweeps[i],
    };
  }).filter((m): m is NonNullable<typeof m> => m !== null);

  // Sort matches by position so we can splice the translation
  // string into [pre, match, mid, match, mid, ..., tail] segments
  // for rendering.
  enMatches.sort((a, b) => a.start - b.start);

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.appBg }}>
      <div
        style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
          padding: '120px 60px 80px 60px',
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          fontFamily: SYSTEM_FONT,
        }}
      >
        {/* Reference badge — same style as VerseFlowPage but with the
            amber accent so the series identity reads at a glance. */}
        <div
          style={{
            color: COLORS.grammarAccent, fontSize: 24, fontWeight: 600,
            letterSpacing: 1, marginBottom: 18, opacity: cardOpacity,
            textTransform: 'uppercase',
          }}
        >
          Quran {slide.surah}:{slide.ayah}
        </div>

        {/* Verse card */}
        <div
          style={{
            width: '100%', maxWidth: 920, background: COLORS.cardBg,
            borderRadius: 32,
            // The amber strip is the series signature.
            borderLeft: `8px solid ${COLORS.grammarAccent}`,
            padding: '48px 44px',
            boxShadow: '0 6px 24px rgba(0,0,0,0.05)',
            opacity: cardOpacity,
            transform: `translateY(${cardTranslateY}px)`,
            display: 'flex', flexDirection: 'column', gap: 32,
          }}
        >
          {/* Arabic line — RTL, words rendered as inline-blocks so
              we can give selected words a colored pill background. */}
          <div
            dir="rtl"
            style={{
              fontFamily: ARABIC_FONT, fontSize: 64, lineHeight: 1.7,
              color: COLORS.text, textAlign: 'center', wordSpacing: 8,
            }}
          >
            {words.map((w, i) => {
              const h = highlightByIdx.get(i);
              if (h) {
                return (
                  <span
                    key={i}
                    style={{
                      position: 'relative', display: 'inline-block', padding: '0 8px',
                    }}
                  >
                    {/* Sweep pill — scales from the trailing (right) edge for RTL. */}
                    <span
                      style={{
                        position: 'absolute', inset: 0, borderRadius: 12,
                        background: markerColor(h.hl.marker),
                        transform: `scaleX(${h.sweep})`,
                        transformOrigin: 'right center',
                      }}
                    />
                    <span style={{ position: 'relative' }}>{w}</span>
                  </span>
                );
              }
              return (
                <span key={i} style={{ display: 'inline-block', padding: '0 8px' }}>{w}</span>
              );
            })}
          </div>

          {/* Translation — italic stone, with English pills at matched substrings */}
          <div
            style={{
              fontStyle: 'italic', fontSize: translationFontSize, lineHeight: 1.45,
              color: COLORS.textSoft, textAlign: 'center',
            }}
          >
            {renderTranslationWithPills(slide.translation, enMatches)}
          </div>
        </div>

      </div>
    </AbsoluteFill>
  );
}

// Inline helper — splice the translation around matched substrings,
// applying each match's pastel pill color. Matches must be sorted
// ascending by start position. We don't animate the English sweeps
// individually; the per-match transform-origin is left-edge (LTR)
// and the sweep value is interpolated by the parent.
function renderTranslationWithPills(
  translation: string,
  matches: { start: number; end: number; color: string; sweep: number }[],
) {
  if (matches.length === 0) return translation;

  const parts: React.ReactNode[] = [];
  let cursor = 0;
  for (let i = 0; i < matches.length; i++) {
    const m = matches[i];
    if (cursor < m.start) {
      parts.push(<span key={`pre-${i}`}>{translation.slice(cursor, m.start)}</span>);
    }
    parts.push(
      <span
        key={`m-${i}`}
        style={{
          position: 'relative', display: 'inline-block', padding: '0 6px',
          fontStyle: 'normal', fontWeight: 600, color: COLORS.text,
        }}
      >
        <span
          style={{
            position: 'absolute', inset: 0, borderRadius: 6,
            background: m.color,
            transform: `scaleX(${m.sweep})`, transformOrigin: 'left center',
          }}
        />
        <span style={{ position: 'relative' }}>{translation.slice(m.start, m.end)}</span>
      </span>,
    );
    cursor = m.end;
  }
  if (cursor < translation.length) {
    parts.push(<span key="tail">{translation.slice(cursor)}</span>);
  }
  return parts;
}
