"""Generate mnemonic images for Quranic root words.

Two-phase pipeline:
  1. Cloud Ollama crafts a vivid, mnemonic FLUX image prompt from root data
  2. Hugging Face FLUX.1-schnell generates the image

Images are saved to data/mnemonic_images/{root_bw}.webp and the path is
stored in learning_curriculum.mnemonic_image_path.

Usage:
    python generate_mnemonic_images.py --root gfr          # single root
    python generate_mnemonic_images.py                      # all 50 roots
    python generate_mnemonic_images.py --dry-run            # preview prompts
    python generate_mnemonic_images.py --force --root gfr   # regenerate
    python generate_mnemonic_images.py --variants 3         # generate 3 images per root

Environment variables:
    OLLAMA_CLOUD_URL   Base URL for cloud Ollama (default: http://localhost:11434)
    OLLAMA_API_KEY     API key for cloud Ollama (if required)
    HF_API_TOKEN       Hugging Face API token (required for image generation)
"""

import argparse
import io
import json
import os
import sys
import time

import requests

from app import DB_PATH, get_db

# ── Configuration ──────────────────────────────────────────────────────────

OLLAMA_CLOUD_URL = os.environ.get("OLLAMA_CLOUD_URL", "http://localhost:11434")
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "minimax-m2.5:cloud")

HF_API_TOKEN = os.environ.get("HF_API_TOKEN", "")

# AI Horde — free distributed GPU network, anonymous key works
HORDE_BASE = "https://stablehorde.net/api/v2"
HORDE_KEY = os.environ.get("HORDE_API_KEY", "0000000000")  # anonymous key

# Consistent art style across all 50 root images
ART_STYLE = (
    "minimalist watercolor illustration, warm earth tones, contemplative mood, "
    "clean composition, no text, no Arabic script, no calligraphy, no people, "
    "no hands, no fingers, no human body parts, no faces, no infants, "
    "no depictions of prophets or divine figures"
)

IMAGE_DIR = os.path.join(os.path.dirname(__file__), "data", "mnemonic_images")

# ── System prompt for Ollama ────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You create ICONIC VISUAL MNEMONICS for Arabic root words.

THE GOAL: When a student thinks of this root, ONE unforgettable image should
flash in their mind. The image must be so vivid and specific that it burns into
memory — like a logo for the word.

WHAT MAKES A GREAT MNEMONIC IMAGE:
- ONE bold, iconic object that embodies the root's CONCRETE/PHYSICAL origin
- Visually striking — high contrast, clear silhouette, would work as a logo
- Instantly recognizable: a helmet, a key, a scale, a seed, a shield, a flame
- NOT a scene or story — just the object, powerful and centered
- NOT abstract, NOT vague (no "glowing light", no "vast landscape", no "mist")

EXAMPLE — غ ف ر (ghafara) = to forgive:
  Physical origin: to cover/protect (a helmet covers the head)
  Image: A single bronze helmet, centered, heroic angle
  Caption: "Helmet covers to protect. Forgiveness covers the sin. غَفَرَ"

PROCESS:
1. Find the root's CONCRETE physical origin (use the etymology/cognates provided)
2. Pick ONE iconic object that embodies it — something a child could draw
3. Write a short caption: physical meaning → Quranic meaning (one sentence max)

Return JSON:
{
  "image_prompt": "...",
  "caption": "..."
}

Rules for image_prompt (40-70 words — SHORTER is better for image generators):
1. ONE object, centered, bold composition — like a product photo or icon
2. Name the specific object, its material, color, and lighting
3. Keep it SIMPLE — fewer elements = better generated image
4. NO Arabic text, no calligraphy, no writing
5. NO people, hands, fingers, faces, human body parts, mouths, eyes, or infants
6. NO prophets, angels, or divine figures
7. End with the art style specification provided

