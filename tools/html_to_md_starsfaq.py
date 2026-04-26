#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["beautifulsoup4", "html5lib"]
# ///
"""
html_to_md_starsfaq.py — Convert Stars!-R-Us HTML articles to clean markdown.

Usage:
    uv run tools/html_to_md_starsfaq.py

Reads every .htm file in:
    local-data/starsfaq/www.starsfaq.com/articles/sru/

Writes .md files to:
    docs/references/starsfaq/

The index page (art_economics.htm) is converted to index.md with category
sections and links to each article. All other files are converted as articles.

To add a single article not caught by the spider:
    wget --directory-prefix=local-data/starsfaq/www.starsfaq.com/articles/sru \\
         http://www.starsfaq.com/articles/sru/artNNN.htm
    uv run tools/html_to_md_starsfaq.py

Quirks handled:
  - Root tag is <htm> not <html> — fixed before parsing.
  - Unclosed <p> and <h4> tags: html5lib parser handles implicit closing.
  - <h4> tags often contain their following <p> children (html5lib nesting) —
    inline_text() extracts only the heading text; block children are processed
    separately.
  - <br><br> used as paragraph separator within <p> tags — split on double newline.
  - Email-quoted lines (starting with >) converted to markdown blockquotes and
    merged into a single block per paragraph.
  - HTML comments stripped (BeautifulSoup Comment is a NavigableString subclass
    and would otherwise appear as text).
  - Malformed wrapper tags (e.g. <href="...">) treated as transparent containers.
  - Mixed UTF-8 / Latin-1 encoding in source files normalised before parsing.
  - Navigation links ("Back to Article Main Page") removed from output.
"""

import re
from pathlib import Path
from bs4 import BeautifulSoup, Comment, NavigableString, Tag

INPUT_DIR = Path(__file__).parent.parent / "local-data/starsfaq/www.starsfaq.com/articles/sru"
OUTPUT_DIR = Path(__file__).parent.parent / "docs/references/starsfaq"

PARSER = 'html5lib'
BLOCK_TAGS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'table', 'ul', 'ol', 'blockquote', 'pre'}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def element_text(elem: Tag) -> str:
    """Render element text, converting <br> to newline."""
    parts = []
    for child in elem.children:
        if isinstance(child, Comment):
            continue
        if isinstance(child, NavigableString):
            parts.append(str(child))
        elif isinstance(child, Tag):
            if child.name == 'br':
                parts.append('\n')
            elif child.name not in ('script', 'style'):
                parts.append(element_text(child))
    return ''.join(parts)


def has_quoted_lines(text: str) -> bool:
    return any(line.strip().startswith('>') for line in text.splitlines() if line.strip())


def quoted_to_blockquote(text: str) -> str:
    out = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith('>'):
            content = s[1:].strip()
            out.append(f'> {content}' if content else '>')
        elif s:
            out.append(s)
    return '\n'.join(out)


def is_nav_link(tag: Tag) -> bool:
    text = tag.get_text().lower()
    return 'back to' in text or 'article main page' in text


def table_to_markdown(table: Tag) -> str:
    # html5lib inserts <tbody>; fall back to direct children
    tbody = table.find('tbody') or table
    rows = []
    for tr in tbody.find_all('tr', recursive=False):
        # recursive=False avoids picking up cells from nested tables
        cells = [clean_text(td.get_text()) for td in tr.find_all(['td', 'th'], recursive=False)]
        if any(cells):
            rows.append(cells)

    if not rows:
        return ''

    col_count = max(len(r) for r in rows)
    for row in rows:
        row += [''] * (col_count - len(row))

    widths = [max(max(len(r[i]) for r in rows), 3) for i in range(col_count)]

    def fmt(row: list[str]) -> str:
        return '| ' + ' | '.join(cell.ljust(widths[i]) for i, cell in enumerate(row)) + ' |'

    sep = '| ' + ' | '.join('-' * w for w in widths) + ' |'
    return '\n'.join([fmt(rows[0]), sep] + [fmt(r) for r in rows[1:]])


