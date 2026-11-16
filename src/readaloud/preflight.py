"""Static scan and CLI suggestions before synthesis."""

from __future__ import annotations

import json
import re
import shlex
import sys
from dataclasses import dataclass, field
from pathlib import Path

from readaloud.tidy import TidyOptions, tidy

BENCHMARK_PER_KB_LIMIT = 30.0
_HEADING = re.compile(r"^#{1,6}\s+\S", re.M)
_TABLE_LINE = re.compile(r"^\s*\|.*\|\s*$", re.M)
_FENCE_OPEN = re.compile(r"^```|^~~~", re.M)
_CITE_BRACKET = re.compile(r"\[(?:\^?\d+(?:\s*[,;\-–]\s*\^?\d+)*)\]")
_CURRENCY_RISK = re.compile(r"A\$|~\$\d|\$\d+/\w")
_MULTI_DOLLAR_LINE = re.compile(r"\$[^$\n]{0,200}\$[^$\n]{0,200}\$")


@dataclass
class StructureScan:
    headings: int = 0
    table_lines: int = 0
    code_fences: int = 0
    code_fence_chars: int = 0
    list_items: int = 0
    cite_brackets: int = 0
    currency_risk_lines: int = 0
    multi_dollar_lines: int = 0


@dataclass
class SuggestPassthrough:
    """CLI options echoed into the suggested run line."""

    allow_partial_pdf: bool = False
    pdf_engine: str = "inspector"
    work: Path = field(default_factory=lambda: Path("work"))
    output: Path = field(default_factory=lambda: Path("library"))
    normalize: bool = False
    pronunciations: Path | None = None


@dataclass
class PreflightReport:
    path: Path
    chars_in: int
    spoken_kb: float
    chunks: int
    chapters: int
    segments_by_kind: dict[str, int]
    stats_math_spans: int
    stats_code_omitted: int
    structure: StructureScan
    kokoro_per_kb: float | None
    reasons: list[str] = field(default_factory=list)
    suggested_argv: list[str] = field(default_factory=list)


def scan_structure(text: str) -> StructureScan:
    scan = StructureScan()
    scan.headings = len(_HEADING.findall(text))
    scan.table_lines = len(_TABLE_LINE.findall(text))
    scan.cite_brackets = len(_CITE_BRACKET.findall(text))
    for line in text.splitlines():
        if _CURRENCY_RISK.search(line):
            scan.currency_risk_lines += 1
        if line.count("$") >= 2 and _MULTI_DOLLAR_LINE.search(line):
            scan.multi_dollar_lines += 1
    for match in re.finditer(r"(```[^\n]*\n.*?```|~~~[^\n]*\n.*?~~~)", text, re.S):
        scan.code_fences += 1
        scan.code_fence_chars += len(match.group(0))
    return scan


def load_kokoro_benchmark(work: Path) -> float | None:
    path = work / "benchmark" / "summary.json"
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    engine = payload.get("engine")
    if engine is not None and engine != "kokoro":
        return None
    per_kb = payload.get("per_kb")
    if isinstance(per_kb, (int, float)):
        return float(per_kb)
    return None


def _append_passthrough(argv: list[str], passthrough: SuggestPassthrough) -> None:
    if passthrough.allow_partial_pdf:
        argv.append("--allow-partial-pdf")
    if passthrough.pdf_engine != "inspector":
        argv.extend(["--pdf-engine", passthrough.pdf_engine])
    if passthrough.work.resolve() != Path("work").resolve():
        argv.extend(["--work", str(passthrough.work)])
    if passthrough.output.resolve() != Path("library").resolve():
        argv.extend(["-o", str(passthrough.output)])
    if passthrough.normalize:
        argv.append("--normalize")
    if passthrough.pronunciations is not None:
        argv.extend(["--pronunciations", str(passthrough.pronunciations)])


