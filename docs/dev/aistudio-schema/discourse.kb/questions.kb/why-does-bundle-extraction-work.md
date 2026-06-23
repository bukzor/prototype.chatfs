---
resolved: claims.kb/schema-recoverable-from-bundle.md
sources: [sources.kb/readme.md]
depends: [claims.kb/getter-recovery-is-partial.md]
tags: [jspb, schema, rationale]
---

Why is the schema recoverable from minified JS at all — doesn't minification
destroy it?

Resolved **as a mechanism question**: Google's immutable JS protos preserve the
load-bearing parts. Field numbers are integer literals, accessor names survive
minification, and the primitive encodes type/cardinality — see
`claims.kb/schema-recoverable-from-bundle.md` and its deduction. Per-message
recovery is complete in structure, ~57 % in typing (the partial primitive
legend).

**Scope caveat — do not read this as "the target schema is recovered."** The
mechanism surfaces only getter-exposed fields. On `ResolveDriveResource` — which
*does* carry the conversation — it recovers ~2 of the Prompt message's ~14+
fields; the turn/role/content fields have no accessor in these bundles, so they
are not recovered (`claims.kb/getter-recovery-is-partial.md`).