# ---------------------------------------------------------------------------
# Article conversion
# ---------------------------------------------------------------------------

def _load(html_path: Path) -> BeautifulSoup:
    raw = html_path.read_bytes()
    # Try UTF-8; fall back to Latin-1 for old HTML files that mix encodings
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        text = raw.decode('latin-1')
    # Normalize non-breaking spaces
    text = text.replace(' ', ' ').replace('\xc2\xa0', ' ')
    # These files use <htm> instead of <html> — fix before parsing
    text = re.sub(r'(?i)</?htm(\s|>)', lambda m: m.group(0).replace('htm', 'html', 1), text)
    return BeautifulSoup(text, PARSER)


def convert_article(html_path: Path, output_path: Path) -> None:
    soup = _load(html_path)
    body = soup.find('body') or soup

    blocks: list[str] = []

    # Extract title/author from <h3>
    h3 = body.find('h3')
    if h3:
        parts = [p.strip() for p in element_text(h3).split('\n') if p.strip()]
        if parts:
            blocks.append(f'# {parts[0]}')
            for p in parts[1:]:
                blocks.append(f'*{p}*')
        h3.decompose()

    # Remove nav links before body walk
    for a in list(body.find_all('a', href=True)):
        if is_nav_link(a):
            parent = a.find_parent(['h1', 'h2', 'h3', 'h4'])
            (parent or a).decompose()

    def flush_parts(parts: list[str]) -> None:
        raw_text = ''.join(parts).strip()
        if not raw_text:
            return
        # Split on blank lines (double <br> or whitespace-only lines)
        segments = re.split(r'\n[ \t]*\n', raw_text)
        bq_lines: list[str] = []

        def flush_bq() -> None:
            if bq_lines:
                blocks.append('\n'.join(bq_lines))
                bq_lines.clear()

        for seg in segments:
            seg_norm = re.sub(r'[ \t]*\n[ \t]*', '\n', seg).strip()
            if not seg_norm:
                continue
            if has_quoted_lines(seg_norm):
                # Accumulate consecutive quoted segments into one blockquote block
                bq_lines.append(quoted_to_blockquote(seg_norm))
            else:
                flush_bq()
                seg_clean = re.sub(r'\s+', ' ', seg_norm).strip()
                if seg_clean:
                    blocks.append(seg_clean)

        flush_bq()

    def process_p(p: Tag) -> None:
        parts: list[str] = []
        for child in p.children:
            if isinstance(child, Comment):
                continue
            if isinstance(child, NavigableString):
                parts.append(str(child))
            elif isinstance(child, Tag):
                if child.name == 'br':
                    parts.append('\n')
                elif child.name in BLOCK_TAGS:
                    flush_parts(parts)
                    parts.clear()
                    process_elem(child)
                elif child.name == 'a':
                    href = child.get('href', '')
                    txt = clean_text(child.get_text())
                    if href and 'starsfaq.com' not in href:
                        parts.append(f'[{txt}]({href})')
                    else:
                        parts.append(txt)
                else:
                    parts.append(element_text(child))
        flush_parts(parts)

    def inline_text(elem: Tag) -> str:
        """Extract only inline content — stops at block-level children."""
        parts = []
        for child in elem.children:
            if isinstance(child, Comment):
                continue
            if isinstance(child, NavigableString):
                parts.append(str(child))
            elif isinstance(child, Tag):
                if child.name == 'br':
                    parts.append('\n')
                elif child.name not in BLOCK_TAGS:
                    parts.append(inline_text(child))
        return ''.join(parts)

    def process_elem(elem: Tag) -> None:
        name = elem.name
        if name in ('script', 'style'):
            return
        if name == 'h4':
            # Only inline text for the heading itself; block children processed after.
            # html5lib nests following <p> tags inside <h4> due to missing </h4>,
            # so we must process those block children explicitly.
            text = clean_text(inline_text(elem)).rstrip(':').strip()
            if text:
                blocks.append(f'## {text}')
            for child in elem.children:
                if isinstance(child, Tag) and child.name in BLOCK_TAGS:
                    process_elem(child)
        elif name in ('h1', 'h2', 'h3'):
            text = clean_text(elem.get_text())
            if text:
                level = {'h1': '#', 'h2': '##', 'h3': '###'}[name]
                blocks.append(f'{level} {text}')
        elif name == 'p':
            process_p(elem)
        elif name == 'table':
            md = table_to_markdown(elem)
            if md:
                blocks.append(md)
        elif name in ('ul', 'ol'):
            items = [f'- {clean_text(li.get_text())}'
                     for li in elem.find_all('li', recursive=False)]
            if items:
                blocks.append('\n'.join(items))
        else:
            # Unknown/wrapper tags (div, center, font, malformed tags) — recurse
            for child in elem.children:
                if isinstance(child, Comment):
                    continue
                if isinstance(child, Tag):
                    process_elem(child)
                elif isinstance(child, NavigableString):
                    text = str(child).strip()
                    if text:
                        blocks.append(text)

    for child in body.children:
        if isinstance(child, Comment):
            continue
        if isinstance(child, Tag):
            process_elem(child)
        elif isinstance(child, NavigableString):
            text = str(child).strip()
            if text:
                if has_quoted_lines(text):
                    blocks.append(quoted_to_blockquote(text))
                else:
                    blocks.append(text)

    output = '\n\n'.join(b for b in blocks if b.strip())
    output = re.sub(r'\n{3,}', '\n\n', output).strip() + '\n'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding='utf-8')
    print(f'  {html_path.name} -> {output_path.name}')


