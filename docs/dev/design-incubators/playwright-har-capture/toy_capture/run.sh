#!/bin/bash
set -euo pipefail
export DEBUG="${DEBUG:-0}"

onerror() {
  error="$?"
  echo >&2 "ERROR($error)"
  exit "$error"
}
trap onerror ERR

HERE="$(dirname "$0")"
ROOT="$(dirname "$HERE")"

URL="${1:-http://127.0.0.1:8000}"
HAR="${2:-$ROOT/out.har}"

if (( DEBUG > 0 )); then
  set -x
fi

node "$HERE/capture.mjs" --url "$URL" --har "$HAR"
