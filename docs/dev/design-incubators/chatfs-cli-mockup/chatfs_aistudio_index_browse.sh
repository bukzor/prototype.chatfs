#!/bin/bash
# chatfs_aistudio_index_browse.sh — capture aistudio.google.com's prompt index.
#
# stdout: one index entry per line (jsonl) — pluck flattens every
# ListPrompts response it sees, so this catches as many pages as
# har-browse's session actually triggers. This account's 42 prompts fit
# one page, so a scroll-triggered second page is unverified here — same
# har-browse "wait until has_more=false" gap tracked for claude (todo.md).
set -euo pipefail
export DEBUG="${DEBUG:-0}"

onerror() {
  error="$?"
  echo >&2 "ERROR($error)"
  exit "$error"
}
trap onerror ERR

HERE="$(cd "$(dirname "$0")" && pwd)"
CDP="$HERE/aistudio.index.cdp.jsonl"   # debug intermediate

if (( DEBUG > 0 )); then
  set -x
fi

echo >&2 "Capturing aistudio.google.com/library → $CDP ..."
har-browse https://aistudio.google.com/library | tee "$CDP" | "$HERE/chatfs_aistudio_index_pluck.jq"
