#!/usr/bin/env python3
"""Mirror and translate the Elite Games Stars! documentation subtree."""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


BASE_URL = "https://www.elite-games.ru/stars/doc/"
DEFAULT_OUTPUT = Path("docs/references/elite-games-ru-en")
RAW_HOST_ROOT = "www.elite-games.ru/stars/doc"
USER_AGENT = "Mozilla/5.0 (compatible; OpenStars EliteGames importer/1.0)"
CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output directory for the mirrored and translated docs",
    )
    parser.add_argument(
        "--skip-mirror",
        action="store_true",
        help="Reuse an existing mirror and only rebuild the extracted/translated files",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only process the first N HTML files for testing",
    )
    return parser.parse_args()


def run_wget(output: Path) -> None:
    raw_root = output / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    command = [
        "wget",
        "--mirror",
        "--no-parent",
        "--no-verbose",
        "--adjust-extension",
        "--directory-prefix",
        str(raw_root),
        BASE_URL,
    ]
    result = subprocess.run(command, check=False)
    if result.returncode not in (0, 8):
        raise subprocess.CalledProcessError(result.returncode, command)


def load_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(path: Path, cache: dict[str, str]) -> None:
    path.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def page_files(raw_root: Path) -> list[Path]:
    doc_root = raw_root / RAW_HOST_ROOT
    files = sorted(doc_root.rglob("*.html")) + sorted(doc_root.rglob("*.shtml"))
    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in files:
        if path not in seen:
            deduped.append(path)
            seen.add(path)
    return deduped


def source_url_for(raw_root: Path, file_path: Path) -> str:
    relative = file_path.relative_to(raw_root / RAW_HOST_ROOT).as_posix()
    if relative == "index.html":
        return BASE_URL
    if relative.endswith(".shtml.html"):
        return BASE_URL + relative[: -len(".html")]
    if relative.endswith(".html"):
        return BASE_URL + relative[: -len(".html")] + "/"
    return BASE_URL + relative


