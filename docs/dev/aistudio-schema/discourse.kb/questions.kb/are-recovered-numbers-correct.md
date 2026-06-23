---
candidate-resolutions: [claims.kb/numbers-cross-checked-against-prompt-shape.md]
sources: [sources.kb/readme.md]
tags: [aistudio, schema, validation, doubt]
---

**The core question of the enterprise.** The toolkit recovers field numbers,
names, and a message graph from the bundle — but are they *correct*? The
recovery mechanism (`claims.kb/schema-recoverable-from-bundle.md`) justifies
that extraction is *possible*; it does not establish that any particular
recovered number is the right one, that the graph walk reached the intended
messages, or that nothing was mis-typed under the partial primitive legend.

**Partly resolved — split by coverage.** A real `ResolveDriveResource` payload
was decoded: the getter-exposed numbers (Name idx0, Metadata idx4, DisplayName
idx0) land exactly as recovered, so *for those fields* correctness is confirmed
(`claims.kb/numbers-cross-checked-against-prompt-shape.md`, ~0.9). **Still open
for the fields that matter:** the turn/role/content numbers are never recovered
(no getter — `claims.kb/getter-recovery-is-partial.md`), so their correctness
can't even be posed yet. Fully resolving this needs those numbers recovered
(wider capture, or positional RE) and then checked against a payload.
