import unittest

from readaloud.helper import MENU, cheat_sheet, python_invocation


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

    def test_python_invocation_uses_module(self) -> None:
        invocation = python_invocation()
        self.assertEqual(invocation[-2:], ["-m", "readaloud"])


if __name__ == "__main__":
    unittest.main()