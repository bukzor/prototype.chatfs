#!/bin/bash
# Extract /api/conversation response from a Playwright HAR file.
# Usage: toy_pluck.sh < out.har > extracted.json
set -euo pipefail
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

jq '
  .log.entries[]
  | select(.request.url | endswith("/api/conversation"))
  | .response.content
  | if .encoding == "base64" then .text | @base64d | fromjson
    else .text | fromjson end
'
