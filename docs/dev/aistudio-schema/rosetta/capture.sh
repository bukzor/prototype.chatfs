#!/bin/bash
# Capture the golden pair for one subject: the SAME subject in both
# encodings — positional JSPB and named alt=json. Steps 1-2 of the
# reproducibility loop (see ../README.md); the pair verify.py checks against.
#
# Needs live auth. If ../curl-aistudio returns HTTP 401, run ../aistudio-reauth.
#
# Usage: ./capture.sh resolvedrive [PROMPT_ID]
#        ./capture.sh listprompts [PAGE_SIZE]
set -euo pipefail
shopt -s failglob
export DEBUG="${DEBUG:-0}"
onerror() { echo >&2 "ERROR($?) at line $LINENO"; exit 1; }
trap onerror ERR
(( DEBUG > 0 )) && set -x

HERE="$(cd "$(dirname "$0")" && pwd)"
SUBJECT="${1:?usage: capture.sh {resolvedrive|listprompts} [param]}"

case "$SUBJECT" in
resolvedrive)
  PARAM="${2:-1vU6BlpV69d2MvI6L_oYGo_E-ZqmaI3eR}"
  body="[\"$PARAM\"]"
  METHOD=ResolveDriveResource
  ;;
listprompts)
  PARAM="${2:-100}"
  body="[$PARAM]"
  METHOD=ListPrompts
  ;;
*)
  echo >&2 "unknown subject: $SUBJECT (want resolvedrive|listprompts)"
  exit 1
  ;;
esac

"$HERE/../curl-aistudio" -d "$body" "$METHOD" \
  | jq . > "$HERE/$SUBJECT.jspb.json"
"$HERE/../curl-aistudio" -d "$body" "$METHOD?alt=json" -H 'Accept: application/json' \
  | jq . > "$HERE/$SUBJECT.alt-json.json"

echo >&2 "wrote $SUBJECT.jspb.json + $SUBJECT.alt-json.json ($METHOD, param $PARAM)"
