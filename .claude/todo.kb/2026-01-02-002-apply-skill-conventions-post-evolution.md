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

Waiting on:
1. llm.kb: `.d → .kb` rename complete
2. llm-collab: skeleton updated with `milestones.kb/` and `design.kb/` patterns

## Proposed Solution

1. ~~Retire STATUS.md~~ (deleted 2026-03-28)
2. ~~Refactor development-plan/~~ (deleted 2026-03-28, superseded by design.kb/)
3. ~~Evaluate design.kb/ treatment~~ (done: `docs/dev/design.kb/` created; `technical-design.md` deleted)

## Implementation Steps

- [ ] Wait for skill evolution to complete
- [x] ~~Create devlog entry absorbing STATUS.md content~~ (STATUS.md deleted without migration — content was stale)
- [x] ~~Delete STATUS.md~~ (done 2026-03-28)
- [x] ~~Rename development-plan/~~ (deleted 2026-03-28, superseded by design.kb/)
- [x] ~~design.kb/ created~~ (done 2026-03-28: `docs/dev/design.kb/`)
- [ ] Update all references to old paths (in progress)
- [x] ~~Evaluate design.kb/ need~~ (done — created with full layered structure)

## Success Criteria

- [x] STATUS.md retired (deleted)
- [ ] `docs/dev/milestones.kb/` exists with proper CLAUDE.md
- [ ] All internal links updated
- [ ] `llm-collab-session-start` pattern works in this repo
