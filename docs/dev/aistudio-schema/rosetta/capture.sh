#!/bin/bash
# Capture the golden pair for ListPrompts (the index/library RPC): the SAME
# page of prompts in both encodings — positional JSPB and named alt=json.
# Steps 1-2 of the reproducibility loop (see ../README.md); the pair
# verify.py checks against.
#
# Needs live auth. If ../curl-aistudio returns HTTP 401, run ../aistudio-reauth.
#
# Usage: ./capture.sh [PAGE_SIZE]
set -euo pipefail
shopt -s failglob
export DEBUG="${DEBUG:-0}"
onerror() { echo >&2 "ERROR($?) at line $LINENO"; exit 1; }
trap onerror ERR
(( DEBUG > 0 )) && set -x

HERE="$(cd "$(dirname "$0")" && pwd)"
PAGE_SIZE="${1:-100}"
body="[$PAGE_SIZE]"

"$HERE/../curl-aistudio" -d "$body" ListPrompts \
  | jq . > "$HERE/listprompts.jspb.json"
"$HERE/../curl-aistudio" -d "$body" 'ListPrompts?alt=json' -H 'Accept: application/json' \
  | jq . > "$HERE/listprompts.alt-json.json"

echo >&2 "wrote listprompts.jspb.json + listprompts.alt-json.json (page size $PAGE_SIZE)"
