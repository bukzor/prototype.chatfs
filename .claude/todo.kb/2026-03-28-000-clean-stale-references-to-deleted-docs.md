<anthropic-skill-ownership llm-subtask />

---
required-reading:
  - docs/dev/design/CLAUDE.md
---

# Clean Stale References to Deleted Docs

**Priority:** Medium
**Complexity:** Low (mechanical find-and-update)
**Context:** Session 2026-03-28 deleted `technical-design.md`, `technical-design/`,
`development-plan.md`, `development-plan/`, and `STATUS.md`. These were the
API-direct era docs, replaced by `docs/dev/design/` (layered design.kb).

## What Happened

The project's design documentation was restructured:
- `technical-design.md` + subdocs → `docs/dev/design/040-design.kb/`
- `development-plan.md` + subdocs → deleted (no replacement yet; deliverables
  will emerge from implementation)
- `STATUS.md` → deleted (superseded by /llm-subtask system)
- `background.kb/` content migrated → `design/040-design.kb/` (8 files moved)

Root `CLAUDE.md` and `design-incubators/README.md` were updated. But 13
other files still reference the deleted docs.

## Files to Fix

**Top-level project docs:**
- `TODO.md` — references STATUS.md
- `HACKING.md` — references STATUS.md, technical-design
- `README.md` — references STATUS.md, technical-design

**Dev docs:**
- `docs/dev/design-rationale.md` — references technical-design.md, development-plan.md
- `docs/dev/README.md` — references technical-design.md, development-plan.md
- `docs/README.md` — references STATUS.md

**Incubators:**
- `docs/dev/design-incubators/multi-domain-support/README.md` — references technical-design
- `docs/dev/design-incubators/multi-domain-support/CLAUDE.md` — references technical-design

**Code READMEs:**
- `lib/chatfs/README.md` — references technical-design
- `lib/chatfs/layer/vfs/README.md` — references technical-design
- `lib/chatfs/layer/cli/README.md` — references technical-design

**Stale todos:**
- `.claude/todo.kb/2026-01-02-000-harmonize-with-llm-skills.md` — references STATUS.md
- `.claude/todo.kb/2026-01-02-002-apply-skill-conventions-post-evolution.md` — references technical-design, development-plan

## How to Fix

For each file:
1. Read it
2. Replace `technical-design.md` / `technical-design/*.md` references with
   appropriate `docs/dev/design/` paths (usually `040-design.kb/`)
3. Replace `development-plan.md` references — either point to design.kb
   deliverables (if they exist by then) or remove the reference
4. Remove `STATUS.md` references entirely
5. Check whether the file is otherwise stale enough to warrant deletion
   (especially the code READMEs and old todo items)

**Do NOT modify devlogs** — they are historical records.

## Search command

```bash
grep -rl 'technical-design\.\|development-plan\.\|STATUS\.md' \
  --include='*.md' \
  docs/ lib/ README.md HACKING.md TODO.md .claude/todo.kb/
```
