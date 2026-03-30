#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pymupdf>=1.26.5",
#   "rapidocr-onnxruntime>=1.4.4",
# ]
# ///

from __future__ import annotations

import argparse
import os
import statistics
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import fitz
from rapidocr_onnxruntime import RapidOCR

DEFAULT_PDF = Path("docs/references/manual/Stars-manual.pdf")
DEFAULT_OUTPUT_DIR = Path("docs/references/manual/extracted-technology-tables")


@dataclass(frozen=True)
class OcrCell:
    text: str
    score: float
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
            "Render selected Stars! manual PDF pages to PNG and convert OCR output into "
            "Markdown table drafts."
        )
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        default=DEFAULT_PDF,
        help=f"Source PDF path. Default: {DEFAULT_PDF}",
    )
    parser.add_argument(
        "--pages",
        default="241-252",
        help="1-based page numbers or ranges, for example '241-252' or '241-243,250'.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for extracted images and markdown. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Render DPI for PNG extraction. Higher DPI can improve OCR. Default: 300",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.35,
        help="Discard OCR boxes below this confidence score. Default: 0.35",
    )
    return parser.parse_args()


def parse_page_ranges(spec: str) -> list[int]:
    pages: set[int] = set()
    for chunk in spec.split(","):
        token = chunk.strip()
        if not token:
            continue
        if "-" in token:
            start_str, end_str = token.split("-", 1)
            start = int(start_str)
            end = int(end_str)
            if start > end:
                raise ValueError(f"Invalid page range '{token}': start exceeds end")
            pages.update(range(start, end + 1))
            continue
        pages.add(int(token))
    if not pages:
        raise ValueError("No pages selected")
    return sorted(pages)


def ensure_pages_exist(doc: fitz.Document, pages: Iterable[int]) -> None:
    page_count = doc.page_count
    for page_num in pages:
        if page_num < 1 or page_num > page_count:
            raise ValueError(f"Page {page_num} is out of range for PDF with {page_count} pages")


def render_page_image(doc: fitz.Document, page_num: int, output_path: Path, dpi: int) -> None:
    page = doc.load_page(page_num - 1)
    scale = dpi / 72
    pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    pixmap.save(output_path)


def normalize_text(text: str) -> str:
    return " ".join(text.split()).strip()


def to_ocr_cell(item: list) -> OcrCell | None:
    box, text, score = item
    cleaned = normalize_text(str(text))
    if not cleaned:
        return None
    xs = [point[0] for point in box]
    ys = [point[1] for point in box]
    return OcrCell(
        text=cleaned,
        score=float(score),
        x0=min(xs),
        y0=min(ys),
        x1=max(xs),
        y1=max(ys),
    )


def extract_cells(image_path: Path, engine: RapidOCR, min_score: float) -> list[OcrCell]:
    result, _ = engine(str(image_path))
    if not result:
        return []
    cells = [to_ocr_cell(item) for item in result]
    return sorted(
        [
            cell
            for cell in cells
            if cell is not None and cell.score >= min_score and not is_noise_cell(cell.text)
        ],
        key=lambda cell: (cell.y_center, cell.x0),
    )


