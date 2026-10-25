"""Split a Markdown knowledge file into heading-aware chunks for embedding."""

import re
from dataclasses import dataclass

MAX_CHARS = 800
PERSIAN = re.compile(r"[؀-ۿ]")


@dataclass
class Chunk:
    """Text to embed, prefixed with its document title and section heading."""

    content: str
    heading: str
    lang: str


def detect_lang(text: str) -> str:
    """'fa' if at least 10% of the letters are Persian, else 'en'.

    The threshold is low because Persian text often lists English tool names.
    """
    letters = [c for c in text if c.isalpha()]
    persian = sum(1 for c in letters if PERSIAN.match(c))
    return "fa" if letters and persian * 10 >= len(letters) else "en"


def split_sections(markdown: str) -> tuple[str, list[tuple[str, list[str]]]]:
    """Return the '# ' title and (heading path, body lines) for each section.

    The heading path joins the current '##' and '###' headings, e.g. 'English > Origin'.
    """
    title, h2, h3 = "", "", ""
    sections: list[tuple[str, list[str]]] = []
    for line in markdown.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## "):
            h2, h3 = line[3:].strip(), ""
            sections.append((h2, []))
        elif line.startswith("### "):
            h3 = line[4:].strip()
            sections.append((f"{h2} > {h3}", []))
        elif line.strip():
            if not sections:
                sections.append(("", []))
            sections[-1][1].append(line.strip())
    return title, [(h, body) for h, body in sections if body]


def pack_lines(lines: list[str]) -> list[str]:
    """Group lines into pieces of at most MAX_CHARS; the next piece repeats the last
    line of the previous one as overlap when it fits. A single longer line stays whole."""
    pieces, current = [], []
    for line in lines:
        if current and len("\n".join([*current, line])) > MAX_CHARS:
            pieces.append("\n".join(current))
            last = current[-1]
            current = [last] if len(last) + len(line) < MAX_CHARS else []
        current.append(line)
    pieces.append("\n".join(current))
    return pieces


def chunk_markdown(markdown: str) -> tuple[str, list[Chunk]]:
    """Return the document title and its chunks."""
    title, sections = split_sections(markdown)
    chunks = []
    for heading, lines in sections:
        for piece in pack_lines(lines):
            prefix = f"{title} | {heading}" if heading else title
            lang = detect_lang(f"{heading}\n{piece}")
            chunks.append(Chunk(f"{prefix}\n{piece}", heading, lang))
    return title, chunks
