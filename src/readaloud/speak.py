"""Kokoro ONNX on CPU, with Piper as the speed fallback."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import wave
from pathlib import Path

MODEL_URL = (
    "https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX"
    "/resolve/main/onnx/model.onnx"
)
VOICES_URL = (
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
    "model-files-v1.0/voices-v1.0.bin"
)
MODEL_NAME = "model.onnx"
VOICES_NAME = "voices-v1.0.bin"
SENTENCE_PAUSE = 0.20
HEADING_PAUSE = 0.45
CHUNK_LIMIT = 400
DOT_PLACEHOLDER = "\ue002"
DOWNLOAD_TIMEOUT_S = 600
PIPER_DOWNLOAD_TIMEOUT_S = 600
MARKER_TIMEOUT_S = 1800
FFMPEG_MUX_TIMEOUT_S = 3600
MIN_MODEL_BYTES = 1_000_000
MIN_VOICES_BYTES = 1_000_000

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_DECIMAL = re.compile(r"\d+\.\d+")
_INITIAL = re.compile(r"\b[A-Z]\.")
_BUILTIN_ABBREVS = (
    "w.r.t.",
    "et al.",
    "e.g.",
    "i.e.",
    "approx.",
    "Prof.",
    "Mrs.",
    "etc.",
    "Fig.",
    "Dr.",
    "Mr.",
    "Ms.",
    "Sr.",
    "Jr.",
    "St.",
    "Ch.",
    "Vol.",
    "No.",
    "Eq.",
    "vs.",
    "cf.",
)


def _pronunciation_abbrev_protectors() -> tuple[str, ...]:
    try:
        from readaloud.tidy import load_pronunciations, repo_root

        mapping = load_pronunciations(repo_root() / "pronunciations.txt")
    except OSError:
        return ()
    return tuple(term for term in mapping if term.endswith(".") and term not in _BUILTIN_ABBREVS)


def _protect_abbreviations(text: str, extra: tuple[str, ...] = ()) -> str:
    abbrevs = sorted(set(_BUILTIN_ABBREVS) | set(extra), key=len, reverse=True)
    for abbr in abbrevs:
        if abbr in text:
            text = text.replace(abbr, abbr.replace(".", DOT_PLACEHOLDER))

    def _decimal(match: re.Match[str]) -> str:
        return match.group(0).replace(".", DOT_PLACEHOLDER)

    text = _DECIMAL.sub(_decimal, text)
    return _INITIAL.sub(lambda match: match.group(0).replace(".", DOT_PLACEHOLDER), text)


def _restore_dots(text: str) -> str:
    return text.replace(DOT_PLACEHOLDER, ".")


def split_sentences(text: str, extra_abbrevs: tuple[str, ...] | None = None) -> list[str]:
    if extra_abbrevs is None:
        extra_abbrevs = _pronunciation_abbrev_protectors()
    protected = _protect_abbreviations(text.strip(), extra_abbrevs)
    return [
        _restore_dots(sentence)
        for sentence in _SENTENCE_SPLIT.split(protected)
        if sentence.strip()
    ]


def _is_phoneme_limit_error(error: ValueError) -> bool:
    message = str(error).lower()
    markers = ("phoneme", "token", "length", "510", "too long", "maximum", "limit")
    return any(marker in message for marker in markers)


def lang_for(voice: str) -> str:
    if voice.startswith(("bf_", "bm_")):
        return "en-gb"
    return "en-us"


def split_long(text: str, limit: int = CHUNK_LIMIT) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= limit or " " not in text:
        return [text]
    for separator in ("; ", ": ", ", ", " "):
        index = text.rfind(separator, 0, limit + len(separator))
        if index <= 0:
            continue
        if separator == " ":
            left = text[:index].strip()
            right = text[index + 1 :].strip()
        else:
            left = (text[:index] + separator.strip()).strip()
            right = text[index + len(separator) :].strip()
        if left and right:
            return split_long(left, limit) + split_long(right, limit)
    return [text]


def speech_pieces(text: str) -> list[str]:
    pieces: list[str] = []
    for sentence in split_sentences(text):
        pieces.extend(split_long(sentence))
    return [piece for piece in pieces if piece]


def download(url: str, dest: Path, *, min_bytes: int = 1) -> None:
    import urllib.request

    if not url.startswith("https://"):
        raise ValueError(f"Refusing non-HTTPS download: {url}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    temporary = dest.with_suffix(dest.suffix + ".part")
    if temporary.is_file():
        temporary.unlink()
    request = urllib.request.Request(url, headers={"User-Agent": "readaloud"})
    print(f"downloading {dest.name}")
    try:
        with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_S) as response, temporary.open(
            "wb"
        ) as handle:
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                handle.write(block)
    except OSError:
        if temporary.is_file():
            temporary.unlink()
        raise
    size = temporary.stat().st_size
    if size < min_bytes:
        temporary.unlink()
        raise RuntimeError(
            f"Download of {dest.name} was too small ({size} bytes). Delete any partial file and retry."
        )
    temporary.replace(dest)


def fetch_models(models_dir: Path) -> tuple[Path, Path]:
    models_dir.mkdir(parents=True, exist_ok=True)
    model = models_dir / MODEL_NAME
    voices = models_dir / VOICES_NAME
    if not model.is_file() or model.stat().st_size < MIN_MODEL_BYTES:
        download(MODEL_URL, model, min_bytes=MIN_MODEL_BYTES)
    else:
        print(f"already present: {model}")
    if not voices.is_file() or voices.stat().st_size < MIN_VOICES_BYTES:
        download(VOICES_URL, voices, min_bytes=MIN_VOICES_BYTES)
    else:
        print(f"already present: {voices}")
    return model, voices


class KokoroEngine:
    def __init__(self, model_path: Path, voices_path: Path, voice: str) -> None:
        self.model_path = model_path
        self.voices_path = voices_path
        self.voice = voice
        self._kokoro = None

    def ensure(self) -> None:
        if self._kokoro is not None:
            return
        if not self.model_path.is_file() or not self.voices_path.is_file():
            raise FileNotFoundError(
                "Kokoro weights are missing. Run: python -m readaloud --fetch-models"
            )
        os.environ["ONNX_PROVIDER"] = "CPUExecutionProvider"
        try:
            from kokoro_onnx import Kokoro
        except ImportError as error:
            raise RuntimeError(
                "kokoro-onnx is not installed. Run ./install.sh on the desktop."
            ) from error

        self._kokoro = Kokoro(str(self.model_path), str(self.voices_path))

    def synthesize(self, text: str, dest: Path) -> None:
        import soundfile as sf

        self.ensure()
        if self._kokoro is None:
            raise RuntimeError("Kokoro engine is not loaded.")
        try:
            audio, sample_rate = self._kokoro.create(
                text,
                voice=self.voice,
                speed=1.0,
                lang=lang_for(self.voice),
                sentence_pause=0.0,
                clause_pause=0.1,
            )
        except ValueError as error:
            if not _is_phoneme_limit_error(error):
                raise
            smaller = split_long(text, max(CHUNK_LIMIT // 2, 80))
            if len(smaller) <= 1:
                raise
            parts = []
            rate = 24000
            for piece in smaller:
                audio, rate = self._kokoro.create(
                    piece,
                    voice=self.voice,
                    speed=1.0,
                    lang=lang_for(self.voice),
                    sentence_pause=0.0,
                    clause_pause=0.1,
                )
                parts.append(audio)
            import numpy as np

            audio = np.concatenate(parts)
            sample_rate = rate
        dest.parent.mkdir(parents=True, exist_ok=True)
        sf.write(dest, audio, sample_rate)


class PiperEngine:
    def __init__(self, voice: str, data_dir: Path) -> None:
        self.voice_name = voice
        self.data_dir = data_dir
        self._voice = None

    def model_path(self) -> Path:
        return self.data_dir / f"{self.voice_name}.onnx"

    def ensure(self) -> None:
        if self._voice is not None:
            return
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.model_path().is_file():
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "piper.download_voices",
                    self.voice_name,
                    "--download-dir",
                    str(self.data_dir),
                ],
                check=False,
                timeout=PIPER_DOWNLOAD_TIMEOUT_S,
            )
            if completed.returncode != 0 or not self.model_path().is_file():
                raise RuntimeError(
                    f"Could not download Piper voice {self.voice_name}."
                )
        from piper import PiperVoice

        self._voice = PiperVoice.load(self.model_path(), use_cuda=False)

    def synthesize(self, text: str, dest: Path) -> None:
        self.ensure()
        if self._voice is None:
            raise RuntimeError("Piper voice is not loaded.")
        dest.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(dest), "wb") as handle:
            started = False
            for chunk in self._voice.synthesize(text):
                if not started:
                    handle.setframerate(chunk.sample_rate)
                    handle.setsampwidth(chunk.sample_width)
                    handle.setnchannels(chunk.sample_channels)
                    started = True
                handle.writeframes(chunk.audio_int16_bytes)
            if not started:
                raise RuntimeError(f"Piper produced no audio for {text!r}")
