# User-Interface Mechanisms

Ways the user's tools can reach cached conversation data. Each file describes
one mechanism for exposing the cache to editors, shells, file managers, and
other existing tooling.

## What belongs here

- A specific mechanism for making cached conversations available to user tools
- What the user's experience looks like (commands, paths, latency model)
- How it relates to the cache and the sync control plane
- Tradeoffs (standard-tool compatibility, scale, policy safety, dependencies)

## What does NOT belong

- Which mechanism is currently chosen — see `../user-interface.md`
- Sync control plane details — see `../sync-control-plane.md`
- Cache internals — see `../black-box-decomposition.md` (BB3) and the cache
  component docs once they exist

## When to add

New mechanisms worth considering (or considered and rejected with durable
reasoning) get their own file. Transient framing variations don't.
