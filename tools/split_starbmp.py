#!/usr/bin/env python3
"""Split Stars! sprite sheet BMPs into individual PNG images.

Usage:
    uv run --with pillow tmp/split_starbmp.py [--input tmp/starbmp] [--output tmp/starbmp_split]

Reads BMP sprite sheets extracted from the original Stars! (1995) executable
and splits them into individual cell images saved as PNGs. The dominant
background colour in each sheet is replaced with transparency.
"""

import argparse
import os
from pathlib import Path

from PIL import Image


def dominant_colour(img: Image.Image, sample_step: int = 4) -> tuple[int, int, int]:
    """Return the most common RGB colour by sampling the image."""
    w, h = img.size
    counts: dict[tuple[int, int, int], int] = {}
    for y in range(0, h, sample_step):
        for x in range(0, w, sample_step):
            c = img.getpixel((x, y))
            counts[c] = counts.get(c, 0) + 1
    return max(counts, key=counts.get)


MIN_GRID_CELLS = 2
MAX_GRID_CELLS = 200


def detect_cell_size(w: int, h: int) -> int | None:
    """Pick the best cell size for a sprite sheet based on its dimensions.

    Returns None for single images or full-screen artwork (e.g. the 640x480
    splash screen) that shouldn't be split.
    """
    for size in (64, 32):
        if w % size == 0 and h % size == 0:
            cols, rows = w // size, h // size
            total = cols * rows
            if total >= MIN_GRID_CELLS and total <= MAX_GRID_CELLS:
                return size
    return None


def cell_has_content(
    img: Image.Image,
    x0: int,
    y0: int,
    cell_w: int,
    cell_h: int,
    bg: tuple[int, int, int],
    threshold: float = 0.005,
) -> bool:
    """Return True if at least `threshold` fraction of pixels differ from bg."""
    total = cell_w * cell_h
    needed = int(total * threshold)
    diff = 0
    for y in range(y0, y0 + cell_h, 2):
        for x in range(x0, x0 + cell_w, 2):
            if img.getpixel((x, y)) != bg:
                diff += 1
                if diff >= needed:
                    return True
    return False


def replace_bg_with_alpha(
    img: Image.Image, bg: tuple[int, int, int], tolerance: int = 8
) -> Image.Image:
    """Replace pixels close to the background colour with transparency."""
    rgba = img.convert("RGBA")
    pixels = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if (
                abs(r - bg[0]) <= tolerance
                and abs(g - bg[1]) <= tolerance
                and abs(b - bg[2]) <= tolerance
            ):
                pixels[x, y] = (r, g, b, 0)
    return rgba


def process_sprite_sheet(
    bmp_path: Path, out_dir: Path, *, make_transparent: bool = True
) -> int:
    """Split a single BMP sprite sheet into individual PNGs. Returns count saved."""
    img = Image.open(bmp_path).convert("RGB")
    w, h = img.size
    stem = bmp_path.stem

    cell_size = detect_cell_size(w, h)
    if cell_size is None:
        # Not a grid — save the whole image as-is
        sheet_dir = out_dir / stem
        sheet_dir.mkdir(parents=True, exist_ok=True)
        out_path = sheet_dir / f"{stem}.png"
        if make_transparent:
            bg = dominant_colour(img)
            result = replace_bg_with_alpha(img, bg)
        else:
            result = img
        result.save(out_path)
        print(f"  {bmp_path.name}: single image -> {out_path.name}")
        return 1

    cols = w // cell_size
    rows = h // cell_size
    bg = dominant_colour(img)

    sheet_dir = out_dir / stem
    sheet_dir.mkdir(parents=True, exist_ok=True)

    saved = 0
    for row in range(rows):
        for col in range(cols):
            x0 = col * cell_size
            y0 = row * cell_size

            if not cell_has_content(img, x0, y0, cell_size, cell_size, bg):
                continue

            cell = img.crop((x0, y0, x0 + cell_size, y0 + cell_size))
            if make_transparent:
                cell = replace_bg_with_alpha(cell, bg)

            idx = row * cols + col
            out_path = sheet_dir / f"{stem}_{idx:03d}_r{row}c{col}.png"
            cell.save(out_path)
            saved += 1

    print(
        f"  {bmp_path.name}: {w}x{h}, {cell_size}px cells, "
        f"bg={bg}, {saved}/{rows * cols} cells saved"
    )
    return saved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("tmp/starbmp"),
        help="Directory containing extracted BMP files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tmp/starbmp_split"),
        help="Output directory for individual PNGs",
    )
    parser.add_argument(
        "--no-transparency",
        action="store_true",
        help="Keep original background instead of making it transparent",
    )
    args = parser.parse_args()

    if not args.input.is_dir():
        parser.error(f"Input directory not found: {args.input}")

    args.output.mkdir(parents=True, exist_ok=True)

    bmp_files = sorted(args.input.glob("*.bmp"))
    print(f"Found {len(bmp_files)} BMP files in {args.input}\n")

    total = 0
    for bmp_path in bmp_files:
        count = process_sprite_sheet(
            bmp_path, args.output, make_transparent=not args.no_transparency
        )
        total += count

    print(f"\nDone — {total} images saved to {args.output}")


if __name__ == "__main__":
    main()
