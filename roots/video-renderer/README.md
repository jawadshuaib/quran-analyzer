# al-nuqta video renderer (Remotion experiment)

Standalone Remotion project that renders word-detail Shorts as
React components with frame-driven animation. Self-contained: its
own `node_modules`, no shared deps with the main backend or
frontend. Generates ElevenLabs TTS narration with character-level
timestamps and overlays karaoke captions synchronized to the audio.

## Architecture

```
roots/video-renderer/
├── src/
│   ├── Root.tsx                       Remotion entry — registers the composition
│   ├── compositions/
│   │   └── WordDetail.tsx             Sequences slides; layers per-slide audio + karaoke
│   ├── slides/
│   │   ├── shared.ts                  Design tokens
│   │   ├── RootPage.tsx               Slide A: large root letters + meaning
│   │   ├── VerseFlowPage.tsx          Slide B: flowing verse with sweep highlight
│   │   ├── WordToWordPage.tsx         Slide C: word grid with post-land pulse
│   │   ├── OutroPage.tsx              Slide D: al-nuqta brand splash
│   │   └── KaraokeOverlay.tsx         Bottom-anchored caption synced to audio
│   └── types.ts                       Zod schema (slides + narration)
├── scripts/
│   ├── narration.mjs                  ElevenLabs TTS + sha256 cache
│   └── render.mjs                     Programmatic render entry
├── audio-cache/                       Gitignored. mp3 + alignment, keyed by hash
├── public/                            Audio files served by Remotion at render time
├── sample-payload.json                Smoke-test payload (mutated by narration prep)
├── .env.example                       Copy to .env, fill in API key
├── package.json                       Independent from main app
├── tsconfig.json
└── remotion.config.ts                 Codec / FPS / concurrency knobs
```

## Quick start

```bash
cd roots/video-renderer
npm install
npx remotion browser ensure        # one-time: install headless Chromium
cp .env.example .env                # fill in ELEVENLABS_API_KEY + voice id
```

Then either preview in the studio (free):

```bash
npm run prepare-narration          # one-time API call (~$0.02), audio cached
npm run studio                     # opens localhost:3000
```

…or render an MP4 end-to-end:

```bash
npm run render:sample              # → out/sample.mp4
```

## How narration works

Each slide can carry a `narration: { text }` block. Running
`npm run prepare-narration` (or `npm run render:sample`) calls
ElevenLabs's `/with-timestamps` endpoint to:

1. Generate the TTS mp3.
2. Get character-level timing data (when each character is spoken).

Both are stored in `audio-cache/<sha256-hash>.{mp3,json}` and
copied into `public/` so Remotion can serve them. The hash is
keyed on `(voice_id, model_id, text)` — change any of those and
the cache invalidates for that slide; everything else stays cached.

The renderer mutates `sample-payload.json` in place to add
`audioFile`, `alignment`, and `durationSec` to each narration
block. The alignment data is what drives the karaoke overlay's
per-word highlight tracking. (The alignment data is bulky in JSON
but small in absolute terms — ~5 KB per slide. Whether you commit
it is a stylistic call: committing makes builds reproducible
without an API key, but increases the diff noise on script edits.)

When the slide's narration runs longer than its visual `durationSec`,
the prep step bumps `durationSec` up so the audio never gets cut
mid-word at the slide boundary. A 0.4s tail buffer is added.

## Karaoke overlay

`KaraokeOverlay.tsx` renders a bottom-anchored caption with three
states per word:

- **Future** (35% opacity, white): coming up
- **Current** (full opacity, soft gold, scaled 1.06): being spoken now
- **Past** (full opacity, white, semibold): already said

The overlay sits inside a subtle dark gradient so white text reads
clearly on light backgrounds (root page, verse cards) without
overpowering them.

When `narration.displayText` is set, the caption shows that text
instead of `narration.text`. Useful when the TTS input uses
phonetic spellings ("noon-zay-lam") but you want the caption to
show proper transliteration ("nūn-zāy-lām") or the Arabic letters
themselves. The two are word-aligned positionally — accurate when
word counts match.

## Payload schema

See `src/types.ts`. Discriminated union of slide types:

- `'root'` — root page with Arabic letters + meaning
- `'verse-flow'` — full RTL verse with target word highlighted (sweep)
- `'word-to-word'` — grid breakdown with pulse on highlighted cell
- `'outro'` — al-nuqta brand splash

Add a new slide type by:

1. Adding a variant to the `Slide` zod union in `types.ts`
2. Creating `src/slides/<NewSlide>Page.tsx`
3. Adding a `case` to `SlideRenderer` in `compositions/WordDetail.tsx`

The exhaustiveness check in `SlideRenderer` will compile-error
until you wire the new variant in.

## Backend integration (future phase)

Backend Python invokes `render.mjs` via `subprocess`:

```python
import json, subprocess, tempfile
RENDERER_DIR = "roots/video-renderer"

def render_word_detail(payload: dict, output_path: str) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        payload_path = f.name
    proc = subprocess.run([
        "node", "--env-file-if-exists=.env",
        "scripts/render.mjs",
        "--payload", payload_path,
        "--out", output_path,
    ], cwd=RENDERER_DIR, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"render failed: {proc.stderr}")
    return json.loads(proc.stdout.strip().splitlines()[-1])
```

Wired up properly, a new "Visual word-detail" pipeline can build
the payload from existing `ai_word_meanings` + verse data, populate
`narration.text` per slide from a Claude-generated script, and call
the renderer. The audio cache means re-renders of the same script
are free.

## Gotchas

- **First render needs Chromium**: `npx remotion browser ensure`
  once per machine. CI must do this before `render.mjs`.
- **Don't share `node_modules`**: this project pins its own deps so
  the main app's React build isn't affected.
- **Fonts via `@remotion/google-fonts`**: CSS `@import` doesn't
  render reliably in headless Chromium; we load Amiri in `Root.tsx`
  so it's guaranteed available.
- **ElevenLabs cost**: ~$0.02 per slide first time (then cached
  forever). The full 4-slide demo costs about $0.08 to prep.
- **`.env` is gitignored**: don't commit your API key. Use
  `.env.example` as the template.
