// Narration helper — generates ElevenLabs TTS audio + character-
// level alignment for each slide that has a narration block, and
// caches the result by sha256 hash so re-runs are free.
//
// Cache layout:
//   audio-cache/<hash>.mp3        — the audio
//   audio-cache/<hash>.json       — { alignment, durationSec, voiceId, modelId, text }
//   public/<hash>.mp3             — copy used by Remotion at render time
//
// Hash key is sha256(voiceId + modelId + text). Changing the voice
// or the script invalidates the cache for that slide; everything
// else stays cached.

import { readFileSync, writeFileSync, mkdirSync, existsSync, copyFileSync } from 'node:fs';
import { resolve, dirname, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const RENDERER_ROOT = resolve(__dirname, '..');
const CACHE_DIR = resolve(RENDERER_ROOT, 'audio-cache');
const PUBLIC_DIR = resolve(RENDERER_ROOT, 'public');

const ELEVENLABS_BASE = 'https://api.elevenlabs.io';
const DEFAULT_MODEL = 'eleven_multilingual_v2';

function hashFor(voiceId, modelId, text) {
  return createHash('sha256')
    .update(voiceId + '|' + modelId + '|' + text)
    .digest('hex')
    .slice(0, 16);
}

function ensureDirs() {
  if (!existsSync(CACHE_DIR)) mkdirSync(CACHE_DIR, { recursive: true });
  if (!existsSync(PUBLIC_DIR)) mkdirSync(PUBLIC_DIR, { recursive: true });
}

// Hit ElevenLabs /with-timestamps endpoint. Returns { audioBuffer,
// alignment, durationSec }. Throws on non-2xx; caller decides how
// to surface the error.
async function callElevenLabs({ apiKey, voiceId, modelId, text }) {
  const url = `${ELEVENLABS_BASE}/v1/text-to-speech/${voiceId}/with-timestamps`;
  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      'xi-api-key': apiKey,
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({
      text,
      model_id: modelId,
      voice_settings: {
        // Match the existing pipeline's defaults — stable enough to
        // not waver on long sentences, expressive enough to not
        // sound like a flat reader.
        stability: 0.5,
        similarity_boost: 0.75,
      },
    }),
  });
  if (!resp.ok) {
    const body = await resp.text().catch(() => '');
    throw new Error(`ElevenLabs ${resp.status}: ${body.slice(0, 500)}`);
  }
  const json = await resp.json();
  if (!json.audio_base64) throw new Error('ElevenLabs response missing audio_base64');
  if (!json.alignment) throw new Error('ElevenLabs response missing alignment');

  const audioBuffer = Buffer.from(json.audio_base64, 'base64');
  // ElevenLabs alignment shape: { characters, character_start_times_seconds, character_end_times_seconds }
  const a = json.alignment;
  const alignment = {
    characters: a.characters,
    starts: a.character_start_times_seconds,
    ends: a.character_end_times_seconds,
  };
  const durationSec = alignment.ends.length
    ? alignment.ends[alignment.ends.length - 1]
    : 0;
  return { audioBuffer, alignment, durationSec };
}

// Generate (or load from cache) one slide's narration. Returns the
// patch object that should be merged into slide.narration.
async function generateOne({ apiKey, voiceId, modelId, text }) {
  ensureDirs();
  const hash = hashFor(voiceId, modelId, text);
  const audioPath = resolve(CACHE_DIR, `${hash}.mp3`);
  const metaPath = resolve(CACHE_DIR, `${hash}.json`);
  const publicPath = resolve(PUBLIC_DIR, `${hash}.mp3`);

  if (existsSync(audioPath) && existsSync(metaPath)) {
    const meta = JSON.parse(readFileSync(metaPath, 'utf8'));
    // Stage to public/ in case it's been cleaned out.
    if (!existsSync(publicPath)) copyFileSync(audioPath, publicPath);
    return {
      audioFile: `${hash}.mp3`,
      alignment: meta.alignment,
      durationSec: meta.durationSec,
      cached: true,
    };
  }

  // Cache miss — call the API.
  if (!apiKey) {
    throw new Error(
      'ELEVENLABS_API_KEY missing and audio not cached. ' +
      'Set it in .env or your shell, or pre-populate audio-cache/.',
    );
  }
  console.error(`[narration] Generating audio (${hash}) — text: "${text.slice(0, 60)}…"`);
  const { audioBuffer, alignment, durationSec } = await callElevenLabs({
    apiKey, voiceId, modelId, text,
  });

  writeFileSync(audioPath, audioBuffer);
  writeFileSync(
    metaPath,
    JSON.stringify({ alignment, durationSec, voiceId, modelId, text }, null, 2),
  );
  copyFileSync(audioPath, publicPath);

  return {
    audioFile: `${hash}.mp3`,
    alignment,
    durationSec,
    cached: false,
  };
}

