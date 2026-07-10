#!/bin/bash
# chatfs_claude_index_browse.sh — capture claude.ai index pages.
#
# stdout: one /chat_conversations_v2 page per line (jsonl).
set -euo pipefail
export DEBUG="${DEBUG:-0}"

onerror() {
  error="$?"
  echo >&2 "ERROR($error)"
  exit "$error"
}
trap onerror ERR

HERE="$(cd "$(dirname "$0")" && pwd)"
CDP="$HERE/claude.index.cdp.jsonl"   # debug intermediate

if (( DEBUG > 0 )); then
  set -x
fi

echo >&2 "Capturing claude.ai index → $CDP ..."
har-browse https://claude.ai/recents | tee "$CDP" | "$HERE/chatfs_claude_index_pluck.jq"
