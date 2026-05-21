# BB1 *is* har-browse

Redefine BB1 (the first black box in chatfs's pipeline decomposition) as
har-browse, not as "capture in general."

## Why

- har-browse didn't have a name when the BB1/BB2/BB3 framing was
  originally adopted (see
  `docs/dev/design.kb/040-design.kb/black-box-decomposition.md`).
- The "multiple BB1 implementations" framing (one per target site) added
  contract layering that doesn't pay off in practice. Future site-
  specific behavior is *parameterization of har-browse*, not parallel BB1
  implementations.

## Consequences

- The BB1↔BB2 contract is the **cdp-jsonl schema**, owned by har-browse
  (lives in `packages/rs-har-browse/schema/`; see
  `decision.kb/schema-home-and-naming.md`).
- Site-specific behavior (claude.ai, chatgpt.com, etc.) becomes
  parameters / config / extraction-layer concerns, not new BB1 impls.
- The scope-audit's
  (`packages/har-browse/dev.kb/rust-port.kb/scope-audit.md`)
  "multiple BB1 implementations foreseeable" framing dies. Schema home
  decision (was Q1 in the audit) falls out as har-browse-owned.

## Execution

Workspace's `docs/dev/design.kb/` needs editing wherever BB1 is
defined or referenced to reflect this redefinition. Deferred to future
session.

Decided 2026-05-21.
