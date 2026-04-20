<anthropic-skill-ownership llm-subtask />

---
required-reading:
  - docs/dev/design.kb/CLAUDE.md
  - docs/dev/design.kb/010-mission.kb/chatfs.md
  - docs/dev/design-rationale.md
---

# Reconcile design-rationale.md with Current Architecture

**Priority:** Medium
**Complexity:** Medium (substantive content revision, not mechanical)
**Discovered:** 2026-04-20 spot check during devlog GC

## Problem Statement

`docs/dev/design-rationale.md` is stale. Its link targets were updated
in the 2026-03-28 / 2026-04-20 cleanups, but its content still
describes the superseded architecture:

- Uses the four-layer model (`M1-CLAUDE / M2-VFS / M3-CACHE / M4-CLI`)
  that was replaced by the BB1/BB2/BB3 black-box decomposition
- Describes the "Unofficial claude.ai API (st1vms)" approach, superseded
  by browser-driven HAR capture (see `design-incubators/playwright-har-capture/`)
- "Lazy Filesystem Model" section lists "Option B: Lazy creation with
  mtime tracking via explicit CLI calls" — but the current design uses
  FUSE mount (Option C in that file, which it rejected)
- "Plumbing/porcelain split" evolution notes reference terminology
  that no longer exists

The file contradicts `docs/dev/design.kb/010-mission.kb/chatfs.md`
and `README.md`.

Subdocs under `docs/dev/design-rationale/`:
- `layered-architecture.md` — "Status: TODO - Deep dive to be written if needed"
  (never filled; references M1-M4)
- `lazy-filesystem.md` — likely stale (not verified in detail)
- `unofficial-api.md` — describes an API approach no longer used

## Proposed Solution

Two plausible paths:

### Option A: Rewrite to match current architecture
Rewrite `design-rationale.md` with:
- BB1 (browser capture) / BB2 (extract) / BB3 (render) as the design
- FUSE mount as the user-facing surface
- Browser HAR capture vs. unofficial API as the capture decision
- Keep the useful meta-decisions (JSONL interchange, documentation-first)

### Option B: Delete in favor of design.kb/
`design.kb/` already has mission / goals / requirements / design.
`design-rationale.md` may be redundant. Decisions could be captured
as ADRs under `design.kb/` or as `why:` links in requirements.

**Lean:** A mix. Rewrite `design-rationale.md` as a concise "why
we made these choices" overview, and delete the stub subdocs under
`design-rationale/`. Move capture-model rationale (HAR vs. unofficial
API) into `design.kb/` or an ADR — it's substantive enough to deserve
first-class treatment.

## Historical Source Material

Git preserves the prior devlogs that captured earlier decisions:

```bash
git show HEAD~1:docs/dev/devlog/2025-10-30-000-project-documentation-foundation.md
git show HEAD~1:docs/dev/devlog/2025-11-04-000-architecture-evolution-3-to-4-layers.md
```

(Those devlogs were GC'd in the 2026-04-20 cleanup because they
documented the superseded architecture.)

## Implementation Steps

- [ ] Read current `design-rationale.md` fully + all three subdocs
- [ ] Compare against current `design.kb/` collections
- [ ] Decide: rewrite, redirect, or delete
- [ ] If rewriting: preserve the still-valid meta-decisions (JSONL,
      documentation-first)
- [ ] Update all inbound links (CLAUDE.md, README.md, docs/README.md,
      docs/dev/README.md all still link to design-rationale.md)

## Success Criteria

- [ ] `design-rationale.md` either describes the current architecture
      or has been replaced with a redirect / deleted
- [ ] No document links to outdated decision rationales
- [ ] `grep -r "M1-CLAUDE\|M2-VFS\|M3-CACHE\|M4-CLI" docs/` returns
      only devlogs (historical) and technical-policy/design.kb where
      intentional
