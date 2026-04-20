<anthropic-skill-ownership llm-subtask />

---
required-reading:
  - docs/dev/design.kb/CLAUDE.md
---

# Review lib/chatfs/ for Ideas Worth Salvaging

**Status:** Done — 2026-04-20. Promoted to `packages/chatfs/`.
**Priority:** Low
**Complexity:** Medium (requires reading old docs + current design.kb/)

## Resolution

**Outcome:** moved, not deleted. `lib/chatfs/` → `packages/chatfs/`, wired
as a uv workspace member, installed by default via `uv sync` at the
workspace root, exposes a `chatfs` CLI entry point.

Initial pass concluded "nothing salvageable" based on the empty docstring
content — superseded M1-M4 scaffolding with zero implementation code. That
review conflated "no salvageable *content*" with "no real concern." The
concerns the old tree labeled (cache layer, init/config surface) are real
forward work; moving the package reserves the Python home for them rather
than forcing a later recreate-from-scratch.

Walking the subtask's four specific questions:

- **API-direct vs browser capture.** Docstring claims were structural and
  obsolete; no concerns not already covered by the current design
  (opaque-extractor-boundary, capture-pattern, HAR capture).
- **Cache staleness tracking.** The old mtime-based model required network
  per read, incompatible with `030-requirements.kb/no-network-on-read.md`.
  But a cache layer itself remains a real concern in the new design: plain
  files backing the FUSE mount, with retrieval-time mtime and HTTP-style
  cache-control metadata. Not yet captured in design.kb/ — pending future
  design work.
- **CLI UX (`chatfs-init` etc.).** Not spec'd in the old tree. The
  daemon's one-time setup surface (mount point config, profile enrollment)
  is a real concern, not yet captured in design.kb/ — pending future
  design work.
- **Normalized JSONL schema.** Covered by
  `040-design.kb/canonical-conversation-graph.md`.

## Follow-ups

Spawned during resolution, not yet tracked as subtasks:

- **Cache layer design** (in flux). Plain-filesystem cache adjacent to the
  mount point, mtime = retrieval time, HTTP cache-control metadata alongside
  content. FUSE-over-obscured-content ruled out (mount replaces kernel view);
  cache at a sibling path (e.g. `$XDG_CACHE_HOME/chatfs/`) is the clean
  answer.
- **Daemon setup / init surface.** What `chatfs init` does, how providers
  are enrolled, mount-point configuration.
- **`layer/` subtree cleanup.** The M1-M4 submodule scaffolding moved along
  with the package; docstrings still reference the superseded architecture.
  Not load-bearing (empty __init__.py files), so deferred.
- **Maybe-P3: rewrite in Rust.** The top-level CLI could eventually live
  with the Rust daemon rather than in Python. Not decided; maybe never.

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
