# Design — chatfs-cli

Decisions about the shape of the capture/splat/render pipeline and the CLI
surface that drives it.

## What belongs here

- CLI command structure (nouns, verbs, locator sub-nouns)
- Regeneration semantics (freshness, idempotence, fail-modes)
- Contracts between pipeline stages (what each stage may rely on, what it
  must not synthesize)

## What does NOT belong

- Cross-package seams — the on-disk cache contract is
  `docs/dev/technical-policy.kb/path-ownership.md`; subsystem boundaries
  are the project `040-design.kb/`
- Implementation details of individual modules (live in the modules
  themselves or in devlogs)
