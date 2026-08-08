# 2026-08-08 — chatfs-cli Graduates from the Incubator, with Its design.kb

**Status:** Accepted
**Scope:** `packages/chatfs-cli/`, `docs/dev/design.kb/040-design.kb/`,
`docs/dev/design-incubators/chatfs-cli-mockup/`

## Context

The chatfs-cli-mockup incubator carried the working pipeline — capture →
splat → render, all three providers — plus the design.kb that grew
alongside it. Its README's standing contract: "Lessons settled here get
folded back to project-level design.kb."

The code graduated 2026-08-07 (umbrella children 000/001): module-shape
refactor, then promotion to `packages/chatfs-cli/` with installed kebab
entry points and a required `--cache <dir>`. That left the documentation
half of the contract open, and one diagnosed casualty of *not* having a
scoping rule: project `stack-split.md` had assigned cache layout,
markdown generation, orchestration, and a provider registry to Rust —
stale because a project-level doc asserted one subsystem's internals,
which nothing forced pipeline work to revisit.

## Decision

The incubator's design.kb moves wholesale to
`packages/chatfs-cli/design.kb/` (2026-08-08, umbrella child 005) — the
docs follow the code they govern. The project tower
(`docs/dev/design.kb/040-design.kb/`) is **seams-only**: it states how
subsystems meet (invocation direction, path ownership, the three-runtime
split), never any single package's internals. Package-internal decisions
live in the package's own design.kb.

Applied concretely:

- `stack-split.md` rewritten seams-only: three runtimes joined by
  subprocess + files; internals delegated to `package-division.md`, the
  path-ownership contract, and package kbs.
- Migrated entries updated to ground truth as they moved (dotted module
  names, kebab commands, `--cache`), not copied verbatim.
- Where a moved entry answered a question the project tower still asks,
  the tower keeps a `[!QUESTION]`/`[!TODO]` block or a pointer, not a
  duplicate.

## Alternatives Considered

- **Fold the entries into the project tower.** Honors the README's
  letter, but recreates the stack-split failure mode at scale: every
  package-internal claim in the project tower is a doc nothing forces
  package work to maintain.
- **Leave the design.kb in the incubator.** The incubator is closed; a
  live kb inside a dead directory is where links rot. The kb was already
  package-scoped in content — only its address was wrong.
- **Move with stub files left behind.** Symlink/pointer stubs at the old
  paths would preserve inbound links, but the interim cross-kb
  convention is backlink-sweep-on-move; a repo-wide grep fixed every
  live reference instead (devlogs deliberately left historical).

## Consequences

**Positive:**

- The drift class stack-split exemplified is structurally gone: package
  internals are documented next to the code whose changes invalidate
  them.
- The incubator's fold-back contract is closed; the directory remains
  only as history plus `chatfs.demo/` fixtures.

**Negative:**

- Design knowledge now lives in two towers; readers must know the
  seams-only rule to know where to look. `CLAUDE.md` and the tower
  CLAUDE.mds carry the pointer.

**Neutral:**

- Cross-kb reference conventions (symlinks vs stubs vs plain paths)
  remain interim, tracked upstream in llm-kb's
  cross-kb-cooperation-conventions todo.

## Related

- Umbrella: `.claude/todo.kb/2026-07-13-000-graduation-and-integration.md`
  (children 000/001 code, 005 docs)
- Seams the tower keeps: `docs/dev/design.kb/040-design.kb/stack-split.md`,
  `docs/dev/technical-policy.kb/path-ownership.md`,
  `docs/dev/design.kb/040-design.kb/package-division.md`
- New home: `packages/chatfs-cli/design.kb/`
