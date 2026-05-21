---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 2.0
    rationale: |
      Enumeration + per-candidate evaluation done; decisions
      recorded. Residual: execute promotions on 3 files + update
      sibling cross-references. ~2h mechanical migration.
    confidence: tentative
  benefit-2w:
    "@value": 0.5
    rationale: |
      Closes a tech-debt loop. The promoted `.kb/` collections give
      better organization for future entries. Modest, ~$50 of
      "structural cleanliness."
    confidence: tentative
  cost-of-delay-2w:
    "@value": 0.0
    rationale: |
      Self-classified "not blocking." Promotion-signal items grow
      slowly; 2w delay only adds marginal scope.
    confidence: tentative
---

# Scan design.kb for promotion signals

**Priority:** Medium (technical-debt cleanup; not blocking)
**Complexity:** Medium (whole-tree scan + per-candidate decision + execute)
**Context:**
- `Skill(llm-kb)` — promotion signals section
- `Skill(llm-design-kb)` — promote listing entries step in maintenance
- Recent precedent: `chat-as-directory.md` → `chat-as-directory.kb/`

## Problem Statement

The chatfs-mockup-chatgpt design.kb has accreted over several sessions.
Per `Skill(llm-kb)`, single `.md` entries should be promoted to `.kb/`
collections when they show "promotion signals":

- Plural filename (e.g. `patterns.md`, `alternatives.md`)
- Parallel sections of the same type (multiple `##` describing items
  of the same kind)
- Listing-heavy content (most of the file is a numbered list, table,
  or parallel enumeration)
- Per-item growth pressure (each item wants its own paragraph,
  frontmatter, lifecycle, or exceeds ~50 tokens of explanation)

Without periodic scans, entries that should have become collections
linger as long monolithic files. The recent `chat-as-directory.md`
factorization is one example; others likely exist.

## Current Situation

Entries to scan, in scope of relevance:

- `docs/dev/design-incubators/chatfs-mockup-chatgpt/design.kb/040-design.kb/`
  — 6 entries plus the new `chat-as-directory.kb/` sub-collection.
- `docs/dev/design.kb/040-design.kb/` — project-level design entries,
  some already promoted (`capture-pattern.kb/`, `user-interface.kb/`).
- `docs/dev/design.kb/`'s other layers (mission, goals, requirements,
  future-work) — likely smaller, lower priority but worth a pass.
- `docs/dev/background.kb/`, `docs/dev/technical-policy.kb/` — out of
  scope for this todo (different conventions).

## Proposed Solution

For each candidate file:

1. Read it fully.
2. Check against the four promotion signals.
3. Decide: promote (split to sub-kb), absorb (consolidate with another
   entry), or leave (signals not yet present).
4. If promote: factor per the chat-as-directory precedent — slim main
   entry retains the headline; sub-kb gets per-aspect files; CLAUDE.md
   in the sub-kb scopes "what belongs / does not / when to add."

## Implementation Steps

- [x] Enumerate candidate files with sizes and section counts.
- [x] Per-file read + signal evaluation; record decisions below.
- [ ] Execute promotions (deferred — see Decisions).
- [ ] After each promotion, update sibling entries.
- [x] Run `llm.kb-validate` against both design.kb trees. Project-level
      clean (38 files, 0 errors). Incubator was missing
      `040-design.jsonschema.yaml`; fixed by symlinking the parent
      schema (`design.kb/040-design.jsonschema.yaml -> ../../../design.kb/040-design.jsonschema.yaml`).
      Now clean (11 files, 0 errors).

## Decisions

**Strong promote (1):**

- `chatfs-mockup-chatgpt/.../cli-command-shape.md` — listing-heavy
  (hierarchy block, script-name table), parallel sections (noun /
  verb / sub-noun rationale), per-command growth pressure as the CLI
  surface widens. Already covered by sibling todo
  `2026-05-05-002-plan-and-create-noun-verb-model-sub-kb.md`. No
  duplicate work here.

**Borderline — flag for future (3):**

- `design.kb/040-design.kb/jsonl-interchange.md` (43 lines).
  "Alternatives considered" has 4 sub-headings of "Why not X" form.
  Per `Skill(llm-design-kb)` Alternatives-Considered guidance, inline
  works for 1-3; promote to a sub-kb when alternatives grow per-item
  content. Currently each alternative is 2-3 sentences — not yet.
- `design.kb/040-design.kb/sync-control-plane.md` (41 lines). Two
  parallel listings: "Prior art surveyed" (5 items) and "Why not
  trigger on read()" (5 items). Items are one-liners; growth pressure
  not yet present.
- `design.kb/040-design.kb/stack-split.md` (33 lines). Two "Why not"
  sections (rejected alternatives). Could be promoted alongside any
  alternatives sub-kb pattern that emerges.

**No promote (current scan):**

- `chatfs-mockup-chatgpt/.../deterministic-regeneration.md`,
  `stdio-pipeline-shape.md`, `no-partial-synthesis.md`,
  `browse-incidental-capture.md` — sections are different concerns,
  not parallel of the same type.
- `design.kb/040-design.kb/canonical-conversation-graph.md`,
  `work-enqueueing-model.md`, `black-box-decomposition.md`,
  `rotate-90-degrees-layout.md` — small enumerations tightly coupled
  to surrounding prose; no growth pressure.
- `design.kb/{010,020,030,070}-*.kb/*` — all entries 11-19 lines;
  far below promotion-pressure thresholds.

**Already promoted (3):**

- `chatfs-mockup-chatgpt/.../chat-as-directory.md` →
  `chat-as-directory.kb/` (this session).
- `design.kb/040-design.kb/capture-pattern.md` →
  `capture-pattern.kb/` (prior).
- `design.kb/040-design.kb/user-interface.md` →
  `user-interface.kb/` (prior).

## Cadence note

This scan completed on 2026-05-05. Next scan recommended:
- After landing the noun-verb sub-kb (todo 002), re-evaluate the
  three borderline entries.
- Otherwise, after every ~5 sessions with substantive design work,
  or when any single design entry crosses ~80 lines.

## Open Questions

- Project-level `docs/dev/design.kb/` in scope, or only the incubator?
  Probably both, with project-level lower priority.
- Cross-cutting "extraction" (a section that generalizes beyond its
  host, like identity-scoped cleanup moving from chat-as-directory to
  deterministic-regeneration) — is that the same operation as
  promotion, or a separate move worth tracking? Note if a pattern
  emerges.

## Success Criteria

- [ ] Every entry in scope has been evaluated against the four
      signals.
- [ ] Decisions (promote / absorb / leave) recorded for each.
- [ ] Promotions executed; sibling cross-references updated.
- [ ] No remaining entries with obvious unaddressed signals (plural
      filename, listing-heavy, etc.).

## Notes

Periodic maintenance pass, not one-shot. Capture a recurring cadence
in the post-mortem (every N sessions? after every major design
chapter?) so future sessions know when to repeat.
