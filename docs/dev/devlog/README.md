# Devlog

Chronological record of development sessions.

Each entry is a file named `YYYY-MM-DD-NNN-short-title.md`. Entries
capture session focus, decisions made, and what to pick up next.

Use `ls docs/dev/devlog/` for the current index — no hand-curated list
here.

Subproject-scoped sessions log with their subproject, not here — e.g.
`packages/har-browse/docs/dev/devlog/`,
`docs/dev/design-incubators/chatfs-cli-mockup/devlog/`. This directory
holds project-wide sessions and those predating a subproject's own
devlog.

## What belongs in a devlog entry

- **Focus** — what the session was about
- **What happened** — substantive work done
- **Decisions** — non-obvious calls and their rationale (durable
  architectural decisions may also warrant an ADR; see `Skill(llm-collab)`)
- **Next session** — where to pick up

## What does NOT belong

- Mechanical task lists — those go in `.claude/todo.kb/`
- Status snapshots — use `.claude/todo.md`
- Deep design rationale — that goes in `docs/dev/design.kb/` (inline with the
  relevant entry)
