#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null) || {
  echo "build refused: cannot resolve repository root" >&2
  exit 1
}

exec "$SCRIPT_DIR/run-with-brand-env.sh" "$REPO_ROOT/.venv/bin/python" \
  "$REPO_ROOT/design/marks/generate_marks.py" "$@"
