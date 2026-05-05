# 2026-04-29 — Drop Freshness Caches in chatfs-mockup-chatgpt Pipeline

**Status:** Accepted
**Scope:** `docs/dev/design-incubators/chatfs-mockup-chatgpt/`

## Context

Three accelerators existed in the pipeline before this decision:

- `chatgpt-page-capture.py` kept a 1000-hour CDP cache.
- `chatgpt-index.sh` kept a 60-minute CDP cache.
- `path render` mtime-gated `chatgpt-splat` against `$UUID.json`.

All three short-circuited stages when their outputs looked fresh. They
were originally added to make hand-driven iteration tolerable.

## Decision

Remove all three. Every pipeline stage presumes its outputs are stale
and rebuilds them from scratch. There are no freshness caches in the
user-facing scripts.

## Consequences

Skipping a stage because its output looks fresh hides:

- Code changes to the stage itself (output is stale w.r.t. the new code).
- Code changes to *external tools* the stage shells out to —
  `chatgpt-splat`'s mtime won't bump even when the binary is rebuilt.
- Upstream input changes (the conversation may have new turns since
  capture).
- Partial-write failures (a half-written cache survives the freshness
  check).

Running a stage twice in a row now produces the same bytes the second
time as the first — modulo upstream changes the user is asking about.

If browse latency becomes the bottleneck for a workflow, the answer is
an opt-in developer flag, not a default-on cache. The current incubator
has no such flag.

## See also

- `docs/dev/design-incubators/chatfs-mockup-chatgpt/design.kb/040-design.kb/deterministic-regeneration.md` — forward-facing rule.
- `docs/dev/devlog/2026-04-29-000-chatfs-mockup-chatgpt-url-flow-and-determinism.md` — session that landed the change.
