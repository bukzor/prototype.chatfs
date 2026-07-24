#!/bin/bash
# One YAML document per candidate in capture-implementation-frontier.kb/*.md
# (skipping CLAUDE.md), each prefixed with a title (from the file's H1) and
# its relative path, then the file's own frontmatter. The frontmatter is the
# source of truth; this is a synthesized read-through of it.
set -euo pipefail
shopt -s failglob
export DEBUG="${DEBUG:-0}"

onerror() {
  error="$?"
  echo >&2 "ERROR($error)"
  exit "$error"
}
trap onerror ERR

if (( DEBUG > 0 )); then
  set -x
fi

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
kb="capture-implementation-frontier.kb"

( cd "$here"
  first=1
  for f in "$kb"/*.md; do
    [[ "$(basename "$f")" == CLAUDE.md ]] && continue
    if (( first )); then
      first=0
    else
      echo ---
    fi
    title="$(sed -n '/^# /{s/^# //;p;q}' "$f")"
    md-frontmatter "$f" |
      jq --arg title "$title" --arg file "$kb/$(basename "$f")" \
        '{title: $title, file: $file} + .["@value"]' |
      yq -P .
  done
)
