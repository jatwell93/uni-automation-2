import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from readaloud.extract import ReadAloudError, _extract_inspector


class ExtractInspectorTests(unittest.TestCase):
    def _result(
        self,
        *,
        pdf_type: str,
        markdown: str,
        pages_needing_ocr: list[int],
        page_count: int,
    ) -> mock.Mock:
        result = mock.Mock()
        result.pdf_type = pdf_type
        result.markdown = markdown
        result.pages_needing_ocr = pages_needing_ocr
        result.page_count = page_count
        return result

    def _run(self, *, allow_partial: bool = False, skipped_path: Path | None = None) -> str:
        fake = mock.Mock()
        fake.process_pdf.return_value = self._result(
            pdf_type="mixed",
            markdown="Intro.\n",
            pages_needing_ocr=[2, 5],
            page_count=10,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "paper.pdf"
            path.write_bytes(b"%PDF-1.4")
            skipped = skipped_path or root / "skipped.txt"
            with mock.patch.dict(sys.modules, {"pdf_inspector": fake}):
                return _extract_inspector(
                    path,
                    allow_partial=allow_partial,
                    skipped_pages_path=skipped,
                ), skipped

    def test_mixed_pdf_with_missing_pages_fails_by_default(self) -> None:
        fake = mock.Mock()
        fake.process_pdf.return_value = self._result(
            pdf_type="mixed",
            markdown="# Title\n\nBody text.\n",
            pages_needing_ocr=[2],
            page_count=10,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "paper.pdf"
            path.write_bytes(b"%PDF-1.4")
            with mock.patch.dict(sys.modules, {"pdf_inspector": fake}):
                with self.assertRaises(ReadAloudError):
                    _extract_inspector(path)

    def test_allow_partial_records_skipped_pages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skipped = Path(directory) / "skipped.txt"
            text, written = self._run(allow_partial=True, skipped_path=skipped)
            self.assertEqual(text, "Intro.\n")
            self.assertEqual(written.read_text(encoding="utf-8"), "2, 5\n")


if __name__ == "__main__":
    unittest.main()