def extract_title(document: str) -> str:
    match = re.search(r"<title>(.*?)</title>", document, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return "Untitled"
    title = cleanup_text(match.group(1))
    title = re.sub(r"\s*\(Elite Games\)\s*$", "", title)
    return title


def extract_main_html(document: str) -> str:
    document = re.sub(r"(?is)<script.*?</script>", "", document)
    document = re.sub(r"(?is)<style.*?</style>", "", document)
    chat_split = re.split(r"<!--\s*chat\s*-->", document, maxsplit=1, flags=re.IGNORECASE)
    body = chat_split[0]
    start_patterns = [
        r'(?is)<td[^>]*valign="?top"?[^>]*>',
        r"(?is)<body[^>]*>",
    ]
    for pattern in start_patterns:
        match = re.search(pattern, body)
        if match:
            body = body[match.end() :]
            break
    return body


def html_to_text(fragment: str) -> str:
    replacements = [
        (r"(?i)<br\s*/?>", "\n"),
        (r"(?i)</p>", "\n\n"),
        (r"(?i)</div>", "\n"),
        (r"(?i)</tr>", "\n"),
        (r"(?i)</table>", "\n"),
        (r"(?i)</li>", "\n"),
        (r"(?i)<li[^>]*>", "- "),
        (r"(?i)<tr[^>]*>", ""),
        (r"(?i)<t[dh][^>]*>", " | "),
        (r"(?i)</t[dh]>", " "),
        (r"(?i)</h[1-6]>", "\n\n"),
        (r"(?i)<h[1-6][^>]*>", ""),
        (r"(?i)<hr[^>]*>", "\n---\n"),
    ]
    text = fragment
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    text = re.sub(r"(?is)<!--.*?-->", "", text)
    text = re.sub(r"(?is)<a [^>]*href=['\"]([^'\"]+)['\"][^>]*>", "", text)
    text = re.sub(r"(?is)<img [^>]*alt=['\"]([^'\"]*)['\"][^>]*>", r" [Image: \1] ", text)
    text = re.sub(r"(?is)<img [^>]*>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", "", text)
    text = cleanup_text(text)
    lines = [normalise_table_row(line) for line in text.splitlines()]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def normalise_table_row(line: str) -> str:
    line = re.sub(r"(?:\s*\|\s*){2,}", " | ", line.strip())
    return line.strip(" |")


def cleanup_text(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    text = text.replace("\r", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def chunk_text(text: str, max_chars: int = 3000) -> list[str]:
    paragraphs = re.split(r"(\n\s*\n)", text)
    chunks: list[str] = []
    current = ""
    for part in paragraphs:
        if len(current) + len(part) <= max_chars:
            current += part
            continue
        if current:
            chunks.append(current)
            current = ""
        if len(part) <= max_chars:
            current = part
            continue
        for line in part.splitlines(keepends=True):
            if len(current) + len(line) > max_chars and current:
                chunks.append(current)
                current = ""
            current += line
        if current and len(current) >= max_chars:
            chunks.append(current)
            current = ""
    if current:
        chunks.append(current)
    return [chunk for chunk in chunks if chunk.strip()]


def translate_chunk(text: str, cache: dict[str, str]) -> str:
    if text in cache:
        return cache[text]
    if not CYRILLIC_RE.search(text):
        cache[text] = text
        return text
    translated = request_translation(text)
    cache[text] = translated
    time.sleep(0.2)
    return translated


def request_translation(text: str) -> str:
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=ru&tl=en&dt=t&q={quote(text)}"
    )
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    translated = "".join(item[0] for item in payload[0] if item and item[0])
    return translated.strip()


def translate_text(text: str, cache: dict[str, str]) -> str:
    chunks = chunk_text(text)
    return "\n\n".join(translate_chunk(chunk, cache) for chunk in chunks)


def output_relative_path(raw_root: Path, file_path: Path) -> Path:
    relative = file_path.relative_to(raw_root / RAW_HOST_ROOT)
    if relative.name == "index.html":
        return relative.with_name("index.md")
    if relative.as_posix().endswith(".shtml.html"):
        return relative.with_suffix("").with_suffix(".md")
    if relative.suffix == ".html":
        return relative.with_suffix(".md")
    return relative.with_suffix(".md")


def destination_paths(output: Path, raw_root: Path, file_path: Path) -> tuple[Path, Path]:
    relative = file_path.relative_to(raw_root / RAW_HOST_ROOT)
    source_copy = output / "source-html" / relative
    translated = output / "translated-markdown" / output_relative_path(raw_root, file_path)
    return source_copy, translated


def translate_page(
    output: Path,
    raw_root: Path,
    file_path: Path,
    cache: dict[str, str],
) -> dict[str, str]:
    document = file_path.read_text(encoding="cp1251", errors="replace")
    title = extract_title(document)
    translated_title = translate_text(title, cache)
    text = html_to_text(extract_main_html(document))
    source_url = source_url_for(raw_root, file_path)
    translated = translate_text(text, cache)
    source_copy, translated_path = destination_paths(output, raw_root, file_path)

    source_copy.parent.mkdir(parents=True, exist_ok=True)
    translated_path.parent.mkdir(parents=True, exist_ok=True)

    source_copy.write_text(document, encoding="utf-8")
    translated_body = (
        f"# {translated_title}\n\n"
        f"Source URL: {source_url}\n\n"
        f"Original title: {title}\n\n"
        "Note: Automatically translated from Russian. Review against the source "
        "HTML before relying on subtle rules wording.\n\n"
        f"{translated}\n"
    )
    translated_path.write_text(translated_body, encoding="utf-8")

    return {
        "title": title,
        "translated_title": translated_title,
        "source_url": source_url,
        "source_html": source_copy.relative_to(output).as_posix(),
        "translated_markdown": translated_path.relative_to(output).as_posix(),
    }


def write_readme(output: Path, manifest: list[dict[str, str]]) -> None:
    lines = [
        "# Elite Games Stars! Docs",
        "",
        "This folder contains a mirrored snapshot of `https://www.elite-games.ru/stars/doc/`",
        "and an automatic English translation pass.",
        "",
        "## Structure",
        "",
        "- `raw/` — direct wget mirror of the source site",
        "- `source-html/` — UTF-8 re-encoded HTML copies for pages we processed",
        "- `translated-markdown/` — extracted English translations in Markdown",
        "- `manifest.json` — mapping from source URLs to generated files",
        "",
        "## Caveats",
        "",
        "- Translation is automatic, not hand-edited.",
        "- Tables are flattened into readable text rows rather than recreated as exact HTML tables.",
        "- Re-check subtle mechanics against the original Russian before treating wording as authoritative.",
        "",
        f"Processed pages: {len(manifest)}",
        "",
    ]
    (output / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    if not args.skip_mirror:
        run_wget(output)

    raw_root = output / "raw"
    files = page_files(raw_root)
    if args.limit:
        files = files[: args.limit]

    cache_path = output / "translation-cache.json"
    cache = load_cache(cache_path)
    manifest: list[dict[str, str]] = []
    for file_path in files:
        manifest.append(translate_page(output, raw_root, file_path, cache))
        save_cache(cache_path, cache)

    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_readme(output, manifest)


if __name__ == "__main__":
    main()
