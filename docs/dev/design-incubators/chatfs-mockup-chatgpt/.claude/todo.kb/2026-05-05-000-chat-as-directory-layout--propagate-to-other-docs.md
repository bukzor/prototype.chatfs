---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 1.0
    rationale: |
      Doc-consistency sweep — README pipeline diagram + Run-it example
      + frontmatter validation script. ~1h mechanical work plus
      sanity checks against the new chat-as-directory layout.
    confidence: tentative
  benefit-2w:
    "@value": 0.3
    rationale: |
      Doc consistency win — future agents orienting on the layout
      stop tripping over stale flat-layout references. No
      implementation unblocked.
    confidence: tentative
  cost-of-delay-2w:
    "@value": 0.0
    rationale: |
      File self-classifies "does not block implementation; doc
      consistency." Other agents may misread layout from the stale
      docs, but cost manifests one-shot per encounter, not a flowing
      tax. Set to 0; not zero in expectation but trivial.
    confidence: tentative
---

# chat-as-directory layout — propagate to other docs

**Priority:** Medium (does not block implementation; doc consistency)
**Complexity:** Low (mechanical search-and-replace + diagram refresh)
**Context:**
- `design.kb/040-design.kb/chat-as-directory.md` (the new layout)
- `design.kb/040-design.kb/chat-as-directory.kb/*.md`
- `design.kb/040-design.kb/deterministic-regeneration.md`

## Problem Statement

The chat-as-directory redesign (storage at `.chat/$UUID/`, view as
symlinks under `YYYY/MM/…`) was captured in `chat-as-directory.md`
and its sub-kb, plus the per-stage list in
`deterministic-regeneration.md`. Other docs in the same neighborhood
still describe the old flat layout (`meta.json`, `$UUID.json`,
`$UUID.splat/`, `$TITLE.md` siblings under a ts-dir). Future readers
hit conflicting descriptions.

## Current Situation

Stale references to the old layout exist in:

- `design.kb/040-design.kb/browse-incidental-capture.md` — refers to
  `$UUID.json` (new name: `conversation.json`); paths look flat under
  the ts-dir.
- `design.kb/040-design.kb/no-partial-synthesis.md` — `meta.json`
  filename still accurate, but should note the new location under
  `.chat/$UUID/`.
- `README.md` — pipeline diagram (`chatfs.demo/chatgpt/YYYY/MM/DD/...`
  block) and the `Run it` snippet describe the old layout entirely.
- `design.kb/040-design.kb/cli-command-shape.md` — script names
  unchanged, but example outputs / paths may reference old shape.
- `design.kb/040-design.kb/stdio-pipeline-shape.md` — orchestrator
  examples may reference ts-dir as the addressable target; new
  canonical address is `.chat/$UUID/`.

## Proposed Solution

Per-doc minimal-touch update:

- Rename references: `$UUID.json` → `conversation.json`;
  `$UUID.splat/` → unpacked `messages/` + `conversations/`.
- Update path examples to show `.chat/$UUID/` for storage and
  `YYYY/MM/...` for view.
- Refresh the README pipeline diagram + `Run it` example to match
  current scripts (after implementation lands; co-sequence with that).
- Confirm cross-references in `chat-as-directory.md` and its sub-kb
  resolve correctly to the updated docs.

## Implementation Steps

- [x] `browse-incidental-capture.md`: update `$UUID.json` →
  `conversation.json`; clarify that the index pluck's match populates
  `.chat/$UUID/meta.json`.
- [x] `no-partial-synthesis.md`: `meta.json` examples → note the
  `.chat/$UUID/meta.json` location.
- [x] `cli-command-shape.md`: scan for layout-specific examples; update
  if found. (Hierarchy block: `<ts-dir>` → `<chat-dir>`.)
- [x] `stdio-pipeline-shape.md`: update orchestrator-target examples
  if they assume ts-dir. (`<ts-dir>` → `<chat-dir>`; `$UUID.json` →
  `conversation.json`; `$TITLE.md` → `chat.md`.)
- [ ] `README.md`: rewrite pipeline diagram and `Run it` block.
  Deferred — co-sequence with implementation so the `Run it` example
  reflects tested paths.
- [x] Re-read `chat-as-directory.md` "See also" section after updates;
  verify cross-references still resolve.
- [ ] `bin/validate-frontmatter` against the design.kb tree. Script
  not present in repo; skip until/unless added.

## Open Questions

- Order: do this BEFORE or AFTER the implementation (which lands the
  layout change in actual `chatfs.demo/`)? Either works; doing it
  AFTER lets the README's `Run it` example reflect tested paths.

## Success Criteria

- [ ] No design.kb file references the pre-redesign layout in a way
  that contradicts `chat-as-directory.md`.
- [ ] README pipeline diagram + `Run it` match current scripts.
- [ ] Frontmatter validation passes.

## Notes

This is purely doc maintenance; no design decisions to make. If a
contradiction surfaces that requires a decision, escalate to a session
discussion rather than guess.
