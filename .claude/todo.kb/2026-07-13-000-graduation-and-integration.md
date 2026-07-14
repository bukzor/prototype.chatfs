---
managed-by: Skill(llm-subtask)
required-reading:
  - docs/dev/design.kb/040-design.kb/package-division.md
suggested-reading:
  - docs/dev/devlog/2026-07-13-000-graduation-and-integration-planning.md
cost-benefit-sweh:
  timebox:
    "@value": 40.0
    rationale: >
      Rollup over six children: module refactor ~4h, promotion ~4h,
      contract v1 ~2h, bin crate + mount MVP ~8h, control plane +
      enqueueing ~16h (as-needed scope, widest error bars), design.kb
      reconciliation ~4h. Children carry their own estimates; this cap
      is the reassess point for the arc as a whole.
    confidence: tentative
  benefit-2w:
    "@value": 4.0
    rationale: >
      The mount MVP alone makes every captured conversation greppable in
      daily work (the mission's payoff). Full control plane extends that
      to sync-on-demand. Realistically only the first children land
      within 2w.
    confidence: tentative
  cost-of-delay-2w:
    "@value": 0.5
    rationale: >
      No external deadline. Main delay cost is the incubator's flat-script
      shape taxing each further session (pyright workaround, sibling
      imports) and design.kb staleness (stack-split) misleading new work.
    confidence: tentative
---

# Graduation & Integration — incubator → packages → mount

**Priority:** High — the project's active arc as of 2026-07-13.
**Complexity:** High (as a whole; children are individually Low-Medium)
**Context:** Planned 2026-07-13 (devlog
`docs/dev/devlog/2026-07-13-000-graduation-and-integration-planning.md`).
The chatfs-cli-mockup incubator is feature-complete for three providers;
chatfs-fuser is solid through read-only dynamic serving (M1/M2). This
umbrella takes the pipeline from incubator scripts to a packaged
`chatfs-cli`, adds the Rust `chatfs` binary, and integrates them into the
FUSE mount the top-level design specifies.

## Problem Statement

The working pipeline lives as ~30 flat sibling-importing scripts inside
`docs/dev/design-incubators/chatfs-cli-mockup/`, invocable only from that
directory. The FUSE layer exists as a generic crate with no chatfs binary.
Nothing mounts. The design.kb still describes a two-way Rust/Node split
that ground truth has outgrown.

## Children (in `2026-07-13-000-graduation-and-integration.kb/`)

- [ ] [000 — module-shape refactor](2026-07-13-000-graduation-and-integration.kb/2026-07-13-000-module-shape-refactor.md)
- [ ] [001 — promote to packages/chatfs-cli](2026-07-13-000-graduation-and-integration.kb/2026-07-13-001-promote-to-packages-chatfs-cli.md)
- [x] [002 — path-ownership contract v1](2026-07-13-000-graduation-and-integration.kb/2026-07-13-002-path-ownership-contract-v1.md) — landed 2026-07-14 as `docs/dev/technical-policy.kb/path-ownership.md`.
- [ ] [003 — `chatfs` bin crate + `chatfs mount` MVP](2026-07-13-000-graduation-and-integration.kb/2026-07-13-003-chatfs-bin-crate-and-mount-mvp.md)
- [ ] [004 — control plane + work-enqueueing](2026-07-13-000-graduation-and-integration.kb/2026-07-13-004-control-plane-and-work-enqueueing.md)
- [ ] [005 — design.kb reconciliation + graduation ADR](2026-07-13-000-graduation-and-integration.kb/2026-07-13-005-design-kb-reconciliation-and-graduation-adr.md)

Dependency edges live in each child's `blocked-by:` frontmatter. Shape:

    000 ──► 001 ──► 003 ──► 004
                     ▲       ▲ ▲
    002 ────────────(─)──────┘ │
         └─────► 005           │
    atomic-regeneration ───────┘   (incubator todo, pre-existing)

The 001→003 edge is representational only (the `packages/chatfs` directory
name is freed by 001's rename); 003 is conceptually independent and can be
prototyped against the incubator's `chatfs.demo/` tree at any time.

## Related, outside this umbrella

- **Atomic chat-dir regeneration** — first-priority incubator todo
  (`docs/dev/design-incubators/chatfs-cli-mockup/.claude/todo.kb/2026-07-13-000-Atomic-chat-dir-regeneration---stage-and-rename--never-rewrite-in-place.md`);
  lands before or with 000/001, consumed by 004.
- **`.data/` scratch dot-d migration** — incubator todo
  (`docs/dev/design-incubators/chatfs-cli-mockup/.claude/todo.kb/2026-07-14-000-Migrate-data-scratch-files-into-dot-d-sibling-directories.md`);
  implements 002's `.data/` scratch convention. Orthogonal — no
  `blocked-by` edge to anything in this umbrella; cheapest to land
  alongside 000's file-touching pass but not required to.
- **Cross-kb cooperation conventions** — upstream in llm-kb
  (`~/.claude/skills/llm-kb/.claude/todo.kb/2026-07-13-000-cross-kb-cooperation-conventions.md`);
  005 uses interim conventions rather than waiting.

## Interim decisions in force (usable now; considered track proceeds independently)

1. Cross-kb conventions: symlinks for shared files, relative paths for
   cross-kb references, repo-wide backlink grep on any move/delete.
2. Path-ownership contract: descriptive v1 of current reality (child 002);
   revision expected, reviewed per se.
3. Extension-point naming: declared in `package-division.md`, exercised
   only when needed.
4. Python import package stays `chatfs` (distribution `chatfs-cli`);
   reopen only on demonstrated confusion.

## Success Criteria

- [ ] `uv sync` installs `chatfs-cli`; every pipeline entry point runs from
      `$PATH` against a user-chosen cache root.
- [ ] `chatfs mount --cache DIR MOUNTPOINT` serves captured conversations
      to standard tools.
- [ ] Sync is triggerable through the mount (control plane) without
      violating no-network-on-read; kill-mid-sync leaves prior content
      serving (atomic-cache-updates verification).
- [ ] Project design.kb states seams only; package-scoped kbs own
      internals; graduation recorded as ADR.

## Notes

Scheduling philosophy agreed 2026-07-13: no pre-integration M3 milestone —
control-plane scope is resolved as-needed inside integration (child 004).
Incubator tactical items are carried, not drained; unclosed incubator todos
re-home with the code at child 001.
