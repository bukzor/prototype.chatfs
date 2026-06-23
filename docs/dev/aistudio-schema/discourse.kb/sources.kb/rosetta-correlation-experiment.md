---
kind: investigation
title: "JSPB↔alt-json golden-pair correlation (2026-06-23)"
tags: [aistudio, decode, rosetta, primary]
---

Fetched one prompt in both encodings for the *same* `ResolveDriveResource`
response — `rosetta/resolvedrive.jspb.json` (positional) and
`rosetta/resolvedrive.alt-json.json` (named) — then correlated them to test
whether a static position→name map can be derived by alignment alone. Tooling:
`rosetta/correlate.py` (field-number ordering heuristic), checked against the
hand-curated SCHEMA in `rosetta/convert.py` and the bundle field numbers from
`walk-graph.py`. The user authorized use of their own token against their own
prompt.

Results:

- **The ordering heuristic reproduces most of the SCHEMA** — for fully-populated
  messages the monotonic "claim the next type-compatible slot" rule recovers the
  correct `slot → field` map (e.g. `runSettings`, `metadata.owner`).
- **It mis-assigns whenever a field is absent in the sample.** A null slot has no
  named counterpart, so the cursor skips it and a later field is claimed at the
  earlier slot. Observed: in `metadata.lastModified.user`, `isMe` is absent →
  `photoUri` is claimed at slot 1, but its true number is 2; in the chunk
  message, `createTime` is reported at slot 35 (the `aspectRatio` slot) because
  intervening slots are null. The hand-curated SCHEMA + bundle numbers give the
  correct positions (`photoUri`=2, `createTime`=32).
- **Conversion round-trips "similar enough."** `convert.py` on the JSPB fixture
  is name/shape-equal to the real alt=json (`rosetta/verify.py`), tolerating
  value-representation differences (bool 0/1, enum ints, timestamp `[s,ns]` vs
  RFC3339). This validates the *curated* SCHEMA, not the ordering heuristic.

Single prompt tested; stability across prompt types (repeated fields, oneofs,
varied absent/optional slots) not yet exercised.
