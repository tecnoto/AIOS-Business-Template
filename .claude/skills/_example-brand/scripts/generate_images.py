#!/usr/bin/env python3
"""
Brand Image Generator — DALL-E 3 wrapper with brand-specific style injection.

This is an EXAMPLE. Customize BRAND_STYLES for your business.

Usage:
    python3 generate_images.py --type hero --prompt "description" --output path/
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Find project root
def _find_root():
    path = Path(__file__).resolve().parent
    while path != path.parent:
        if (path / "CLAUDE.md").exists():
            return path
        path = path.parent
    return Path.cwd()

PROJECT_ROOT = _find_root()
load_dotenv(PROJECT_ROOT / ".env")

# === CUSTOMIZE THIS FOR YOUR BRAND ===

BRAND_STYLES = {
    "default": {
        "name": "My Business",
        "palette": "navy blue (#1a365d), white, and gold (#d69e2e) accents",
        "aesthetic": "Clean, modern, professional. Subtle gradients. No text in images.",
        "avoid": "Cartoonish, cluttered, stock-photo look, people's faces",
    },
    # Add more brand variants if you manage multiple brands:
    # "brand-b": { "name": "...", "palette": "...", ... },
}

IMAGE_TYPES = {
    "hero": {
        "size": "1792x1024",
        "style_suffix": "Wide cinematic composition, hero banner format.",
    },
    "illustration": {
        "size": "1024x1024",
        "style_suffix": "Clean illustration style, centered subject.",
    },
    "og-image": {
        "size": "1792x1024",
        "style_suffix": "Open Graph preview image, bold and clear at small sizes.",
    },
    "icon": {
        "size": "1024x1024",
        "style_suffix": "App icon style, simple geometric, works at 64px.",
    },
}


def generate_image(prompt, image_type="hero", brand="default", output_dir=None):
    """Generate a branded image using DALL-E 3."""
    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai package required. Install: pip install openai")
        sys.exit(1)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set in .env")
        sys.exit(1)

    brand_style = BRAND_STYLES.get(brand, BRAND_STYLES["default"])
    img_config = IMAGE_TYPES.get(image_type, IMAGE_TYPES["hero"])

    full_prompt = (
        f"{prompt}. "
        f"Brand: {brand_style['name']}. "
        f"Color palette: {brand_style['palette']}. "
        f"Style: {brand_style['aesthetic']} "
        f"Avoid: {brand_style['avoid']}. "
        f"{img_config['style_suffix']}"
    )

    print(f"Generating {image_type} image for {brand_style['name']}...")
    print(f"Prompt: {full_prompt[:200]}...")

    client = OpenAI(api_key=api_key)
    response = client.images.generate(
        model="dall-e-3",
        prompt=full_prompt,
        size=img_config["size"],
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    print(f"Generated: {image_url}")

    # Download if output directory specified
    if output_dir:
        import requests
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        filename = f"{image_type}_{brand}.png"
        filepath = output_path / filename
        img_data = requests.get(image_url).content
        filepath.write_bytes(img_data)
        print(f"Saved: {filepath}")

    return image_url


def main():
    parser = argparse.ArgumentParser(description="Generate branded images")
    parser.add_argument("--type", default="hero", choices=IMAGE_TYPES.keys())
    parser.add_argument("--prompt", required=True, help="Image description")
    parser.add_argument("--brand", default="default", help="Brand variant")
    parser.add_argument("--output", help="Output directory")
    args = parser.parse_args()

    generate_image(args.prompt, args.type, args.brand, args.output)


if __name__ == "__main__":
    main()
