#!/usr/bin/env python3
"""Upscale Stars! sprite images using the OpenAI image edit API.

Usage:
    uv run --with openai,pillow tmp/upscale_starbmp.py [options]

Takes individual PNGs produced by split_starbmp.py and sends them through
the OpenAI gpt-image-1 edit endpoint to clean up, add transparency, and
upscale. The API returns 1024x1024; we then resize to the target (default
128x128, i.e. 2x the original 64x64).

Requires OPENAI_API_KEY in environment.
"""

import argparse
import base64
import sys
import time
from pathlib import Path

from openai import OpenAI
from PIL import Image


def upscale_image(
    client: OpenAI,
    src_path: Path,
    dst_path: Path,
    *,
    target_size: int,
    model: str,
    quality: str,
) -> dict:
    """Send one image to the OpenAI edit API and save the result."""
    img = Image.open(src_path).convert("RGB")
    bg_colour = img.getpixel((0, 0))
    bg_desc = (
        "grey" if bg_colour[0] > 100 and bg_colour[0] == bg_colour[1]
        else "black" if bg_colour == (0, 0, 0)
        else "white" if bg_colour == (255, 255, 255)
        else f"rgb{bg_colour}"
    )

    # prompt = (
    #     f"This is a small icon from a 1995 strategy video game. "
    #     f"It has a solid {bg_desc} background. "
    #     f"Clean up and upscale this icon to be crisp and detailed while "
    #     f"faithfully retaining the original retro 90s pixel-art game style, "
    #     f"colours, and subject matter. Do not add, remove, or alter any "
    #     f"elements — just make the existing artwork cleaner and sharper. "
    #     f"Remove the solid {bg_desc} background so only the item remains."
    # )
    prompt = (
        f"This is a small icon from a 1995 strategy video game. "
        f"It has a solid {bg_desc} background. "
        f"Clean up and upscale this icon to be crisp and clean. Do not add, remove, or alter any "
        f"elements — just make the existing artwork cleaner and sharper. "
        f"Remove the solid {bg_desc} background so only the item remains."
    )


    with open(src_path, "rb") as f:
        result = client.images.edit(
            model=model,
            image=f,
            prompt=prompt,
            background="transparent",
            output_format="png",
            size="1024x1024",
            quality=quality,
        )

    b64_data = result.data[0].b64_json
    raw_bytes = base64.b64decode(b64_data)

    # Save full-size API output, then resize to target
    from io import BytesIO
    api_img = Image.open(BytesIO(raw_bytes))
    resized = api_img.resize((target_size, target_size), Image.LANCZOS)

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    resized.save(dst_path)

    usage = getattr(result, "usage", None)
    tokens = usage.total_tokens if usage else "?"
    return {"tokens": tokens, "revised_prompt": getattr(result.data[0], "revised_prompt", None)}


def collect_images(input_dir: Path, folders: list[str] | None) -> list[Path]:
    """Collect PNG files from the input directory, optionally filtered by subfolder."""
    images = []
    if folders:
        for folder_name in folders:
            folder = input_dir / folder_name
            if folder.is_dir():
                images.extend(sorted(folder.glob("*.png")))
            else:
                print(f"Warning: folder {folder} not found, skipping")
    else:
        for folder in sorted(input_dir.iterdir()):
            if folder.is_dir():
                images.extend(sorted(folder.glob("*.png")))
    return images


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, default=Path("tmp/starbmp_split"),
        help="Directory of split PNGs (default: tmp/starbmp_split)",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("tmp/starbmp_upscaled"),
        help="Output directory (default: tmp/starbmp_upscaled)",
    )
    parser.add_argument(
        "--folders", nargs="*",
        help="Only process these subfolders (e.g. bmp500 bmp501)",
    )
    parser.add_argument(
        "--target-size", type=int, default=128,
        help="Final image size in pixels (default: 128, i.e. 2x from 64)",
    )
    parser.add_argument(
        "--limit", type=int, default=5,
        help="Max images to process (default: 5 for testing, use 0 for all)",
    )
    parser.add_argument(
        "--model", default="gpt-image-1",
        help="OpenAI image model (default: gpt-image-1)",
    )
    parser.add_argument(
        "--quality", default="medium", choices=["low", "medium", "high"],
        help="Output quality (default: medium)",
    )
    parser.add_argument(
        "--delay", type=float, default=1.0,
        help="Seconds to wait between API calls (default: 1.0)",
    )
    parser.add_argument(
        "--skip-existing", action="store_true",
        help="Skip images that already exist in the output directory",
    )
    args = parser.parse_args()

    if not args.input.is_dir():
        parser.error(f"Input directory not found: {args.input}")

    client = OpenAI()
    args.output.mkdir(parents=True, exist_ok=True)

    images = collect_images(args.input, args.folders)
    if args.limit > 0:
        images = images[:args.limit]

    print(f"Processing {len(images)} images")
    print(f"  model={args.model}, quality={args.quality}, target={args.target_size}x{args.target_size}")
    print(f"  input={args.input}, output={args.output}")
    print()

    succeeded = 0
    failed = 0

    for i, src_path in enumerate(images):
        rel = src_path.relative_to(args.input)
        dst_path = args.output / rel

        if args.skip_existing and dst_path.exists():
            print(f"  [{i+1}/{len(images)}] {rel} — skipped (exists)")
            succeeded += 1
            continue

        try:
            info = upscale_image(
                client, src_path, dst_path,
                target_size=args.target_size,
                model=args.model,
                quality=args.quality,
            )
            print(f"  [{i+1}/{len(images)}] {rel} — ok (tokens={info['tokens']})")
            succeeded += 1
        except Exception as e:
            print(f"  [{i+1}/{len(images)}] {rel} — FAILED: {e}", file=sys.stderr)
            failed += 1

        if i < len(images) - 1 and args.delay > 0:
            time.sleep(args.delay)

    print(f"\nDone — {succeeded} succeeded, {failed} failed")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
