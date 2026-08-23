#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null) || {
  echo "brand environment refused: cannot resolve repository root" >&2
  exit 1
}
[ "$#" -gt 0 ] || {
  echo "usage: run-with-brand-env.sh COMMAND [ARG ...]" >&2
  exit 2
}
[ -x "$REPO_ROOT/.venv/bin/python" ] || {
  echo "brand environment refused: .venv is missing; follow BRAND-SURFACES.md" >&2
  exit 1
}
command -v brew >/dev/null 2>&1 || {
  echo "brand environment refused: Homebrew Cairo cannot be resolved" >&2
  exit 1
}
CAIRO_PREFIX=$(brew --prefix cairo 2>/dev/null) || {
  echo "brand environment refused: Homebrew Cairo is not installed" >&2
  exit 1
}
[ -d "$CAIRO_PREFIX/lib" ] || {
  echo "brand environment refused: Cairo library directory is missing" >&2
  exit 1
}

if [ -n "${DYLD_FALLBACK_LIBRARY_PATH:-}" ]; then
  export DYLD_FALLBACK_LIBRARY_PATH="$CAIRO_PREFIX/lib:$DYLD_FALLBACK_LIBRARY_PATH"
else
  export DYLD_FALLBACK_LIBRARY_PATH="$CAIRO_PREFIX/lib"
fi
export PYTHONDONTWRITEBYTECODE=1

exec "$@"
