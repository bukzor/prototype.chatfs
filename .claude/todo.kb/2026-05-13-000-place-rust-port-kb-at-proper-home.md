---
anthropic-skill-ownership: llm-subtask
---

# Place the rust-port kb at a proper home

**Priority:** Medium (defer until at least one more session of thinking)
**Complexity:** Medium-to-high (touches paths, crate names, contracts scope)
**Context:** Conversation 2026-05-13; planning the Rust port of `har-browse`. Charter at `../../packages/har-browse/dev.kb/rust-port.md`.

## Problem Statement

The work-area kb lives at `packages/har-browse/dev.kb/rust-port.kb/`, but the work *creates new crates outside `har-browse/`* — `playwright-lite` and `har-browse-rs` are siblings of `har-browse`, not children. The kb is geographically misplaced for a workspace-spanning effort.

Surfaces as friction in three places:

- Procedure docs hard-code `packages/har-browse/dev.kb/rust-port.kb/...` paths even though the work isn't har-browse-scoped.
- Zero discoverability from project entry points (root `CLAUDE.md`, package `CLAUDE.md`) at the time of writing.
- Durable contracts produced by the port (JSONL schema, BARRIER invariants) lack a clean promotion target until the work itself has one. This needs to be decided **before** commits `0750`/`1000`/`1050` write those contracts.

## Current Situation

Work kb at `packages/har-browse/dev.kb/rust-port.{md,kb/}` with 28 content files (charter, facts, decisions, procedures, 15 commit docs, hidden template).

Existing precedent for active multi-package work: `docs/dev/design-incubators/{fuser-vfs,fork-representation,chatfs-cli-mockup}/`.

## Open Questions (for the future session)

- Incubator vs first-class packages? User intuition (2026-05-13) leans away from an incubator since the work outputs real crates — possibly `packages/rs-playwright-lite/` and `packages/rs-har-browse/`.
- Where does the work-area kb live once the crates are first-class? (Workspace-root `dev.kb/`, crate-local `dev.kb/`, or `docs/dev/<something>`?)
- Contracts-home decision follows from the kb-location decision (see `Skill(llm-kb)` for the "how to scope" framing; may need new guidance there).

## Notes

This needs its own session — do not pick reactively mid-port. But it must be decided before commits `0750`/`1000`/`1050` land, because those create durable contracts that need a target home.
