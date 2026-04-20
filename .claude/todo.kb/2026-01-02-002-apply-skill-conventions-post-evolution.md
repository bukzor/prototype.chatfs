<anthropic-skill-ownership llm-subtask />

---
required-reading:
  - ~/.claude/skills/llm-collab/SKILL.md
  - ~/.claude/skills/llm-collab/skeleton/CLAUDE.md
suggested-reading:
  - ~/.claude/skills/llm-collab/references.kb/file-types.kb/
  - ~/.claude/skills/llm-collab/references.kb/file-types.kb/devlog.md
parent: 2026-01-02-000-harmonize-with-llm-skills.md
depends-on:
  - ~/.claude/skills/llm.kb/.claude/todo.kb/2026-01-02-000-complete-d-to-kb-rename.md
  - ~/.claude/skills/llm-collab/.claude/todo.kb/2025-12-11-000-update-skeleton-to-match-docsdev-pattern-from-git-partial.md
---

# Apply Skill Conventions Post-Evolution

**Priority:** Medium
**Complexity:** Medium
**Context:** Part of harmonize-with-llm-skills effort, runs after skill evolution complete

## Problem Statement

After skill evolution completes, apply modern conventions to prototype.chatfs:
- `development-plan/` should become `milestones.kb/` (per llm-collab pattern)
- STATUS.md already deleted (2026-03-28)
- Consider `design.kb/` pattern for design docs

## Current Situation

- `design.kb/` pattern delivered via the `llm-design-kb` skill (extracted 2026-03-24) — unblocks layered design here (already applied under `docs/dev/design.kb/`).
- `milestones.kb/` pattern — still not defined in llm-collab; tracked upstream under `2025-12-11-000-update-skeleton-...md`.
- llm-kb `.d → .kb` rename — still in progress upstream but does not block chatfs.

## Proposed Solution

1. Retire STATUS.md — done 2026-03-28
2. Refactor development-plan/ — done 2026-03-28 (deleted, superseded by design.kb/)
3. Evaluate design.kb/ treatment — done 2026-03-28 (`docs/dev/design.kb/` created)
4. `docs/dev/milestones.kb/` — deferred (see Implementation Steps)

## Implementation Steps

- [x] Create devlog entry absorbing STATUS.md content (STATUS.md deleted without migration — content was stale)
- [x] Delete STATUS.md (done 2026-03-28)
- [x] Rename development-plan/ (deleted 2026-03-28, superseded by design.kb/)
- [x] design.kb/ created (done 2026-03-28: `docs/dev/design.kb/`)
- [x] Update all references to old paths (done 2026-04-20)
- [x] Evaluate design.kb/ need (done — created with full layered structure)
- [ ] Create `docs/dev/milestones.kb/` — **deferred** (double-blocked: no milestone content yet, skills-repo pattern not defined)

## Success Criteria

- [x] STATUS.md retired (deleted)
- [x] All internal links updated (done 2026-04-20)
- [x] CLAUDE.md + `.claude/todo.md` + devlog pattern works for fresh-agent orientation (verified 2026-04-20)
- [ ] `docs/dev/milestones.kb/` exists with proper CLAUDE.md — deferred

## Notes

The `milestones.kb/` gap is tracked in the parent
(`2026-01-02-000-harmonize-with-llm-skills.md`) under Deferred. Revisit
when the first implementation milestone is concrete enough to structure.
