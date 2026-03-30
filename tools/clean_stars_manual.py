from __future__ import annotations

import re
import argparse
from pathlib import Path


DEFAULT_INPUT_PATH = Path("docs/references/Stars-manual.raw.md")
DEFAULT_OUTPUT_PATH = Path("docs/references/Stars-manual.md")

HEADER_RE = re.compile(r"^715 Stars Guide .* Page (?:[ivxlcdm]+|\d+)$", re.IGNORECASE)
PAGE_NUM_RE = re.compile(r"^\d+-\d+$")
ROMAN_RE = re.compile(r"^[IVXLCDM]+$")
TOC_ENTRY_RE = re.compile(r"^(?P<title>.+?)\s+(?P<page>\d+-\d+)$")


def is_spaced_caps(line: str) -> bool:
    stripped = line.strip()
    return bool(re.fullmatch(r"[A-Z][A-Z !&'\-\.]*(?:\s+[A-Z !&'\-\.]+)*", stripped)) and bool(
        re.search(r"(?:^| )([A-Z!]|-)(?: (?:[A-Z!]|-))+", stripped)
    )


def is_running_header(line: str) -> bool:
    stripped = line.strip()
    if re.fullmatch(r"-\s+[A-Z0-9 !&'()./\-]+", stripped) and not re.search(r"[a-z]", stripped):
        return True
    if re.search(r"[A-Z]?\d+\s*-\s*\d+$|[A-Z]-\d+$", stripped):
        prefix = re.sub(r"\s+(?:[A-Z]?\d+\s*-\s*\d+|[A-Z]-\d+)$", "", stripped).strip()
        if prefix and not re.search(r"[a-z]", prefix):
            return True
    return False


def is_upper_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) > 90 or "http" in stripped.lower():
        return False
    stripped = re.sub(r"\s+\d+-\d+$", "", stripped)
    if stripped.startswith(("1.", "2.", "3.", "4.", "5.", "-", "*")):
        return False
    alpha_chars = [ch for ch in stripped if ch.isalpha()]
    if not alpha_chars:
        return False
    if any(ch.islower() for ch in alpha_chars):
        return False
    words = stripped.split()
    if len(words) > 10:
        return False
    return True


def is_sentence(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith(("#", "-", "*", ">")):
        return False
    if re.match(r"^\d+\.", stripped):
        return False
    return bool(re.search(r"[a-z]", stripped))


def normalize_bullet(line: str) -> str:
    stripped = line.strip()
    if stripped.startswith("¯ "):
        return f"- {stripped[2:].strip()}"
    if stripped == "·":
        return "- "
    if stripped.startswith("· "):
        return f"- {stripped[2:].strip()}"
    return stripped


def flush_paragraph(buffer: list[str], out: list[str]) -> None:
    if not buffer:
        return
    text = " ".join(part.strip() for part in buffer)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    out.append(text)
    out.append("")
    buffer.clear()


def clean_lines(raw_text: str) -> list[str]:
    text = raw_text.replace("\f", "\n")
    raw_lines = [line.rstrip() for line in text.splitlines()]

    filtered: list[str] = []
    prev_blank = True

    for line in raw_lines:
        stripped = line.strip()
        if HEADER_RE.match(stripped):
            continue
        if is_spaced_caps(stripped):
            continue
        if is_running_header(stripped):
            continue
        if stripped == "":
            if not prev_blank:
                filtered.append("")
            prev_blank = True
            continue
        filtered.append(stripped)
        prev_blank = False

    merged: list[str] = []
    i = 0
    while i < len(filtered):
        line = filtered[i]
        if line in {"Winning", "Stars! Copy"}:
            i += 1
            continue
        if line in {"- Conditions, p", "- Protection, p"}:
            i += 1
            continue
        if line.startswith("creating a race in chapter 20, Designing Custom Races."):
            i += 1
            continue
        if line.lower().startswith("learn about"):
            i += 1
            while i < len(filtered):
                candidate = filtered[i]
                if candidate == "":
                    i += 1
                    break
                if len(candidate) > 50 or is_sentence(candidate) or re.match(r"^\d+\.\s", candidate):
                    break
                i += 1
            continue
        if re.match(r"^\d+\.$", line):
            j = i + 1
            while j < len(filtered) and filtered[j] == "":
                j += 1
            if j < len(filtered):
                merged.append(f"{line} {filtered[j]}")
                i = j + 1
                continue
        merged.append(line)
        i += 1

    out: list[str] = []
    paragraph: list[str] = []
    in_toc = False
    chapter_number: str | None = None

    def emit_heading(level: int, text: str) -> None:
        flush_paragraph(paragraph, out)
        heading = "#" * level + f" {text.strip()}"
        if out and out[-1] != "":
            out.append("")
        out.append(heading)
        out.append("")

    for index, line in enumerate(merged):
        next_line = merged[index + 1] if index + 1 < len(merged) else ""

        if line == "":
            flush_paragraph(paragraph, out)
            continue

        if PAGE_NUM_RE.match(line):
            continue

        if ROMAN_RE.match(line) and len(line) <= 8 and not in_toc:
            continue

        toc_match = TOC_ENTRY_RE.match(line)
        if line == "CONTENTS":
            emit_heading(2, "Contents")
            in_toc = True
            continue
        if in_toc and toc_match:
            flush_paragraph(paragraph, out)
            out.append(f"- {toc_match.group('title').strip()}")
            continue
        if in_toc and (line.isdigit() or (line.isupper() and not toc_match and len(line.split()) <= 6)):
            if line == "WELCOME":
                in_toc = False
            elif ROMAN_RE.match(line):
                continue
            else:
                emit_heading(3, line)
                continue

        if line.isdigit() and is_upper_heading(next_line):
            flush_paragraph(paragraph, out)
            chapter_number = line
            continue

        heading_line = re.sub(r"\s+\d+-\d+$", "", line).strip()
        if is_upper_heading(heading_line):
            level = 1 if chapter_number else 2
            title = f"{chapter_number}. {heading_line}" if chapter_number else heading_line
            emit_heading(level, title)
            chapter_number = None
            continue

        normalized = normalize_bullet(line)
        if normalized == "- ":
            flush_paragraph(paragraph, out)
            out.append("-")
            continue

        if normalized.startswith("- "):
            flush_paragraph(paragraph, out)
            out.append(normalized)
            continue

        if re.match(r"^\d+\.\s", normalized):
            flush_paragraph(paragraph, out)
            out.append(normalized)
            continue

        if paragraph and is_sentence(paragraph[-1]) and is_sentence(normalized):
            paragraph.append(normalized)
        else:
            flush_paragraph(paragraph, out)
            paragraph.append(normalized)

    flush_paragraph(paragraph, out)

    # Remove repeated blank lines and dangling list placeholders.
    final_lines: list[str] = []
    prev_blank = True
    for line in out:
        if line == "-":
            continue
        if line == "":
            if prev_blank:
                continue
            final_lines.append(line)
            prev_blank = True
        else:
            final_lines.append(line)
            prev_blank = False

    return final_lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", default=str(DEFAULT_INPUT_PATH))
    parser.add_argument("output", nargs="?", default=str(DEFAULT_OUTPUT_PATH))
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    raw_text = input_path.read_text(encoding="utf-8")
    cleaned = "\n".join(clean_lines(raw_text)).rstrip() + "\n"
    output_path.write_text(cleaned, encoding="utf-8")


if __name__ == "__main__":
    main()
