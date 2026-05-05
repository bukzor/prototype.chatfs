---
anthropic-skill-ownership: llm-subtask
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

- [ ] Enumerate candidate files with sizes and section counts:
      `find ... -name '*.md' -not -name 'CLAUDE.md' | xargs wc -l`.
- [ ] Per-file read + signal evaluation; record decisions in this
      file as a checklist.
- [ ] Execute promotions (one per session if numerous; do not batch
      large factorizations).
- [ ] After each promotion, update sibling entries that reference the
      promoted entry's sections.
- [ ] Run `bin/validate-frontmatter` after each batch.

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
