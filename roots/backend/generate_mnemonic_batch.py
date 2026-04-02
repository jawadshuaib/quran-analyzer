"""Batch generate placeholder mnemonic images using SD-Turbo.

User will replace with ChatGPT-generated images later.
Usage: python generate_mnemonic_batch.py
"""

import os
import time
import torch
from diffusers import AutoPipelineForText2Image

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data", "mnemonic_images")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "mnemonic_images")

# Each root maps to a short, SD-Turbo-friendly prompt
PROMPTS = {
    # Unit 11: Life, Death & Eternity
    "Hyy": "oil painting of a green sprouting seedling bursting through dry earth, vibrant life, dark background",
    "mwt": "oil painting of a single withered brown leaf falling from a bare tree, twilight purple sky",
    "dnw": "oil painting of a shimmering soap bubble floating in golden light, iridescent colors",
    "nhr": "oil painting of a golden sunrise over a flowing river, warm orange and gold reflections",
    "xld": "oil painting of an ancient massive oak tree on a hill, golden sunlight, deep roots visible",
    "Awl": "oil painting of a bright morning star shining alone in a dark blue pre-dawn sky",

    # Unit 12: Prayer & Devotion
    "Slw": "oil painting of a glowing prayer rug on the ground, warm amber light, golden horizon",
    "sjd": "oil painting of a large seashell facing downward on wet sand, ocean background, blue gold",
    "sbH": "oil painting of a songbird singing on a flowering branch at dawn, golden morning light",
    "$kr": "oil painting of an overflowing cornucopia with fruits and grains on a wooden table, golden light",
    "twb": "oil painting of an open doorway with bright warm light streaming through from the other side",

    # Unit 13: Virtue & Character
    "SlH": "oil painting of perfectly balanced golden scales on a marble pedestal, soft golden light",
    "Sdq": "oil painting of a crystal prism splitting white light into a rainbow, dark background",
    "TwE": "oil painting of a noble falcon perched on a leather glove, desert dusk background",
    "Sbr": "oil painting of a lighthouse standing firm against crashing ocean waves in a storm, light beam",
    "Hbb": "oil painting of two olive tree branches intertwined growing together, warm green and gold",

    # Unit 14: Sin & Deviation
    "Dll": "oil painting of a winding path splitting into many trails in a dark misty forest",
    "$rk": "oil painting of a shattered golden crown lying in broken pieces on the ground, dark tones",
    "Edw": "oil painting of a white and black chess knight pieces facing each other, dramatic lighting",
    "$Tn": "oil painting of a black serpent coiled around a dead tree stump, red glowing eyes, dark background",
    "Hrm": "oil painting of a sealed ancient chest with heavy iron lock and chains, amber lighting",
    "gyr": "oil painting of a single white chess piece among black chess pieces, dramatic side lighting",

    # Unit 15: Perception & Heart
    "smE": "oil painting of an ornate golden ear trumpet on velvet fabric, warm brass tones",
    "qlb": "oil painting of a luminous red and gold glass heart on a dark pedestal, glowing from within",
    "$hd": "oil painting of an open eye reflected perfectly in a still pool of water, blue and gold",
    "bSr": "oil painting of a brass telescope pointed at a starry night sky on a hilltop",
    "nZr": "oil painting of a magnifying glass hovering over an intricate map, warm golden tones",
    "bED": "oil painting of a pomegranate split open showing ruby red seeds spilling out",
    "sAl": "oil painting of a large question mark carved in ancient stone, golden courtyard light",

    # Unit 16: Community & Family
    "Ahl": "oil painting of a warm glowing lantern at center of a circular stone table with chairs",
    "Amm": "oil painting of a vast flock of birds flying in formation across a golden sunset sky",
    "Abw": "oil painting of an ancient gnarled tree with massive trunk and spreading roots, sunlit meadow",
    "bny": "oil painting of stone blocks being stacked to build an arch, sunlight streaming through",
    "Ans": "oil painting of countless footprints in sand stretching to the horizon, warm desert tones",
    "wld": "oil painting of a bird nest with three speckled eggs in a flowering tree branch, morning light",
    "Axw": "oil painting of two matching swords crossed on a shield, silver and blue tones",

    # Unit 17: Divine Power & Provision
    "qdr": "oil painting of a mighty thunderbolt striking from storm clouds, electric blue and gold",
    "EZm": "oil painting of a colossal mountain peak rising above clouds, snow-capped, majestic",
    "rzq": "oil painting of golden wheat sheaves in a harvested field, abundant, warm sunset",
    "Ezz": "oil painting of a golden lion standing proudly on a rocky outcrop, mane flowing, regal",
    "fDl": "oil painting of an overflowing golden chalice with honey spilling over its rim",
    "kbr": "oil painting of a towering stone pillar reaching into clouds, viewed from below, imposing",
    "nSr": "oil painting of a triumphant banner flag planted on a hilltop, golden sunlight through clouds",
    "ydy": "oil painting of two cupped open palms offering upward holding a glowing sphere of light",

    # Unit 18: Prophecy & Recompense
    "nbA": "oil painting of a glowing scroll unrolling in mid-air, golden light emanating, dark background",
    "wEd": "oil painting of a sealed covenant document with wax seal on a stone tablet, golden tones",
    "n*r": "oil painting of a blazing signal fire atop a watchtower at night, red-orange flames",
    "b$r": "oil painting of a white dove carrying an olive branch descending through golden sunlight",
    "wHy": "oil painting of a beam of white light descending from heavens through parting clouds to mountaintop",
    "sbl": "oil painting of a straight illuminated path through a dark forest, golden light on both sides",
    "mvl": "oil painting of a mirror reflecting a candle flame showing a different scene, a bright sun",

    # Unit 19: Actions & Movement
    "xrj": "oil painting of a butterfly emerging from a chrysalis, bright wings unfolding, dark bark",
    "dxl": "oil painting of grand ornate golden doors swung open, bright light flooding through gateway",
    "tbE": "oil painting of footprints in fresh snow leading forward on a mountain path, dawn light",
    "rjE": "oil painting of a boomerang mid-flight against a sunset sky, golden light trail",
    "qtl": "oil painting of a broken sword lying on dark ground, blade snapped, dramatic somber lighting",
    "dwn": "oil painting of a deep canyon viewed from above, layers of rock descending into shadow",
    "xlf": "oil painting of a crossroads where two paths diverge in an autumnal forest",
    "rwd": "oil painting of a brass compass needle pointing to a glowing northern star",
    "lqy": "oil painting of two rivers merging at a confluence, blue and green waters blending, aerial view",

    # Unit 20: Religion & Judgment
    "slm": "oil painting of an olive branch laid across a closed book on a peaceful stone altar",
    "dyn": "oil painting of a balance scale against a cosmic starry sky, weighing a feather and a stone",
    "jzy": "oil painting of golden coins pouring from a cloud into a harvest basket below",
    "nEm": "oil painting of a lush garden with a flowing fountain, flowers blooming, vibrant greens and gold",
    "xwf": "oil painting of a small flickering candle flame in vast darkness, tiny light in shadow",
    "jmE": "oil painting of many streams converging into one great river, seen from above",
    "kvr": "oil painting of an endless field of blooming sunflowers stretching to the horizon, golden",
    "swA": "oil painting of two identical stones on opposite sides of a perfectly level surface, mirror image",
}


