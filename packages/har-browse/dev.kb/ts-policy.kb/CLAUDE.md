# TypeScript Policy

Decisions and supporting facts about how TypeScript is used in this package.

## What belongs here

- **Decisions** (`decision-*.md`) — normative policy choices about TS usage
  (what to enable, what to ban, how to enforce).
- **Facts** (`fact-*.md`) — empirically-verified properties of Node, tsserver,
  or TS tooling that decisions rest on.
- **Gotchas** (`gotcha-*.md`) — specific footguns or surprising behaviors
  worth flagging to future authors.

## What does NOT belong here

- General TypeScript tutorials or upstream documentation (link out instead).
- One-off migration tasks or todos → `.claude/todo.md`.
- Design knowledge about the package's architecture → `design.kb/`.

## When to add a file

- A new **decision** when making a normative call about TS that future authors
  should follow (or revisit explicitly).
- A new **fact** when an empirical finding informed or could inform such a
  decision.
- A new **gotcha** when a specific failure mode is non-obvious and worth
  pre-warning.

When verifying an existing fact yields a different result (Node version
update, TS version update, etc.), update the file in place and note the
verifying environment.
