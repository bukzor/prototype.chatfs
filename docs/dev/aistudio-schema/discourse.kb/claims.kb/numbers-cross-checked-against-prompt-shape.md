---
status: asserted
likelihood: 0.9
sources: [sources.kb/readme.md, sources.kb/bundle-audit.md]
depends: [claims.kb/schema-recoverable-from-bundle.md]
tags: [aistudio, schema, validation]
---

The recovered field numbers are correct **for the fields that have getters** —
now directly validated, not just corroborated. Decoding a real
`ResolveDriveResource` payload places `Name` at idx0, `Metadata` at idx4, and
`Metadata.DisplayName` at idx0 — exactly the positions `walk-graph` reports.
This is a live-payload check, stronger than the README's prescribed cross-check
against `aistudio-jspb-prompt-shape.md`.

**Scope.** The validation covers only the ~2 getter-exposed Prompt fields. The
turn/role/content positions are *not* covered — they have no getter
(`claims.kb/getter-recovery-is-partial.md`), so there is nothing recovered to
check there. Correctness of the recovered subset: high (~0.9). Coverage of that
subset: low.
