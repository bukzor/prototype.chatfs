---
why:
  - har-capture-learning
---

# Validate the Capture → Extract → Emit Pipeline Shape

Confirm that the BB1→BB2→BB3 decomposition works as a concrete CLI pipeline:
a capture tool produces a HAR, a plucker extracts structured data, an emitter
renders markdown. Each step is independently testable, composable via stdin/stdout
or file I/O, and fails noisily.