def analyze_text(
    path: Path,
    text: str,
    *,
    work: Path,
    passthrough: SuggestPassthrough | None = None,
) -> PreflightReport:
    passthrough = passthrough or SuggestPassthrough()
    structure = scan_structure(text)
    base = tidy(text, TidyOptions())
    rows_preview = tidy(text, TidyOptions(tables="rows"))
    table_row_count = sum(1 for s in rows_preview.segments if s.kind == "table_row")
    list_count = sum(1 for s in base.segments if s.kind == "list_item")
    structure.list_items = list_count

    from readaloud.cli import pieces_for

    chunks = len(pieces_for(base))
    chapters = sum(1 for s in base.segments if s.kind == "heading")
    kinds: dict[str, int] = {}
    for segment in base.segments:
        kinds[segment.kind] = kinds.get(segment.kind, 0) + 1

    spoken_kb = len(base.spoken.encode("utf-8")) / 1024
    kokoro_per_kb = load_kokoro_benchmark(work)

    reasons: list[str] = []
    flags: dict[str, str] = {}

    if table_row_count >= 2 or structure.table_lines >= 3:
        flags["tables"] = "rows"
        reasons.append(
            f"tables ({table_row_count} spoken rows, {structure.table_lines} source lines) — row-by-row is easier to follow"
        )

    if structure.code_fences >= 1 and (
        structure.code_fence_chars > 400 or structure.code_fences >= 2
    ):
        flags["code"] = "omit"
        reasons.append(
            f"code blocks ({structure.code_fences}, {structure.code_fence_chars} chars) — diagrams are hard to listen to"
        )

    if base.stats.math_spans > 0 or structure.multi_dollar_lines > 0 or structure.currency_risk_lines > 0:
        flags["math"] = "keep"
        parts = []
        if base.stats.math_spans:
            parts.append(f"{base.stats.math_spans} math span(s) under default omit")
        if structure.currency_risk_lines:
            parts.append(f"{structure.currency_risk_lines} line(s) with A$ / prices")
        if structure.multi_dollar_lines:
            parts.append(f"{structure.multi_dollar_lines} line(s) with multiple $ (omit can garble text)")
        reasons.append(" — ".join(parts) + " — use --math keep")

    if list_count >= 8 or (list_count >= 3 and spoken_kb > 5):
        reasons.append(f"{list_count} list items — already split with pauses in recent readaloud")

    if structure.cite_brackets >= 12:
        reasons.append(
            f"{structure.cite_brackets} bracket citations — consider --citations numeric for denser papers"
        )
        if spoken_kb > 8:
            flags["citations"] = "numeric"

    slow_kokoro = kokoro_per_kb is not None and kokoro_per_kb > BENCHMARK_PER_KB_LIMIT
    large_job = spoken_kb > 12
    if slow_kokoro or large_job:
        flags["engine"] = "piper"
        if slow_kokoro:
            reasons.append(
                f"last Kokoro benchmark {kokoro_per_kb:.1f} s/KB (over {BENCHMARK_PER_KB_LIMIT:.0f}) — use Piper"
            )
        elif large_job:
            reasons.append(f"~{spoken_kb:.1f} KB spoken — long job; Piper is usually faster on this class of CPU")

    if not flags.get("engine") and kokoro_per_kb is None and spoken_kb > 8:
        reasons.append("no work/benchmark/summary.json — run `python -m readaloud --benchmark` once to tune engine choice")

    argv = [sys.executable, "-m", "readaloud", str(path.resolve())]
    for key in ("engine", "tables", "math", "code", "citations"):
        if key in flags:
            argv.extend([f"--{key}", flags[key]])
    _append_passthrough(argv, passthrough)

    return PreflightReport(
        path=path,
        chars_in=base.stats.chars_in,
        spoken_kb=spoken_kb,
        chunks=chunks,
        chapters=chapters,
        segments_by_kind=kinds,
        stats_math_spans=base.stats.math_spans,
        stats_code_omitted=0,
        structure=structure,
        kokoro_per_kb=kokoro_per_kb,
        reasons=reasons,
        suggested_argv=argv,
    )


def format_report(report: PreflightReport) -> str:
    lines = [
        f"check: {report.path.name}",
        f"  spoken: ~{report.spoken_kb:.1f} KB ({report.chunks} synthesis chunks, {report.chapters} chapters)",
        f"  segments: {', '.join(f'{k}={v}' for k, v in sorted(report.segments_by_kind.items()))}",
        (
            f"  structure: headings={report.structure.headings} tables={report.structure.table_lines} "
            f"fences={report.structure.code_fences} list_items={report.structure.list_items} "
            f"cite_brackets={report.structure.cite_brackets}"
        ),
    ]
    if report.kokoro_per_kb is not None:
        lines.append(f"  Kokoro benchmark on this machine: {report.kokoro_per_kb:.1f} s/KB")
    if report.reasons:
        lines.append("  suggestions:")
        for reason in report.reasons:
            lines.append(f"    - {reason}")
    else:
        lines.append("  suggestions: default flags look fine")
    lines.append("")
    lines.append(f"  run: {shlex.join(report.suggested_argv)}")
    return "\n".join(lines) + "\n"


def analyze_path(
    path: Path,
    *,
    pdf_engine: str,
    allow_partial_pdf: bool,
    work: Path,
    stem: str,
    passthrough: SuggestPassthrough | None = None,
) -> PreflightReport:
    from readaloud.extract import extract_file

    work_dir = work / stem
    text = extract_file(
        path,
        pdf_engine,
        allow_partial_pdf=allow_partial_pdf,
        skipped_pages_path=work_dir / "pdf-skipped-pages.txt",
    )
    if passthrough is None:
        passthrough = SuggestPassthrough(
            allow_partial_pdf=allow_partial_pdf,
            pdf_engine=pdf_engine,
            work=work,
        )
    return analyze_text(path, text, work=work, passthrough=passthrough)