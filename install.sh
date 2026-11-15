#!/usr/bin/env bash
# Set up the desktop: system packages, a Python 3.12 venv, and the package.
# Does not download Kokoro weights. Run that next with --fetch-models.
set -euo pipefail
cd "$(dirname "$0")" || exit 1

install_packages() {
  if ! command -v apt-get >/dev/null 2>&1; then
    echo "Install espeak-ng, ffmpeg, and Python 3.12, then rerun ./install.sh." >&2
    echo "On Arch the package names are espeak-ng, ffmpeg, and python." >&2
    exit 1
  fi
  sudo apt-get update
  sudo apt-get install -y espeak-ng ffmpeg python3.12 python3.12-venv
}

if ! command -v python3.12 >/dev/null 2>&1 \
  || ! command -v ffmpeg >/dev/null 2>&1 \
  || ! command -v espeak-ng >/dev/null 2>&1; then
  install_packages
fi

if ! python3.12 -m venv .venv; then
  install_packages
  python3.12 -m venv .venv
fi

.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -e . --no-deps

cat <<'EOF'

Next, on this desktop:

  .venv/bin/python -m readaloud --fetch-models
  .venv/bin/python -m readaloud --benchmark

The first command downloads the Kokoro weights. This script does not.
EOF
