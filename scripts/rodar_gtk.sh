#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
if [[ -z "${PYTHON_BIN:-}" ]]; then
    if [[ -x ".venv-gtk/bin/python" ]]; then
        PYTHON_BIN=".venv-gtk/bin/python"
    else
        PYTHON_BIN="/usr/bin/python3"
    fi
fi

export TK_SILENCE_DEPRECATION=1
exec "$PYTHON_BIN" simulador.py
