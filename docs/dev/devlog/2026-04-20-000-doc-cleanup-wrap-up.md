# 2026-04-20: Doc Cleanup Wrap-Up

## Focus

Finish the stale-reference cleanup started on 2026-03-28 and commit the
in-progress changes.

## What Happened

The 2026-03-28 session had renamed `docs/dev/design/` →
`docs/dev/design.kb/` and deleted `technical-design.md`,
`development-plan.md`, and `STATUS.md`, but left 13 files with stale
references uncommitted. This session:

- Verified each staged edit actually resolves its stale references
- Rewrote `README.md` to describe the FUSE+Playwright BB1/BB2/BB3 model
  (was still describing the old `chatfs-ls`/`chatfs-cat` CLI and four-layer
  M1-M4 architecture)
- Rewrote `HACKING.md` project structure for the `packages/` layout
  (chatfs-fuser Rust crate, bukzor.chatgpt-export Python); dropped the
  defunct `lib/chatfs/...` tree description
- Deleted `TODO.md` (432 lines, stale since 2025-11-05, entirely
  superseded by `.claude/todo.md` + `.claude/todo.kb/`)
- Marked the three related subtasks as done:
  - `2026-01-02-001-migrate-todo-to-subtask-format.md` — TODO.md gone
  - `2026-03-28-000-clean-stale-references-to-deleted-docs.md` — 13 files
    addressed
  - Parent `2026-01-02-000-harmonize-with-llm-skills.md` — Phase 2
    tactical items all done locally; skills-repo Phase 1 still pending

## Decisions

**Kept `lib/chatfs/` in place.** It's a dead shell — seven empty
`__init__.py` files plus three (now-updated) READMEs for a 4-layer
architecture that's been superseded by BB1/BB2/BB3 and the `packages/`
layout. Retaining it as a placeholder until we have a confirmed Python
home for whatever replaces it.

**TODO.md deleted rather than cleaned.** The content was two Claude
sessions deep in a documentation plan (Phase 1 through Phase 4) for an
architecture that no longer exists. No item was salvageable into the new
design.kb/ structure.

## Next Session

- Harmonize-with-llm-skills parent task still has two open items:
  - Phase 1: skills-repo `.d → .kb` rename + llm-collab skeleton
    (blocks `milestones.kb/` creation here)
  - `milestones.kb/` creation (post-Phase 1)
- Follow-up candidate: decide whether `lib/chatfs/` should be deleted
  once a Python replacement is confirmed sufficient.

## Links

- [../../../.claude/todo.kb/2026-03-28-000-clean-stale-references-to-deleted-docs.md]
- [../../../.claude/todo.kb/2026-01-02-001-migrate-todo-to-subtask-format.md]
- [../../../.claude/todo.kb/2026-01-02-000-harmonize-with-llm-skills.md]
