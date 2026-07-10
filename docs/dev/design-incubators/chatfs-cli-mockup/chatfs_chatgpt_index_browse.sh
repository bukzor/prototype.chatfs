#!/bin/bash
# chatfs_chatgpt_index_browse.sh — capture chatgpt.com index pages.
#
# stdout: one /backend-api/conversations page per line (jsonl).
set -euo pipefail
export DEBUG="${DEBUG:-0}"

onerror() {
  error="$?"
  echo >&2 "ERROR($error)"
  exit "$error"
}
trap onerror ERR

HERE="$(cd "$(dirname "$0")" && pwd)"
CDP="$HERE/chatgpt.index.cdp.jsonl"   # debug intermediate

if (( DEBUG > 0 )); then
  set -x
fi

echo >&2 "Capturing chatgpt.com index → $CDP ..."
har-browse https://chatgpt.com | tee "$CDP" | "$HERE/chatfs_chatgpt_index_pluck.jq"
