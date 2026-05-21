# Rename `policy-safe-automation-boundary.md` → `policy-whitehat-automation-boundary.md`

Rename
`docs/dev/technical-policy.kb/policy-safe-automation-boundary.md` to
`docs/dev/technical-policy.kb/policy-whitehat-automation-boundary.md`.
Update all references.

## Why

- "Safe" has too many meanings (memory-safety, type-safety, thread-
  safety, user-safety, etc.) to convey the policy's actual content
  unambiguously.
- "Whitehat" specifies the **ethical / non-adversarial security
  stance** — we don't scrape, we don't extract tokens for browserless
  retrieval, we don't drive the service against its consent. That's
  the policy's substance.

## Scope of the rename

- File rename (git mv).
- Update references in:
  - `packages/har-browse/dev.kb/rust-port.kb/scope-audit.md` (Q3).
  - Any other doc that cites the policy by filename (find via grep).
- The body content of the policy stays unchanged under this decision;
  any content edits are separate decisions.

## Execution

Deferred to the kb-migration / scope-audit-execution session (see
session-planning notes in
`sessions.kb/dev-kb-five-collection-pattern.md`).

Decided 2026-05-21.
