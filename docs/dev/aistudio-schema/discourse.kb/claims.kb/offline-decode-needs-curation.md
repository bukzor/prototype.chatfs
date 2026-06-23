---
status: asserted
likelihood: 0.9
depends: [sources.kb/rosetta-correlation-experiment.md]
tags: [aistudio, decode, rosetta, goal]
---

Offline JSPB decode is achievable, but **not** as a fully-deterministic
alignment "without reverse engineering": the static position→name map must be
**hand-curated and cross-checked against the bundle**, then frozen.

Once frozen, decoding any captured JSPB body offline is purely mechanical and
deterministic — `rosetta/convert.py` does exactly this, and `rosetta/verify.py`
confirms the output is name/shape-equal to the real alt=json for the golden
pair. The reverse engineering is a one-time cost paid when *building* the map
(correlate → cross-check against `walk-graph.py` → curate SCHEMA), not a
per-decode cost.

This is a partial, qualified answer to "decode deterministically without RE":
*yes deterministic per-decode, no on the without-RE part* — the map cannot be
derived from a capture by alignment alone (`claims.kb/ordering-alignment-is-ambiguous.md`)
and field names are absent client-side (`claims.kb/field-names-absent-client-side.md`).
