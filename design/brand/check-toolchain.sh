#!/usr/bin/env bash

set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null) || {
  echo "TOOLCHAIN INVALID: cannot resolve repository root" >&2
  exit 1
}

EXPECTED_PYTHON=$(tr -d '[:space:]' < "$REPO_ROOT/.python-version")
EXPECTED_UV="0.12.10"
EXPECTED_CAIRO="1.18.4"
fail=0

if ! command -v uv >/dev/null 2>&1; then
  echo "uv: MISSING (expected $EXPECTED_UV)" >&2
  fail=1
else
  uv_version=$(uv --version | awk '{print $2}')
  if [ "$uv_version" = "$EXPECTED_UV" ]; then
    echo "uv: $uv_version"
  else
    echo "uv: $uv_version (expected $EXPECTED_UV)" >&2
    fail=1
  fi
fi

if [ ! -x "$REPO_ROOT/.venv/bin/python" ]; then
  echo "python: MISSING .venv (expected $EXPECTED_PYTHON)" >&2
  fail=1
else
  python_version=$("$REPO_ROOT/.venv/bin/python" -c 'import platform; print(platform.python_version())')
  if [ "$python_version" = "$EXPECTED_PYTHON" ]; then
    echo "python: $python_version"
  else
    echo "python: $python_version (expected $EXPECTED_PYTHON)" >&2
    fail=1
  fi

  if ! uv pip check --python "$REPO_ROOT/.venv/bin/python"; then
    echo "python packages: dependency check failed" >&2
    fail=1
  fi

  expected_packages=$(sed -n 's/^\([A-Za-z0-9_.-]*==[^[:space:]\\]*\).*/\1/p' \
    "$REPO_ROOT/requirements.lock" | tr '[:upper:]' '[:lower:]' | sort)
  actual_packages=$(uv pip freeze --python "$REPO_ROOT/.venv/bin/python" \
    | tr '[:upper:]' '[:lower:]' | sort)
  if [ "$actual_packages" = "$expected_packages" ]; then
    echo "python packages: exact lock match"
  else
    echo "python packages: installed set differs from requirements.lock" >&2
    fail=1
  fi
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "cairo: Homebrew unavailable (expected $EXPECTED_CAIRO)" >&2
  fail=1
else
  cairo_version=$(brew list --versions cairo 2>/dev/null | awk '{print $2}')
  if [ "$cairo_version" = "$EXPECTED_CAIRO" ]; then
    echo "cairo: $cairo_version"
  else
    shown=${cairo_version:-MISSING}
    echo "cairo: $shown (expected $EXPECTED_CAIRO)" >&2
    fail=1
  fi
fi

BRAND_ENV="$REPO_ROOT/design/brand/run-with-brand-env.sh"
if [ ! -x "$BRAND_ENV" ]; then
  echo "brand environment wrapper: missing or not executable" >&2
  fail=1
elif [ -x "$REPO_ROOT/.venv/bin/python" ] && [ -n "${cairo_version:-}" ]; then
  cairo_prefix=$(brew --prefix cairo 2>/dev/null)
  if [ -d "$cairo_prefix/lib" ]; then
    if "$BRAND_ENV" "$REPO_ROOT/.venv/bin/python" -c \
      'import cairosvg; cairosvg.svg2png(bytestring=b"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1\" height=\"1\"/>")'; then
      echo "cairosvg: native render OK ($cairo_prefix/lib)"
    else
      echo "cairosvg: native render failed ($cairo_prefix/lib)" >&2
      fail=1
    fi
  else
    echo "cairosvg: Cairo library directory missing" >&2
    fail=1
  fi
fi

DISTRIBUTOR_TEST="$REPO_ROOT/design/marks/test_distribute_assets.py"
GENERATOR_TEST="$REPO_ROOT/design/marks/test_generate_marks.py"
if [ ! -f "$DISTRIBUTOR_TEST" ] || [ ! -f "$GENERATOR_TEST" ]; then
  echo "brand regression tests: missing" >&2
  fail=1
elif [ ! -x "$REPO_ROOT/.venv/bin/python" ]; then
  echo "brand regression tests: cannot run without locked Python" >&2
  fail=1
elif [ ! -x "$BRAND_ENV" ]; then
  echo "brand regression tests: cannot run without environment wrapper" >&2
  fail=1
elif "$BRAND_ENV" "$REPO_ROOT/.venv/bin/python" -m unittest discover \
  -s "$REPO_ROOT/design/marks" -p 'test_*.py'; then
  echo "brand regression tests: OK"
else
  echo "brand regression tests: failed" >&2
  fail=1
fi

KARPAL_BUILD="$REPO_ROOT/design/brand/font/source/build-karpal.sh"
if [ ! -f "$KARPAL_BUILD" ]; then
  echo "Karpal source check: build script missing" >&2
  fail=1
elif sh "$KARPAL_BUILD"; then
  echo "Karpal source check: round-trip OK"
else
  echo "Karpal source check: round-trip failed" >&2
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "TOOLCHAIN INVALID" >&2
  exit 1
fi

echo "TOOLCHAIN OK"
