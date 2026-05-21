# decision.kb/ — choices made that future agents must honor or revisit

## What belongs

Architectural, convention, or framing decisions reached in a session whose
rationale should outlive the session. One file per decision. Body states
what was chosen, why (briefly), and where the work to execute it lives.

## What does NOT belong

- **Action items** implementing the decision → `todo.kb/` (in this repo or
  the affected repo). Reference from the decision file.
- **Observations** that informed the decision → `../observation.kb/`.
- **Durable principles** of the form "always do X" → `../principle.kb/`.
  A principle is a rule of thumb; a decision is a specific choice for a
  specific fork.

## When to add

When a non-trivial fork was taken whose rationale should be reachable
without re-reading the session transcript. Tiny choices and reversible
defaults don't need a file.
