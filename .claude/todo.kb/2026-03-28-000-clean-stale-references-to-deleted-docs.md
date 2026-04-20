<anthropic-skill-ownership llm-subtask />

---
required-reading:
  - docs/dev/design.kb/CLAUDE.md
---

# Clean Stale References to Deleted Docs

**Status:** Done (2026-04-20 — all 13 files updated or deleted)
**Priority:** Medium
**Complexity:** Low (mechanical find-and-update)
**Context:** Session 2026-03-28 deleted `technical-design.md`, `technical-design/`,
`development-plan.md`, `development-plan/`, and `STATUS.md`. These were the
API-direct era docs, replaced by `docs/dev/design.kb/` (layered design.kb).

## What Happened

The project's design documentation was restructured:
- `technical-design.md` + subdocs → `docs/dev/design.kb/040-design.kb/`
- `development-plan.md` + subdocs → deleted (no replacement yet; deliverables
  will emerge from implementation)
- `STATUS.md` → deleted (superseded by /llm-subtask system)
- `background.kb/` content migrated → `design/040-design.kb/` (8 files moved)

Root `CLAUDE.md` and `design-incubators/README.md` were updated. But 13
other files still reference the deleted docs.

## Files Fixed (2026-04-20)

**Top-level project docs:**
- [x] `TODO.md` — deleted (432 lines of stale M0-DOCS planning; superseded by `.claude/todo.md`)
- [x] `HACKING.md` — rewrote project structure for `packages/` layout, pointed to `design.kb/`
- [x] `README.md` — rewrote for FUSE+Playwright model, pointed to `design.kb/`

**Dev docs:**
- [x] `docs/dev/design-rationale.md` — pointed to `design.kb/`
- [x] `docs/dev/README.md` — pointed to `design.kb/`, listed `.kb/` siblings
- [x] `docs/README.md` — removed STATUS.md references, pointed to `design.kb/`
- [x] `docs/dev/design-rationale/README.md` — `docs/dev/design/` → `docs/dev/design.kb/`

**Incubators:**
- [x] `docs/dev/design-incubators/multi-domain-support/README.md`
- [x] `docs/dev/design-incubators/multi-domain-support/CLAUDE.md`

**Code READMEs:**
- [x] `lib/chatfs/README.md`
- [x] `lib/chatfs/layer/vfs/README.md`
- [x] `lib/chatfs/layer/cli/README.md`

(`lib/chatfs/` retained — dead shell, but kept until a confirmed Python
replacement lands. Real Python code now lives in `packages/bukzor.chatgpt-export/`.)

**Stale todos:**
- [x] `.claude/todo.kb/2026-01-02-000-harmonize-with-llm-skills.md`
- [x] `.claude/todo.kb/2026-01-02-002-apply-skill-conventions-post-evolution.md`
- [x] Self (this file) — internal `design/` → `design.kb/` references

## How to Fix

For each file:
1. Read it
2. Replace `technical-design.md` / `technical-design/*.md` references with
   appropriate `docs/dev/design.kb/` paths (usually `040-design.kb/`)
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
