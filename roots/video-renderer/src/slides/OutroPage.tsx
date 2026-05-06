import { AbsoluteFill, useCurrentFrame, interpolate, Audio, staticFile } from 'remotion';
import type { OutroSlideT } from '../types';
import { COLORS, SYSTEM_FONT } from './shared';

// Slide D — al-nuqta brand splash.
// Mirrors the existing ffmpeg pipeline outro: warm-charcoal bg,
// site name in big white type centered, tagline in muted white
// below. Site name fades in fast (~250ms / 8 frames), tagline
// follows ~12 frames behind so the eye lands on the site name
// first then drifts down. Holds the rest of the slide static.
export function OutroPage({ slide }: { slide: OutroSlideT }) {
  const frame = useCurrentFrame();

  const siteOpacity = interpolate(frame, [0, 8], [0, 1], { extrapolateRight: 'clamp' });
  const siteTranslateY = interpolate(frame, [0, 16], [8, 0], { extrapolateRight: 'clamp' });

  const taglineOpacity = interpolate(frame, [12, 28], [0, 1], { extrapolateRight: 'clamp' });
  const taglineTranslateY = interpolate(frame, [12, 28], [6, 0], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.outroBg }}>
      {/* Optional sound bite played over the splash. The Python
          orchestrator copies the pipeline's outro_audio_filename
          into public/ before invoking the renderer; we just play
          it here. Layers cleanly with any narration audio (from
          the slide's narration block) — Remotion mixes Audio
          components by default. */}
      {slide.outroAudioFile && (
        <Audio src={staticFile(slide.outroAudioFile)} />
      )}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '0 80px',
          textAlign: 'center',
        }}
      >
        <div
          style={{
            fontFamily: SYSTEM_FONT,
            // Was 130px — wrapped to two lines on some renderings
            // because the dot in "al-nuqta.com" is a soft line break
            // point. 100px fits comfortably on one line at 1080-wide
            // and still reads as the headline element of the splash.
            fontSize: 100,
            fontWeight: 700,
            color: COLORS.outroText,
            letterSpacing: '-0.02em',
            opacity: siteOpacity,
            transform: `translateY(${siteTranslateY}px)`,
            marginBottom: 36,
            // Belt-and-braces: even at 100px, force single line so
            // the dot or hyphen never breaks the brand wordmark.
            whiteSpace: 'nowrap',
          }}
        >
          {slide.siteName}
        </div>
        <div
          style={{
            fontFamily: SYSTEM_FONT,
            fontSize: 44,
            fontWeight: 400,
            color: COLORS.outroTagline,
            letterSpacing: '0.005em',
            opacity: taglineOpacity,
            transform: `translateY(${taglineTranslateY}px)`,
            maxWidth: 920,
            lineHeight: 1.4,
          }}
        >
          {slide.tagline}
        </div>
      </div>
    </AbsoluteFill>
  );
}