def is_noise_cell(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if all(char in "-_=~." for char in stripped):
        return True
    return False


def cluster_values(values: list[float], tolerance: float) -> list[float]:
    if not values:
        return []
    sorted_values = sorted(values)
    clusters: list[list[float]] = [[sorted_values[0]]]
    for value in sorted_values[1:]:
        if abs(value - statistics.mean(clusters[-1])) <= tolerance:
            clusters[-1].append(value)
        else:
            clusters.append([value])
    return [statistics.mean(cluster) for cluster in clusters]


def group_rows(cells: list[OcrCell]) -> list[list[OcrCell]]:
    if not cells:
        return []
    median_height = statistics.median(cell.height for cell in cells)
    tolerance = max(12.0, median_height * 0.7)

    rows: list[list[OcrCell]] = []
    anchors: list[float] = []
    for cell in sorted(cells, key=lambda item: (item.y_center, item.x0)):
        if not anchors:
            rows.append([cell])
            anchors.append(cell.y_center)
            continue
        distances = [abs(cell.y_center - anchor) for anchor in anchors]
        nearest = min(range(len(distances)), key=distances.__getitem__)
        if distances[nearest] <= tolerance:
            rows[nearest].append(cell)
            anchors[nearest] = statistics.mean(item.y_center for item in rows[nearest])
        else:
            rows.append([cell])
            anchors.append(cell.y_center)
    for row in rows:
        row.sort(key=lambda item: item.x0)
    return rows


def estimate_columns(rows: list[list[OcrCell]]) -> list[float]:
    cells = [cell for row in rows for cell in row]
    if not cells:
        return []
    median_height = statistics.median(cell.height for cell in cells)
    tolerance = max(20.0, median_height * 1.8)
    return cluster_values([cell.x0 for cell in cells], tolerance)


def assign_columns(row: list[OcrCell], column_anchors: list[float]) -> list[str]:
    if not column_anchors:
        return [normalize_text(" ".join(cell.text for cell in row))]

    column_buckets: list[list[str]] = [[] for _ in column_anchors]
    for cell in row:
        nearest = min(
            range(len(column_anchors)),
            key=lambda index: abs(cell.x0 - column_anchors[index]),
        )
        column_buckets[nearest].append(cell.text)

    values = [" ".join(parts).strip() for parts in column_buckets]
    while values and values[-1] == "":
        values.pop()
    return values


def normalize_matrix(rows: list[list[str]]) -> list[list[str]]:
    width = max((len(row) for row in rows), default=0)
    matrix = [row + [""] * (width - len(row)) for row in rows]
    return [row for row in matrix if any(cell.strip() for cell in row)]


def choose_header_index(matrix: list[list[str]]) -> int | None:
    if not matrix:
        return None
    for index, row in enumerate(matrix[:3]):
        filled = sum(1 for cell in row if cell.strip())
        if filled >= 2:
            return index
    return None


def markdown_escape(text: str) -> str:
    return text.replace("|", r"\|").replace("\n", "<br>")


def matrix_to_markdown(matrix: list[list[str]]) -> str:
    if not matrix:
        return "_No OCR rows detected._\n"

    header_index = choose_header_index(matrix)
    body_rows = matrix[:]
    if header_index is None:
        column_count = max(len(row) for row in matrix)
        headers = [f"Column {index + 1}" for index in range(column_count)]
    else:
        headers = matrix[header_index]
        body_rows = matrix[:header_index] + matrix[header_index + 1 :]

    lines = [
        "| " + " | ".join(markdown_escape(cell or " ") for cell in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in body_rows:
        padded = row + [""] * (len(headers) - len(row))
        lines.append("| " + " | ".join(markdown_escape(cell or " ") for cell in padded) + " |")
    return "\n".join(lines) + "\n"


def ocr_page_to_markdown(image_path: Path, engine: RapidOCR, min_score: float) -> tuple[str, int]:
    cells = extract_cells(image_path, engine, min_score=min_score)
    rows = group_rows(cells)
    column_anchors = estimate_columns(rows)
    matrix = normalize_matrix([assign_columns(row, column_anchors) for row in rows])
    markdown = matrix_to_markdown(matrix)
    return markdown, len(matrix)


def extract_table_section(markdown_path: Path) -> str:
    content = markdown_path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(content):
        if line.startswith("| ") or line.startswith("_No OCR rows detected._"):
            return "\n".join(content[index:]).strip()
    return markdown_path.read_text(encoding="utf-8").strip()


def build_combined_markdown(entries: list[tuple[int, Path, Path]], combined_path: Path) -> str:
    lines = [
        "# Stars! Technology Tables OCR",
        "",
        "Generated from `docs/references/manual/Stars-manual.pdf`.",
        "",
        "This output is heuristic OCR from rendered page images. Expect to review and fix rows,",
        "column splits, and misread glyphs before folding the tables into the cleaned manual.",
        "",
    ]

    for page_num, image_path, markdown_path in entries:
        relative_image = Path(os.path.relpath(image_path, combined_path.parent))
        page_markdown = extract_table_section(markdown_path)
        lines.extend(
            [
                f"## Page {page_num}",
                "",
                f"![Page {page_num}]({relative_image.as_posix()})",
                "",
                page_markdown,
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()

    pdf_path = args.pdf.resolve()
    output_dir = args.output_dir.resolve()
    images_dir = output_dir / "images"
    markdown_dir = output_dir / "markdown"
    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)
    markdown_dir.mkdir(parents=True, exist_ok=True)

    selected_pages = parse_page_ranges(args.pages)

    with fitz.open(pdf_path) as doc:
        ensure_pages_exist(doc, selected_pages)
        engine = RapidOCR()
        combined_entries: list[tuple[int, Path, Path]] = []

        for page_num in selected_pages:
            image_path = images_dir / f"page-{page_num:03}.png"
            markdown_path = markdown_dir / f"page-{page_num:03}.md"

            render_page_image(doc, page_num, image_path, args.dpi)
            markdown, row_count = ocr_page_to_markdown(
                image_path=image_path,
                engine=engine,
                min_score=args.min_score,
            )

            page_lines = [
                f"# Page {page_num}",
                "",
                f"Source image: `../images/{image_path.name}`",
                "",
                f"Detected OCR rows: {row_count}",
                "",
                markdown.rstrip(),
                "",
            ]
            markdown_path.write_text("\n".join(page_lines), encoding="utf-8")
            combined_entries.append((page_num, image_path, markdown_path))

    combined_path = output_dir / "technology-tables.md"
    combined_markdown = build_combined_markdown(combined_entries, combined_path)
    combined_path.write_text(combined_markdown, encoding="utf-8")

    print(f"Wrote images to {images_dir}")
    print(f"Wrote per-page markdown to {markdown_dir}")
    print(f"Wrote combined markdown to {combined_path}")


if __name__ == "__main__":
    main()
