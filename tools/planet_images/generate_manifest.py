#!/usr/bin/env python3
"""Generate a simple manifest.json for externally hosted planet images.

Example:
  python tools/planet_images/generate_manifest.py \
    --input-dir ./planet-outputs \
    --base-url https://storage.googleapis.com/openstars-assets/planets/v1 \
    --output ./manifest.json
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

KNOWN_CLASSES = (
    "terrestrial",
    "gas_giant",
    "ice",
    "lava",
    "ocean",
    "desert",
    "barren",
    "toxic",
)


def classify(filename: str) -> str:
  lowered = filename.lower()
  for kind in KNOWN_CLASSES:
    if kind in lowered:
      return kind
  return "unknown"


def build_manifest(input_dir: Path, base_url: str, version: str) -> dict[str, object]:
  images_by_class: dict[str, list[str]] = defaultdict(list)

  for path in sorted(input_dir.iterdir()):
    if not path.is_file():
      continue
    if path.suffix.lower() not in {".png", ".webp", ".jpg", ".jpeg"}:
      continue

    images_by_class[classify(path.name)].append(path.name)

  return {
      "version": version,
      "baseUrl": base_url.rstrip("/"),
      "imagesByClass": dict(images_by_class),
  }


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--input-dir", required=True, type=Path)
  parser.add_argument("--base-url", required=True)
  parser.add_argument("--version", default="v1")
  parser.add_argument("--output", required=True, type=Path)
  args = parser.parse_args()

  manifest = build_manifest(args.input_dir, args.base_url, args.version)
  args.output.write_text(f"{json.dumps(manifest, indent=2)}\n", encoding="utf-8")


if __name__ == "__main__":
  main()
