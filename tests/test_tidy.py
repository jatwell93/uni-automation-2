import unittest
from pathlib import Path

from readaloud.mux import ChapterMark, escape_ffmetadata, ffmetadata
from readaloud.speak import speech_pieces, split_long
from readaloud.tidy import TidyOptions, load_pronunciations, repo_root, tidy


def spoken(text: str, **options: str) -> str:
    result = tidy(text, TidyOptions(pronunciations={}, **options))
    return result.spoken


class TidyTests(unittest.TestCase):
    def test_heading_becomes_a_chapter_and_drops_marks(self) -> None:
        result = tidy("# Week 3\n\nThe claim stands.\n", TidyOptions())
        self.assertEqual(result.segments[0].kind, "heading")
        self.assertEqual(result.segments[0].chapter_title, "Week 3")
        self.assertIn("Week 3.", result.spoken)
        self.assertNotIn("#", result.spoken)

    def test_emphasis_is_removed(self) -> None:
        self.assertEqual(spoken("A **bold** and *italic* word.\n"), "A bold and italic word.\n")

    def test_citations_stay_unless_asked(self) -> None:
        text = "GPUs matter [12]. See (Smith et al., 2019).\n"
        self.assertIn("[12]", spoken(text))
        self.assertIn("(Smith et al., 2019)", spoken(text))
        numeric = spoken(text, citations="numeric")
        self.assertNotIn("[12]", numeric)
        self.assertIn("(Smith et al., 2019)", numeric)
        self.assertNotIn("(Smith et al., 2019)", spoken(text, citations="all"))

    def test_math_is_marked_and_counted(self) -> None:
        result = tidy("Loss: $\\sum_i x_i$.\n", TidyOptions())
        self.assertIn("equation omitted", result.spoken)
        self.assertNotIn("\\sum", result.spoken)
        self.assertEqual(result.stats.math_spans, 1)
        kept = tidy("Loss: $\\sum_i x_i$.\n", TidyOptions(math="keep"))
        self.assertIn("\\sum", kept.spoken)
        self.assertEqual(kept.stats.math_spans, 0)

    def test_links_keep_anchor_text_and_drop_bare_urls(self) -> None:
        result = tidy(
            "Read [the paper](https://example.com/a) at https://example.com/b.\n",
            TidyOptions(),
        )
        self.assertIn("the paper", result.spoken)
        self.assertNotIn("https://", result.spoken)
        self.assertGreaterEqual(result.stats.urls_removed, 2)

    def test_line_break_hyphen_joins_and_real_hyphen_stays(self) -> None:
        self.assertIn("condition", spoken("condi-\ntion holds.\n"))
        self.assertNotIn("condi-", spoken("condi-\ntion holds.\n"))
        self.assertIn("self-report", spoken("A self-report scale.\n"))

    def test_page_number_line_is_dropped(self) -> None:
        text = spoken("The result holds.\n\n12\n\nPage 3 of 10\n")
        self.assertIn("The result holds.", text)
        self.assertNotIn("\n12\n", "\n" + text)
        self.assertNotIn("Page 3", text)

    def test_code_is_spoken_unless_omitted(self) -> None:
        source = "Before.\n\n```\nprint(1)\n```\n\nAfter.\n"
        self.assertIn("print(1)", spoken(source))
        self.assertNotIn("```", spoken(source))
        omitted = tidy(source, TidyOptions(code="omit"))
        self.assertIn("code sample omitted", omitted.spoken)
        self.assertNotIn("print(1)", omitted.spoken)
        self.assertEqual(omitted.stats.code_blocks_omitted, 1)

    def test_tables_are_read_in_order(self) -> None:
        source = "| A | B |\n| --- | --- |\n| one | two |\n"
        self.assertIn("A, B.", spoken(source))
        self.assertIn("one, two.", spoken(source))
        self.assertNotIn("|", spoken(source))
        self.assertEqual(spoken(source, tables="skip").strip(), "")

    def test_yaml_front_matter_is_removed(self) -> None:
        text = spoken("---\ntitle: Notes\n---\nThe body.\n")
        self.assertIn("The body.", text)
        self.assertNotIn("title:", text)

    def test_figure_alt_is_spoken_and_empty_figure_is_not_invented(self) -> None:
        self.assertIn("Sales chart", spoken("See ![Sales chart](plot.png).\n"))
        self.assertNotIn("figure", spoken("See ![](plot.png) now.\n").lower())

    def test_percent_kept_is_visible(self) -> None:
        result = tidy("Hello.\n", TidyOptions())
        self.assertGreater(result.stats.chars_in, 0)
        self.assertGreater(result.stats.percent_kept, 0)
        self.assertLessEqual(result.stats.percent_kept, 100)

    def test_pronunciation_file_replaces_terms(self) -> None:
        mapping = load_pronunciations(repo_root() / "pronunciations.txt")
        result = tidy("See Fig. 1, e.g. this one.\n", TidyOptions(pronunciations=mapping))
        self.assertIn("Figure", result.spoken)
        self.assertIn("for example", result.spoken)
        self.assertNotIn("e.g.", result.spoken)

    def test_email_is_removed(self) -> None:
        result = tidy("Write to a@b.edu today.\n", TidyOptions())
        self.assertNotIn("@", result.spoken)
        self.assertEqual(result.stats.emails_removed, 1)


class SpeechSplitTests(unittest.TestCase):
    def test_sentences_stay_intact_and_long_lines_split_on_spaces(self) -> None:
        pieces = speech_pieces("One. Two?")
        self.assertEqual(pieces, ["One.", "Two?"])
        chunks = split_long("alpha beta gamma delta", 12)
        self.assertTrue(all(len(chunk) <= 12 or " " not in chunk for chunk in chunks))
        self.assertEqual(" ".join(chunks), "alpha beta gamma delta")


class ChapterMetadataTests(unittest.TestCase):
    def test_chapters_cover_the_timeline(self) -> None:
        chapters = [ChapterMark("Intro", 0), ChapterMark("A = B", 24000)]
        text = ffmetadata(chapters, 48000, 24000)
        self.assertTrue(text.startswith(";FFMETADATA1\n"))
        self.assertIn("TIMEBASE=1/1000", text)
        self.assertIn("START=0", text)
        self.assertIn("END=1000", text)
        self.assertIn("START=1000", text)
        self.assertIn("END=2000", text)
        self.assertIn(r"title=A \= B", text)
        self.assertNotIn("title=A = B", text)

    def test_escape_keeps_metadata_delimiters(self) -> None:
        self.assertEqual(escape_ffmetadata("a=b;c#d"), r"a\=b\;c\#d")


class MuxTests(unittest.TestCase):
    def test_ffmpeg_writes_a_chaptered_m4b(self) -> None:
        import shutil
        import tempfile
        import wave

        if shutil.which("ffmpeg") is None:
            self.skipTest("ffmpeg is not installed")
        from readaloud.mux import concat_line, mux_m4b

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wav = root / "tone.wav"
            with wave.open(str(wav), "wb") as handle:
                handle.setnchannels(1)
                handle.setsampwidth(2)
                handle.setframerate(24000)
                handle.writeframes(b"\x00\x00" * 24000)
            concat = root / "concat.txt"
            concat.write_text(concat_line(wav), encoding="utf-8")
            meta = root / "chapters.txt"
            meta.write_text(ffmetadata([ChapterMark("Start", 0)], 24000, 24000), encoding="utf-8")
            output = root / "out.m4b"
            mux_m4b(concat, meta, output)
            self.assertGreater(output.stat().st_size, 100)


if __name__ == "__main__":
    unittest.main()
