import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from readaloud.preflight import (
    SuggestPassthrough,
    analyze_text,
    format_report,
    load_kokoro_benchmark,
)


class PreflightTests(unittest.TestCase):
    def test_suggests_tables_rows_for_markdown_table(self) -> None:
        source = (
            "# Plan\n\n"
            "| A | B |\n|---|---|\n| one | two |\n| three | four |\n\n"
            "Paragraph.\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            report = analyze_text(Path("plan.md"), source, work=work)
        self.assertIn("--tables", report.suggested_argv)
        self.assertIn("rows", report.suggested_argv)
        self.assertIn("row-by-row", " ".join(report.reasons))

    def test_suggests_math_keep_for_currency_line(self) -> None:
        source = "Costs: Gemini fallback ≪ A$1/mo at ~110 docs; VPS ~A$15/mo.\n"
        with tempfile.TemporaryDirectory() as directory:
            report = analyze_text(Path("x.md"), source, work=Path(directory))
        self.assertIn("--math", report.suggested_argv)
        self.assertIn("keep", report.suggested_argv)

    def test_suggests_piper_when_benchmark_slow(self) -> None:
        source = "Word " * 2000 + "\n"
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            bench = work / "benchmark"
            bench.mkdir(parents=True)
            (bench / "summary.json").write_text(
                json.dumps({"per_kb": 79.0, "engine": "kokoro"}),
                encoding="utf-8",
            )
            report = analyze_text(Path("long.md"), source, work=work)
        self.assertIn("--engine", report.suggested_argv)
        self.assertIn("piper", report.suggested_argv)

    def test_load_kokoro_benchmark_reads_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            bench = work / "benchmark"
            bench.mkdir()
            (bench / "summary.json").write_text('{"per_kb": 12.5, "engine": "kokoro"}', encoding="utf-8")
            self.assertEqual(load_kokoro_benchmark(work), 12.5)

    def test_load_kokoro_benchmark_ignores_piper_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            bench = work / "benchmark"
            bench.mkdir()
            (bench / "summary.json").write_text('{"per_kb": 5.0, "engine": "piper"}', encoding="utf-8")
            self.assertIsNone(load_kokoro_benchmark(work))

    def test_suggested_command_includes_pdf_passthrough(self) -> None:
        source = "# Doc\n\nBody.\n"
        passthrough = SuggestPassthrough(
            allow_partial_pdf=True,
            pdf_engine="marker",
            work=Path("/tmp/ra-work"),
        )
        with tempfile.TemporaryDirectory() as directory:
            report = analyze_text(
                Path("paper.pdf"), source, work=Path(directory), passthrough=passthrough
            )
        self.assertIn("--allow-partial-pdf", report.suggested_argv)
        self.assertIn("--pdf-engine", report.suggested_argv)
        self.assertIn("marker", report.suggested_argv)
        self.assertIn("/tmp/ra-work", report.suggested_argv)

    def test_format_report_includes_quoted_run_line(self) -> None:
        source = "# Hi\n\nText.\n"
        with tempfile.TemporaryDirectory() as directory:
            report = analyze_text(Path("a b.md"), source, work=Path(directory))
        text = format_report(report)
        self.assertIn("run:", text)
        self.assertIn("a b.md", text)


if __name__ == "__main__":
    unittest.main()