#!/bin/bash
# Introspection battery: does the AI Studio server expose its schema, and how?
# Refreshes auth from a capture (refresh-secrets.sh), then probes via curl-aistudio
# for keyed JSON, discovery docs, and gRPC reflection. Records what works.
#
# Usage: ./live-replay.sh <capture.cdp.jsonl>
set -euo pipefail
shopt -s failglob
export DEBUG="${DEBUG:-0}"
onerror() { echo >&2 "ERROR($?) at line $LINENO"; exit 1; }
trap onerror ERR
(( DEBUG > 0 )) && set -x

CAPTURE="${1:?capture .cdp.jsonl path}"
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(git rev-parse --show-toplevel)"
CURL="$HERE/curl-aistudio"
HDR="$ROOT/trash/replay.hdr"; BODY="$ROOT/trash/replay.body"
mkdir -p "$ROOT/trash"

"$HERE/refresh-secrets.sh" "$CAPTURE"

# A sample request body to replay (the first ResolveDriveResource POST).
body="$(jq -rn 'first(inputs
  | select(.method=="Network.requestWillBeSent"
      and (.params.request.url|test("ResolveDriveResource$"))
      and .params.request.method=="POST")) | .params.request.postData' "$CAPTURE")"
host="https://alkalimakersuite-pa.clients6.google.com"

run() {  # LABEL, then curl-aistudio args (method-or-URL, -d, -H, ...)
  local label="$1"; shift
  : > "$HDR"; : > "$BODY"
  "$CURL" "$@" -D "$HDR" -o "$BODY" >/dev/null 2>&1 || true
  printf '%-32s %s  %s\n' "$label" \
    "$(awk 'NR==1{print $2}' "$HDR")" \
    "$(awk -F': ' 'tolower($1)=="content-type"{print $2;exit}' "$HDR" | tr -d '\r')"
  printf '   '; head -c 200 "$BODY" | tr '\n' ' '; printf '\n'
}

echo "# === baseline (proves auth) ==="
run "A0 verbatim JSPB"       ResolveDriveResource -d "$body"
echo "# === keyed JSON ==="
run "K1 ?alt=json"           'ResolveDriveResource?alt=json' -d "$body" -H 'Accept: application/json'
run "K2 json content-type"   ResolveDriveResource -d "$body" -H 'Content-Type: application/json' -H 'Accept: application/json'
echo "# === discovery docs ==="
run "D1 /\$discovery/rest"   "$host/\$discovery/rest?version=v1"
run "D2 /discovery/v1/apis"  "$host/discovery/v1/apis/makersuite/v1/rest"
echo "# === gRPC reflection ==="
run "R1 list_services"       "$host/\$rpc/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo" -d '["",null,null,null,null,null,"*"]'
echo "# === error shape ==="
run "E1 malformed JSPB"      ResolveDriveResource -d '[12345]'

echo "# bodies: $BODY (last only); headers: $HDR"
