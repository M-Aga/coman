#!/usr/bin/env bash
# Entry point for launching Coman services on POSIX systems.
# Prefers a local virtual environment when present.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON="python3"
if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
elif command -v python >/dev/null 2>&1; then
  PYTHON="python"
fi

if [ -f "requirements.txt" ]; then
  if command -v pip3 >/dev/null 2>&1; then
    pip3 install -r requirements.txt
  else
    "$PYTHON" -m pip install -r requirements.txt
  fi
fi

exec "$PYTHON" -m coman.modules.main "$@"
