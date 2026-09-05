#!/usr/bin/env bash

set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

# uv version policy (owner decision 2026-09-05, replaces the exact pin).
# EXPECTED_UV is the qualified BASELINE and the exact version CI installs.
# Locally, a newer PATCH release of the same major.minor is accepted and
# printed as drift, because Homebrew ships uv patches within days and every
# functional check below still runs against the installed binary. Anything
# older than the baseline, any minor or major change, or a non-numeric
# version fails: qualify deliberately, then move EXPECTED_UV and the CI
# setup-uv pin together. The rule has an executable selftest so it cannot
# drift from its prose: `check-toolchain.sh --selftest`, also run below.
EXPECTED_UV="0.12.10"

# uv_drift BASELINE ACTUAL -> prints exact | patch | reject
uv_drift() {
  base_major=""; base_minor=""; base_patch=""
  act_major=""; act_minor=""; act_patch=""
  IFS=. read -r base_major base_minor base_patch <<EOF
$1
EOF
  IFS=. read -r act_major act_minor act_patch <<EOF
$2
EOF
  case "$act_major.$act_minor.$act_patch" in
    *[!0-9.]*|.*|*..*|*.) echo reject; return 0 ;;
  esac
  [ -n "$act_major" ] && [ -n "$act_minor" ] && [ -n "$act_patch" ] || { echo reject; return 0; }
  if [ "$act_major" -eq "$base_major" ] && [ "$act_minor" -eq "$base_minor" ]; then
    if [ "$act_patch" -eq "$base_patch" ]; then echo exact
    elif [ "$act_patch" -gt "$base_patch" ]; then echo patch
    else echo reject
    fi
  else
    echo reject
  fi
}

# uv_drift_selftest -> exit 0 when every case matches, 1 otherwise
uv_drift_selftest() {
  cases="0.12.10:0.12.10:exact
0.12.10:0.12.11:patch
0.12.10:0.12.100:patch
0.12.10:0.12.9:reject
0.12.10:0.12.1:reject
0.12.10:0.13.0:reject
0.12.10:0.11.99:reject
0.12.10:1.0.0:reject
0.12.10:0.12.10rc1:reject
0.12.10:0.12:reject
0.12.10::reject"
  selftest_fail=0; selftest_n=0
  while IFS=: read -r c_base c_actual c_want; do
    [ -n "$c_base" ] || continue
    selftest_n=$((selftest_n + 1))
    c_got=$(uv_drift "$c_base" "$c_actual")
    if [ "$c_got" != "$c_want" ]; then
      echo "uv drift rule: selftest case '$c_actual' vs '$c_base' got $c_got, want $c_want" >&2
      selftest_fail=1
    fi
  done <<EOF
$cases
EOF
  if [ "$selftest_fail" -eq 0 ]; then
    echo "uv drift rule: selftest OK ($selftest_n cases)"
    return 0
  fi
  return 1
}

if [ "${1:-}" = "--selftest" ]; then
  uv_drift_selftest
  exit $?
fi

REPO_ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null) || {
  echo "TOOLCHAIN INVALID: cannot resolve repository root" >&2
  exit 1
}

EXPECTED_PYTHON=$(tr -d '[:space:]' < "$REPO_ROOT/.python-version")
EXPECTED_CAIRO="1.18.4"
fail=0

if ! uv_drift_selftest; then
  fail=1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv: MISSING (baseline $EXPECTED_UV)" >&2
  fail=1
else
  uv_version=$(uv --version | awk '{print $2}')
  case "$(uv_drift "$EXPECTED_UV" "$uv_version")" in
    exact)
      echo "uv: $uv_version"
      ;;
    patch)
      echo "uv: $uv_version (baseline $EXPECTED_UV, patch drift accepted; CI pins the baseline)"
      ;;
    *)
      echo "uv: $uv_version (baseline $EXPECTED_UV: downgrade, minor or major change, or unparseable; qualify and move both pins)" >&2
      fail=1
      ;;
  esac
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
