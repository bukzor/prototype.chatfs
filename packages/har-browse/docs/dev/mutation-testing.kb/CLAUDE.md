# Mutation Testing

Post-hoc TDD for har-browse. Each file records a single planned mutation
of the implementation — a bug we could plausibly inject — and tracks
whether the test suite reliably catches it.

Workflow: Skill(mutation-testing). Read it before adding entries.
Off-limits during mutation planning (Skill step 2) — even `ls` contaminates.

Each entry is a markdown file with frontmatter:

- `status`: `todo` (not attempted), `done` (tests catch it), `gap`
  (tests cannot be hardened; deferred).
- `attempts` (gap only): number of strengthening tries.

Body sections:

- Top paragraph: what the bug would cause if it shipped.
- `## Injection`: the specific code change to make.
- `## Test Coverage` (done): tests that catch it (path:line where useful).
- `## Test Result` (gap): why hardening failed; what was tried.

Filenames describe the bug, not the symptom — e.g.
`barrier-emit-before-bodies-settle.md`, not `responses-arrive-late.md`.

## Order

Smallest-leaf-first. Cache + user-agent are pure functions; inject is
DOM-isolated; capture.mjs is integration-level and goes last.
