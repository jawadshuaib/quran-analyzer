#!/usr/bin/env node
// Programmatic Remotion render entry point.
//
// Usage:
//   node scripts/render.mjs --payload <path> --out <path> [--concurrency N]
//
// Reads a JSON payload (validated against src/types.ts schema),
// bundles src/Root.tsx, and writes an MP4 to --out. Stdout is a
// single line of JSON so backend Python can json.loads(...) it
// directly. Stderr carries Remotion's progress logs.
//
// Backend integration shape (Python pseudocode):
//   proc = subprocess.run([
//     "node", "scripts/render.mjs",
//     "--payload", payload_path,
//     "--out",     output_path,
//   ], capture_output=True, text=True, cwd=RENDERER_DIR)
//   result = json.loads(proc.stdout)  # { ok, mp4_path, durationFrames, fps }

import { bundle } from '@remotion/bundler';
import {
  renderMedia,
  selectComposition,
  ensureBrowser,
} from '@remotion/renderer';
import { readFileSync, writeFileSync, mkdirSync, existsSync, copyFileSync } from 'node:fs';
import { dirname, resolve, isAbsolute, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import { prepareNarration } from './narration.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const RENDERER_ROOT = resolve(__dirname, '..');
const ENTRY_POINT = resolve(RENDERER_ROOT, 'src', 'Root.tsx');
const PUBLIC_DIR = resolve(RENDERER_ROOT, 'public');

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next && !next.startsWith('--')) {
        args[key] = next;
        i++;
      } else {
        args[key] = true;
      }
    }
  }
  return args;
}

function fatal(msg, extra) {
  // Single-line JSON on stdout so the caller can parse it. The
  // human-readable error stays on stderr.
  console.error(`[render.mjs] ERROR: ${msg}`);
  if (extra) console.error(extra);
  process.stdout.write(JSON.stringify({ ok: false, error: msg }) + '\n');
  process.exit(1);
}

const args = parseArgs(process.argv);
if (!args.payload) fatal('Missing --payload <path-to-json>');
if (!args.out) fatal('Missing --out <path-to-mp4>');

const payloadPath = isAbsolute(args.payload)
  ? args.payload
  : resolve(process.cwd(), args.payload);
const outPath = isAbsolute(args.out)
  ? args.out
  : resolve(process.cwd(), args.out);

if (!existsSync(payloadPath)) {
  fatal(`Payload file not found: ${payloadPath}`);
}

let payload;
try {
  payload = JSON.parse(readFileSync(payloadPath, 'utf8'));
} catch (e) {
  fatal(`Failed to parse payload JSON: ${e.message}`);
}

if (!Array.isArray(payload?.slides) || payload.slides.length === 0) {
  fatal('Payload must contain a non-empty slides[] array');
}

// Run narration prep BEFORE bundling so audio files exist in
// public/ when Remotion serves them. Cache hits are free; cache
// misses hit the ElevenLabs API. Slide durations are bumped to
// match audio length where audio is longer than the visual dwell.
//
// Mutates the input file in place so the studio (which imports
// sample-payload.json directly) picks up the same karaoke data.
console.error('[render.mjs] Preparing narration…');
payload = await prepareNarration(payload);
writeFileSync(payloadPath, JSON.stringify(payload, null, 2) + '\n');
console.error(`[render.mjs] Updated payload in place → ${basename(payloadPath)}`);

// If audio is referenced, ensure it lives in public/. Caller can
// either drop it in there beforehand or pass --audio <path> and
// we'll copy it. Filenames clash deterministically by source name,
// so two simultaneous renders should use unique audio filenames.
if (args.audio) {
  const src = isAbsolute(args.audio) ? args.audio : resolve(process.cwd(), args.audio);
  if (!existsSync(src)) fatal(`Audio file not found: ${src}`);
  if (!existsSync(PUBLIC_DIR)) mkdirSync(PUBLIC_DIR, { recursive: true });
  const target = resolve(PUBLIC_DIR, basename(src));
  copyFileSync(src, target);
  payload.audioFile = basename(src);
  console.error(`[render.mjs] Staged audio → public/${basename(src)}`);
}

mkdirSync(dirname(outPath), { recursive: true });

console.error('[render.mjs] Ensuring headless Chromium…');
await ensureBrowser();

console.error('[render.mjs] Bundling…');
const bundleLocation = await bundle({
  entryPoint: ENTRY_POINT,
  publicPath: '/',
});

console.error('[render.mjs] Selecting composition…');
const composition = await selectComposition({
  serveUrl: bundleLocation,
  id: 'word-detail',
  inputProps: { payload },
});

console.error(
  `[render.mjs] Rendering ${composition.durationInFrames} frames at ` +
    `${composition.fps}fps → ${outPath}`,
);

const concurrency = args.concurrency
  ? parseInt(args.concurrency, 10)
  : null;

await renderMedia({
  composition,
  serveUrl: bundleLocation,
  codec: 'h264',
  outputLocation: outPath,
  inputProps: { payload },
  concurrency,
  // jpeg keeps render fast; we don't need transparency for these
  // slides. CRF 18 is visually lossless for the kind of flat-color
  // typography content these slides produce.
  imageFormat: 'jpeg',
  crf: 18,
  onProgress: ({ progress }) => {
    if (progress > 0 && progress < 1) {
      process.stderr.write(`\r[render.mjs] ${Math.round(progress * 100)}%   `);
    }
  },
});
process.stderr.write('\n');

const result = {
  ok: true,
  mp4_path: outPath,
  durationFrames: composition.durationInFrames,
  fps: composition.fps,
  width: composition.width,
  height: composition.height,
  videoId: payload.videoId ?? null,
};
process.stdout.write(JSON.stringify(result) + '\n');
