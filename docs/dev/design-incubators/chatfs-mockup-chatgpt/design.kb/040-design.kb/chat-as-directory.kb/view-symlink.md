# View Symlink as Front Door

The user-facing entry point is `YYYY/.../$TITLE.md` — a symlink whose
target is `.chat/$UUID/chat.md`. The view path is UUID-free; the
storage path isn't, but users don't normally tread the storage layer.

## Stable canonical filename

The canonical filename inside storage is `chat.md`, not `$TITLE.md`.
Renaming a chat means just updating the view symlink — `chat.md`
itself never moves. This keeps the storage layer immutable across
title edits.

## Pre-render dangling

Pre-render, the view symlink dangles: its target `chat.md` doesn't
exist yet. Reading the symlink fails with ENOENT. Post-render, the
symlink resolves naturally.

The earlier layout used a self-symlink (`$TITLE.md` → its own basename,
dereferences to ELOOP) as the "not yet materialized" signal. That
trick is unnecessary here: a normal symlink to a not-yet-existing
target is already the right signal.
