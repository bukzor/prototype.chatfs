<anthropic-skill-ownership llm-subtask />

---
required-reading:
  - ~/.claude/skills/llm-kb/SKILL.md
  - ~/.claude/skills/llm-collab/SKILL.md
  - ~/.claude/skills/llm-subtask/SKILL.md
  - ~/.claude/skills/llm-design-kb/SKILL.md
suggested-reading:
  - ~/.claude/skills/llm-kb/docs/adr/2025-12-03-000-pivot-from-d-to-kb-naming-convention.md
  - ~/.claude/skills/llm-collab/.claude/todo.kb/2025-12-11-000-update-skeleton-to-match-docsdev-pattern-from-git-partial.md
---

# Harmonize prototype.chatfs with llm-* Skill Conventions

**Priority:** Medium
**Complexity:** Medium
**Context:** Multi-repo coordination between prototype.chatfs and the skills monorepo

## Problem Statement

prototype.chatfs predates the llm-* skills and uses outdated conventions:

- CLAUDE.md missing skill-dependency frontmatter
- Root `TODO.md` instead of `.claude/todo.md` + `.claude/todo.kb/`
- `STATUS.md` (obsolete pattern, replaced by devlog + todo system)
- Design docs outside the `design.kb/` layered pattern
- Skills themselves still evolving (`.d → .kb` partial in llm-kb;
  `milestones.kb/` pattern not yet in the llm-collab skeleton)

## Current Situation

### Skills monorepo at `~/.claude/skills/` (symlinks to `~/repo/github.com/bukzor/bukzor-agent-skills/`)

| Skill           | Purpose                                  | Status                                                                                  |
| --------------- | ---------------------------------------- | --------------------------------------------------------------------------------------- |
| llm-kb          | Structured `.kb/` knowledge bases        | Skill renamed `llm.kb → llm-kb` (2026-03-02); `complete-example/` internals still `.d/` |
| llm-collab      | Multi-session coordination               | `docs/dev/` restructure done; no `milestones.kb/` pattern defined yet                   |
| llm-design-kb   | Layered design knowledge                 | Extracted from llm-collab (2026-03-24); in use here                                     |
| llm-subtask     | Four-tier task management                | In use here                                                                             |

### prototype.chatfs

- `.claude/todo.md` + `.claude/todo.kb/` in place; TODO.md deleted (2026-04-20)
- STATUS.md deleted (2026-03-28)
- CLAUDE.md has `depends:` frontmatter — but still references `skills/llm.kb` (old name) and omits `skills/llm-design-kb`
- `docs/dev/design.kb/` layered design in place
- `docs/dev/design-rationale.md` content is stale (describes the superseded M1-M4 architecture) — see subtask `2026-04-20-001`
- `docs/dev/milestones.kb/` absent — deferred (no milestone content yet; skills pattern not defined either)
- `lib/chatfs/` retained as dead shell pending review — see subtask `2026-04-20-000`

## Subtasks

### Phase 1 — Skills repo (upstream)

- [ ] [llm-kb: Complete `.d → .kb` rename](~/.claude/skills/llm-kb/.claude/todo.kb/2026-01-02-000-complete-d-to-kb-rename.md) — does not block chatfs (we do not use `complete-example/`)
- [ ] [llm-collab: Define `milestones.kb/` pattern in skeleton](~/.claude/skills/llm-collab/.claude/todo.kb/2025-12-11-000-update-skeleton-to-match-docsdev-pattern-from-git-partial.md) — blocks creating `docs/dev/milestones.kb/` here, but we have no milestone content to put there yet
- [x] llm-collab: `docs/dev/` skeleton restructure — done via `2026-02-09-000-design-kb-pattern-for-living-design-docs.md` in llm-collab
- [x] llm-design-kb: extracted as its own skill — done 2026-03-24

### Phase 2 — prototype.chatfs

- [x] [Migrate TODO.md to subtask format](2026-01-02-001-migrate-todo-to-subtask-format.md)
- [x] [Clean stale references to deleted docs](2026-03-28-000-clean-stale-references-to-deleted-docs.md)
- [~] [Apply skill conventions post-evolution](2026-01-02-002-apply-skill-conventions-post-evolution.md) — STATUS.md / development-plan / design.kb work done; only `milestones.kb/` remains and is deferred
- [ ] [Reconcile design-rationale.md with current architecture](2026-04-20-001-reconcile-design-rationale-with-current-architecture.md)
- [ ] [Review lib/chatfs/ for salvageable ideas](2026-04-20-000-review-lib-chatfs-for-integration.md)
- [ ] Fix CLAUDE.md `depends:` — rename `skills/llm.kb` → `skills/llm-kb`, add `skills/llm-design-kb`

### Tactical

- [x] Add CLAUDE.md frontmatter
- [x] Create devlog entry for 2026-01-02 (`docs/dev/devlog/2026-01-02-000-harmonization-planning-session.md`)

## Success Criteria

- [x] prototype.chatfs CLAUDE.md has `depends:` frontmatter (pending minor name fix)
- [x] prototype.chatfs uses `.claude/todo.md` + `.claude/todo.kb/`
- [x] STATUS.md retired (deleted 2026-03-28)
- [x] `docs/dev/design.kb/` layered design in place
- [x] Fresh agent can orient via CLAUDE.md + `.claude/todo.md` + devlog (verified 2026-04-20 via /session-start)
- [ ] `docs/dev/design-rationale.md` describes the current architecture
- [ ] `lib/chatfs/` reviewed (kept or removed with rationale)
- [ ] CLAUDE.md `depends:` uses current skill names and includes `llm-design-kb`
- [ ] (Upstream) llm-kb `complete-example/` uses `.kb/` consistently
- [ ] (Upstream) llm-collab skeleton defines `milestones.kb/` pattern

## How to Execute

### Chatfs-local remaining work (actionable now, any order)

1. `2026-04-20-001-reconcile-design-rationale-with-current-architecture.md` — medium priority, medium effort
2. `2026-04-20-000-review-lib-chatfs-for-integration.md` — low priority, small effort
3. CLAUDE.md `depends:` fix — tiny, do alongside either of the above

### Upstream work (when motivated; does not block chatfs today)

1. `~/.claude/skills/llm-kb/.claude/todo.kb/2026-01-02-000-complete-d-to-kb-rename.md`
2. `~/.claude/skills/llm-collab/.claude/todo.kb/2025-12-11-000-update-skeleton-...md` — specifically, define the `milestones.kb/` pattern

### Deferred

`docs/dev/milestones.kb/` creation — double-blocked:
- No milestone content yet (project still in design phase, pre-implementation)
- No skills-repo pattern to follow

Revisit when the first implementation milestone is concrete enough to structure.

## Notes

**Cross-repo coordination:** Skills repo subtasks include `related-effort:`
links back to this parent for context.

**Cross-references:**
- llm-kb ADR on `.d → .kb`: `~/.claude/skills/llm-kb/docs/adr/2025-12-03-000-pivot-from-d-to-kb-naming-convention.md` (Status: Proposed; promote to Accepted after rename lands)
- llm-collab skeleton TODO: `~/.claude/skills/llm-collab/.claude/todo.kb/2025-12-11-000-update-skeleton-to-match-docsdev-pattern-from-git-partial.md`
