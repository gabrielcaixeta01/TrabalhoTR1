#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
exec "$PYTHON_BIN" simulador.py