Rules for caption (15-25 words max):
1. One sentence bridging physical origin → Quranic meaning
2. End with the root in Arabic
3. Be insightful, not encyclopedic — if the connection is obvious, keep it short
4. Only explain the bridge if it's genuinely non-obvious

Respond with ONLY the JSON object. No markdown fences, no explanation."""


def craft_image_prompt(root_bw: str, root_arabic: str, root_story: str, derivatives: list) -> tuple[str, str]:
    """Call cloud Ollama to craft a mnemonic image prompt + caption.

    Returns (image_prompt, caption).
    """
    # Build a brief summary of derivatives for context
    deriv_lines = []
    for d in derivatives[:8]:
        line = f"- {d['lemma_arabic']} ({d['meaning_gloss']})"
        deriv_lines.append(line)
    derivs_text = "\n".join(deriv_lines) if deriv_lines else "(no derivatives)"

    # Give Ollama the full story (up to 500 chars) for better understanding
    story_snippet = root_story[:500].rstrip() + ("..." if len(root_story) > 500 else "")

    user_prompt = f"""\
Arabic root: {root_arabic} (Buckwalter: {root_bw})

Root story (etymology, core meaning, and theology):
{story_snippet}

Key derivatives and their meanings:
{derivs_text}

YOUR TASK:
1. What is the ONE concrete object that captures this root's physical origin?
   (helmet, key, scale, seed, shield, rope, flame, path, seal, etc.)
2. Describe that object for an image generator — bold, centered, iconic.
3. Write a brief caption bridging physical → Quranic meaning.

Art style to append at the END of image_prompt:
"{ART_STYLE}"

