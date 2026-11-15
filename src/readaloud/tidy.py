"""Deterministic speech rules. Nothing here summarizes or paraphrases."""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

CODE_MARK = "\ue000CODE{n}\ue001"
MATH_OMITTED = "equation omitted"
CODE_OMITTED = "code sample omitted"

_FENCE = re.compile(r"(```[^\n]*\n.*?```|~~~[^\n]*\n.*?~~~)", re.S)
_INLINE_CODE = re.compile(r"`([^`\n]+)`")
_DISPLAY_DOLLAR = re.compile(r"\$\$.*?\$\$", re.S)
_DISPLAY_BRACKET = re.compile(r"\\\[.*?\\\]", re.S)
_INLINE_PAREN = re.compile(r"\\\(.*?\\\)", re.S)
_INLINE_DOLLAR = re.compile(r"\$[^$\n]+\$")
_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_URL = re.compile(r"https?://\S+|www\.\S+", re.I)
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_CITE_NUM = re.compile(r"\[(?:\^?\d+(?:\s*[,;\-–]\s*\^?\d+)*)\]")
_CITE_YEAR = re.compile(
    r"\((?:[A-Z][A-Za-z'`-]+(?:\s+(?:and|&)\s+[A-Z][A-Za-z'`-]+|\s+et\s+al\.?)?"
    r"(?:,\s*)+)+(?:19|20)\d{2}[a-z]?(?:;\s*[^()]{0,80})?\)"
)
_YAML = re.compile(r"\A---\n.*?\n---\n?", re.S)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
_PAGE_LINE = re.compile(
    r"^\s*(?:Page\s+)?\d{1,4}\s*(?:of\s+\d{1,4})?\s*$", re.I
)
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_BULLET = re.compile(r"^\s*[-*+]\s+")
_ORDERED = re.compile(r"^\s*\d+[.)]\s+")
_QUOTE = re.compile(r"^\s*>\s?")
_TABLE_LINE = re.compile(r"^\s*\|.*\|\s*$")
_TABLE_RULE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
_RULE = re.compile(r"^\s*([-*_])\1{2,}\s*$")
_BOLD = re.compile(r"(\*\*|__)(.*?)\1")
_ITALIC = re.compile(r"(\*|_)(?=\S)(.+?)(?<=\S)\1")
_HYPHEN_BREAK = re.compile(r"(\w)-\n(\w)")


@dataclass
class TidyOptions:
    math: str = "omit"
    code: str = "speak"
    tables: str = "speak"
    citations: str = "keep"
    pronunciations: dict[str, str] = field(default_factory=dict)


@dataclass
class TidyStats:
    chars_in: int = 0
    chars_out: int = 0
    math_spans: int = 0
    urls_removed: int = 0
    link_urls_stripped: int = 0
    emails_removed: int = 0
    code_blocks_omitted: int = 0

    @property
    def percent_kept(self) -> int:
        if self.chars_in <= 0:
            return 100
        return (self.chars_out * 100) // self.chars_in


@dataclass
class Segment:
    text: str
    kind: str
    chapter_title: str | None = None


@dataclass
class TidyResult:
    spoken: str
    segments: list[Segment]
    stats: TidyStats


def repo_root() -> Path:
    home = os.environ.get("READALOUD_HOME")
    if home:
        path = Path(home).expanduser().resolve()
        if (path / "pronunciations.txt").is_file():
            return path
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pronunciations.txt").is_file() and (parent / "pyproject.toml").is_file():
            return parent
    return Path.cwd()


def load_pronunciations(path: Path | None = None) -> dict[str, str]:
    source = path or (repo_root() / "pronunciations.txt")
    mapping: dict[str, str] = {}
    if not source.is_file():
        return mapping
    for raw in source.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        term, spoken = line.split("=", 1)
        term = term.strip()
        spoken = spoken.strip()
        if term and spoken:
            mapping[term] = spoken
    return mapping


def apply_pronunciations(text: str, mapping: dict[str, str]) -> str:
    for term in sorted(mapping, key=len, reverse=True):
        replacement = mapping[term]
        pattern = re.compile(rf"(?<!\w){re.escape(term)}(?!\w)")
        text = pattern.sub(replacement, text)
    return text


