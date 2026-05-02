# al-nuqta video renderer (Remotion experiment)

Standalone Remotion project that renders word-detail Shorts as
React components instead of ffmpeg + ASS overlays. Self-contained:
its own `node_modules`, no shared deps with the main backend or
frontend.

## Why this exists

The current educational pipeline composes videos with ffmpeg + ASS
subtitle layers. That works but the visual language is tightly
coupled to ffmpeg's text rendering and there's nowhere to express
animation fluently. This project lets us prototype richer per-slide
designs (RootPage, VerseFlowPage, WordToWordPage) using ordinary
React components with frame-driven animation, in 1080×1920 vertical
format that drops straight into the existing YouTube Shorts upload
flow.

The mockups under `src/slides/` are direct adaptations of the
designer-supplied HTML files (`A.html` / `B.html` / `C.html`),
restyled to fill a vertical 1080×1920 canvas.

## Architecture

```
roots/video-renderer/
├── src/
│   ├── Root.tsx                       Remotion entry — registers the composition
│   ├── compositions/
│   │   └── WordDetail.tsx             Sequences slides; overlays optional audio
│   ├── slides/
│   │   ├── shared.ts                  Design tokens (colors, fonts, sizes)
│   │   ├── RootPage.tsx               Slide A: large root letters + meaning
│   │   ├── VerseFlowPage.tsx          Slide B: flowing verse with highlight
│   │   └── WordToWordPage.tsx         Slide C: word-by-word grid breakdown
│   └── types.ts                       Zod schema for the JSON payload
├── scripts/
│   └── render.mjs                     Programmatic render entry (subprocess target)
├── public/                            Audio files referenced by slides
├── sample-payload.json                Smoke-test payload
├── package.json                       Independent from main app
├── tsconfig.json
└── remotion.config.ts                 Codec / FPS / concurrency knobs
```

## Quick start

```bash
cd roots/video-renderer
npm install
npx remotion browser ensure        # one-time: install headless Chromium
npm run studio                     # launches the Remotion studio at localhost:3000
```

The studio is the iteration loop — edit a slide component, see it
update live with the default payload from `Root.tsx`.

## Render an MP4 from a payload

```bash
npm run render:sample              # uses sample-payload.json → out/sample.mp4
# or, manually:
node scripts/render.mjs --payload sample-payload.json --out out/test.mp4
```

To attach narration audio:

```bash
node scripts/render.mjs \
  --payload sample-payload.json \
  --audio /tmp/narration.mp3 \
  --out out/test.mp4
```

`--audio` copies the file into `public/` and rewrites the payload's
`audioFile` field; the video duration extends to cover the audio.

## Payload schema

See `src/types.ts`. A payload is `{ slides: Slide[], audioFile?,
videoId?, title? }` where each slide has a discriminated `type`
(`'root'`, `'verse-flow'`, `'word-to-word'`) and per-type props.
Add a new slide kind by:

1. Adding a variant to the `Slide` zod union in `types.ts`
2. Creating `src/slides/<NewSlide>Page.tsx`
3. Adding a `case` to `SlideRenderer` in `compositions/WordDetail.tsx`

The exhaustiveness check in `SlideRenderer` will compile-error
until you wire the new variant in, so you can't ship a partial
implementation by accident.

## Backend integration (next phase)

Backend Python invokes `render.mjs` via `subprocess`:

```python
import json, subprocess, tempfile
RENDERER_DIR = "roots/video-renderer"

def render_word_detail(payload: dict, output_path: str) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        payload_path = f.name
    proc = subprocess.run([
        "node", "scripts/render.mjs",
        "--payload", payload_path,
        "--out", output_path,
    ], cwd=RENDERER_DIR, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"render failed: {proc.stderr}")
    # Renderer writes a single JSON line to stdout
    return json.loads(proc.stdout.strip().splitlines()[-1])
```

Wired up properly, a new "Visual word-detail" pipeline can build the
payload from existing `ai_word_meanings` + verse data and call the
renderer instead of the ffmpeg path.

## Gotchas (per Remotion docs)

- **First render needs Chromium**: `npx remotion browser ensure` once
  per machine. CI must do this before `render.mjs`.
- **Don't share `node_modules`**: this project pins its own deps so
  the main app's React build isn't affected.
- **Fonts via `@remotion/google-fonts`**: CSS `@import` doesn't
  render reliably in headless Chromium; we load Scheherazade and
  Amiri in `Root.tsx` so they're guaranteed to be available.
- **Long videos = slow**: the `concurrency` knob in `remotion.config.ts`
  parallelizes per-frame rendering. Bumping it past 4 mostly thrashes
  on a non-server machine.
