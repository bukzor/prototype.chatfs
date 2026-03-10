# 2026-01-02: Harmonization Planning Session

## Focus

Bring prototype.chatfs into alignment with llm-* skill conventions after 2-month hiatus.

## What Happened

**Context gathering:**
- Analyzed llm.kb, llm-collab, llm-subtask skills (monorepo at `~/.claude/skills/`)
- Discovered prototype.chatfs predates all three skills
- Identified partial `.d → .kb` migration in skills (ADR 2025-12-03-000, status "Proposed")
- Found open TODO in llm-collab for skeleton evolution to `milestones.kb/` and `design.kb/`

**Key findings:**
- STATUS.md is obsolete pattern (replaced by devlog + todo system)
- Root TODO.md should migrate to `.claude/todo.md` + `.claude/todo.kb/`
- CLAUDE.md needs frontmatter declaring skill dependencies
- Skill evolution must complete before full harmonization

**Created:**
- `.claude/todo.md` - Tactical task list
- `.claude/todo.kb/2026-01-02-000-harmonize-with-llm-skills.md` - Top-level strategic plan
- `.claude/todo.kb/2026-01-02-001-migrate-todo-to-subtask-format.md` - TODO.md migration
- `.claude/todo.kb/2026-01-02-002-apply-skill-conventions-post-evolution.md` - Post-evolution work
- `~/.claude/skills/llm.kb/.claude/todo.kb/2026-01-02-000-complete-d-to-kb-rename.md` - Skill evolution task
- `~/.claude/skills/.claude/todo.kb/2026-01-02-000-skill-evolution-for-chatfs-harmonization.md` - Root-level task for skills `/session-start`
- Added frontmatter to CLAUDE.md with skill dependencies
- Added "How to Execute" section to parent task with cross-repo workflow

## Decisions

**Two-phase approach adopted:**
1. Complete skill evolution first (`.d → .kb` rename, skeleton updates)
2. Then apply modern conventions to prototype.chatfs

**Rationale:** Can't apply patterns that aren't fully defined yet.

## Next Session

**Skills repo ready for Phase 1:**
```bash
cd ~/.claude/skills && claude
```
Run `/session-start` — root-level task will surface.

**Parallel option:** TODO.md migration can proceed here independently.

See `.claude/todo.kb/2026-01-02-000-harmonize-with-llm-skills.md` "How to Execute" for full workflow.