def generate_images():
    # Check which already exist
    existing = set(f.replace(".webp", "") for f in os.listdir(OUTPUT_DIR) if f.endswith(".webp"))
    to_generate = {k: v for k, v in PROMPTS.items() if k not in existing}

    if not to_generate:
        print("All images already exist!")
        return

    print(f"Generating {len(to_generate)} images ({len(existing)} already exist)")

    # Load SD-Turbo
    print("Loading SD-Turbo model...")
    pipe = AutoPipelineForText2Image.from_pretrained(
        "stabilityai/sd-turbo",
        torch_dtype=torch.float16,
        variant="fp16",
    )
    pipe = pipe.to("mps")
    print("Model loaded!")

    for i, (root_bw, prompt) in enumerate(to_generate.items()):
        print(f"\n[{i+1}/{len(to_generate)}] {root_bw}: {prompt[:60]}...")
        start = time.time()

        image = pipe(
            prompt=prompt,
            num_inference_steps=4,
            guidance_scale=0.0,
            width=512,
            height=512,
        ).images[0]

        # Save as WebP
        out_path = os.path.join(OUTPUT_DIR, f"{root_bw}.webp")
        image.save(out_path, "WEBP", quality=85)

        # Also copy to assets
        assets_path = os.path.join(ASSETS_DIR, f"{root_bw}.webp")
        image.save(assets_path, "WEBP", quality=85)

        elapsed = time.time() - start
        print(f"  Saved {root_bw}.webp ({elapsed:.1f}s)")

    print(f"\nDone! Generated {len(to_generate)} images.")


if __name__ == "__main__":
    generate_images()
