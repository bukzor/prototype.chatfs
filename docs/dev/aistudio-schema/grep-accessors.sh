#!/bin/bash
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

# One immutable-JS-proto accessor per line, from bundle JS on stdin:
#   get<Name>() { return _.<prim>(this, [<Ctor>,] <number> [, ...]) }
# Bundles may be minified (one line) or prettified (multi-line); fold all
# newlines to spaces first so a single -oE pass matches either, then -o
# keeps just the accessor up to the primitive call's closing paren.
tr '\n' ' ' | grep -oE 'get[A-Z][A-Za-z0-9]*\(\) *\{ *return _\.[A-Za-z0-9]+\(this,[^)]*\)'
