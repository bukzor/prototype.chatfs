<anthropic-skill-ownership llm-subtask />

---
required-reading:
  - ~/.claude/skills/llm-collab/SKILL.md
  - ~/.claude/skills/llm-collab/skeleton/CLAUDE.md
suggested-reading:
  - ~/.claude/skills/llm-collab/references.kb/file-types.kb/development-plan.md
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
- STATUS.md should be retired (obsolete pattern)
- Consider `design.kb/` pattern for design docs

## Current Situation

Waiting on:
1. llm.kb: `.d → .kb` rename complete
2. llm-collab: skeleton updated with `milestones.kb/` and `design.kb/` patterns

## Proposed Solution

1. Retire STATUS.md (absorb into devlog entry)
2. Refactor `docs/dev/development-plan/` → `docs/dev/milestones.kb/`
3. Evaluate if monolithic design-rationale.md/technical-design.md need `design.kb/` treatment

## Implementation Steps

- [ ] Wait for skill evolution to complete
- [ ] Create devlog entry absorbing STATUS.md content
- [ ] Delete STATUS.md
- [ ] Rename `development-plan/` → `milestones.kb/`
- [ ] Add `milestones.kb/CLAUDE.md` per llm.kb pattern
- [ ] Update all references to old paths
- [ ] Evaluate design.kb/ need (may not be necessary)

## Success Criteria

- [ ] STATUS.md retired
- [ ] `docs/dev/milestones.kb/` exists with proper CLAUDE.md
- [ ] All internal links updated
- [ ] `llm-collab-session-start` pattern works in this repo