Return the JSON object with "image_prompt" and "caption":"""

    url = f"{OLLAMA_CLOUD_URL.rstrip('/')}/api/chat"
    headers = {"Content-Type": "application/json"}
    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {"temperature": 0.5, "num_ctx": 4096},
    }

    print(f"    Crafting prompt via Ollama ({OLLAMA_MODEL})...", end="", flush=True)
    start = time.time()
    resp = requests.post(url, headers=headers, json=payload, timeout=180)
    resp.raise_for_status()
    elapsed = time.time() - start

    raw = resp.json().get("message", {}).get("content", "").strip()
    print(f" done ({elapsed:.1f}s)")

    # Parse JSON response — strip markdown fences if present
    cleaned = raw
    if "```" in cleaned:
        # Extract content between fences
        parts = cleaned.split("```")
        for part in parts[1:]:
            if "{" in part:
                cleaned = part.split("\n", 1)[-1] if part.startswith("json") else part
                break
    cleaned = cleaned.strip().rstrip("`")

    try:
        result = json.loads(cleaned)
        image_prompt = result.get("image_prompt", "").strip()
        caption = result.get("caption", "").strip()
    except json.JSONDecodeError:
        # Fallback: treat entire response as image prompt, generate generic caption
        print(f"    [WARN] Failed to parse JSON, using raw text as prompt")
        image_prompt = raw
        caption = ""

    if not caption:
        caption = f"Visual mnemonic for the root {root_arabic}"

    return image_prompt, caption


# ── Local SD-Turbo pipeline (lazy-loaded) ──────────────────────────────────

_local_pipe = None


def _get_local_pipe():
    """Lazy-load SD-Turbo on MPS (Apple Silicon) or CUDA, with float32 for MPS."""
    global _local_pipe
    if _local_pipe is not None:
        return _local_pipe

    import torch
    from diffusers import AutoPipelineForText2Image

    device = "mps" if torch.backends.mps.is_available() else (
        "cuda" if torch.cuda.is_available() else "cpu"
    )
    dtype = torch.float32 if device == "mps" else torch.float16

    print(f"    Loading SD-Turbo on {device} ({dtype})...", end="", flush=True)
    start = time.time()
    _local_pipe = AutoPipelineForText2Image.from_pretrained(
        "stabilityai/sd-turbo",
        torch_dtype=dtype,
    )
    _local_pipe = _local_pipe.to(device)
    _local_pipe.enable_attention_slicing()
    _local_pipe.set_progress_bar_config(disable=True)
    elapsed = time.time() - start
    print(f" ready ({elapsed:.1f}s)")
    return _local_pipe


def generate_image_local(prompt: str, variant: int = 0) -> bytes:
    """Generate image using local SD-Turbo (fast on Apple Silicon / CUDA)."""
    pipe = _get_local_pipe()

    print(f"    Generating locally (SD-Turbo)...", end="", flush=True)
    start = time.time()
    image = pipe(
        prompt,
        num_inference_steps=4,
        guidance_scale=0.0,
        width=512,
        height=512,
        generator=__import__("torch").Generator(pipe.device).manual_seed(42 + variant),
    ).images[0]
    elapsed = time.time() - start
    print(f" done ({elapsed:.1f}s)")

    buf = io.BytesIO()
    image.save(buf, "WEBP", quality=85)
    return buf.getvalue()


def generate_image_horde(prompt: str, variant: int = 0) -> bytes:
    """Fallback: generate via AI Horde (free, anonymous, slower)."""
    payload = {
        "prompt": prompt,
        "params": {
            "sampler_name": "k_euler",
            "width": 512,
            "height": 512,
            "steps": 20,
            "cfg_scale": 7,
            "n": 1,
            "seed": str(42 + variant),
        },
        "models": ["Deliberate"],
        "r2": True,
        "shared": False,
    }
    headers = {"apikey": HORDE_KEY, "Content-Type": "application/json"}

    print(f"    Submitting to AI Horde...", end="", flush=True)
    start = time.time()
    resp = requests.post(f"{HORDE_BASE}/generate/async", json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    job_id = resp.json()["id"]
    print(f" job {job_id[:8]}...")

    for i in range(180):
        time.sleep(5)
        check = requests.get(f"{HORDE_BASE}/generate/check/{job_id}", headers=headers, timeout=10)
        status = check.json()
        if status.get("done"):
            break
        if i % 6 == 0:
            wait = status.get("wait_time", "?")
            queue = status.get("queue_position", "?")
            print(f"    Waiting... ~{wait}s, queue position {queue}", flush=True)
    else:
        raise RuntimeError("AI Horde timed out after 15 minutes")

    result = requests.get(f"{HORDE_BASE}/generate/status/{job_id}", headers=headers, timeout=15)
    result.raise_for_status()
    generations = result.json().get("generations", [])
    if not generations:
        raise RuntimeError("AI Horde returned no generations")

    img_url = generations[0]["img"]
    elapsed = time.time() - start
    print(f"    Downloading image... (total {elapsed:.0f}s)", end="", flush=True)
    img_resp = requests.get(img_url, timeout=30)
    img_resp.raise_for_status()
    print(" done")
    return img_resp.content


def generate_image(prompt: str, variant: int = 0) -> bytes:
    """Generate image — local SD-Turbo first, AI Horde as fallback."""
    try:
        return generate_image_local(prompt, variant)
    except Exception as e:
        print(f"\n    Local generation failed ({e}), falling back to AI Horde...")
        return generate_image_horde(prompt, variant)


def save_webp(image_bytes: bytes, root_bw: str, variant: int = 0) -> str:
    """Save raw image bytes as WebP. Returns the saved file path."""
    try:
        from PIL import Image
    except ImportError:
        raise ImportError("Pillow is required: pip install Pillow")

    os.makedirs(IMAGE_DIR, exist_ok=True)

    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("RGB")
    img = img.resize((512, 512), Image.LANCZOS)

    suffix = f"_v{variant}" if variant > 0 else ""
    filename = f"{root_bw}{suffix}.webp"
    out_path = os.path.join(IMAGE_DIR, filename)
    img.save(out_path, "WEBP", quality=85)
    return out_path


def process_root(conn, root_bw: str, dry_run: bool, force: bool, variants: int) -> bool:
    """Process a single root. Returns True if processed, False if skipped."""
    row = conn.execute(
        "SELECT root_arabic, root_story, mnemonic_image_path "
        "FROM learning_curriculum WHERE root_buckwalter = ?",
        (root_bw,),
    ).fetchone()

    if not row:
        print(f"  [SKIP] {root_bw} — not in curriculum")
        return False

    if row["mnemonic_image_path"] and not force:
        print(f"  [SKIP] {root_bw} — already has image at {row['mnemonic_image_path']}")
        return False

    root_arabic = row["root_arabic"]
    root_story = row["root_story"] or ""

    # Fetch derivatives for context
    derivs = conn.execute(
        "SELECT lemma_arabic, meaning_gloss FROM learning_derivatives "
        "WHERE root_buckwalter = ? ORDER BY display_order",
        (root_bw,),
    ).fetchall()

    print(f"  Processing {root_arabic} ({root_bw}):")

    # Phase 1: Craft image prompt + caption via Ollama
    image_prompt, caption = craft_image_prompt(root_bw, root_arabic, root_story, [dict(d) for d in derivs])

    print(f"    Prompt: {image_prompt[:120]}...")
    print(f"    Caption: {caption}")

    if dry_run:
        print(f"    [DRY RUN] Would generate {variants} image(s)")
        return True

    # Phase 2: Generate image(s) via AI Horde
    saved_paths = []
    for v in range(variants):
        image_bytes = generate_image(image_prompt, variant=v)
        out_path = save_webp(image_bytes, root_bw, variant=v)
        saved_paths.append(out_path)
        print(f"    Saved: {out_path}")

    # Store path + caption in DB
    rel_path = os.path.relpath(saved_paths[0], os.path.dirname(__file__))
    conn.execute(
        "UPDATE learning_curriculum SET mnemonic_image_path = ?, mnemonic_caption = ? "
        "WHERE root_buckwalter = ?",
        (rel_path, caption, root_bw),
    )
    conn.commit()
    print(f"    DB updated: path={rel_path}, caption={caption[:60]}...")
    return True


def main():
    global OLLAMA_MODEL

    parser = argparse.ArgumentParser(description="Generate mnemonic images for Quranic roots")
    parser.add_argument("--root", help="Single root to process (Buckwalter, e.g. gfr)")
    parser.add_argument("--dry-run", action="store_true", help="Preview prompts without generating images")
    parser.add_argument("--force", action="store_true", help="Regenerate even if image already exists")
    parser.add_argument("--variants", type=int, default=1, help="Number of image variants per root (default: 1)")
    parser.add_argument("--model", default=None, help="Ollama model override")
    args = parser.parse_args()

    if args.model:
        OLLAMA_MODEL = args.model


    conn = get_db()
    try:
        if args.root:
            roots = [args.root]
        else:
            rows = conn.execute(
                "SELECT root_buckwalter FROM learning_curriculum ORDER BY unit_number, priority_score DESC"
            ).fetchall()
            roots = [r["root_buckwalter"] for r in rows]

        print(f"\nMnemonic image generation")
        print(f"Roots: {len(roots)} | Model: {OLLAMA_MODEL} | Dry run: {args.dry_run} | Variants: {args.variants}")
        print(f"Ollama URL: {OLLAMA_CLOUD_URL}")
        print("=" * 60)

        processed = 0
        skipped = 0
        for i, root_bw in enumerate(roots):
            print(f"\n[{i+1}/{len(roots)}]", end=" ")
            ok = process_root(conn, root_bw, args.dry_run, args.force, args.variants)
            if ok:
                processed += 1
                if not args.dry_run:
                    time.sleep(2)  # be kind to free HF tier
            else:
                skipped += 1

        print(f"\n{'='*60}")
        print(f"Done. Processed: {processed}, Skipped: {skipped}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
