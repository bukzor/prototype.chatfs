# observation.kb/ — durable factual snapshots about state

## What belongs

Things that are true about the world (file contents, repo state, user
positions, backlog properties) and that future agents should know without
re-deriving. Each file = one observation.

Includes user-asserted facts and corrections — these are observations
backed by user authority.

## What does NOT belong

- **Rigorously verified claims** with a verification script — those go in
  `../verified-claim.kb/`. Observations here are believed, not necessarily
  scripted-and-checked.
- **Decisions** based on the observation → `../decision.kb/`.
- **Principles** extracted from a pattern of observations →
  `../principle.kb/`.
- **Ephemeral state** that decays within minutes/hours (git status, open
  PTY processes). Use only durable observations.

## When to add

When a fact would otherwise require re-derivation by the next agent.
Skip if the fact is reachable by a single `ls`, `git status`, or
equivalently cheap probe.
