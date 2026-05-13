# Development Knowledge

Decisions, policy, and supporting facts about how this package is built and
maintained. Distinct from `design.kb/` (which captures *what* the package
does and why) — `dev.kb/` captures *how* we develop it.

## Collections

- `ts-policy.kb/` — TypeScript usage policy, supporting empirical facts,
  and known gotchas.
- `rust-port.kb/` — Transient work-area for the in-progress Rust port
  (see `rust-port.md`). Deleted at completion; durable artifacts promoted
  out before sweep.

## What belongs here

Add a new collection (`$topic.kb/`) when development practice for some
specific area accumulates enough decisions/facts/gotchas to warrant its own
maintenance scope. Add files to an existing collection when the topic already
has one.

## What does NOT belong here

- Package architecture / design rationale → `design.kb/`
- Tactical todos and task plans → `.claude/todo.md`, `.claude/todo.kb/`
- Speculative ideas → `.claude/ideas.kb/`
