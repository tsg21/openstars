#!/usr/bin/env python3
"""Batch-generate planet images and save normalized 480x480 PNG files.

This script uses the OpenAI Images API and writes assets directly to disk
for later upload to GCS/CDN.

Example:
  OPENAI_API_KEY=... python tools/planet_images/batch_generate_openai.py \
    --output-dir ./planet-outputs \
    --count-per-class 12
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib import request

API_URL = "https://api.openai.com/v1/images/generations"


@dataclass(frozen=True)
class PlanetClass:
    key: str
    prompt: str


PLANET_CLASSES = (
    PlanetClass(
        key="terrestrial",
        prompt=(
            "A photoreal planet render, terrestrial world with continents and oceans, "
            "space background removed, centered sphere, no text, no watermark."
        ),
    ),
    PlanetClass(
        key="gas-giant",
        prompt=(
            "A photoreal gas giant planet render with atmospheric bands and storm detail, "
            "space background removed, centered sphere, no text, no watermark."
        ),
    ),
    PlanetClass(
        key="ice",
        prompt=(
            "A photoreal icy planet render with frozen crust and pale blue tones, "
            "space background removed, centered sphere, no text, no watermark."
        ),
    ),
    PlanetClass(
        key="lava",
        prompt=(
            "A photoreal lava planet render with glowing fissures and volcanic surface, "
            "space background removed, centered sphere, no text, no watermark."
        ),
    ),
    PlanetClass(
        key="desert",
        prompt=(
            "A photoreal desert planet render with dry canyons and sand basins, "
            "space background removed, centered sphere, no text, no watermark."
        ),
    ),
    PlanetClass(
        key="ocean",
        prompt=(
            "A photoreal ocean planet render with deep blue atmosphere and cloud swirls, "
            "space background removed, centered sphere, no text, no watermark."
        ),
    ),
)


def generate_image_b64(api_key: str, model: str, prompt: str, size: str) -> str:
    payload = json.dumps({"model": model, "prompt": prompt, "size": size}).encode("utf-8")
    req = request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with request.urlopen(req) as response:
        body = response.read().decode("utf-8")

    decoded = json.loads(body)
    return decoded["data"][0]["b64_json"]


def write_resized_png(b64_data: str, output_file: Path, target_size: int) -> None:
    from PIL import Image

    raw = base64.b64decode(b64_data)
    image = Image.open(io.BytesIO(raw)).convert("RGBA")
    resized = image.resize((target_size, target_size), resample=Image.Resampling.LANCZOS)
    resized.save(output_file, format="PNG", optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--count-per-class", type=int, default=10)
    parser.add_argument("--model", default="gpt-image-1")
    parser.add_argument(
        "--api-size",
        default="1024x1024",
        help="Requested generation size from the provider.",
    )
    parser.add_argument(
        "--target-size",
        type=int,
        default=480,
        help="Final saved image width/height in pixels.",
    )
    parser.add_argument(
        "--style-suffix",
        default="High detail, cinematic lighting, science fiction style.",
        help="Appended to every class prompt to keep art direction consistent.",
    )
    parser.add_argument(
        "--no-resize",
        action="store_true",
        help="Save provider output as-is (skip Pillow-based resizing).",
    )
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    for planet_class in PLANET_CLASSES:
        for index in range(1, args.count_per_class + 1):
            output_name = f"{planet_class.key}-{index:03d}.png"
            output_path = args.output_dir / output_name

            if output_path.exists():
                print(f"skip existing {output_name}")
                continue

            varied_prompt = f"{planet_class.prompt} Variation #{index}. {args.style_suffix}"
            b64_image = generate_image_b64(
                api_key=api_key,
                model=args.model,
                prompt=varied_prompt,
                size=args.api_size,
            )
            if args.no_resize:
                output_path.write_bytes(base64.b64decode(b64_image))
            else:
                write_resized_png(b64_image, output_path, args.target_size)
            print(f"wrote {output_name}")


if __name__ == "__main__":
    main()