// Walk a payload, generate audio for every slide that has a
// narration.text but no alignment yet, return the enriched payload.
// Mutates a copy — original is not touched.
//
// This function is the public entry point that scripts/render.mjs
// calls before bundling. It's designed to be idempotent: if every
// slide is already cached, it does no network work.
export async function prepareNarration(payload, env = process.env) {
  const apiKey = env.ELEVENLABS_API_KEY || '';
  const voiceId = env.ELEVENLABS_VOICE_ID || '';
  const modelId = env.ELEVENLABS_MODEL_ID || DEFAULT_MODEL;

  if (!voiceId) {
    console.error(
      '[narration] ELEVENLABS_VOICE_ID not set — skipping narration. ' +
      'Slides will render silently. Set it in .env to enable.',
    );
    return payload;
  }

  const enriched = JSON.parse(JSON.stringify(payload));
  let cacheHits = 0;
  let cacheMisses = 0;

  for (let i = 0; i < enriched.slides.length; i++) {
    const slide = enriched.slides[i];
    const narr = slide.narration;
    if (!narr || !narr.text) continue;

    // "Already prepared" check: alignment + audio file present AND
    // the audio file hash matches the current text. This catches
    // both the unchanged case (skip) and the text-was-edited case
    // (regenerate, since the cached file is for a stale hash).
    if (narr.audioFile && narr.alignment && narr.durationSec) {
      const expectedHash = hashFor(voiceId, modelId, narr.text);
      const expectedFile = `${expectedHash}.mp3`;
      const stagedAt = resolve(PUBLIC_DIR, narr.audioFile);
      if (narr.audioFile === expectedFile && existsSync(stagedAt)) continue;
      // Hash mismatch (text changed) or file missing (cache cleared)
      // — fall through and regenerate.
    }

    try {
      const result = await generateOne({
        apiKey, voiceId, modelId, text: narr.text,
      });
      slide.narration = {
        ...narr,
        audioFile: result.audioFile,
        alignment: result.alignment,
        durationSec: result.durationSec,
      };
      // Slide must be at least as long as its narration plus a
      // 0.4s tail buffer so the audio doesn't get cut mid-word by
      // the slide transition. Visual dwell wins if it's already
      // longer.
      const audioDwell = result.durationSec + 0.4;
      slide.durationSec = Math.max(slide.durationSec || 0, audioDwell);
      result.cached ? cacheHits++ : cacheMisses++;
    } catch (e) {
      console.error(`[narration] Slide ${i} (${slide.type}) FAILED: ${e.message}`);
      console.error('[narration] Continuing without narration for this slide.');
    }
  }

  console.error(
    `[narration] Done — ${cacheHits} cached, ${cacheMisses} generated, ` +
    `${enriched.slides.filter((s) => s.narration?.audioFile).length} ` +
    `slides with audio.`,
  );
  return enriched;
}

// Standalone CLI entry: `node scripts/narration.mjs <payload>` mutates
// the payload in place to add narration.audioFile + .alignment +
// .durationSec to every slide that has narration.text. Audio files
// land in audio-cache/ (the canonical store) and public/ (where
// Remotion's staticFile() can find them). Used by
// `npm run prepare-narration`.
//
// Mutating in place lets the studio (which always imports
// sample-payload.json) pick up the karaoke data without a second
// loader. The alignment data is small (~5KB/slide); whether you
// commit it is up to you — committing makes renders reproducible
// for collaborators without an ElevenLabs key, but the audio files
// themselves are gitignored so a fresh clone still re-pays the
// (cache-friendly) API call once.
const isCli = import.meta.url === `file://${process.argv[1]}`;
if (isCli) {
  const inputPath = process.argv[2];
  if (!inputPath) {
    console.error('Usage: node scripts/narration.mjs <payload.json>');
    process.exit(1);
  }
  const fullPath = resolve(process.cwd(), inputPath);
  const raw = JSON.parse(readFileSync(fullPath, 'utf8'));
  const enriched = await prepareNarration(raw);
  writeFileSync(fullPath, JSON.stringify(enriched, null, 2) + '\n');
  console.error(`[narration] Updated payload in place → ${basename(fullPath)}`);
}
