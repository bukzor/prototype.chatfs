#!/bin/bash
# Capture the golden pair for one prompt: the SAME conversation in both
# encodings — positional JSPB and named alt=json. Steps 1-2 of the
# reproducibility loop (see ../README.md); the pair verify.py checks against.
#
# Needs live auth. If ../curl-aistudio returns HTTP 401, run ../aistudio-reauth.
#
# Usage: ./capture.sh [PROMPT_ID]
set -euo pipefail
shopt -s failglob
export DEBUG="${DEBUG:-0}"
onerror() { echo >&2 "ERROR($?) at line $LINENO"; exit 1; }
trap onerror ERR
(( DEBUG > 0 )) && set -x

HERE="$(cd "$(dirname "$0")" && pwd)"
ID="${1:-1vU6BlpV69d2MvI6L_oYGo_E-ZqmaI3eR}"
body="[\"$ID\"]"

"$HERE/../curl-aistudio" -d "$body" ResolveDriveResource \
  | jq . > "$HERE/resolvedrive.jspb.json"
"$HERE/../curl-aistudio" -d "$body" 'ResolveDriveResource?alt=json' -H 'Accept: application/json' \
  | jq . > "$HERE/resolvedrive.alt-json.json"

echo >&2 "wrote resolvedrive.jspb.json + resolvedrive.alt-json.json for $ID"
