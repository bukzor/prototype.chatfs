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

Use: `llm-collab-devlog --title "Entry title" -C ../`
