# Collision Tolerance

The contract: **`.chat/$UUID/` is fully consistent under all
eventualities; the view may be lossy under pathological collisions.**

## Cases

- **Same `create_time` (same-second creation).** Both chats get
  distinct `.chat/$UUID/` dirs (always unambiguous). In the view, both
  land under one `YYYY/MM/.../HH:MM:SS±HH:MM/` dir — one
  directory-symlink per chat, named by title.

- **Same `create_time` and same title.** The dir-symlink name collides
  — whichever chat was placed last wins. Storage is still fine; the
  view loses a navigation entry.

## Why we accept this

The view is rebuildable from `.chat/`. A lossy view in a
vanishingly-rare case is acceptable when:
- Both losses are *navigation* losses; no captured or derived data is
  lost.
- The data is recoverable by walking `.chat/` directly, or by
  rebuilding the view (a future verb) which can pick a different
  collision strategy if needed.
- Adding suffix logic (`Title (69dfa57).md`) for the rare case adds
  complexity to every place_meta call for a payoff observable
  approximately never.

If collisions become operationally common, the view-builder grows a
collision strategy (suffix the dir-symlink with `(<short-uuid>)` or
similar). Until then, the simpler invariant ("storage authoritative;
view best-effort under collisions") wins.
