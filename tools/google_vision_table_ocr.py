#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "google-cloud-vision>=3.10.2",
# ]
# ///

from __future__ import annotations

import argparse
import os
import statistics
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OcrCell:
    text: str
    confidence: float
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def x_center(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def y_center(self) -> float:
        return (self.y0 + self.y1) / 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Send an image to Google Cloud Vision OCR and convert detected table text "
            "into Markdown."
        )
    )
    parser.add_argument("image", type=Path, help="Path to the source image file.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Write Markdown to this file. Defaults to stdout.",
    )
    parser.add_argument(
        "--credentials",
        type=Path,
        help=(
            "Optional service account JSON file. If omitted, the script uses "
            "Application Default Credentials."
        ),
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.0,
        help="Discard words below this confidence threshold. Default: 0.0",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Optional H1 title for the Markdown output.",
    )
    return parser.parse_args()


def normalise_text(text: str) -> str:
    return " ".join(text.split()).strip()


def is_noise_cell(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if all(char in "-_=~." for char in stripped):
        return True
    return False


def vertices_to_bounds(vertices: list[object]) -> tuple[float, float, float, float]:
    xs = [float(getattr(vertex, "x", 0) or 0) for vertex in vertices]
    ys = [float(getattr(vertex, "y", 0) or 0) for vertex in vertices]
    return min(xs), min(ys), max(xs), max(ys)


def extract_cells(annotation: object, min_confidence: float) -> list[OcrCell]:
    cells: list[OcrCell] = []
    for page in getattr(annotation, "pages", []):
        for block in getattr(page, "blocks", []):
            for paragraph in getattr(block, "paragraphs", []):
                for word in getattr(paragraph, "words", []):
                    text = normalise_text("".join(symbol.text for symbol in word.symbols))
                    confidence = float(getattr(word, "confidence", 0.0) or 0.0)
                    if confidence < min_confidence or is_noise_cell(text):
                        continue
                    x0, y0, x1, y1 = vertices_to_bounds(word.bounding_box.vertices)
                    cells.append(
                        OcrCell(
                            text=text,
                            confidence=confidence,
                            x0=x0,
                            y0=y0,
                            x1=x1,
                            y1=y1,
                        )
                    )
    return sorted(cells, key=lambda cell: (cell.y_center, cell.x0))


def cluster_values(values: list[float], tolerance: float) -> list[float]:
    if not values:
        return []
    sorted_values = sorted(values)
    clusters: list[list[float]] = [[sorted_values[0]]]
    for value in sorted_values[1:]:
        if abs(value - statistics.mean(clusters[-1])) <= tolerance:
            clusters[-1].append(value)
            continue
        clusters.append([value])
    return [statistics.mean(cluster) for cluster in clusters]


def group_rows(cells: list[OcrCell]) -> list[list[OcrCell]]:
    if not cells:
        return []

    median_height = statistics.median(cell.height for cell in cells)
    tolerance = max(10.0, median_height * 0.75)

    rows: list[list[OcrCell]] = []
    anchors: list[float] = []
    for cell in cells:
        if not anchors:
            rows.append([cell])
            anchors.append(cell.y_center)
            continue
        distances = [abs(cell.y_center - anchor) for anchor in anchors]
        nearest_index = min(range(len(distances)), key=distances.__getitem__)
        if distances[nearest_index] <= tolerance:
            rows[nearest_index].append(cell)
            anchors[nearest_index] = statistics.mean(item.y_center for item in rows[nearest_index])
            continue
        rows.append([cell])
        anchors.append(cell.y_center)

    for row in rows:
        row.sort(key=lambda cell: cell.x0)
    return rows


def estimate_columns(rows: list[list[OcrCell]]) -> list[float]:
    cells = [cell for row in rows for cell in row]
    if not cells:
        return []
    median_height = statistics.median(cell.height for cell in cells)
    tolerance = max(18.0, median_height * 1.8)
    return cluster_values([cell.x0 for cell in cells], tolerance)


def assign_columns(row: list[OcrCell], column_anchors: list[float]) -> list[str]:
    if not column_anchors:
        return [normalise_text(" ".join(cell.text for cell in row))]

    column_buckets: list[list[str]] = [[] for _ in column_anchors]
    for cell in row:
        nearest_index = min(
            range(len(column_anchors)),
            key=lambda index: abs(cell.x0 - column_anchors[index]),
        )
        column_buckets[nearest_index].append(cell.text)

    values = [" ".join(parts).strip() for parts in column_buckets]
    while values and values[-1] == "":
        values.pop()
    return values


def normalise_matrix(rows: list[list[str]]) -> list[list[str]]:
    width = max((len(row) for row in rows), default=0)
    matrix = [row + [""] * (width - len(row)) for row in rows]
    return [row for row in matrix if any(cell.strip() for cell in row)]


def choose_header_index(matrix: list[list[str]]) -> int | None:
    if not matrix:
        return None
    for index, row in enumerate(matrix[:3]):
        filled_cells = sum(1 for cell in row if cell.strip())
        if filled_cells >= 2:
            return index
    return None


def markdown_escape(text: str) -> str:
    return text.replace("|", r"\|").replace("\n", "<br>")


def matrix_to_markdown(matrix: list[list[str]], title: str | None = None) -> str:
    lines: list[str] = []
    if title:
        lines.extend([f"# {title}", ""])

    if not matrix:
        lines.append("_No OCR rows detected._")
        return "\n".join(lines).rstrip() + "\n"

    header_index = choose_header_index(matrix)
    body_rows = matrix[:]
    if header_index is None:
        column_count = max(len(row) for row in matrix)
        headers = [f"Column {index + 1}" for index in range(column_count)]
    else:
        headers = matrix[header_index]
        body_rows = matrix[:header_index] + matrix[header_index + 1 :]

    lines.extend(
        [
            "| " + " | ".join(markdown_escape(cell or " ") for cell in headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
        ]
    )
    for row in body_rows:
        padded = row + [""] * (len(headers) - len(row))
        lines.append("| " + " | ".join(markdown_escape(cell or " ") for cell in padded) + " |")

    return "\n".join(lines).rstrip() + "\n"


def run_vision_ocr(image_path: Path) -> object:
    from google.cloud import vision

    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_path.read_bytes())
    response = client.document_text_detection(image=image)
    if response.error.message:
        raise RuntimeError(f"Google Cloud Vision error: {response.error.message}")
    return response.full_text_annotation


def build_markdown(image_path: Path, title: str | None, min_confidence: float) -> str:
    annotation = run_vision_ocr(image_path)
    cells = extract_cells(annotation, min_confidence=min_confidence)
    rows = group_rows(cells)
    column_anchors = estimate_columns(rows)
    matrix = normalise_matrix([assign_columns(row, column_anchors) for row in rows])
    return matrix_to_markdown(matrix, title=title)


def main() -> None:
    args = parse_args()

    image_path = args.image.resolve()
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    if args.credentials is not None:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(args.credentials.resolve())

    title = args.title or image_path.stem.replace("-", " ").replace("_", " ").title()
    markdown = build_markdown(
        image_path=image_path,
        title=title,
        min_confidence=args.min_confidence,
    )

    if args.output is None:
        print(markdown, end="")
        return

    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Wrote Markdown table to {output_path}")


if __name__ == "__main__":
    main()
