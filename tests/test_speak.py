import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from readaloud.speak import CHUNK_LIMIT, KokoroEngine, _is_phoneme_limit_error, split_long


class PhonemeLimitTests(unittest.TestCase):
    def test_is_phoneme_limit_error(self) -> None:
        self.assertTrue(_is_phoneme_limit_error(ValueError("phoneme limit exceeded")))
        self.assertFalse(_is_phoneme_limit_error(ValueError("voice not found")))

    @mock.patch("readaloud.speak.KokoroEngine.ensure")
    def test_unknown_value_error_is_not_retried(self, ensure: mock.Mock) -> None:
        ensure.return_value = None
        engine = KokoroEngine(Path("/dev/null"), Path("/dev/null"), "af_heart")
        fake = mock.Mock()
        fake.create.side_effect = ValueError("Nothing to synthesize")
        engine._kokoro = fake
        fake_soundfile = mock.Mock()
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "out.wav"
            with mock.patch.dict(sys.modules, {"soundfile": fake_soundfile}):
                with self.assertRaises(ValueError):
                    engine.synthesize("Hello.", destination)
        self.assertEqual(fake.create.call_count, 1)


class SplitLongTests(unittest.TestCase):
    def test_pathological_string_splits_under_limit(self) -> None:
        text = " ".join("0123456789" for _ in range(120))
        parts = split_long(text, CHUNK_LIMIT)
        self.assertGreater(len(parts), 2)
        self.assertTrue(all(len(part) <= CHUNK_LIMIT for part in parts))


if __name__ == "__main__":
    unittest.main()