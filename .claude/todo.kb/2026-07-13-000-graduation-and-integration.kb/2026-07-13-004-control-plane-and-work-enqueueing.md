---
managed-by: Skill(llm-subtask)
blocked-by:
  - 2026-07-13-003-chatfs-bin-crate-and-mount-mvp.md
  - 2026-07-13-002-path-ownership-contract-v1.md
  - docs/dev/design-incubators/chatfs-cli-mockup/.claude/todo.kb/2026-07-13-000-Atomic-chat-dir-regeneration---stage-and-rename--never-rewrite-in-place.md
cost-benefit-sweh:
  timebox:
    "@value": 16.0
    rationale: >
      Widest error bars in the umbrella: writable-file support in
      chatfs-fuser, the in-daemon job queue, subprocess orchestration of
      chatfs-cli, and the waiting_user/browser plumbing. As-needed scope
      discipline is the cost control — build only what the next use case
      demands.
    confidence: hypothetical
  benefit-2w:
    "@value": 1.0
    rationale: >
      Completes the lazy-filesystem goal (sync-on-demand through the
      mount), but sits behind three blockers; unlikely to start within
      2w.
    confidence: tentative
---

# Control plane + work-enqueueing (in-integration, as-needed)

**Priority:** Medium — final integration child; starts after 002/003.
**Complexity:** High
**Context:** Design already written:
`docs/dev/design.kb/040-design.kb/sync-control-plane.md` (`control` /
`status` / `needs_sync/`, write-to-trigger, never sync-on-read) and
`work-enqueueing-model.md` (jobs keyed `(provider, conv_ref)` with dedup;
states idle/syncing/waiting_user/failed/done; staging → atomic rename;
failures never corrupt cache). Scheduling philosophy (2026-07-13): this
was fuser-vfs's unscheduled M3; agreed to resolve as-needed inside
integration rather than as a standalone milestone — the risky
kernel-facing parts were retired by M1/M2, and the remaining risks are
integration-shaped.

## Problem Statement

The read-only mount serves what exists; nothing connects a user's "sync
this" intent to the chatfs-cli pipeline. Add the control plane per the
design docs, executing pipeline runs as background jobs that update the
cache atomically.

## Implementation Steps

- [ ] chatfs-fuser: writable virtual files (`write`, maybe `setattr` for
      touch-as-trigger) — extend the builder in the crate's stateless
      idiom; expect POSIX write-semantics questions (partial writes,
      open flags) to surface here, settle them in the crate's
      technical-policy.kb as they do.
- [ ] In-daemon job queue (decided 2026-07-13: bespoke, not Rayon —
      that's CPU-bound data-parallelism; jobs here are subprocess-wait-
      bound and need keyed dedup + introspectable state): channel +
      worker threads + `Mutex<HashMap<JobKey, JobState>>`.
- [ ] Jobs invoke `chatfs-<provider>-…` entry points (subprocess; the
      path-ownership contract bounds what they may write); output lands
      via the atomic staging convention.
- [ ] `status` / `needs_sync/` read-side surfaces from queue state.
- [ ] `waiting_user`: capture jobs need a human-driven browser —
      DISPLAY/session plumbing from a daemon context; expected trouble
      spot, design when reached.

## Open Questions

- Deliberately many — this child is as-needed by construction. Record
  resolutions in the crate/package design kbs as they land, not here.

## Success Criteria

- [ ] `echo sync <id> > control` (or `touch`) syncs one conversation
      end-to-end through the mount; `grep -r` triggers nothing.
- [ ] Kill a sync mid-flight: mount keeps serving prior content
      (atomic-cache-updates verification passes at the mount).
- [ ] `status` reflects job lifecycle including `waiting_user`.
