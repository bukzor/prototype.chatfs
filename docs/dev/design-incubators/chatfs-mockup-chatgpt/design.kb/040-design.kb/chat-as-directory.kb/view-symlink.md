# View Symlink as Front Door

The user-facing entry point is `YYYY/.../$TITLE.md` — a symlink whose
target is `.chat/$UUID/chat.md`. The view path is UUID-free; the
storage path isn't, but users don't normally tread the storage layer.

## Stable canonical filename

The canonical filename inside storage is `chat.md`, not `$TITLE.md`.
Renaming a chat means just updating the view symlink — `chat.md`
itself never moves. This keeps the storage layer immutable across
title edits.

## Frontmatter for portability

`chat.md` carries `uuid:` frontmatter:

```markdown
---
uuid: 69dfa575-c0e0-832c-99c2-4e1919ab50de
---

# 000 · user · 14:53:42
[…]
```

The frontmatter exists for documents that travel outside the tree
(copy/paste, attached to email, etc.) — the file remains
self-identifying without depending on its path. `uuid` is the only
field there because it's the only one not derivable from location
inside the tree.

## Pre-render dangling

Pre-render, the view symlink dangles: its target `chat.md` doesn't
exist yet. Reading the symlink fails with ENOENT. Post-render, the
symlink resolves naturally.

The earlier layout used a self-symlink (`$TITLE.md` → its own basename,
dereferences to ELOOP) as the "not yet materialized" signal. That
trick is unnecessary here: a normal symlink to a not-yet-existing
target is already the right signal.
