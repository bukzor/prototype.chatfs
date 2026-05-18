---
managed-by: Skill(llm-subtask)
---

# Rename incubator to chatfs-cli-mockup

**Priority:** Medium (precursor to multi-provider sketch)
**Complexity:** Low (mechanical rename + targeted reference updates)
**Context:** Conversation 2026-05-11; project todo item 4 (Multi-provider sketch).

## Problem Statement

The incubator is named `chatfs-mockup-chatgpt`. Once we add `claude/`
alongside `chatgpt/` for the multi-provider sketch, that name is
misleading — the incubator isn't chatgpt-specific. We want to rename
before starting claude work so the diff stays clean (one rename commit,
then provider additions).

## Current Situation

- Path: `docs/dev/design-incubators/chatfs-mockup-chatgpt/`
- The README's stated trajectory ("fold lessons back into design.kb
  and delete or archive this incubator") understates what's here: the
  noun-verb CLI surface is durable product, not throwaway scaffolding.
- 14 files reference the string `chatfs-mockup-chatgpt`. Survey done.

## Proposed Solution

**New name: `chatfs-cli-mockup`.**

Sharpened framing (from user, 2026-05-11):

> This is a prototype of a later `chatfs-cli` crate that will be
> load-bearing for the final chatfs. CLI shape survives the FUSE
> transition — FUSE invokes BB1/BB2/BB3 lazily under the hood, but the
> same commands exist as direct entry points for batch runs, testing,
> and pipelines. "cli" is durable in a way "chatgpt" never was.

Why `-mockup-` stays for now: still uses fake `chatfs.demo/` paths,
not on `$PATH`, design knowledge hasn't been promoted to project level
yet. Graduates to `packages/chatfs-cli/` (no `-mockup`) when those
three things change together. Want to be mindful about
incubator→release promotion, not auto-trigger it.

## Implementation Steps

- [ ] `git mv docs/dev/design-incubators/chatfs-mockup-chatgpt docs/dev/design-incubators/chatfs-cli-mockup`
- [ ] Update live references (string `chatfs-mockup-chatgpt` → `chatfs-cli-mockup`):
    - [ ] `pyproject.toml` — pyright `extraPaths`
    - [ ] `.claude/todo.md` (project) — section header + path references in items 1, 3
    - [ ] `docs/dev/adr/2026-04-29-000-no-freshness-caches.md` — `Scope:` line + See-also paths (keep title; historical)
    - [ ] Incubator interior: `README.md`, `design.kb/CLAUDE.md`, `design.kb/040-design.kb/CLAUDE.md`, `.claude/todo.kb/2026-05-05-001-…`, `.claude/todo.kb/2026-05-05-002-…`, `.claude/todo.md`
- [ ] Rewrite README closing paragraph with sharpened framing (proposed text in Notes below).
- [ ] Leave devlog filenames and in-body path references alone (historical record; rename is a discoverable point in `git log`).
- [ ] Commit as one rename commit.
- [ ] Restart Claude from the new path (old cwd dangles after `git mv`).

## Open Questions

- [x] Naming: `chatfs-cli-mockup` (vs `chatfs-mockup`, `chatfs-cli`). Resolved 2026-05-11.
- [x] Devlog policy: leave in-body path references alone. Resolved 2026-05-11.
- [ ] README reframing text — proposed in Notes; pending user sign-off.

## Success Criteria

- [ ] `grep -r chatfs-mockup-chatgpt` returns only devlog hits (historical).
- [ ] `tree docs/dev/design-incubators/chatfs-cli-mockup/` renders without dangling internal refs.
- [ ] pyright still clean against the renamed `extraPaths`.
- [ ] `git log --oneline` shows one rename commit, not interleaved with content changes.

## Notes

**Proposed README closing replacement.** Current text:

> Once the shape feels right, fold lessons back into design.kb and
> delete or archive this incubator.

Proposed replacement:

> This is a prototype of a future `chatfs-cli` crate that will be
> load-bearing for the final chatfs — the same CLI surface FUSE
> invokes lazily under the hood. Lessons settled here get folded back
> to project-level `design.kb/`; the scripts themselves graduate to
> `packages/chatfs-cli/` when ready.

**Why this todo lives at project level** (not in
`docs/dev/design-incubators/chatfs-mockup-chatgpt/.claude/todo.kb/`):
the rename changes the incubator's own path, so an incubator-local
todo file would rename mid-execution. The rename also touches project-
scoped files (`pyproject.toml`, the ADR). Project scope is the right
home.
