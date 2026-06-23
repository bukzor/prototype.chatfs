---
status: asserted
likelihood: 0.97
sources: [sources.kb/rosetta-correlation-experiment.md]
date-observed: 2026-06-23
tags: [aistudio, decode, rosetta, doubt]
---

Deriving the JSPB `slot → field-name` map by **positional alignment alone is
ambiguous**: it is correct only for messages where every field is populated in
the sample.

The alignment rests on proto field-number ordering — `?alt=json` emits fields in
ascending field number, so the matching JSPB slots rise monotonically, and you
can walk the named fields in order, claiming the next type-compatible slot. But
a field absent from this instance leaves a **null slot with no named
counterpart**, so the cursor skips ahead and the next named field is mis-claimed
at the earlier slot. Observed in the golden pair: with `isMe` absent, `photoUri`
is assigned slot 1 (true number 2); `createTime` lands on slot 35 (the
`aspectRatio` slot, true number 32) past intervening nulls.

So the ordering heuristic is an **authoring aid, not an oracle**. A correct map
needs an external check — the bundle field numbers (`walk-graph.py`) or a
fully-populated sample — which is why `rosetta/convert.py`'s SCHEMA is
hand-curated rather than generated.
