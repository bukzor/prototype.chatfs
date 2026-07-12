--- # workaround: anthropics/claude-code#13003
requires:
    - Skill(llm-collab)
---

# Development Log

Chronological record of development sessions scoped to this incubator
(`../`). See `../../devlog/` for the project-wide log.

## What Belongs

Devlogs capture what diffs can't — reasoning, principles, conventions:
- Decisions and their rationale (especially rejected alternatives)
- Conventions established and principles discovered
- Tradeoffs that shaped the approach

## What Does NOT Belong

- Lists of completed items (that's `git log`)
- Active task tracking (that's `../.claude/todo.md`)
- Architectural decisions (→ `docs/dev/adr/`)
- Code documentation (→ inline comments, docstrings)

## Creating Entries

`llm-collab-devlog` hardcodes a `docs/dev/devlog/` path and cannot target
this bare `devlog/` (verified 2026-07-12 — `-C ../` from here still looks
for `docs/dev/devlog/` under the incubator root, which doesn't exist).
Create entries by hand: `YYYY-MM-DD-NNN-slug.md`, numbering restarts at
`000` per date, following the existing entries' structure (skeleton:
`~/.claude/skills/llm-collab/skeleton/docs/dev/devlog/YYYY-MM-DD-000-example-entry.md`).
