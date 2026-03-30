from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


SOURCE = Path("docs/references/manual/Stars-manual.md")
ROOT = Path("docs/references/manual")
CHAPTERS_DIR = ROOT / "chapters"
README = ROOT / "README.md"


@dataclass(frozen=True)
class Section:
    slug: str
    title: str
    start_marker: str
    end_marker: str | None = None
    level: int = 1


SECTIONS: list[Section] = [
    Section("00-front-matter", "Front Matter", "## STARS!", "### 1"),
    Section("01-welcome-to-the-stars-universe", "1. Welcome to the Stars! Universe", "### 1", "### 2"),
    Section("02-single-player-setup", "2. Single Player Setup", "### 2", "### 3"),
    Section("03-multi-player-setup", "3. Multi-Player Setup", "### 3", "### 4"),
    Section("04-things-every-stars-player-should-know", "4. Things Every Stars! Player Should Know", "### 4", "### 5"),
    Section("05-the-stars-screen", "5. The Stars! Screen", "### 5", "### 6"),
    Section("06-planets", "6. Planets", "### 6", "### 7"),
    Section("07-production", "7. Production", "### 7", "### 8"),
    Section("08-research", "8. Research", "### 8", "### 9"),
    Section("09-ship-and-starbase-design", "9. Ship and Starbase Design", "### 9", "### 10 MANAGING FLEETS"),
    Section("10-managing-fleets", "10. Managing Fleets", "### 10 MANAGING FLEETS", "### 11 NAVIGATION"),
    Section("11-navigation", "11. Navigation", "### 11 NAVIGATION", "### 12"),
    Section("12-colonization", "12. Colonization", "### 12", "### 13 MINING"),
    Section("13-mining", "13. Mining", "### 13 MINING", "### 14"),
    Section("14-transporting-freight", "14. Transporting Freight", "### 14", "### 15"),
    Section("15-the-basics-of-combat", "15. The Basics of Combat", "### 15", "### 16"),
    Section("16-patrolling", "16. Patrolling", "### 16", "### 17"),
    Section("17-scanning-and-cloaking", "17. Scanning and Cloaking", "### 17", "### 18"),
    Section("18-reports", "18. Reports", "### 18", "### 19 DIPLOMACY AND TRADE"),
    Section("19-diplomacy-and-trade", "19. Diplomacy and Trade", "### 19 DIPLOMACY AND TRADE", "### RACE CREATION"),
    Section("20-designing-custom-races", "20. Designing Custom Races", "### 20 DESIGNING CUSTOM RACES", "### 21"),
    Section("21-predefined-races", "21. Predefined Races", "### 21", "### 22"),
    Section("22-alternate-reality-races", "22. Alternate Reality Races", "### 22", "### THE GUTS OF STARS!"),
    Section("23-the-guts-of-combat", "23. The Guts of Combat", "### 23", "### 24"),
    Section("24-the-guts-of-cloaking", "24. The Guts of Cloaking", "### 24", "### 25"),
    Section("25-the-guts-of-mass-drivers", "25. The Guts of Mass Drivers", "### 25", "### 26"),
    Section("26-the-guts-of-minefields", "26. The Guts of Minefields", "### 26", "### BACK OF THE BOOK"),
    Section("appendix-a-keyboard-shortcuts", "Appendix A. Keyboard Shortcuts", "### KEYBOARD SHORTCUTS", "### B"),
    Section("appendix-b-technology-tables", "Appendix B. Technology Tables", "### TECHNOLOGY TABLES", "### FILES USED IN STARS!"),
    Section("appendix-c-files-used-in-stars", "Appendix C. Files Used in Stars!", "### FILES USED IN STARS!", "### FREQUENTLY ASKED"),
    Section("appendix-d-frequently-asked-questions", "Appendix D. Frequently Asked Questions", "### FREQUENTLY ASKED", "### INDEX"),
    Section("index", "Index", "### INDEX", None),
]


def find_marker(lines: list[str], marker: str) -> int:
    for i, line in enumerate(lines):
        if line.strip() == marker:
            return i
    raise ValueError(f"Could not find marker: {marker}")


