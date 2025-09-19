#!/usr/bin/env bash
VENV_DIR="$(dirname "$0")/.venv"
if [ -f "$VENV_DIR/bin/activate" ]; then
    . "$VENV_DIR/bin/activate"
fi

python "$(dirname "$0")/src/rag/adapters/cli/run_rag.py" "$@"
