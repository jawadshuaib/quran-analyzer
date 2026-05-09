import { AbsoluteFill, Img, useCurrentFrame, useVideoConfig, interpolate, Easing, Audio, staticFile } from 'remotion';
import type { OutroSlideT } from '../types';

/**
 * Outro splash — Mushaf design.
 *
 * Replaces the earlier warm-charcoal site-name splash. Operator
 * brought in a marketing design (03_Mushaf Page.html) and asked us
 * to use it for grammar-insights and word-origins outros. The card
 * shows a blurred photograph of an open Mushaf as the background,
 * a serif headline ("Learn Qur'an every day."), and a yellow
 * SUBSCRIBE pill with a bell glyph as the CTA.
 *
 * Animation choreography (5s @ 30fps = 150 frames):
 *   0–8     Background fades in from black.
 *   8–60    Subtle Ken Burns: bg scales 1.04 → 1.00 over the
 *           full slide, drifting the eye into stillness.
 *   12–32   Headline fades in with a 12px translate-y, opacity
 *           and y eased out.
 *   40–58   Subscribe pill fades in with a tiny scale bounce
 *           (0.96 → 1.00) so it lands as the call-to-action,
 *           not part of the headline.
 *   45–end  Bell glyph in the pill jingles every ~30 frames
 *           — small rotation, never beyond ±10°, to draw the
 *           eye one last time before the slide ends.
 *
 * The original outro audio bite ("for more details, see the
 * description") still mounts when present. siteName + tagline on
 * OutroSlideT are ignored now — kept on the schema for backward
 * compatibility.
 */
export function OutroPage({ slide }: { slide: OutroSlideT }) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Background fade-in + Ken Burns scale.
  const bgOpacity = interpolate(frame, [0, 8], [0, 1], { extrapolateRight: 'clamp' });
  const bgScale = interpolate(frame, [8, 60], [1.04, 1.0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.ease),
  });

  // Headline — fade + 12px translateY.
  const titleOpacity = interpolate(frame, [12, 32], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.ease),
  });
  const titleTranslateY = interpolate(frame, [12, 32], [12, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.ease),
  });

  // Subscribe pill — fade + scale bounce.
  const ctaOpacity = interpolate(frame, [40, 58], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ctaScale = interpolate(frame, [40, 58], [0.96, 1.0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  // Bell jingle — small rotational pulse, 30-frame cycle, capped
  // at ±8°. Damped sine so it settles cleanly instead of looping.
  const bellAngle =
    frame > 45
      ? Math.sin((frame - 45) / 5) * 8 * Math.exp(-(frame - 45) / 90)
      : 0;

  // Map seconds-from-start so the (background) Ken Burns lasts the
  // full slide regardless of slide duration. Currently the slide is
  // 5s but the renderer occasionally extends it to fit narration
  // audio, and we want the zoom to feel consistent.
  void fps; // keep the hook for parity with other slides

  return (
    <AbsoluteFill style={{ overflow: 'hidden' }}>
      {/* Optional sound bite played over the splash. The Python
          orchestrator copies the pipeline's outro_audio_filename
          into public/ before invoking the renderer; we just play
          it here. Layers cleanly with any narration audio (from
          the slide's narration block) — Remotion mixes Audio
          components by default. */}
      {slide.outroAudioFile && (
        <Audio src={staticFile(slide.outroAudioFile)} />
      )}

      {/* Background photograph — blurred + Ken-Burns zoom. The
          Img tag lets Remotion pre-load the asset for headless
          render reliability. */}
      <div
        style={{
          position: 'absolute', inset: 0,
          opacity: bgOpacity,
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('mushaf-outro-bg.png')}
          style={{
            width: '100%', height: '100%',
            objectFit: 'cover',
            objectPosition: 'center center',
            filter: 'blur(2px) saturate(1.05)',
          }}
        />
        {/* Warm cream overlay so white text is unambiguously
            legible against the busy bg without flattening the
            photograph's depth. Vertical gradient: lighter at top
            and bottom, slightly darker in the middle band where
            the headline sits — counter-intuitive but it keeps the
            CTA pill clean against the bottom while the headline
            text reads against the slightly-darker center. */}
        <div
          style={{
            position: 'absolute', inset: 0,
            background:
              'linear-gradient(180deg, rgba(50, 35, 18, 0.18) 0%, rgba(50, 35, 18, 0.42) 50%, rgba(50, 35, 18, 0.22) 100%)',
          }}
        />
      </div>

      {/* Foreground card — headline + CTA, vertically split with
          large gap. Fixed inner max-width so the typography reflows
          cleanly on different aspect ratios should we ever render
          16:9 from the same composition. */}
      <div
        style={{
          position: 'absolute', inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '0 96px',
          textAlign: 'center',
          color: '#FFFFFF',
        }}
      >
        {/* Headline — Fraunces serif (loaded in Root.tsx). 132px on
            1080-wide gives roughly the proportional size the design
            mockup carries on its 270-wide canvas. */}
        <div
          style={{
            fontFamily: 'Fraunces, "Times New Roman", Georgia, serif',
            fontWeight: 600,
            fontSize: 132,
            lineHeight: 1.04,
            letterSpacing: '-0.01em',
            color: '#FFFFFF',
            opacity: titleOpacity,
            transform: `translateY(${titleTranslateY}px)`,
            // Subtle drop-shadow so the text never disappears into
            // the busiest patches of the Mushaf bg.
            textShadow:
              '0 2px 14px rgba(0,0,0,0.55), 0 0 32px rgba(0,0,0,0.25)',
            maxWidth: 880,
          }}
        >
          Learn Qur'an
          <br />
          every day.
        </div>

        {/* SUBSCRIBE pill. Yellow background, black text, bell
            glyph on the right with a tiny jingle animation. */}
        <div
          style={{
            marginTop: 96,
            opacity: ctaOpacity,
            transform: `scale(${ctaScale})`,
            transformOrigin: 'center center',
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 18,
              backgroundColor: '#FFD60A',
              color: '#0A0A0A',
              fontFamily:
                '-apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", system-ui, sans-serif',
              fontSize: 56,
              fontWeight: 800,
              letterSpacing: '0.06em',
              padding: '24px 56px',
              borderRadius: 999,
              boxShadow:
                '0 6px 24px rgba(0,0,0,0.35), 0 0 0 1px rgba(0,0,0,0.05)',
            }}
          >
            <span>SUBSCRIBE</span>
            <span
              style={{
                display: 'inline-block',
                transform: `rotate(${bellAngle}deg)`,
                transformOrigin: 'top center',
                fontSize: 56,
              }}
              aria-hidden
            >
              {/* Bell glyph rendered as inline SVG so it's identical
                  across rendering containers (system emoji fonts
                  drift wildly between macOS / Linux Chromium). */}
              <svg width="52" height="52" viewBox="0 0 24 24" fill="#0A0A0A">
                <path d="M12 2a1.5 1.5 0 0 1 1.5 1.5v.7a6 6 0 0 1 4.5 5.8v3l1.7 2.4A1 1 0 0 1 18.9 17H5.1a1 1 0 0 1-.8-1.6L6 13v-3a6 6 0 0 1 4.5-5.8v-.7A1.5 1.5 0 0 1 12 2zm-2.5 17h5a2.5 2.5 0 0 1-5 0z" />
              </svg>
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
}
