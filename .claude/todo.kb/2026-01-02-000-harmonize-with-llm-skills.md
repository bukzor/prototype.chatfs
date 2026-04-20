<anthropic-skill-ownership llm-subtask />

---
required-reading:
  - ~/.claude/skills/llm.kb/SKILL.md
  - ~/.claude/skills/llm-collab/SKILL.md
  - ~/.claude/skills/llm-subtask/SKILL.md
suggested-reading:
  - ~/.claude/skills/llm.kb/references/pattern-guide.md
  - ~/.claude/skills/llm.kb/docs/adr/2025-12-03-000-pivot-from-d-to-kb-naming-convention.md
  - ~/.claude/skills/llm-collab/.claude/todo.kb/2025-12-11-000-update-skeleton-to-match-docsdev-pattern-from-git-partial.md
---

# Harmonize prototype.chatfs with llm-* Skill Conventions

**Priority:** High
**Complexity:** Medium
**Context:** Session 2026-01-02, multi-repo coordination

## Problem Statement

prototype.chatfs predates the llm-* skills and uses outdated conventions:
- No CLAUDE.md frontmatter (missing skill dependencies)
- Uses root `TODO.md` instead of `.claude/todo.md` + `.claude/todo.kb/`
- Used `STATUS.md` (now deleted, replaced by devlog + todo system)
- Skills themselves have incomplete evolution (`.d → .kb` partial)

## Current Situation

**Skills (monorepo at `~/.claude/skills/`):**

| Skill | Purpose | Status |
|-------|---------|--------|
| llm.kb | Structured `.kb/` knowledge bases | `.d → .kb` rename partial (todo.kb done, complete-example still .d) |
| llm-collab | Multi-session coordination | Skeleton TODO open for milestones.kb/design.kb patterns |
| llm-subtask | Four-tier task management | Ready to use |

**prototype.chatfs gaps:**
- Last meaningful work: 2025-11-05 (devlog)
- STATUS.md: deleted (was last updated 2025-11-02)
- TODO.md: 432 lines of M0-DOCS phase breakdown (stale)

**Key insight:** Can't fully harmonize prototype.chatfs until skill evolution completes.

## Proposed Solution

Two-phase approach:
1. **Complete skill evolution** - Finish `.d → .kb` migration, update llm-collab skeleton
2. **Apply to prototype.chatfs** - Add frontmatter, migrate TODO.md (STATUS.md already deleted)

## Subtasks

### Phase 1: Skill Evolution

- [ ] [llm.kb: Complete .d → .kb rename](~/.claude/skills/llm.kb/.claude/todo.kb/2026-01-02-000-complete-d-to-kb-rename.md)
- [ ] [llm-collab: Update skeleton](~/.claude/skills/llm-collab/.claude/todo.kb/2025-12-11-000-update-skeleton-to-match-docsdev-pattern-from-git-partial.md) (existing TODO)

### Phase 2: prototype.chatfs Harmonization

- [ ] [Migrate TODO.md to subtask format](2026-01-02-001-migrate-todo-to-subtask-format.md)
- [ ] [Apply skill conventions post-evolution](2026-01-02-002-apply-skill-conventions-post-evolution.md)

### Tactical (in .claude/todo.md)

- [ ] Add CLAUDE.md frontmatter
- [ ] Create devlog entry for 2026-01-02

## Success Criteria

- [ ] All skills use `.kb/` naming consistently
- [ ] llm-collab skeleton uses `milestones.kb/` and `design.kb/` patterns
- [ ] prototype.chatfs CLAUDE.md has `depends:` frontmatter
- [ ] prototype.chatfs uses `.claude/todo.md` + `.claude/todo.kb/`
- [x] STATUS.md retired (deleted 2026-03-28)
- [ ] Fresh agent can orient via `llm-collab-session-start` pattern

## How to Execute

This task spans two git repositories. Execute phases in separate sessions.

### Phase 1: Skills Repo

**Location:** `~/.claude/skills/`

```bash
cd ~/.claude/skills && claude
```

Run `/session-start`. If the skill evolution tasks aren't surfaced, the session should:
1. Create `~/.claude/skills/.claude/todo.kb/` with a root-level task
2. Reference the existing skill-specific subtasks:
   - `llm.kb/.claude/todo.kb/2026-01-02-000-complete-d-to-kb-rename.md`
   - `llm-collab/.claude/todo.kb/2025-12-11-000-update-skeleton-...md`

**Recommended order:** llm-collab skeleton first (makes llm.kb rename simpler).

**Verification (run from any directory):**
```bash
# llm.kb: No .d/ directories in complete-example
ls -d ~/.claude/skills/llm.kb/complete-example/*.d/ 2>/dev/null && echo "INCOMPLETE" || echo "DONE"

# llm.kb: ADR status updated to Accepted
grep -A1 "^## Status" ~/.claude/skills/llm.kb/docs/adr/2025-12-03-000-*.md
```

### Phase 2: prototype.chatfs

**Location:** This repo
**Precondition:** Phase 1 verification passes

Run `/session-start` here. Execute subtasks:
1. `2026-01-02-001-migrate-todo-to-subtask-format.md`
2. `2026-01-02-002-apply-skill-conventions-post-evolution.md`

### Parallel Work

`2026-01-02-001-migrate-todo-to-subtask-format.md` (TODO.md migration) can proceed in parallel with Phase 1 — no dependency on skill evolution.

## Notes

**Cross-repo coordination:** Skills repo subtasks have `related-effort` links back to this parent task for context on why the work matters.

**Cross-references:**
- llm.kb ADR on `.d → .kb`: `docs/adr/2025-12-03-000-pivot-from-d-to-kb-naming-convention.md`
- llm-collab TODO on skeleton: `.claude/todo.kb/2025-12-11-000-update-skeleton-...md`
