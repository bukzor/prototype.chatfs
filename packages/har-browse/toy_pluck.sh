#!/bin/bash
# Extract /api/conversation response body from a JSONL CDP event stream.
# Usage: toy_pluck.sh < events.jsonl > extracted.json
#
# The body rides on Network.responseReceived events, stashed at
# params.response.body (per chrome-har convention), with optional
# params.response.encoding = "base64".
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
  select(.method == "Network.responseReceived"
         and (.params.response.url | endswith("/api/conversation")))
  | if .params.response.encoding == "base64"
    then .params.response.body | @base64d | fromjson
    else .params.response.body | fromjson end
'
