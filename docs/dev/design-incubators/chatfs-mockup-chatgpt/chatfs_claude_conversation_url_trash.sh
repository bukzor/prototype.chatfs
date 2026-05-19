#!/bin/bash
# Move the products of `chatfs_claude_conversation_url_browse.py <url>`
# into a date-labelled subdir of repo-root `trash/` — the chat dir
# itself plus any view symlinks that point into it. After moving each
# symlink, `rmdir -p` walks up the view-tree path, removing any
# parents left empty; stops at the first non-empty ancestor.
set -euo pipefail

usage() { echo "usage: $0 <claude-url>" >&2; exit 2; }
[ $# -eq 1 ] || usage

url="$1"
uuid="${url##*/}"

here="$(cd "$(dirname "$0")" && pwd)"
root="$here/chatfs.demo/claude"
trash="$(git -C "$here" rev-parse --show-toplevel)/trash/$(date -Ins)"

mkdir -p "$trash"

mv "$root/.chat/$uuid" "$trash/"

export trash
find "$root" -maxdepth 5 -type l -lname "*$uuid*" -print0 |
    xargs -0 -n1 sh -euc '
        link="$1"
        set -x
        mv "$link" "$trash/"
        rmdir -p "$(dirname "$link")" 2>/dev/null || :
    ' -

echo "Moved to: $trash" >&2
