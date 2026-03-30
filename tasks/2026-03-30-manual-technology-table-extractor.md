# Manual Technology Table Extractor

Status: ✅ Complete

## Goal

Add a `uv`-runnable Python tool that extracts the Stars! manual technology table pages from the PDF as images and converts their OCR output into Markdown tables.

## Steps

- [x] Review the existing manual-processing scripts and choose a dependency approach that works with `uv`.
- [x] Add a standalone extraction script under `tools/` with inline `uv` dependencies.
- [x] Support selected page ranges, PNG page extraction, OCR, and Markdown output.
- [x] Verify the script entrypoint and document the expected usage in the script help text.

## Notes

- ✅ Implemented `tools/extract_manual_technology_tables.py` as a self-contained `uv run` script using PyMuPDF for page rendering and RapidOCR for OCR.
- ✅ The script writes per-page PNG renders, per-page Markdown, and a combined Markdown file with image links and reconstructed tables.
- ✅ Table reconstruction is heuristic. It groups OCR boxes into rows and approximate columns, which is a good starting point for manual cleanup but may still need hand-fixing for noisy scans.
