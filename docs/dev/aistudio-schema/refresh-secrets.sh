#!/bin/bash
# Extract AI Studio auth from a CDP capture into secrets/aistudio.headers.curl —
# a curl --config (cookie + SAPISIDHASH + X-Goog-Api-Key + Origin + ...) good for
# replaying any MakerSuite $rpc call. Auth is method-agnostic, so the first
# MakerSuiteService POST in the capture suffices. Output is gitignored.
#
# Usage: ./refresh-secrets.sh <capture.cdp.jsonl>
set -euo pipefail
shopt -s failglob
export DEBUG="${DEBUG:-0}"
onerror() { echo >&2 "ERROR($?) at line $LINENO"; exit 1; }
trap onerror ERR
(( DEBUG > 0 )) && set -x

CAPTURE="${1:?capture .cdp.jsonl path}"
ROOT="$(git rev-parse --show-toplevel)"
OUT="$ROOT/secrets/aistudio.headers.curl"
mkdir -p "$ROOT/secrets"

# Auth is method-agnostic. The real on-the-wire headers live in
# requestWillBeSentExtraInfo; take the FIRST such event that already carries an
# AI Studio Authorization (origin-pinned) — guaranteed to have what we need, no
# requestId join. Emit each header except HTTP/2 pseudo-headers, per-call
# Content-Type/Accept, and the request's own Content-Length/Encoding (curl
# recomputes those for the new body).
auth_event="$(jq -cn 'first(inputs
  | select(.method=="Network.requestWillBeSentExtraInfo"
      and (.params.headers|has("authorization"))
      and .params.headers.origin=="https://aistudio.google.com"))' "$CAPTURE")"
[ -n "$auth_event" ] || { echo >&2 "no authenticated AI Studio request in $CAPTURE"; exit 2; }

jq -r '.params.headers | to_entries[]
  | select(.key|startswith(":")|not)
  | select((.key|ascii_downcase) as $k | ["content-type","accept","content-length","content-encoding"]|index($k)|not)
  | "header = \"\(.key): \(.value)\""' <<<"$auth_event" > "$OUT"

[ -s "$OUT" ] || { echo >&2 "extracted no headers"; exit 3; }
ts="$(jq -r '.params.headers.authorization | capture("(?<t>[0-9]{10})").t // "?"' <<<"$auth_event")"
echo "wrote $OUT  (SAPISIDHASH stamped at epoch ${ts})"