# ---------------------------------------------------------------------------
# Index conversion
# ---------------------------------------------------------------------------

def convert_index(html_path: Path, output_path: Path) -> None:
    soup = _load(html_path)
    body = soup.find('body') or soup

    blocks: list[str] = []

    h1 = body.find('h1')
    if h1:
        blocks.append(f'# {clean_text(h1.get_text())}')

    # html5lib nests each <table> inside its parent <li>, so each li = category + articles
    for li in body.find_all('li'):
        table = li.find('table')
        if not table:
            continue

        # Category name = li's own text before the table
        cat_parts = []
        for node in li.children:
            if isinstance(node, Tag) and node.name == 'table':
                break
            if isinstance(node, NavigableString):
                cat_parts.append(str(node))
            elif isinstance(node, Tag):
                cat_parts.append(node.get_text())
        cat_name = clean_text(''.join(cat_parts))
        if cat_name:
            blocks.append(f'## {cat_name}')

        # Article entries from the table
        entries = []
        tbody = table.find('tbody') or table
        for tr in tbody.find_all('tr', recursive=False):
            tds = tr.find_all(['td', 'th'], recursive=False)
            if not tds:
                continue
            a = tds[0].find('a', href=True)
            if not a:
                continue
            href = a['href']
            title = clean_text(a.get_text()).strip('"')
            author  = clean_text(tds[1].get_text()) if len(tds) > 1 else ''
            year    = clean_text(tds[2].get_text()) if len(tds) > 2 else ''
            version = clean_text(tds[3].get_text()) if len(tds) > 3 else ''
            md_name = href.replace('.htm', '.md')
            meta = ' | '.join(filter(None, [author, year, version]))
            entries.append(f'- [{title}]({md_name}) — {meta}')
        if entries:
            blocks.append('\n'.join(entries))

    output = '\n\n'.join(b for b in blocks if b.strip())
    output = re.sub(r'\n{3,}', '\n\n', output).strip() + '\n'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding='utf-8')
    print(f'  {html_path.name} -> {output_path.name}')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    html_files = sorted(INPUT_DIR.glob('*.htm'))
    print(f'Converting {len(html_files)} files to {OUTPUT_DIR}')
    for html_file in html_files:
        if html_file.name == 'art_economics.htm':
            convert_index(html_file, OUTPUT_DIR / 'index.md')
        else:
            convert_article(html_file, OUTPUT_DIR / html_file.with_suffix('.md').name)
    print('Done.')


if __name__ == '__main__':
    main()
