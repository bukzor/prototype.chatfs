# sessions.kb/ — session-output records worth preserving

## What belongs

Narrative records produced by a working session whose value is durable —
meta-planning decisions, deliberations that span multiple topics,
synthesis documents distilled from a conversation. One file per session
(or per coherent sub-session if a single session covered multiple
independent topics).

## What does NOT belong

- **Specific decisions** distilled out of the session → `../decision.kb/`.
  The session record can cite them; it should not be the only home.
- **Principles** distilled out of the session → `../principle.kb/`.
- **Ephemeral notes** (mid-session todo, scratch thinking) — use
  `../../trash/` or similar.
- **Per-commit narrative** within an ongoing porting effort — those have
  their own home (e.g. `rust-port.kb/commits.kb/`).

## When to add

When the session's value is in its synthesis (not yet distilled into
individual decisions/principles) and that synthesis is worth pointing
future agents at. Stale sessions can be pruned once their durable
content has been promoted to the role-specific kbs.

## Naming

Topic slug, kebab-case. Date prefix optional (the file's git history
records timing).
