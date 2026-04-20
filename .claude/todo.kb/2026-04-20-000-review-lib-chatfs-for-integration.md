<anthropic-skill-ownership llm-subtask />

---
required-reading:
  - docs/dev/design.kb/CLAUDE.md
---

# Review lib/chatfs/ for Ideas Worth Salvaging

**Priority:** Low
**Complexity:** Medium (requires reading old docs + current design.kb/)

## Problem Statement

`lib/chatfs/` is a dead shell from the superseded 4-layer architecture
(M1-CLAUDE / M2-VFS / M3-CACHE / M4-CLI). It contains empty `__init__.py`
stubs and READMEs describing a model replaced by the BB1/BB2/BB3
black-box decomposition in `docs/dev/design.kb/040-design.kb/`.

We kept it in place (2026-04-20) rather than deleting it, because the
old architecture likely captured some real considerations that may not
have been carried forward.

## Goal

Systematically walk through the old `lib/chatfs/` structure and decide
for each idea/consideration:

1. **Already covered** in `design.kb/` — nothing to do
2. **Worth integrating** — open a design.kb update task
3. **Intentionally dropped** — note why, so future reviewers don't revisit
4. **Obsolete** — drop silently

## Scope

**Old structure to review:**
- `lib/chatfs/layer/native/claude/` (M1-CLAUDE: direct API wrapper)
- `lib/chatfs/layer/vfs/` (M2-VFS: normalized JSONL schema)
- `lib/chatfs/layer/cache/` (M3-CACHE: persistent storage, staleness)
- `lib/chatfs/layer/cli/` (M4-CLI: `chatfs-init`, `chatfs-ls`, `chatfs-cat`)

**Reference material** (some deleted, may need `git log`):
- Old `technical-design.md` + `technical-design/` subdocs
- Old `development-plan.md` + `development-plan/` subdocs
- Devlogs from 2025-10-30 through 2025-11-05
- Current `docs/dev/design.kb/040-design.kb/`

## Specific Questions to Answer

- **API-direct vs browser capture.** The old model used unofficial API;
  the new one uses browser-driven HAR capture. Did the old model address
  any concerns (schema stability, auth, rate-limiting) that the capture
  model doesn't?
- **Cache staleness tracking.** Old M3-CACHE had explicit staleness via
  mtime. Does `design.kb/` specify equivalent semantics, or is this
  implicit?
- **CLI UX.** Old M4-CLI specified `chatfs-init`/`-ls`/`-cat` with
  filesystem-like path conventions (`//provider/...`). With the pivot
  to FUSE mount, standard `ls`/`cat` replace these — but did the old
  design cover something like init/config that the FUSE model still
  needs?
- **Normalized JSONL schema.** M2-VFS was about cross-provider
  normalization. Where does that live now?
  `040-design.kb/canonical-conversation-graph.md` probably covers it —
  verify.

## Deliverable

One of:
- `design.kb/` updates (if salvage found)
- A short followup devlog entry summarizing "nothing new, all covered"
- Deletion of `lib/chatfs/` once review is complete

## How to Execute

Not urgent. Queue for a session with spare bandwidth. Should be
doable in one focused pass once the harmonization work lands.
