"""Read .txt, .md, and born-digital .pdf into markdown or plain text."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

TEXT_SUFFIXES = {".txt", ".md", ".markdown"}
PARTIAL_PAGE_FRACTION = 0.05
MARKER_TIMEOUT_S = 1800


class ReadAloudError(Exception):
    """A problem the reader can fix, printed without a traceback."""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def extract_pdf(
    path: Path,
    engine: str = "inspector",
    *,
    allow_partial: bool = False,
    skipped_pages_path: Path | None = None,
) -> str:
    if engine == "marker":
        return _extract_marker(path)
    if engine != "inspector":
        raise ReadAloudError(f"Unknown PDF engine {engine!r}. Use inspector or marker.")
    return _extract_inspector(path, allow_partial=allow_partial, skipped_pages_path=skipped_pages_path)


def extract_file(
    path: Path,
    pdf_engine: str = "inspector",
    *,
    allow_partial_pdf: bool = False,
    skipped_pages_path: Path | None = None,
) -> str:
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return read_text(path)
    if suffix == ".pdf":
        return extract_pdf(
            path,
            pdf_engine,
            allow_partial=allow_partial_pdf,
            skipped_pages_path=skipped_pages_path,
        )
    raise ReadAloudError(
        f"Unsupported file {path.name}. Use .txt, .md, or .pdf."
    )


def _format_skipped_pages(pages: list[int] | tuple[int, ...] | set[int]) -> str:
    ordered = sorted(set(int(page) for page in pages))
    return ", ".join(str(page) for page in ordered)


def _extract_inspector(
    path: Path,
    *,
    allow_partial: bool = False,
    skipped_pages_path: Path | None = None,
) -> str:
    try:
        import pdf_inspector
    except ImportError as error:
        raise ReadAloudError(
            "pdf-inspector is not installed. Run ./install.sh on the desktop."
        ) from error

    result = pdf_inspector.process_pdf(str(path))
    kind = str(result.pdf_type).lower()
    markdown = result.markdown
    if kind in {"scanned", "image_based"} or not markdown or not markdown.strip():
        raise ReadAloudError(
            f"{path.name} has no text layer ({kind or 'empty'}). "
            "Optional local preprocess, not installed by install.sh, and outside "
            "the 30 second budget:\n"
            f"  ocrmypdf {path} output.pdf\n"
            "Then run readaloud on output.pdf."
        )
    skipped_pages = list(result.pages_needing_ocr or [])
    if skipped_pages:
        total = int(getattr(result, "page_count", 0) or 0)
        if total <= 0 and skipped_pages:
            total = max(skipped_pages)
        skipped = len(skipped_pages)
        fraction = (skipped / total) if total else 1.0
        should_fail = kind == "mixed" or fraction > PARTIAL_PAGE_FRACTION
        page_list = _format_skipped_pages(skipped_pages)
        if should_fail and not allow_partial:
            raise ReadAloudError(
                f"{path.name} is missing a text layer on page(s): {page_list}. "
                f"That is {skipped} of {total or 'unknown'} page(s). "
                "Optional local preprocess, not installed by install.sh, and outside "
                "the 30 second budget:\n"
                f"  ocrmypdf {path} output.pdf\n"
                "Then run readaloud on output.pdf, or pass --allow-partial-pdf."
            )
        print(
            f"warning: {path.name} is {kind}; "
            f"{skipped} page(s) had no text layer and were not spoken: {page_list}."
        )
        if skipped_pages_path is not None:
            skipped_pages_path.parent.mkdir(parents=True, exist_ok=True)
            skipped_pages_path.write_text(page_list + "\n", encoding="utf-8")
    return markdown


def _extract_marker(path: Path) -> str:
    executable = shutil.which("marker_single")
    if executable is None:
        raise ReadAloudError(
            "marker_single is not on PATH. Install the optional extra with "
            "`pip install marker-pdf` and do not pass --use_llm."
        )
    with tempfile.TemporaryDirectory(prefix="readaloud-marker-") as directory:
        try:
            completed = subprocess.run(
                [
                    executable,
                    str(path),
                    "--output_dir",
                    directory,
                    "--output_format",
                    "markdown",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=MARKER_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired as error:
            raise ReadAloudError(
                f"marker_single timed out after {MARKER_TIMEOUT_S} seconds."
            ) from error
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise ReadAloudError(
                "marker_single failed. Check `marker_single --help` for this version's "
                f"flags, and do not pass --use_llm. {detail}"
            )
        markdown_files = sorted(Path(directory).rglob("*.md"))
        if not markdown_files:
            raise ReadAloudError("marker_single produced no markdown.")
        return markdown_files[0].read_text(encoding="utf-8", errors="replace")
