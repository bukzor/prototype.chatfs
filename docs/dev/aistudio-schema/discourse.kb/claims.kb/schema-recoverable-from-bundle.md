---
status: asserted
tags: [jspb, schema, rationale]
---

The schema is mechanically recoverable from the minified bundle: field
numbers, names, cardinality, and the nested-message graph can all be read back
out of the generated accessors. This is *why the approach works*.

Conclusion of `deductions.kb/immutable-protos-leak-schema.md`.
