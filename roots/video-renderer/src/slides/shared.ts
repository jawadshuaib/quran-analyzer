// Design tokens — single source of truth for colors, fonts, sizes
// used across all slides. Mirrors the values from the user-supplied
// HTML mockups (A.html / B.html / C.html) so the rendered video
// matches the design intent.

export const COLORS = {
  pageBg: '#F4F2EA',     // root-page bg (cream-warm)
  appBg: '#E9E7DF',      // verse-card surrounding bg
  cardBg: '#FBFAF5',     // verse card body
  text: '#1A1A1A',       // primary
  textSoft: '#2A2A2A',   // translation italic
  textMuted: '#9A9A9A',  // word-to-word English glosses
  highlight: '#FFF1A8',  // soft yellow highlight (matched word) — used as a BACKGROUND pill
  // Saturated gold for use as TEXT color (e.g. karaoke active word
  // over the dark caption gradient). The pale-yellow `highlight`
  // disappears as a foreground color; this one pops without
  // looking like a different design language. Matches the gold
  // the existing ffmpeg pipeline uses (&H0000D7FF in ASS notation).
  highlightText: '#FFD700',
  toggleOn: '#34C759',
  toggleOff: '#D9D9DD',
  hairline: '#ECEAE2',
  chev: '#B5B3AC',
  // Outro background — warm charcoal, matches the existing ffmpeg
  // pipeline outro so the channel's videos close consistently no
  // matter which renderer produced them.
  outroBg: '#2D2620',
  outroText: '#FFFFFF',
  outroTagline: 'rgba(255, 255, 255, 0.5)',
} as const;

// Vertical 1080x1920 to match the existing educational pipeline
// output. Long-form / 16:9 variants can come later.
export const VIDEO_WIDTH = 1080;
export const VIDEO_HEIGHT = 1920;
export const FPS = 30;

// Slide-entrance animation — eases the slide in over 18 frames
// (~600ms at 30fps). Slow enough to feel intentional, fast enough
// not to eat the dwell time.
export const ENTRY_FRAMES = 18;

// System font stack matches the mockups (.SF Pro on macOS, Segoe on
// Windows). Remotion ships fonts via @remotion/google-fonts but the
// mockups use system fonts for the Latin text — sticking with that
// keeps the rendered video visually identical to the design source.
export const SYSTEM_FONT =
  '-apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", system-ui, sans-serif';

// Loaded via @remotion/google-fonts in Root.tsx for reliable
// headless-Chromium rendering (CSS @import isn't reliable per the
// Remotion docs).
export const ARABIC_FONT = '"Scheherazade New", Amiri, "Traditional Arabic", serif';
