"""Command line for the local reading-to-audio pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

from readaloud.extract import ReadAloudError, extract_file
from readaloud.mux import ChapterMark, concat_line, ffmetadata, mux_m4b, write_silence
from readaloud.speak import (
    HEADING_PAUSE,
    LIST_ITEM_PAUSE,
    SENTENCE_PAUSE,
    TABLE_ROW_PAUSE,
    KokoroEngine,
    PiperEngine,
    fetch_models,
    speech_pieces,
)
from readaloud.tidy import TidyOptions, TidyResult, load_pronunciations, repo_root, tidy

INPUT_SUFFIXES = {".txt", ".md", ".markdown", ".pdf"}
BENCHMARK_TEXT = (
    "A university reading is a sequence of claims, examples, and qualifications. "
    "The point of this benchmark is to time speech synthesis on about one kilobyte "
    "of plain prose after the model has already been loaded. It is not a summary, "
    "and it does not stand in for a real paper. Listen for a steady voice, then "
    "compare the printed seconds per kilobyte with the thirty second line. "
    "Citations such as Smith 2019 stay in a normal run. Equations are marked "
    "rather than spelled as markup. Headings become chapters. A second sentence "
    "adds a little more length so the sample clears one kilobyte of UTF-8 text "
    "without repeating the same clause. The desktop CPU is the clock that matters. "
    "A longer sample keeps the measurement near one kilobyte, which is the unit "
    "in the speed bar. Ordinary course prose has sentences of uneven length, a "
    "few names, and the occasional abbreviation. This paragraph stays plain so "
    "the timer measures the voice rather than PDF extraction or chapter encoding. "
    "That is the whole of this sample, and nothing more."
)


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(
        description="Read a university file aloud, locally, without rewriting it."
    )
    argument_parser.add_argument(
        "input",
        nargs="?",
        help="A .txt, .md, or .pdf file, a folder of those files, or - for stdin",
    )
    argument_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("library"),
        help="Directory for the .m4b and sidecars (default: library)",
    )
    argument_parser.add_argument(
        "--work",
        type=Path,
        default=Path("work"),
        help="Directory for resumable sentence chunks (default: work)",
    )
    argument_parser.add_argument("--voice", default="af_heart")
    argument_parser.add_argument("--engine", choices=("kokoro", "piper"), default="kokoro")
    argument_parser.add_argument("--piper-voice", default="en_US-lessac-medium")
    argument_parser.add_argument("--math", choices=("omit", "keep"), default="omit")
    argument_parser.add_argument("--code", choices=("speak", "omit"), default="speak")
    argument_parser.add_argument(
        "--tables",
        choices=("speak", "rows", "skip"),
        default="speak",
        help="speak flattens a table to one paragraph; rows speaks each line with Header/Row labels",
    )
    argument_parser.add_argument(
        "--citations",
        choices=("keep", "numeric", "all"),
        default="keep",
        help="keep leaves citations; all also drops (Author, 2019) parentheticals and may remove other prose in notes",
    )
    argument_parser.add_argument(
        "--allow-partial-pdf",
        action="store_true",
        help="Continue when some PDF pages lack a text layer; writes work/<name>/pdf-skipped-pages.txt",
    )
    argument_parser.add_argument(
        "--pdf-engine", choices=("inspector", "marker"), default="inspector"
    )
    argument_parser.add_argument(
        "--normalize",
        action="store_true",
        help="Apply ffmpeg loudnorm during the single encode",
    )
    argument_parser.add_argument("--pronunciations", type=Path)
    argument_parser.add_argument(
        "--fetch-models",
        action="store_true",
        help="Download Kokoro ONNX weights into models/",
    )
    argument_parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Time about 1 KB of plain text after a warmup sentence",
    )
    return argument_parser


def make_engine(args: argparse.Namespace, root: Path):
    if args.engine == "piper":
        return PiperEngine(args.piper_voice, root / "models" / "piper"), args.piper_voice
    model, voices = root / "models" / "model.onnx", root / "models" / "voices-v1.0.bin"
    return KokoroEngine(model, voices, args.voice), args.voice


def tidy_options(args: argparse.Namespace) -> TidyOptions:
    return TidyOptions(
        math=args.math,
        code=args.code,
        tables=args.tables,
        citations=args.citations,
        pronunciations=load_pronunciations(args.pronunciations),
    )


def options_fingerprint(
    engine_name: str,
    voice: str,
    options: TidyOptions,
    pronunciations_path: Path | None,
) -> str:
    payload: dict[str, object] = {
        "engine": engine_name,
        "voice": voice,
        "math": options.math,
        "code": options.code,
        "tables": options.tables,
        "citations": options.citations,
        "pronunciation_keys": sorted(options.pronunciations.keys()),
    }
    if pronunciations_path and pronunciations_path.is_file():
        payload["pronunciations_file"] = str(pronunciations_path.resolve())
        payload["pronunciations_mtime"] = pronunciations_path.stat().st_mtime
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:16]


def load_manifest(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"warning: ignoring corrupt manifest {path}", file=sys.stderr)
        return {}


def publish_library_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    shutil.copy2(source, temporary)
    temporary.replace(destination)


def collect_inputs(value: str | None) -> list[Path] | None:
    if value is None or value == "-":
        return None
    path = Path(value)
    if path.is_dir():
        files = [
            item
            for item in path.iterdir()
            if item.is_file() and item.suffix.lower() in INPUT_SUFFIXES
        ]
        return sorted(files, key=lambda item: item.name.lower())
    return [path]


def safe_stem(name: str) -> str:
    cleaned = "".join(character if character.isalnum() or character in "._-" else "-" for character in name)
    cleaned = cleaned.strip(".-") or "reading"
    return cleaned[:120]


def pieces_for(result: TidyResult) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for segment in result.segments:
        parts = speech_pieces(segment.text)
        for index, piece in enumerate(parts):
            opens_chapter = index == 0 and segment.kind == "heading"
            if opens_chapter:
                kind = "heading"
            elif segment.kind in ("list_item", "table_row"):
                kind = segment.kind
            else:
                kind = "body"
            items.append(
                {
                    "text": piece,
                    "kind": kind,
                    "chapter": (segment.chapter_title or "") if opens_chapter else "",
                }
            )
    return items


def synthesize_items(
    engine,
    items: list[dict[str, str]],
    work: Path,
    engine_name: str,
    voice: str,
    fingerprint: str,
) -> float:
    work.mkdir(parents=True, exist_ok=True)
    manifest_path = work / "manifest.json"
    previous = load_manifest(manifest_path)
    previous_items = previous.get("items") or []
    reusable = (
        previous.get("engine") == engine_name
        and previous.get("voice") == voice
        and previous.get("fingerprint") == fingerprint
    )
    started = time.perf_counter()
    completed: list[dict[str, str]] = []
    for index, item in enumerate(items):
        destination = work / f"{index:05d}.wav"
        cached = (
            reusable
            and index < len(previous_items)
            and previous_items[index].get("text") == item["text"]
            and destination.is_file()
            and destination.stat().st_size > 44
        )
        if not cached:
            engine.synthesize(item["text"], destination)
        completed.append(item)
        manifest_path.write_text(
            json.dumps(
                {
                    "engine": engine_name,
                    "voice": voice,
                    "fingerprint": fingerprint,
                    "items": completed,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    return time.perf_counter() - started


def build_audio(items: list[dict[str, str]], work: Path, output: Path, title: str, normalize: bool) -> None:
    import soundfile as sf

    if not items:
        raise ReadAloudError("Nothing left to speak after the speech rules.")
    first = work / "00000.wav"
    silence_body = work / "silence-body.wav"
    silence_list = work / "silence-list.wav"
    silence_table = work / "silence-table.wav"
    silence_heading = work / "silence-heading.wav"
    write_silence(first, silence_body, SENTENCE_PAUSE)
    write_silence(first, silence_list, LIST_ITEM_PAUSE)
    write_silence(first, silence_table, TABLE_ROW_PAUSE)
    write_silence(first, silence_heading, HEADING_PAUSE)
    body_frames = sf.info(silence_body).frames
    list_frames = sf.info(silence_list).frames
    table_frames = sf.info(silence_table).frames
    heading_frames = sf.info(silence_heading).frames
    sample_rate = sf.info(first).samplerate

    chapters: list[ChapterMark] = []
    cursor = 0
    first_heading = next((index for index, item in enumerate(items) if item["kind"] == "heading"), None)
    if first_heading is None or first_heading > 0:
        chapters.append(ChapterMark(title, 0))

    lines: list[str] = []
    for index, item in enumerate(items):
        wav = work / f"{index:05d}.wav"
        if item["kind"] == "heading" and item["chapter"]:
            chapters.append(ChapterMark(item["chapter"], cursor))
        frames = sf.info(wav).frames
        lines.append(concat_line(wav))
        cursor += frames
        if index + 1 < len(items):
            kind = item["kind"]
            if kind == "heading":
                pause = silence_heading
                pause_frames = heading_frames
            elif kind == "list_item":
                pause = silence_list
                pause_frames = list_frames
            elif kind == "table_row":
                pause = silence_table
                pause_frames = table_frames
            else:
                pause = silence_body
                pause_frames = body_frames
            lines.append(concat_line(pause))
            cursor += pause_frames

    concat_path = work / "concat.txt"
    meta_path = work / "chapters.txt"
    concat_path.write_text("".join(lines), encoding="utf-8")
    meta_path.write_text(ffmetadata(chapters, cursor, sample_rate), encoding="utf-8")
    mux_m4b(concat_path, meta_path, output, normalize=normalize)


def print_report(result: TidyResult, extract_s: float, synth_s: float) -> None:
    stats = result.stats
    spoken_bytes = len(result.spoken.encode("utf-8"))
    kilobytes = spoken_bytes / 1024 if spoken_bytes else 0
    per_kb = synth_s / kilobytes if kilobytes else 0
    print(
        f"chars {stats.chars_in} -> {stats.chars_out} ({stats.percent_kept}% kept)"
    )
    print(f"math spans replaced: {stats.math_spans}")
    print(f"link URLs stripped: {stats.link_urls_stripped}")
    print(f"bare URLs removed: {stats.urls_removed}")
    if stats.emails_removed:
        print(f"emails removed: {stats.emails_removed}")
    print(f"code blocks omitted: {stats.code_blocks_omitted}")
    print(f"extraction: {extract_s:.2f}s")
    print(f"synthesis: {synth_s:.2f}s ({per_kb:.1f} s/KB of spoken text)")
    if kilobytes and per_kb > 30:
        print("Over 30 seconds per KB. Rerun this file with --engine piper.")


def convert_text(
    text: str,
    stem: str,
    args: argparse.Namespace,
    engine,
    voice: str,
    extract_s: float,
) -> None:
    options = tidy_options(args)
    result = tidy(text, options)
    work = args.work / stem
    work.mkdir(parents=True, exist_ok=True)
    extracted_work = work / "extracted.md"
    spoken_work = work / "spoken.txt"
    audio_work = work / f"{stem}.m4b"
    normalized = text if text.endswith("\n") else text + "\n"
    extracted_work.write_text(normalized, encoding="utf-8")
    spoken_work.write_text(result.spoken, encoding="utf-8")
    items = pieces_for(result)
    fingerprint = options_fingerprint(args.engine, voice, options, args.pronunciations)
    synth_s = synthesize_items(engine, items, work, args.engine, voice, fingerprint)
    build_audio(items, work, audio_work, stem, args.normalize)
    output_dir = args.output
    publish_library_file(extracted_work, output_dir / f"{stem}.extracted.md")
    publish_library_file(spoken_work, output_dir / f"{stem}.spoken.txt")
    publish_library_file(audio_work, output_dir / f"{stem}.m4b")
    print_report(result, extract_s, synth_s)
    print(f"wrote {output_dir / f'{stem}.m4b'}")


def convert_path(path: Path, args: argparse.Namespace, engine, voice: str) -> None:
    if not path.is_file():
        raise ReadAloudError(f"Not a file: {path}")
    stem = safe_stem(path.stem)
    work = args.work / stem
    started = time.perf_counter()
    text = extract_file(
        path,
        args.pdf_engine,
        allow_partial_pdf=args.allow_partial_pdf,
        skipped_pages_path=work / "pdf-skipped-pages.txt",
    )
    extract_s = time.perf_counter() - started
    convert_text(text, stem, args, engine, voice, extract_s)


def run_benchmark(args: argparse.Namespace, root: Path) -> int:
    engine, _voice = make_engine(args, root)
    bench_dir = args.work / "benchmark"
    bench_dir.mkdir(parents=True, exist_ok=True)
    try:
        started = time.perf_counter()
        engine.ensure()
        load_s = time.perf_counter() - started
    except (FileNotFoundError, RuntimeError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    engine.synthesize("This warmup sentence is not timed.", bench_dir / "warmup.wav")
    started = time.perf_counter()
    engine.synthesize(BENCHMARK_TEXT, bench_dir / "bench.wav")
    synth_s = time.perf_counter() - started
    kilobytes = len(BENCHMARK_TEXT.encode("utf-8")) / 1024
    per_kb = synth_s / kilobytes
    print(f"model load: {load_s:.2f}s")
    print(f"synthesis: {synth_s:.2f}s for {kilobytes:.2f} KB ({per_kb:.1f} s/KB)")
    if per_kb > 30:
        print("Over 30 seconds per KB. Rerun real jobs with --engine piper.")
    else:
        print("Under 30 seconds per KB.")
    return 0


def main(argv: list[str] | None = None) -> int:
    argument_parser = parser()
    args = argument_parser.parse_args(argv)
    root = repo_root()
    if args.fetch_models:
        fetch_models(root / "models")
        print("Weights are in models/. Later runs stay offline.")
        return 0
    if args.benchmark:
        return run_benchmark(args, root)

    inputs = collect_inputs(args.input)
    if inputs is None:
        if args.input is None and sys.stdin.isatty():
            argument_parser.print_help()
            return 2
        text = sys.stdin.read()
        engine, voice = make_engine(args, root)
        try:
            started = time.perf_counter()
            engine.ensure()
            print(f"model load: {time.perf_counter() - started:.2f}s")
        except (FileNotFoundError, RuntimeError, OSError) as error:
            print(f"error: {error}", file=sys.stderr)
            return 1
        try:
            convert_text(text, "stdin", args, engine, voice, 0.0)
        except (ReadAloudError, RuntimeError, OSError, ValueError) as error:
            print(f"error: {error}", file=sys.stderr)
            return 1
        return 0

    if not inputs:
        print("error: the folder has no .txt, .md, or .pdf files.", file=sys.stderr)
        return 1

    engine, voice = make_engine(args, root)
    try:
        started = time.perf_counter()
        engine.ensure()
        print(f"model load: {time.perf_counter() - started:.2f}s")
    except (FileNotFoundError, RuntimeError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    failures = 0
    for path in inputs:
        print(f"== {path}")
        try:
            convert_path(path, args, engine, voice)
        except (ReadAloudError, RuntimeError, OSError, ValueError) as error:
            failures += 1
            failed = args.output / f"{safe_stem(path.stem)}.failed.txt"
            args.output.mkdir(parents=True, exist_ok=True)
            failed.write_text(str(error) + "\n", encoding="utf-8")
            print(f"error: {path.name}: {error}", file=sys.stderr)
    if len(inputs) > 1:
        print(f"done: {len(inputs) - failures} ok, {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