def _count_sub(pattern: re.Pattern[str], text: str, replacement: str) -> tuple[str, int]:
    count = 0

    def _replace(_match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return replacement

    return pattern.sub(_replace, text), count


def _strip_emphasis(text: str) -> str:
    previous = None
    while previous != text:
        previous = text
        text = _BOLD.sub(r"\2", text)
        text = _ITALIC.sub(r"\2", text)
    return text


def _table_speech(lines: list[str]) -> str:
    rows: list[str] = []
    for line in lines:
        if _TABLE_RULE.match(line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        cells = [cell for cell in cells if cell and not re.fullmatch(r":?-{3,}:?", cell)]
        if cells:
            rows.append(", ".join(cells) + ".")
    return " ".join(rows)


def _ensure_sentence(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    if stripped[-1] in ".!?":
        return stripped
    return stripped + "."


def tidy(text: str, options: TidyOptions | None = None) -> TidyResult:
    options = options or TidyOptions()
    stats = TidyStats(chars_in=len(text))
    working = unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")
    working = _YAML.sub("", working, count=1)
    working = _HTML_COMMENT.sub("", working)

    code_blocks: list[str] = []

    def _hold_fence(match: re.Match[str]) -> str:
        body = match.group(0)
        body = re.sub(r"^```[^\n]*\n|^~~~[^\n]*\n", "", body)
        body = re.sub(r"```\s*$|~~~\s*$", "", body)
        code_blocks.append(body.strip("\n"))
        return "\n" + CODE_MARK.format(n=len(code_blocks) - 1) + "\n"

    working = _FENCE.sub(_hold_fence, working)
    working = _INLINE_CODE.sub(r"\1", working)

    if options.math == "omit":
        for pattern in (_DISPLAY_DOLLAR, _DISPLAY_BRACKET, _INLINE_PAREN, _INLINE_DOLLAR):
            working, found = _count_sub(pattern, working, f" {MATH_OMITTED} ")
            stats.math_spans += found

    def _image(match: re.Match[str]) -> str:
        alt = match.group(1).strip()
        return f" {alt} " if alt else " "

    working = _IMAGE.sub(_image, working)

    def _link(match: re.Match[str]) -> str:
        stats.link_urls_stripped += 1
        return match.group(1)

    working = _LINK.sub(_link, working)
    working, bare_urls = _count_sub(_URL, working, " ")
    stats.urls_removed += bare_urls
    working, stats.emails_removed = _count_sub(_EMAIL, working, " ")

    if options.citations in {"numeric", "all"}:
        working = _CITE_NUM.sub(" ", working)
    if options.citations == "all":
        working = _CITE_YEAR.sub(" ", working)

    working = _HYPHEN_BREAK.sub(r"\1\2", working)

    segments: list[Segment] = []
    paragraph: list[str] = []
    table: list[str] = []

    def flush_paragraph() -> None:
        if not paragraph:
            return
        joined = _strip_emphasis(" ".join(paragraph))
        joined = re.sub(r"[ \t]+", " ", joined).strip()
        paragraph.clear()
        if joined:
            segments.append(Segment(joined, "body"))

    def flush_table() -> None:
        if not table:
            return
        rows = list(table)
        table.clear()
        if options.tables == "skip":
            return
        spoken = _strip_emphasis(_table_speech(rows))
        if spoken:
            segments.append(Segment(spoken, "body"))

    for raw_line in working.split("\n"):
        line = raw_line.rstrip()
        code_match = re.fullmatch(r"\s*\ue000CODE(\d+)\ue001\s*", line)
        if code_match:
            flush_paragraph()
            flush_table()
            block = code_blocks[int(code_match.group(1))]
            if options.code == "omit":
                stats.code_blocks_omitted += 1
                segments.append(Segment(CODE_OMITTED + ".", "body"))
            elif block.strip():
                segments.append(Segment(_ensure_sentence(_strip_emphasis(block)), "body"))
            continue

        if _TABLE_LINE.match(line) or _TABLE_RULE.match(line):
            flush_paragraph()
            table.append(line)
            continue
        flush_table()

        if not line.strip():
            flush_paragraph()
            continue
        if _PAGE_LINE.match(line) or _RULE.match(line):
            flush_paragraph()
            continue

        heading = _HEADING.match(line)
        if heading:
            flush_paragraph()
            words = _strip_emphasis(heading.group(2)).strip()
            words = re.sub(r"[ \t]+", " ", words)
            if words:
                segments.append(Segment(_ensure_sentence(words), "heading", words))
            continue

        cleaned = _QUOTE.sub("", line)
        cleaned = _BULLET.sub("", cleaned)
        cleaned = _ORDERED.sub("", cleaned)
        cleaned = cleaned.strip()
        if cleaned:
            paragraph.append(cleaned)

    flush_paragraph()
    flush_table()

    spoken_segments: list[Segment] = []
    for segment in segments:
        text = apply_pronunciations(segment.text, options.pronunciations)
        text = re.sub(r"[ \t]+", " ", text).strip()
        text = re.sub(r"\s+([.,;:!?])", r"\1", text)
        if text:
            spoken_segments.append(
                Segment(text, segment.kind, segment.chapter_title)
            )

    spoken = "\n\n".join(segment.text for segment in spoken_segments)
    if spoken:
        spoken += "\n"
    stats.chars_out = len(spoken)
    return TidyResult(spoken=spoken, segments=spoken_segments, stats=stats)
