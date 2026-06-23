#!/bin/bash
set -euo pipefail
shopt -s failglob
export DEBUG="${DEBUG:-0}"

onerror() {
  error="$?"
  echo >&2 "ERROR($error)"
  exit "$error"
}
trap onerror ERR

if (( DEBUG > 0 )); then
  set -x
fi

# Prettier-format the extracted bundles in parallel — one process per file so
# the ~4 MB main module overlaps the small ones (wall time ~= the slowest file,
# not the sum).
#
# --ignore-path /dev/null is load-bearing: bundles/ is git-ignored (derived
# data), and prettier honors .gitignore by default, so without this it
# SILENTLY skips every file and reports success.
cd "$(dirname "$0")"

# Target dir defaults to bundles/; a redo .do passes its tmp dir instead.
dir=${1:-bundles}

printf '%s\0' "$dir"/*.js \
  | xargs -0 -P "$(nproc)" -n1 \
      npx --no-install prettier --write --ignore-path /dev/null
