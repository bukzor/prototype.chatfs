---
managed-by: Skill(llm-subtask)
blocked-by:
  - 2026-07-13-001-promote-to-packages-chatfs-cli.md
related-effort: docs/dev/design.kb/040-design.kb/package-division.md
cost-benefit-sweh:
  timebox:
    "@value": 8.0
    rationale: >
      chatfs-fuser's builder already serves fresh dynamic trees; the MVP
      is a bin crate wiring a cache-root walk into FilesystemBuilder plus
      arg parsing and mount lifecycle. Fuser-side surprises (symlink-heavy
      trees, `:` in dirnames) are the contingency.
    confidence: tentative
  benefit-2w:
    "@value": 2.0
    rationale: >
      First user-visible product: captured conversations served to
      grep/ls/cat/editors. Delivers the mission's composability for
      already-captured data even before any laziness.
    confidence: tentative
---

# `chatfs` bin crate + `chatfs mount` read-only MVP

**Priority:** High
**Complexity:** Medium
**Context:** Package division:
`docs/dev/design.kb/040-design.kb/package-division.md` (crate `chatfs` =
the umbrella binary; `chatfs-fuser` stays a generic lib). Mount UX:
`chatfs mount --cache DIR MOUNTPOINT`, cache root always an argument
(decided 2026-07-13 — per-mount stability is all the VFS needs; XDG
defaults are deferrable ergonomics).

**The `blocked-by` edge is representational only** — child 001's rename
frees the `packages/chatfs` directory name. Conceptually this is
independent and can be prototyped any time against the incubator's
`chatfs.demo/` tree; relax the edge by starting in a scratch dir if
parallelism is wanted.

## Problem Statement

chatfs-fuser is a library; nothing mounts chatfs data. Create the bin
crate and serve a materialized cache tree read-only — the substrate the
control plane (child 004) extends.

## Implementation Steps

- [ ] New cargo workspace member `packages/chatfs`: bin crate `chatfs`,
      subcommand `mount` (leave room for the future dispatcher — see
      `070-future-work.kb/cli-subcommand-dispatcher.md`).
- [ ] Wire cache-root traversal into `FilesystemBuilder` (dynamic
      `dir_each` over the date tree and `.chat/`), preserving symlinks
      and hiding `.data/` per current `ls` conventions.
- [ ] Mount lifecycle: foreground, block until `fusermount -u` (current
      chatfs-fuser behavior); daemonization deferred until wanted.
- [ ] Smoke against a real captured tree: `ls`/`cat`/`rg`/editor open, the
      M1 acceptance list.

## Open Questions

- Serve the cache dir as passthrough vs re-derive the view in the daemon —
  MVP answer is passthrough (the materialized tree *is* the layout);
  revisit only if the control plane needs virtual entries interleaved.

## Success Criteria

- [ ] `chatfs mount --cache <dir> <mountpoint>` serves an existing
      captured tree; M1 acceptance items pass against it.
- [ ] `cargo test` green; crate follows chatfs-fuser's conventions
      (edition 2024, workspace member).
