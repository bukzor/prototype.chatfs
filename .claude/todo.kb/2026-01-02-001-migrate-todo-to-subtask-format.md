<anthropic-skill-ownership llm-subtask />

---
required-reading:
  - ~/.claude/skills/llm-subtask/SKILL.md
  - $PWD/TODO.md
suggested-reading:
  - ~/.claude/skills/llm-subtask/references/four-tier-system.md
parent: 2026-01-02-000-harmonize-with-llm-skills.md
---

# Migrate TODO.md to Subtask Format

**Priority:** High
**Complexity:** Low
**Context:** Part of harmonize-with-llm-skills effort

## Problem Statement

prototype.chatfs uses a root `TODO.md` (432 lines) instead of the llm-subtask pattern:
- `.claude/todo.md` for tactical items (one-liners, cross-session checkboxes)
- `.claude/todo.kb/` for strategic items (planning docs, multi-step breakdowns)

## Current Situation

`TODO.md` contains M0-DOCS phase breakdown:
- Phase 1: Validate Level 1 (mostly complete)
- Phase 1.25: Architecture Evolution (complete)
- Phase 1.4: Integrate Open Questions (complete)
- Phase 1.5: Terminology Cleanup (complete)
- Phase 2: Breadth-First Validation (in progress, many unchecked items)
- Phase 3: Mark Deferred Details (not started)
- Phase 4: Validate Against Success Criteria (not started)

Much of this is 2 months stale and may no longer be relevant.

## Proposed Solution

1. Create `.claude/todo.md` with tactical items
2. Extract any still-relevant strategic breakdowns to `.claude/todo.kb/`
3. Delete root `TODO.md` (git preserves history)

## Implementation Steps

- [ ] Read TODO.md, identify still-relevant items
- [ ] Create `.claude/todo.md` with tactical items
- [ ] Create strategic todo.kb files for multi-phase work (if any)
- [ ] Verify no critical context lost
- [ ] `git rm TODO.md`

## Success Criteria

- [ ] `.claude/todo.md` exists with tactical items
- [ ] Root `TODO.md` deleted
- [ ] `subtask load` shows current work correctly
