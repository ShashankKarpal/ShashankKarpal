#!/usr/bin/env bash

set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CANONICAL_ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null) || {
  echo "FLEET INCOMPLETE: cannot resolve canonical repository" >&2
  exit 1
}
FLEET_ROOT=$(dirname -- "$CANONICAL_ROOT")

if [ "${1:-}" = "--root" ]; then
  if [ "$#" -lt 2 ]; then
    echo "usage: $0 [--root REPOSITORY_PARENT] [repo ...]" >&2
    exit 64
  fi
  FLEET_ROOT=$2
  shift 2
fi

if [ "$#" -gt 0 ]; then
  repos=("$@")
else
  repos=(
    ledge
    content-digest-app
    helios
    zest
    switchdeck
    claude-tokens
    shashankkarpal
  )
fi

fail=0
for repo in "${repos[@]}"; do
  repo_dir="$FLEET_ROOT/$repo"
  if [ ! -d "$repo_dir/.git" ]; then
    echo "$repo: MISSING REPO" >&2
    fail=1
    continue
  fi

  if ! git -C "$repo_dir" fetch --quiet; then
    echo "$repo: FETCH FAILED" >&2
    fail=1
    continue
  fi

  if ! upstream=$(git -C "$repo_dir" rev-parse --abbrev-ref '@{upstream}' 2>/dev/null); then
    echo "$repo: NO UPSTREAM" >&2
    fail=1
    continue
  fi

  if ! status=$(git -C "$repo_dir" status --porcelain --untracked-files=all); then
    echo "$repo: STATUS FAILED" >&2
    fail=1
    continue
  fi
  if [ -n "$status" ]; then
    dirty=$(printf '%s\n' "$status" | wc -l | tr -d ' ')
  else
    dirty=0
  fi

  if ! ahead=$(git -C "$repo_dir" rev-list --count "$upstream"..HEAD); then
    echo "$repo: AHEAD CHECK FAILED" >&2
    fail=1
    continue
  fi
  if ! behind=$(git -C "$repo_dir" rev-list --count HEAD.."$upstream"); then
    echo "$repo: BEHIND CHECK FAILED" >&2
    fail=1
    continue
  fi

  if [ "$dirty" -ne 0 ] || [ "$ahead" -ne 0 ] || [ "$behind" -ne 0 ]; then
    fail=1
  fi
  echo "$repo: dirty=$dirty ahead=$ahead behind=$behind"
done

if [ "$fail" -ne 0 ]; then
  echo "FLEET INCOMPLETE" >&2
  exit 1
fi

echo "FLEET CLEAN"
