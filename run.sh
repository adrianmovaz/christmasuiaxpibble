#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
unset NO_COLOR
exec python3 "$PROJECT_DIR/christmas.py" --music "$PROJECT_DIR/pibble.mp3" "$@"
