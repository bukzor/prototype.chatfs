---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 2.0
    rationale: |
      Mechanical git-mv + grep-replace across ~14 references + README
      reframe. Pending user sign-off on README wording. Low complexity
      per the file's own assessment.
    confidence: tentative
  benefit-2w:
    "@value": 0.3
    rationale: |
      Unblocks multi-provider sketch (the renaming is its precursor).
      Modest direct benefit, larger second-order benefit if multi-
      provider work lands shortly after.
    confidence: tentative
  cost-of-delay-2w:
    "@value": 0.1
    rationale: |
      The misleading name doesn't break anything; only blocks adding
      `claude/` alongside `chatgpt/` in the incubator. Low per-2w
      drag.
    confidence: tentative
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

- [x] `git mv docs/dev/design-incubators/chatfs-mockup-chatgpt docs/dev/design-incubators/chatfs-cli-mockup`
      (2026-07-10)
- [x] Update live references (string `chatfs-mockup-chatgpt` → `chatfs-cli-mockup`):
    - [x] `pyproject.toml` — pyright `extraPaths`
    - [x] `.claude/todo.md` (project) — section header + path reference in
          item 3 (item 1's reference turned out to be a devlog filename —
          kept, historical)
    - [x] `docs/dev/adr/2026-04-29-000-no-freshness-caches.md` — `Scope:` line +
          design.kb See-also path (title and devlog See-also kept; historical)
    - [x] Incubator interior: `README.md`, `design.kb/CLAUDE.md`,
          `design.kb/040-design.kb/CLAUDE.md`, `.claude/todo.md`,
          `dev.kb/claims.kb/har-browse-cdp-may-trail-visual-interactability.md`
          (the `2026-05-05-*` todo.kb files from the 2026-05-11 survey no
          longer existed). References accreted since the survey, also swept:
          `docs/dev/aistudio-schema/` (README, bundles.do, .claude/todo.md,
          2 discourse.kb files) and
          `docs/dev/design.kb/040-design.kb/canonical-conversation-graph.md`.
- [x] Rewrite README closing paragraph with sharpened framing (proposed text in
      Notes below, amended: graduation target is `$REPO/lib/chatfs/`, per the
      2026-07-10 libraryization decision — not `packages/chatfs-cli/`).
- [x] Leave devlog filenames and in-body path references alone (historical
      record; rename is a discoverable point in `git log`).
- [x] Commit as one rename commit. (2026-07-10; concurrent unrelated edits
      committed separately.)
- [x] Restart Claude from the new path (old cwd dangles after `git mv`).
      Turned out unnecessary: the harness followed the moved cwd mid-session.

## Open Questions

- [x] Naming: `chatfs-cli-mockup` (vs `chatfs-mockup`, `chatfs-cli`). Resolved 2026-05-11.
- [x] Devlog policy: leave in-body path references alone. Resolved 2026-05-11.
- [x] README reframing text — proposed in Notes; approved 2026-07-10 with one
      amendment: graduation target `$REPO/lib/chatfs/` once libraryized.

## Success Criteria

- [x] `grep -r chatfs-mockup-chatgpt` returns only historical hits: devlog
      filenames/bodies, devlog-filename refs in project todo.md, the ADR title,
      and this file's own record. Verified 2026-07-10.
- [x] `tree docs/dev/design-incubators/chatfs-cli-mockup/` renders without
      dangling internal refs; no symlink targets the old path
      (`find docs -type l -lname '*chatfs-mockup-chatgpt*'` empty).
- [x] pyright still clean against the renamed `extraPaths` (basedpyright
      0/0/0; pytest 19/19).
- [x] `git log --oneline` shows one rename commit, not interleaved with content
      changes (concurrent todo/plan edits and the focus.md removal committed
      separately).

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
