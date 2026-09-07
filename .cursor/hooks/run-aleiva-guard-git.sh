#!/usr/bin/env bash
# Launcher: prefer python3, then py -3 (Windows), then python.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$DIR/aleiva-guard-git.py"
fi
if command -v py >/dev/null 2>&1; then
  exec py -3 "$DIR/aleiva-guard-git.py"
fi
exec python "$DIR/aleiva-guard-git.py"
