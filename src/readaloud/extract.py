"""Read .txt, .md, and born-digital .pdf into markdown or plain text."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

TEXT_SUFFIXES = {".txt", ".md", ".markdown"}


class ReadAloudError(Exception):
    """A problem the reader can fix, printed without a traceback."""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def extract_pdf(path: Path, engine: str = "inspector") -> str:
    if engine == "marker":
        return _extract_marker(path)
    if engine != "inspector":
        raise ReadAloudError(f"Unknown PDF engine {engine!r}. Use inspector or marker.")
    return _extract_inspector(path)


def extract_file(path: Path, pdf_engine: str = "inspector") -> str:
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return read_text(path)
    if suffix == ".pdf":
        return extract_pdf(path, pdf_engine)
    raise ReadAloudError(
        f"Unsupported file {path.name}. Use .txt, .md, or .pdf."
    )


def _extract_inspector(path: Path) -> str:
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
    if result.pages_needing_ocr:
        print(
            f"warning: {path.name} is {kind}; "
            f"{len(result.pages_needing_ocr)} page(s) had no text layer and were not spoken."
        )
    return markdown


def _extract_marker(path: Path) -> str:
    executable = shutil.which("marker_single")
    if executable is None:
        raise ReadAloudError(
            "marker_single is not on PATH. Install the optional extra with "
            "`pip install marker-pdf` and do not pass --use_llm."
        )
    with tempfile.TemporaryDirectory(prefix="readaloud-marker-") as directory:
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
        )
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
