#!/usr/bin/env bash
set -e
cd -- "$(dirname -- "$0")"
RUNTIME_PYTHON="/home/diego/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
if [ -x "$RUNTIME_PYTHON" ]; then
    exec "$RUNTIME_PYTHON" app_graficos.py
fi
exec python3 app_graficos.py
