---
resolved: claims.kb/bundle-is-only-schema-source.md
sources: [sources.kb/readme.md]
tags: [aistudio, schema, rationale]
---

Why brute-force the schema out of the web bundle instead of obtaining it from
the server (reflection, discovery doc, published `.proto`)?

Resolved: all server avenues are closed (unpublished `internal` package, no
reflection, no discovery doc), and the schema ships to the browser anyway —
see `claims.kb/bundle-is-only-schema-source.md` and its deduction.
