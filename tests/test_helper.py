import tempfile
import unittest
from pathlib import Path
from unittest import mock

from readaloud.helper import (
    MENU,
    HelperSession,
    cheat_sheet,
    format_argv_display,
    last_path_file,
    load_last_path,
    python_invocation,
    save_last_path,
)


class HelperTests(unittest.TestCase):
    def test_cheat_sheet_lists_common_recipes(self) -> None:
        text = cheat_sheet()
        self.assertIn("--fetch-models", text)
        self.assertIn("--benchmark", text)
        self.assertIn("--engine piper", text)
        self.assertIn("--tables rows", text)
        self.assertIn("--helper", text)

    def test_menu_lists_numbered_tasks(self) -> None:
        self.assertIn("1  First-time setup", MENU)
        self.assertIn("Plan or markdown", MENU)
        self.assertIn("7  Show cheat sheet", MENU)
        self.assertIn("8  Check a file", MENU)
        self.assertIn("last path", MENU.lower())

    def test_python_invocation_uses_module(self) -> None:
        invocation = python_invocation()
        self.assertEqual(invocation[-2:], ["-m", "readaloud"])

    def test_format_argv_display_quotes_spaces(self) -> None:
        argv = python_invocation() + ["--engine", "piper", "/home/me/My Plan.md"]
        shown = format_argv_display(argv)
        self.assertIn("My Plan.md", shown)
        self.assertNotIn("--engine piper /home", shown)
        self.assertNotEqual(shown, " ".join(argv))

    def test_last_path_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "a file.md"
            sample.write_text("x", encoding="utf-8")
            target = root / "work" / "helper-last-path.txt"
            with mock.patch("readaloud.helper.last_path_file", return_value=target):
                save_last_path(sample)
                self.assertEqual(load_last_path(), sample.resolve())


if __name__ == "__main__":
    unittest.main()