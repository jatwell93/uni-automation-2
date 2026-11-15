"""Join sentence WAVs into one chaptered .m4b."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ChapterMark:
    title: str
    start_frame: int


def escape_ffmetadata(value: str) -> str:
    escaped = value.replace("\\", "\\\\")
    for character in ("=", ";", "#", "\n"):
        escaped = escaped.replace(character, "\\" + character)
    return escaped


def ffmetadata(chapters: list[ChapterMark], total_frames: int, sample_rate: int) -> str:
    lines = [";FFMETADATA1"]
    if sample_rate <= 0:
        sample_rate = 1
    for index, chapter in enumerate(chapters):
        start_ms = int(chapter.start_frame / sample_rate * 1000)
        if index + 1 < len(chapters):
            end_frame = chapters[index + 1].start_frame
        else:
            end_frame = total_frames
        end_ms = int(end_frame / sample_rate * 1000)
        if end_ms <= start_ms:
            end_ms = start_ms + 1
        lines.extend(
            [
                "[CHAPTER]",
                "TIMEBASE=1/1000",
                f"START={start_ms}",
                f"END={end_ms}",
                f"title={escape_ffmetadata(chapter.title)}",
            ]
        )
    return "\n".join(lines) + "\n"


def write_silence(template: Path, dest: Path, seconds: float) -> int:
    import numpy as np
    import soundfile as sf

    info = sf.info(template)
    frames = max(int(seconds * info.samplerate), 1)
    channels = info.channels or 1
    if info.subtype == "FLOAT":
        audio = np.zeros((frames, channels), dtype=np.float32)
    else:
        audio = np.zeros((frames, channels), dtype=np.int16)
    sf.write(dest, audio, info.samplerate, subtype=info.subtype)
    return frames


def concat_line(path: Path) -> str:
    quoted = path.resolve().as_posix().replace("'", r"'\''")
    return f"file '{quoted}'\n"


def mux_m4b(
    concat_list: Path,
    metadata: Path,
    output: Path,
    *,
    normalize: bool = False,
) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is not installed. Run ./install.sh on the desktop.")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_list),
        "-i",
        str(metadata),
        "-map",
        "0:a",
        "-map_metadata",
        "1",
        "-c:a",
        "aac",
        "-b:a",
        "96k",
    ]
    if normalize:
        command.extend(["-af", "loudnorm"])
    command.append(str(output))
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip().splitlines()
        tail = detail[-1] if detail else "ffmpeg failed"
        raise RuntimeError(tail)
