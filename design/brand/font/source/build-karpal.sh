#!/bin/sh
set -eu

SOURCE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
FONT_DIR=$(CDPATH= cd -- "$SOURCE_DIR/.." && pwd)
REPO_ROOT=$(CDPATH= cd -- "$FONT_DIR/../../.." && pwd)
PYTHON="$REPO_ROOT/.venv/bin/python"
SOURCE="$SOURCE_DIR/KarpalGeometric-Regular.ttx"
GOLDEN="$FONT_DIR/KarpalGeometric-Regular.ttf"

if [ ! -x "$PYTHON" ]; then
  echo "missing locked interpreter: $PYTHON" >&2
  echo "follow design/brand/BRAND-SURFACES.md to recreate the toolchain" >&2
  exit 1
fi

if [ ! -f "$SOURCE" ] || [ ! -f "$GOLDEN" ]; then
  echo "missing Karpal source or golden master" >&2
  exit 1
fi

BUILD_DIR=$(mktemp -d "${TMPDIR:-/tmp}/karpal-build.XXXXXX")
trap 'rm -rf "$BUILD_DIR"' EXIT HUP INT TERM
BUILT="$BUILD_DIR/KarpalGeometric-Regular.ttf"

"$PYTHON" -m fontTools.ttx --no-recalc-timestamp -q -o "$BUILT" "$SOURCE"
"$PYTHON" "$SOURCE_DIR/verify-karpal.py" "$GOLDEN" "$BUILT"

echo "Karpal Geometric rebuilt successfully; semantic tables match the v1 golden master."
