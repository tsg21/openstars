#!/usr/bin/env python3
"""Remove the grey background from Stars! component GIF images.

Usage:
    uv run --with openai,pillow tools/upscale_starbmp.py path/to/image.gif
    uv run --with openai,pillow tools/upscale_starbmp.py path/to/dir/ [--limit N]

Uses the OpenAI gpt-image-2 edit API to extract each component onto a
transparent background. Output is saved as PNG alongside the input, or to
--output if specified.

Requires OPENAI_API_KEY in environment.
"""

import argparse
import base64
import sys
import time
from io import BytesIO
from pathlib import Path

from openai import OpenAI
from PIL import Image


def process_image(client: OpenAI, src_path: Path, dst_path: Path, *, model: str, quality: str) -> dict:
    img = Image.open(src_path).convert("RGBA")

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    prompt = (
        "This is a small icon from a 1995 sci-fi strategy video game. "
        "The icon shows a spacecraft component on a solid grey panel background with a thin border. "
        "Remove the grey background and border completely so only the component remains "
        "on a fully transparent background. "
        "Preserve the exact appearance of the component — colours, shape, and style unchanged."
    )

    result = client.images.edit(
        model=model,
        image=("image.png", buf, "image/png"),
        prompt=prompt,
        background="transparent",
        output_format="png",
        size="1024x1024",
        quality=quality,
    )

    b64_data = result.data[0].b64_json
    raw_bytes = base64.b64decode(b64_data)
    api_img = Image.open(BytesIO(raw_bytes))

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    api_img.save(dst_path)

    usage = getattr(result, "usage", None)
    return {"tokens": usage.total_tokens if usage else "?"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="GIF/PNG file or directory to process")
    parser.add_argument("--output", "-o", type=Path, help="Output file or directory")
    parser.add_argument("--model", default="gpt-image-2", help="OpenAI image model (default: gpt-image-2)")
    parser.add_argument("--quality", default="medium", choices=["low", "medium", "high"])
    parser.add_argument("--limit", type=int, default=0, help="Max images to process (0 = all)")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between API calls")
    parser.add_argument("--skip-existing", action="store_true", help="Skip already-processed outputs")
    args = parser.parse_args()

    if not args.input.exists():
        parser.error(f"Input not found: {args.input}")

    if args.input.is_dir():
        files = sorted(args.input.glob("**/*.gif")) + sorted(args.input.glob("**/*.png"))
        if args.limit > 0:
            files = files[:args.limit]
        out_dir = args.output or args.input.parent / (args.input.name + "_processed")
        pairs = [
            (f, out_dir / f.relative_to(args.input).with_suffix(".png"))
            for f in files
        ]
    else:
        out = args.output or args.input.with_suffix(".png")
        pairs = [(args.input, out)]

    client = OpenAI()
    print(f"Processing {len(pairs)} image(s) — model={args.model}, quality={args.quality}")

    succeeded = failed = 0
    for i, (src, dst) in enumerate(pairs):
        if args.skip_existing and dst.exists():
            print(f"  [{i+1}/{len(pairs)}] {src.name} — skipped")
            succeeded += 1
            continue
        try:
            info = process_image(client, src, dst, model=args.model, quality=args.quality)
            print(f"  [{i+1}/{len(pairs)}] {src.name} → {dst} (tokens={info['tokens']})")
            succeeded += 1
        except Exception as e:
            print(f"  [{i+1}/{len(pairs)}] {src.name} — FAILED: {e}", file=sys.stderr)
            failed += 1

        if i < len(pairs) - 1 and args.delay > 0:
            time.sleep(args.delay)

    print(f"\nDone — {succeeded} succeeded, {failed} failed")


if __name__ == "__main__":
    main()
