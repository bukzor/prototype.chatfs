#!/bin/bash
# Capture the golden pair for one endpoint: the SAME subject in both
# encodings — positional JSPB and named alt=json. Steps 1-2 of the
# reproducibility loop (see ../README.md); the pair verify.py checks against.
#
# Endpoint-specific method/param shape lives in ENDPOINT_DIR/meta.json
# (method, default_param, body — a "{param}"-templated request body). A new
# endpoint needs no edit here, just a new endpoint/<name>/meta.json.
#
# Needs live auth. If ../curl-aistudio returns HTTP 401, run ../aistudio-reauth.
#
# Usage: ./capture.sh endpoint/resolvedrive [PROMPT_ID]
#        ./capture.sh endpoint/listprompts [PAGE_SIZE]
set -euo pipefail
shopt -s failglob
export DEBUG="${DEBUG:-0}"
onerror() { echo >&2 "ERROR($?) at line $LINENO"; exit 1; }
trap onerror ERR
(( DEBUG > 0 )) && set -x

HERE="$(cd "$(dirname "$0")" && pwd)"
ENDPOINT_DIR="${1:?usage: capture.sh ENDPOINT_DIR [param]}"
META="$ENDPOINT_DIR/meta.json"

METHOD="$(jq -r .method "$META")"
PARAM="${2:-$(jq -r .default_param "$META")}"
BODY_TEMPLATE="$(jq -r .body "$META")"
BODY="${BODY_TEMPLATE//\{param\}/$PARAM}"

"$HERE/../curl-aistudio" -d "$BODY" "$METHOD" \
  | jq . > "$ENDPOINT_DIR/jspb.json"
"$HERE/../curl-aistudio" -d "$BODY" "$METHOD?alt=json" -H 'Accept: application/json' \
  | jq . > "$ENDPOINT_DIR/alt-json.json"

echo >&2 "wrote $ENDPOINT_DIR/{jspb,alt-json}.json ($METHOD, param $PARAM)"
