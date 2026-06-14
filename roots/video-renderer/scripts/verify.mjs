#!/usr/bin/env node
// Renderer self-report — Gate B, Layer 2.
//
// Given a payload JSON, report (per verse-flow slide) EXACTLY which
// words the renderer would paint and whether the English phrase will
// be found, using the SAME ./src/slides/highlight.mjs resolver the
// React component uses. This closes the gap between "what the Python
// match-gate thinks will render" and "what actually renders": the
// Python side diffs its intent against this report.
//
// No Remotion, no Chromium, no network — pure computation, so it is
// cheap to run on every video in the gate. Prints one line of JSON on
// stdout: { ok, slides: [...] }. On error: { ok:false, error }.
//
// Usage:  node scripts/verify.mjs --payload <path-to-json>

import { readFileSync } from 'node:fs';
import { resolve, dirname, isAbsolute } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describeVerseFlowHighlight } from '../src/slides/highlight.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

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

function fail(msg) {
  process.stdout.write(JSON.stringify({ ok: false, error: msg }) + '\n');
  process.exit(1);
}

const args = parseArgs(process.argv);
if (!args.payload) fail('Missing --payload <path-to-json>');

const payloadPath = isAbsolute(args.payload)
  ? args.payload
  : resolve(process.cwd(), args.payload);

let payload;
try {
  payload = JSON.parse(readFileSync(payloadPath, 'utf8'));
} catch (e) {
  fail(`Failed to read/parse payload: ${e.message}`);
}

if (!Array.isArray(payload?.slides)) fail('Payload has no slides[]');

const slides = payload.slides.map((slide, index) => {
  const base = { index, type: slide.type };
  if (slide.type !== 'verse-flow') {
    return { ...base, highlighted: false };
  }
  const d = describeVerseFlowHighlight(slide);
  return {
    ...base,
    highlighted: true,
    surah: slide.surah ?? null,
    ayah: slide.ayah ?? null,
    wordCount: d.wordCount,
    paintedIndices: d.paintedIndices,
    paintedTokens: d.paintedTokens,
    outOfRangeIndices: d.outOfRangeIndices,
    englishRequested: !!(slide.highlightTranslationText && String(slide.highlightTranslationText).trim()),
    englishFound: d.englishFound,
    englishSpan: d.englishSpan,
  };
});

process.stdout.write(JSON.stringify({ ok: true, slides }) + '\n');
