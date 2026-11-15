import unittest
from unittest import mock

from readaloud.cli import options_fingerprint
from readaloud.tidy import TidyOptions


class ManifestFingerprintTests(unittest.TestCase):
    def test_fingerprint_changes_when_math_option_changes(self) -> None:
        voice = "af_heart"
        one = options_fingerprint(
            "kokoro",
            voice,
            TidyOptions(math="omit"),
            None,
        )
        two = options_fingerprint(
            "kokoro",
            voice,
            TidyOptions(math="keep"),
            None,
        )
        self.assertNotEqual(one, two)

    def test_fingerprint_uses_custom_pronunciation_mtime(self) -> None:
        path = mock.Mock()
        path.is_file.return_value = True
        path.resolve.return_value = path
        with mock.patch.object(path, "stat") as stat:
            stat.return_value = mock.Mock(st_mtime=1.0)
            one = options_fingerprint(
                "kokoro",
                "af_heart",
                TidyOptions(pronunciations={"Foo": "foo"}),
                path,
            )
        with mock.patch.object(path, "stat") as stat:
            stat.return_value = mock.Mock(st_mtime=2.0)
            two = options_fingerprint(
                "kokoro",
                "af_heart",
                TidyOptions(pronunciations={"Foo": "foo"}),
                path,
            )
        self.assertNotEqual(one, two)


if __name__ == "__main__":
    unittest.main()