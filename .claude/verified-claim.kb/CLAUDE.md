# verified-claim.kb/ — assertions backed by a re-runnable verification

## What belongs

Facts that were asserted AND verified by running a script or command. Each
file states the claim, names the verification (`sha256sum`, `find`,
`diff`, etc.), and shows enough output for a future agent to re-run it.

The verification gives the claim higher epistemic weight than a plain
observation — useful when later decisions hinge on it (e.g., "safe to
delete because all copies are bit-identical").

## What does NOT belong

- **Plain observations** without a re-runnable check → `../observation.kb/`.
- **Decisions** that depend on the verified claim → `../decision.kb/`.
- **Verification procedures** (the how-to of running a check) — not
  applicable here; those would live in a methodology kb.

## When to add

When you ran a check whose result is load-bearing for a downstream
decision (especially destructive ones like deletes). Recording the
verification lets future agents re-confirm without re-deriving the
command.
