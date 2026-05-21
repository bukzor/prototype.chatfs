# Adopt role-keyed kb collections at workspace `.claude/`

Adopt the five-collection epistemic-role pattern from homedir-archeology
(`~/claude/homedir-archeology/.claude/*.kb`) at this workspace's
`.claude/`:

- `decision.kb/` — specific choice at a specific fork
- `principle.kb/` — generalizable "always do X" rule
- `observation.kb/` — durable factual snapshot about state
- `verified-claim.kb/` — assertion backed by a re-runnable verification
- `reference.kb/` — stable external pointer
- `sessions.kb/` — session-output records pending distillation

## Why

- Role classification gives natural homes — "where does this go?"
  collapses to "what kind of claim am I making?"
- Distinguishes observation from verified-claim (epistemic gradient that
  matters for destructive operations).
- Distinguishes principle from decision (which our existing `dev.kb/`
  conflates — e.g., `rust-port.kb/decisions.kb/assertion-strategy.md`
  is principle-shaped, not decision-shaped).

## Scope

- **Workspace-level** adoption: `<repo-root>/.claude/{role}.kb/` with
  CLAUDE.md per collection.
- **Per-package** adoption: deferred. A skill (`Skill(llm-dev-kb)`) was
  considered but not built; see
  `sessions.kb/dev-kb-five-collection-pattern.md` for the considerations.
- Existing `packages/har-browse/dev.kb/` content (ts-policy.kb,
  rust-port.kb) is **not migrated** under this decision; migration is
  optional future work informed by the session entry.

Decided 2026-05-21.
