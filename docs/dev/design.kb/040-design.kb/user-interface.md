---
last-updated: "2026-04-20"
why:
  - no-network-on-read
  - explicit-sync-triggers
background:
  - fuse-filesystem
  - google-piper-precedent
---

# User Interface

**Question.** How does the user's tooling reach cached conversation data?

**Answer.** A FUSE mount. A userspace daemon serves the cache as a real
filesystem at a user-chosen mount point; standard tools (`ls`, `cat`,
`grep`, editors, file managers) work unmodified against it. See
`user-interface.kb/fuse-mount.md`.

## Why this one

- **Standard tools work.** The mission
  (`010-mission.kb/chatfs.md`) is Unix composability. That requires a real
  filesystem surface, not a custom CLI or GUI.
- **No custom client per tool.** Every OS-level file operation becomes a
  chatfs client — no integration work per editor, file manager, or
  pipeline.
- **Structural enforcement of `no-network-on-read`.** The daemon's read
  path has no network client; the requirement can't be violated by a
  future code change on accident.
- **Minimal surface.** In-process daemon, no listening ports, no auth. Mount
  lifetime matches the daemon process.

## Alternatives considered

Five mechanisms were on the table. See `user-interface.kb/` for per-mechanism
detail.

- `fuse-mount.md` — **chosen.** Userspace FUSE daemon.
- `explicit-cli.md` — custom commands (`chatfs-ls`, `chatfs-cat`, etc.).
  Earlier designs chose this; the standard-tools win of FUSE proved decisive.
- `webdav-nfs.md` — network filesystem protocols. Significantly larger
  surface area (auth, ports, network reachability) for no additional
  user-visible capability.
- `standalone-gui.md` — dedicated viewer application. Defeats the mission.
  Fine as an additive layer over the FUSE mount; not as a replacement.
- `eager-bulk-sync.md` — periodic rsync-style export to plain files.
  Simpler user model, but incompatible with the lazy-filesystem goal at
  realistic conversation counts.