def clean_heading_line(line: str) -> str:
    text = re.sub(r"^#+\s*", "", line).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def title_case_heading(text: str) -> str:
    keep_upper = {"AI", "FTP", "DOS", "INI", "FAQ", "VCR", "STARS!"}
    words = []
    for word in text.split():
        if word in keep_upper:
            words.append(word)
        elif word.isupper() and len(word) > 1:
            words.append(word.title())
        else:
            words.append(word)
    return " ".join(words)


def canonicalize(text: str) -> str:
    text = text.upper()
    text = re.sub(r"^(APPENDIX [A-Z]\.\s+|\d+\.\s+)", "", text)
    text = text.replace("STARS!-SCREEN", "THE STARS! SCREEN")
    text = re.sub(r"[^A-Z0-9!]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_content(text: str, title: str) -> str:
    lines = text.strip().splitlines()
    while lines and lines[0].strip() == "":
        lines.pop(0)
    while lines and lines[-1].strip() == "":
        lines.pop()

    body = "\n".join(lines).strip()

    # Remove broken numeric/title heading fragments at section starts.
    patterns = [
        r"^(?:###\s+\d+\n)+",
        r"^(?:###\s+0\n)+",
        r"^###\s+[A-Z]\n",
        r"^###\s+" + re.escape(title.split(". ", 1)[-1]).replace(r"\ ", r"\s+") + r"\n",
    ]
    for pattern in patterns:
        body = re.sub(pattern, "", body, count=1, flags=re.IGNORECASE)

    body_lines = body.splitlines()
    while body_lines and body_lines[0].startswith("#"):
        if canonicalize(clean_heading_line(body_lines[0])) == canonicalize(title):
            body_lines.pop(0)
            while body_lines and body_lines[0].strip() == "":
                body_lines.pop(0)
        else:
            break
    body = "\n".join(body_lines).strip()

    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    heading = f"# {title_case_heading(title)}"
    return f"{heading}\n\n{body}\n"


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    lines = text.splitlines()

    CHAPTERS_DIR.mkdir(parents=True, exist_ok=True)

    sections_with_bounds: list[tuple[Section, int, int]] = []
    for idx, section in enumerate(SECTIONS):
        start = find_marker(lines, section.start_marker)
        if section.end_marker:
            end = find_marker(lines, section.end_marker)
        elif idx + 1 < len(SECTIONS):
            end = find_marker(lines, SECTIONS[idx + 1].start_marker)
        else:
            end = len(lines)
        sections_with_bounds.append((section, start, end))

    for section, start, end in sections_with_bounds:
        chunk = "\n".join(lines[start:end]).strip() + "\n"
        normalized = normalize_content(chunk, section.title)
        (CHAPTERS_DIR / f"{section.slug}.md").write_text(normalized, encoding="utf-8")

    front_matter = [s for s in SECTIONS if s.slug == "00-front-matter"][0]
    numbered = [s for s in SECTIONS if re.match(r"^(?!00-)\d\d-", s.slug)]
    appendices = [s for s in SECTIONS if s.slug.startswith("appendix-")]
    index = [s for s in SECTIONS if s.slug == "index"][0]

    readme_lines = [
        "# Stars! Manual",
        "",
        "This folder contains a split, navigable version of the original `Stars-manual.md`.",
        "",
        "## Contents",
        "",
        f"- [{front_matter.title}](chapters/{front_matter.slug}.md)",
    ]
    readme_lines.extend(f"- [{section.title}](chapters/{section.slug}.md)" for section in numbered)
    readme_lines.append("")
    readme_lines.append("## Appendices")
    readme_lines.append("")
    readme_lines.extend(f"- [{section.title}](chapters/{section.slug}.md)" for section in appendices)
    readme_lines.append(f"- [{index.title}](chapters/{index.slug}.md)")
    readme_lines.append("")
    readme_lines.append("## Sources")
    readme_lines.append("")
    readme_lines.append("- [Original PDF](Stars-manual.pdf)")
    readme_lines.append("- [Raw extraction](Stars-manual.raw.md)")
    readme_lines.append("- [Single-file cleaned manual](Stars-manual.md)")
    readme_lines.append("")

    README.write_text("\n".join(readme_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
