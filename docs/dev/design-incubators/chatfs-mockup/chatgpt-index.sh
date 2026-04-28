#!/bin/bash
# chatgpt-index.sh — capture chatgpt.com and pluck the chat-index pages.
# Re-captures chatgpt.index.cdp.jsonl only when missing or older than 1 hour.
#
# Outputs:
#   chatgpt.index.cdp.jsonl  — raw CDP event stream from har-browse
#   chatgpt.index.jsonl      — one page of /backend-api/conversations per line
set -euo pipefail
export DEBUG="${DEBUG:-0}"

onerror() {
  error="$?"
  echo >&2 "ERROR($error)"
  exit "$error"
}
trap onerror ERR

HERE="$(cd "$(dirname "$0")" && pwd)"
CDP="$HERE/chatgpt.index.cdp.jsonl"
INDEX="$HERE/chatgpt.index.jsonl"
MAX_AGE_MIN=60

if (( DEBUG > 0 )); then
  set -x
fi

if [[ -f "$CDP" ]] && [[ -n "$(find "$CDP" -mmin -"$MAX_AGE_MIN" -print -quit)" ]]; then
  echo >&2 "$CDP is fresh (< ${MAX_AGE_MIN}m); skipping capture."
else
  echo >&2 "Capturing $CDP ..."
  har-browse https://chatgpt.com > "$CDP"
fi

"$HERE/chatgpt-index-pluck.jq" < "$CDP" > "$INDEX"

echo >&2 "Wrote $INDEX ($(wc -l < "$INDEX") page(s))."
