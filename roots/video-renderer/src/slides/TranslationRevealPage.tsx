import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from 'remotion';
import type { TranslationRevealSlideT } from '../types';
import { COLORS, ARABIC_FONT, SYSTEM_FONT } from './shared';
import { wrapArabicRuns } from './arabic-runs';

// What Translation Hides — opening reveal slide.
//
// Four-beat choreography (YouTube/Shorts attention model):
//
//   Beat A — HOOK            (0-1.5s)
//     One-line curiosity-bait: "There's a word in this verse..."
//     Plus a small verse reference ("Quran 25:58") so the viewer
//     knows we're talking about a specific verse, not a generic
//     gripe about translations.
//
//   Beat B — ARTIFACT        (1.5-3.5s)
//     Big Arabic word in the center, transliteration under it.
//     This is the visual authority: the viewer SEES the actual
//     Quranic word the rest of the video will unpack. (When the
//     reveal is phrase-level and there's no single word in focus,
//     we skip this beat and stretch the hook beat instead.)
//
//   Beat C — CONVENTIONAL    (3.5-5.5s)
//     "MOST TRANSLATIONS SAY [X]" — the conventional rendering
//     the audience already knows.
//
//   Beat D — REVEAL          (5.5-9s)
//     "but" — then "THE ARABIC ACTUALLY SAYS [Y]". The rose pill
//     pops; the hidden gloss lands.
//
// Why the redesign:
//   The prior version dumped both rows in the first ~2.5s with no
//   context. On 25:58 that meant the viewer saw
//     "Most translations say God is aware of servants' sins.
//      The Arabic actually says He's aware of their tails."
//   in the opening seconds with zero framing. Read cold, "tails"
//   sounds bizarre — viewers skipped before the body of the video
//   ever explained the root-image. The four-beat version delays
//   the contrast until the viewer has (a) heard a curiosity-hook,
//   (b) seen the actual Arabic word in big type, and (c) had
//   roughly two seconds to absorb the conventional reading they
//   already know. Then the reveal lands as a payoff, not a
//   non-sequitur.
//
// Sizing: tuned for the 1080×1920 vertical mobile composition.
// Earlier sizes were tuned for desktop and read as tiny on phone
// screens; this version sizes the hook and Arabic for thumb-stop
// readability.
export function TranslationRevealPage({ slide }: { slide: TranslationRevealSlideT }) {
  const frame = useCurrentFrame();

  // Frame anchors — keep these explicit so the choreography is
  // easy to retune. All in 30fps frames.
  const BEAT_A_IN = 0;       // hook fade-in starts
  const BEAT_A_FULL = 14;    // hook fully on screen
  const BEAT_B_IN = 36;      // Arabic word starts to enter
  const BEAT_B_FULL = 56;    // Arabic word fully on screen
  const BEAT_C_IN = 90;      // conventional row enters
  const BEAT_C_FULL = 110;
  const BUT_IN = 130;        // "but" lands between rows
  const BUT_FULL = 144;
  const BEAT_D_IN = 156;     // hidden row enters
  const BEAT_D_FULL = 180;
  const TAGLINE_IN = 220;
  const TAGLINE_FULL = 240;

  // Determine whether we have a single Arabic artifact to focus
  // on. If the reveal is phrase-level the AI judge omits this and
  // we collapse beats A+B into a single "hook + ref" frame so the
  // pacing doesn't drag.
  const hasArabicArtifact = !!(slide.arabic && slide.arabic.trim());

  // ---------- opacity / transform helpers ----------
  const fadeIn = (a: number, b: number) =>
    interpolate(frame, [a, b], [0, 1], { extrapolateRight: 'clamp' });
  const fadeOut = (a: number, b: number) =>
    interpolate(frame, [a, b], [1, 0], { extrapolateRight: 'clamp' });

  // Beat A — hook line. Fades in fast (it's the first thing the
  // viewer reads, and it's the hook), and then *fades out* when
  // the artifact phase begins so the artifact has the stage.
  const hookOpacity = Math.min(
    fadeIn(BEAT_A_IN, BEAT_A_FULL),
    hasArabicArtifact ? fadeOut(BEAT_B_FULL, BEAT_B_FULL + 12) : 1,
  );
  const hookTranslateY = interpolate(
    frame, [BEAT_A_IN, BEAT_A_FULL], [-12, 0],
    { extrapolateRight: 'clamp' },
  );

  // Beat B — Arabic artifact. Slow scale-up while fading in so it
  // feels weighty, like a piece of evidence being placed on the
  // table. Then it slides up to make room for the contrast in
  // beats C+D — but it stays visible (semi-transparent) so the
  // viewer keeps a thread to the artifact while reading the
  // English.
  const artifactOpacity = hasArabicArtifact
    ? Math.min(
        fadeIn(BEAT_B_IN, BEAT_B_FULL),
        interpolate(
          frame,
          [BEAT_C_IN, BEAT_C_FULL],
          [1, 0.45],
          { extrapolateRight: 'clamp' },
        ),
      )
    : 0;
  const artifactScale = interpolate(
    frame, [BEAT_B_IN, BEAT_B_FULL], [0.92, 1],
    { extrapolateRight: 'clamp', easing: Easing.out(Easing.ease) },
  );
  const artifactTranslateY = interpolate(
    frame, [BEAT_C_IN, BEAT_C_FULL], [0, -120],
    { extrapolateRight: 'clamp', easing: Easing.out(Easing.ease) },
  );

  // Beat C — conventional row.
  const convOpacity = fadeIn(BEAT_C_IN, BEAT_C_FULL);
  const convTranslateY = interpolate(
    frame, [BEAT_C_IN, BEAT_C_FULL], [-12, 0],
    { extrapolateRight: 'clamp' },
  );

  // "but" connector.
  const butOpacity = fadeIn(BUT_IN, BUT_FULL);

  // Beat D — reveal row. Subtle scale-up to draw the eye.
  const hiddenOpacity = fadeIn(BEAT_D_IN, BEAT_D_FULL);
  const hiddenTranslateY = interpolate(
    frame, [BEAT_D_IN, BEAT_D_FULL], [12, 0],
    { extrapolateRight: 'clamp' },
  );
  const hiddenScale = interpolate(
    frame, [BEAT_D_IN, BEAT_D_FULL], [0.96, 1],
    { extrapolateRight: 'clamp', easing: Easing.out(Easing.ease) },
  );

  // Tagline.
  const taglineOpacity = fadeIn(TAGLINE_IN, TAGLINE_FULL);

  // Build the verse reference line — prefer an explicit verseRef,
  // otherwise auto-build from chapter:verse. We keep it small and
  // tucked under the hook line so it doesn't compete with the
  // word itself.
  const refLine = (slide.verseRef && slide.verseRef.trim())
    || (slide.chapter && slide.verse ? `Quran ${slide.chapter}:${slide.verse}` : '');

  // The hook line — let the script override, but provide a
  // sensible default so the slide is never naked. The default
  // is intentionally a curiosity-bait phrase, not a thesis.
  const hookLine = (slide.hookLine && slide.hookLine.trim())
    || (hasArabicArtifact
      ? "There's a word in this verse..."
      : "Most translations miss this.");

  // Auto-scale gloss font by length. Tuned for vertical mobile —
  // these are the BODY lines (the actual "her chastity" / "her
  // private parts" content), so they need to dominate the slide.
  // Previous values felt cramped on phone playback; operator
  // feedback after 66:12 dev render: "English here still looks
  // small." Bumped each tier by ~25%.
  const fontFor = (text: string, big: number, mid: number, small: number) => {
    const n = (text || '').length;
    if (n <= 60) return big;
    if (n <= 110) return mid;
    return small;
  };
  const convFontSize = fontFor(slide.conventionalText, 76, 62, 54);
  const hiddenFontSize = fontFor(slide.hiddenText, 86, 72, 60);

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.appBg, fontFamily: SYSTEM_FONT }}>
      {/* Series mark — pinned at the top throughout the slide so
          the viewer always knows what they're watching. */}
      <div
        style={{
          position: 'absolute', top: 70, left: 0, right: 0,
          color: COLORS.translationAccent,
          fontSize: 46, fontWeight: 700, letterSpacing: 3,
          textTransform: 'uppercase', textAlign: 'center',
        }}
      >
        What Translation Hides
      </div>

      {/* === Beats A + B: hook + artifact overlay layer ===
          These two beats share visual space — the hook sits high,
          the Arabic word sits in the optical center. As the slide
          progresses into Beats C+D, the artifact slides up and
          fades to ~45%, becoming a watermark that anchors the
          word the contrast is about. */}
      <div
        style={{
          position: 'absolute',
          top: 0, left: 0, right: 0,
          height: '100%',
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          pointerEvents: 'none',
          padding: '160px 60px 240px',
        }}
      >
        {/* Hook line */}
        <div
          style={{
            opacity: hookOpacity,
            transform: `translateY(${hookTranslateY}px)`,
            fontSize: 68,
            fontWeight: 600,
            fontStyle: 'italic',
            color: COLORS.translationAccentDeep,
            textAlign: 'center',
            maxWidth: 920,
            lineHeight: 1.2,
            marginBottom: 28,
          }}
        >
          {wrapArabicRuns(hookLine)}
        </div>

        {/* Verse reference */}
        {refLine && (
          <div
            style={{
              opacity: hookOpacity,
              fontSize: 38,
              fontWeight: 600,
              letterSpacing: 1.5,
              color: COLORS.translationConvText,
              textTransform: 'uppercase',
              marginBottom: 40,
            }}
          >
            {refLine}
          </div>
        )}

        {/* Arabic artifact — the word OR phrase the rest of the
            slide unpacks. Slides up and dims (but does NOT vanish)
            as the contrast rows enter below it. Font auto-scales
            on length: single words get the dramatic 150px treatment;
            multi-word phrases (e.g. "أَحْصَنَتْ فَرْجَهَا" — what
            the script's english_emphases mapped to) shrink so they
            fit on screen instead of overflowing. */}
        {hasArabicArtifact && (() => {
          const arLen = (slide.arabic || '').length;
          const arabicFontSize =
            arLen <= 7 ? 150 :
            arLen <= 14 ? 120 :
            arLen <= 24 ? 96 :
            arLen <= 36 ? 78 : 62;
          return (
            <div
              style={{
                opacity: artifactOpacity,
                transform: `translateY(${artifactTranslateY}px) scale(${artifactScale})`,
                display: 'flex', flexDirection: 'column', alignItems: 'center',
                maxWidth: 960,
              }}
            >
              <div
                dir="rtl"
                lang="ar"
                style={{
                  fontFamily: ARABIC_FONT,
                  fontSize: arabicFontSize,
                  lineHeight: 1.25,
                  color: COLORS.text,
                  textAlign: 'center',
                  paddingLeft: 8, paddingRight: 8,
                }}
              >
                {slide.arabic}
              </div>
              {slide.transliteration && (
                <div
                  style={{
                    fontSize: 40,
                    fontStyle: 'italic',
                    color: COLORS.translationConvText,
                    marginTop: 10,
                  }}
                >
                  {slide.transliteration}
                </div>
              )}
              {slide.glossLine && (
                <div
                  style={{
                    // Bumped 32 → 48 — this English line sits
                    // directly under the artifact and is what
                    // anchors the viewer when the Arabic alone is
                    // unfamiliar. Needs to be readable at arm's
                    // length on a phone.
                    fontSize: 48,
                    fontStyle: 'italic',
                    color: COLORS.translationConvText,
                    marginTop: slide.transliteration ? 6 : 18,
                    maxWidth: 880,
                    textAlign: 'center',
                    lineHeight: 1.35,
                  }}
                >
                  &ldquo;{slide.glossLine}&rdquo;
                </div>
              )}
            </div>
          );
        })()}
      </div>

      {/* === Beats C + D: the contrast rows ===
          These sit in the lower half so the artifact (when
          present) keeps a watermark presence in the center. When
          there's no artifact, the rows fill more of the space. */}
      <div
        style={{
          position: 'absolute',
          left: 0, right: 0, bottom: 110,
          display: 'flex', flexDirection: 'column',
          alignItems: 'center',
          gap: 28,
          padding: '0 60px',
        }}
      >
        {/* Conventional row */}
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

        {/* but */}
        <div
          style={{
            opacity: butOpacity,
            color: COLORS.translationConvText,
            fontSize: 56,
            fontStyle: 'italic',
            margin: '4px 0',
          }}
        >
          but
        </div>

        {/* Hidden row */}
        <RevealRow
          label={slide.hiddenLabel}
          text={slide.hiddenText}
          bgColor={COLORS.translationAccentSoft}
          labelColor={COLORS.translationAccent}
          textColor={COLORS.text}
          textSize={hiddenFontSize}
          opacity={hiddenOpacity}
          translateY={hiddenTranslateY}
          scale={hiddenScale}
        />

        {/* Tagline */}
        {slide.tagline && (
          <div
            style={{
              marginTop: 20,
              opacity: taglineOpacity,
              fontSize: 42,
              color: COLORS.translationAccentDeep,
              fontStyle: 'italic',
              textAlign: 'center',
              maxWidth: 900,
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

// One side of the reveal — label pill on top, gloss text below.
// No Arabic prop now — the big artifact lives in the upper layer
// and stays visible (dimmed) as the contrast rows land.
function RevealRow({
  label, text,
  bgColor, labelColor, textColor,
  textSize,
  opacity, translateY, scale,
}: {
  label: string;
  text: string;
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
        gap: 18, width: '100%', maxWidth: 960,
      }}
    >
      <div
        style={{
          background: bgColor,
          padding: '16px 36px',
          borderRadius: 999,
          color: labelColor,
          // Bumped 28 → 38. The label pills ("MOST TRANSLATIONS
          // SAY" / "THE ARABIC ACTUALLY SAYS") were the most
          // anaemic English on the slide at the previous size —
          // operator screenshot showed them dwarfed by the body
          // text. Pill padding bumped to match.
          fontSize: 38,
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
          maxWidth: 940,
          fontWeight: 500,
        }}
      >
        {wrapArabicRuns(text)}
      </div>
    </div>
  );
}
