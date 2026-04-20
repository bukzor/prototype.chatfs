<anthropic-skill-ownership llm-subtask />

---
required-reading:
  - docs/dev/design.kb/CLAUDE.md
  - docs/dev/design.kb/010-mission.kb/chatfs.md
---

# Reconcile design-rationale.md with Current Architecture

**Status:** Done — 2026-04-20
**Priority:** Medium
**Complexity:** Medium (substantive content revision, not mechanical)
**Discovered:** 2026-04-20 spot check during devlog GC

## Resolution

Deleted `docs/dev/design-rationale.md` and the `design-rationale/` subdir
(all three subdocs were TODO stubs). Salvaged content into `design.kb/`:

- **Why existing solutions fail** → extended `010-mission.kb/chatfs.md`.
- **Capture mechanism decision** → promoted `040-design.kb/capture-patterns.md`
  (listing-style, plural) to `040-design.kb/capture-pattern.md` + sub-kb
  `capture-pattern.kb/` (five mechanism entries; network-events chosen).
- **User-facing surface decision** → `040-design.kb/user-interface.md` +
  sub-kb `user-interface.kb/` (five mechanism entries; fuse-mount chosen).
- **JSONL interchange rationale** → new `040-design.kb/jsonl-interchange.md`
  with inline "Why not plain JSON / binary / YAML / NDJSON" alternatives.
- **Documentation-first meta-principle** → intentionally not migrated; it's
  process/culture, not design.

Inbound links updated in README.md, docs/README.md, docs/dev/README.md,
HACKING.md (×2 sections), docs/dev/devlog/README.md.

No ADR directory created this pass; kept the pattern dormant until a decision
with extensive historicity/prose emerges. The inline "Why not X" shape
inside design.kb/ entries handled all four decisions cleanly — informed a
touch-up of `Skill(llm-design-kb)` to codify the alternatives-considered
pattern, and `Skill(llm-kb)` to add promotion-signals guidance.

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

- [x] Read current `design-rationale.md` fully + all three subdocs
- [x] Compare against current `design.kb/` collections
- [x] Decide: rewrite, redirect, or delete — chose delete + salvage into design.kb/
- [x] Preserve the still-valid meta-decisions (JSONL landed as `jsonl-interchange.md`;
      documentation-first left implicit in CLAUDE.md)
- [x] Update all inbound links (5 files updated)

## Success Criteria

- [x] `design-rationale.md` deleted; content salvaged into design.kb/ entries
- [x] No document links to outdated decision rationales
- [x] `M1-CLAUDE|M2-VFS|M3-CACHE|M4-CLI` no longer appears in any active design doc
