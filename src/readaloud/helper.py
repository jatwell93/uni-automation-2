"""Interactive command helper — stdlib only, no extra TUI dependencies."""

from __future__ import annotations

import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from readaloud.tidy import repo_root

MENU = """
Readaloud helper — pick a task (enter a number, or q to quit)

  1  First-time setup       download Kokoro weights, then benchmark this CPU
  2  Plan or markdown       Piper engine, tables read row-by-row (dense specs)
  3  Notes or essay         default voice; Kokoro (use 4 if benchmark was slow)
  4  Faster Piper run       Piper on the last path you used (Enter to reuse)
  5  Born-digital PDF       text-layer extraction (not scanned pages)
  6  Folder of readings     every .txt / .md / .pdf in one directory
  7  Show cheat sheet       copy-paste commands, no prompts
  8  Check a file           scan structure, suggest flags (no synthesis)
  q  Quit
"""

LAST_PATH_NAME = "helper-last-path.txt"


def python_invocation() -> list[str]:
    return [sys.executable, "-m", "readaloud"]


def format_argv_display(argv: list[str]) -> str:
    """Shell-safe string for copy-paste (execution uses argv list, not the shell)."""
    return shlex.join(argv)


def last_path_file() -> Path:
    return repo_root() / "work" / LAST_PATH_NAME


def load_last_path() -> Path | None:
    path = last_path_file()
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return None
    resolved = Path(text).expanduser()
    if resolved.is_file() or resolved.is_dir():
        return resolved.resolve()
    return None


def save_last_path(path: Path) -> None:
    target = last_path_file()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(str(path.resolve()) + "\n", encoding="utf-8")


@dataclass
class HelperSession:
    last_path: Path | None = None

    def remember(self, path: Path) -> None:
        resolved = path.resolve()
        self.last_path = resolved
        save_last_path(resolved)


def cheat_sheet(home: Path | None = None) -> str:
    root = home or repo_root()
    py = format_argv_display(python_invocation())
    lines = [
        f"Run from the repo (or set READALOUD_HOME={root}).",
        "",
        "Setup (once):",
        f"  {py} --fetch-models",
        f"  {py} --benchmark",
        "",
        "Everyday:",
        f"  {py} notes.md",
        f"  {py} PLAN.md --engine piper --tables rows",
        f"  {py} paper.pdf",
        f"  {py} week/",
        "",
        "While a job runs, progress is under work/<name>/; library/ updates only when done.",
        "Read library/<name>.spoken.txt before a long listen.",
        "",
        "Useful flags:",
        "  --engine piper          when --benchmark is over 30 s/KB",
        "  --tables rows           plans and tables with Header/Row lines",
        "  --math keep             keep dollar amounts (default omit can garble A$…)",
        "  --code omit             skip ASCII diagrams in fenced blocks",
        "  --allow-partial-pdf     mixed PDFs; skipped pages listed in work/",
        "",
        "Check before a long run:",
        f"  {py} --check plan.md",
        "",
        "Guided menu (also runs when you type readaloud with no file):",
        f"  {py} --helper",
    ]
    return "\n".join(lines) + "\n"


def _ask(prompt: str, default: str = "") -> str:
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    try:
        reply = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise SystemExit(0)
    return reply or default


def _ask_yes_no(prompt: str, *, default_yes: bool = True) -> bool:
    suffix = "Y/n" if default_yes else "y/N"
    reply = _ask(f"{prompt} ({suffix})", "y" if default_yes else "n").lower()
    if not reply:
        return default_yes
    return reply in {"y", "yes"}


def _ask_existing_file(label: str, *, default: str = "") -> Path:
    while True:
        raw = _ask(label, default)
        if not raw:
            print("  A file path is required.")
            default = ""
            continue
        path = Path(raw).expanduser().resolve()
        if path.is_file():
            return path
        print(f"  Not found: {path}")
        default = ""


def _ask_existing_path(label: str, *, default: str = "") -> Path:
    while True:
        raw = _ask(label, default)
        if not raw:
            print("  A path is required.")
            default = ""
            continue
        path = Path(raw).expanduser().resolve()
        if path.is_file() or path.is_dir():
            return path
        print(f"  Not found: {path}")
        default = ""


def run_command(argv: list[str]) -> int:
    print(f"\n→ {format_argv_display(argv)}\n")
    if not _ask_yes_no("Run this now?"):
        print("Cancelled. Run the line above when ready.")
        return 0
    completed = subprocess.run(argv)
    return int(completed.returncode)


def _setup_sequence() -> int:
    base = python_invocation()
    code = run_command(base + ["--fetch-models"])
    if code != 0:
        return code
    return run_command(base + ["--benchmark"])


def _convert_with_flags(session: HelperSession, path: Path, extra: list[str]) -> int:
    session.remember(path)
    return run_command(python_invocation() + extra + [str(path)])


def dispatch(choice: str, session: HelperSession) -> int | None:
    """Return exit code, or None to show the menu again."""
    if choice in {"q", "quit", "exit"}:
        return 0
    if choice == "7":
        print(cheat_sheet())
        return None
    if choice == "8":
        path = _ask_existing_path("File or folder to check")
        return run_command(python_invocation() + ["--check", str(path)])
    if choice == "1":
        return _setup_sequence()
    if choice == "2":
        path = _ask_existing_file("Path to .md or .txt")
        extras = ["--engine", "piper", "--tables", "rows"]
        if _ask_yes_no("Also use --math keep (safer for A$ amounts)?", default_yes=True):
            extras.append("--math")
            extras.append("keep")
        return _convert_with_flags(session, path, extras)
    if choice == "3":
        path = _ask_existing_file("Path to .txt, .md, or .pdf")
        return _convert_with_flags(session, path, [])
    if choice == "4":
        default = str(session.last_path) if session.last_path else ""
        path = _ask_existing_path("Path to file or folder (Enter = last path)", default=default)
        return _convert_with_flags(session, path, ["--engine", "piper"])
    if choice == "5":
        path = _ask_existing_file("Path to born-digital .pdf")
        return _convert_with_flags(session, path, [])
    if choice == "6":
        path = _ask_existing_path("Folder containing readings")
        session.remember(path)
        engine = []
        if _ask_yes_no("Use Piper for the batch?", default_yes=False):
            engine = ["--engine", "piper"]
        return run_command(python_invocation() + engine + [str(path)])
    print("  Enter 1–8 or q.")
    return None


def run_helper() -> int:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print(cheat_sheet())
        print("(Non-interactive terminal: printed cheat sheet only.)", file=sys.stderr)
        return 0
    session = HelperSession(last_path=load_last_path())
    if session.last_path:
        print(f"Last path: {session.last_path}\n")
    print("Tip: long jobs are silent until the end; watch work/<name>/manifest.json for progress.\n")
    while True:
        print(MENU)
        try:
            choice = input("Choice: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        result = dispatch(choice, session)
        if result is not None:
            return result
        print()