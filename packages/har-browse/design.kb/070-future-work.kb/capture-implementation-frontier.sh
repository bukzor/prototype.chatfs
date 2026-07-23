#!/bin/bash
# Regenerate the candidate comparison table for
# capture-implementation-frontier.md from the frontmatter in
# capture-implementation-frontier.kb/*.md -- the frontmatter is the
# source of truth, this table is a rendering of it. Re-run and paste
# over the "## Comparison Table" section whenever a candidate file's
# frontmatter changes or a candidate is added/removed.
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
kb="$here/capture-implementation-frontier.kb"
kb_name="$(basename "$kb")"

for f in "$kb"/*.md; do
  [[ "$(basename "$f")" == CLAUDE.md ]] && continue
  title="$(sed -n '/^# /{s/^# //;p;q}' "$f")"
  md-frontmatter "$f" |
    jq --arg title "$title" --arg file "$kb_name/$(basename "$f")" \
      '.["@value"] + {title: $title, file: $file}'
done |
  jq -s -r '
    sort_by(
      (if .status == "frontier-optimal" then 0 else 1 end),
      (."owned-loc" | ltrimstr("~") | tonumber? // 999)
    )
    | (["Candidate", "Status", "Owned LOC", "Middleware", "Silent-miss", "Crash-durable", "Stealth", "BB1 purity"]) as $hdr
    | ($hdr | map("---")) as $sep
    | ([$hdr, $sep] + map([
        "[\(.title)](\(.file))",
        .status,
        ."owned-loc",
        .middleware,
        ."silent-miss",
        ."crash-durable",
        .stealth,
        ."bb1-purity"
      ]))
    | .[]
    | "| " + join(" | ") + " |"
  '
