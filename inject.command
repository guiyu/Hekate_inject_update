#!/bin/bash
set -euo pipefail
TASK_DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$TASK_DIR/logs"
"$TASK_DIR/.venv/bin/python" -u "$TASK_DIR/inject.py" "$@" 2>&1 | tee "$TASK_DIR/logs/inject-$(date +%Y%m%d-%H%M%S).log"
