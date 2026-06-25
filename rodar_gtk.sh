#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
exec .venv-gtk/bin/python simulador.py
