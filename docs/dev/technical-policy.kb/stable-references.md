---
force: should
why:
  - determinism
source:
  - user (bukzor)
---

# References Are Append-Stable

Regenerable outputs keep their reference handles stable as input grows:
regenerating after new data arrives must not re-assign existing handles.
Prefer handles append-stable by construction — creation-time rank, immutable
source ids — over emit-order or positional numbering.

No hysteresis to compensate: if stability would require remembering prior
runs, the handle scheme is wrong (see `determinism.md`).
