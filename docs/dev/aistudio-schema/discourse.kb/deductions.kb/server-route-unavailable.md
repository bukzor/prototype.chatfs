---
status: asserted
kind: entailment
conclusion: claims.kb/bundle-is-only-schema-source.md
premises:
  - claims.kb/internal-proto-unpublished.md
  - claims.kb/no-grpc-reflection.md
  - claims.kb/schema-ships-to-browser.md
depends: [claims.kb/alt-json-yields-named-projection.md]
tags: [rationale]
---

**Undercut.** The premises rule out a schema *document* from the server, but the
conclusion ("bundle is the only source") overreaches: `?alt=json` yields the
named field structure directly (`claims.kb/alt-json-yields-named-projection.md`).
The entailment holds only if "schema source" means a formal descriptor, or if
work is constrained to be offline from a capture. See the contested conclusion.


The proto is in an unpublished `google.internal.*` package, so no `.proto` can
be obtained out of band; and the `$rpc` front end offers neither reflection nor
a discovery doc, so nothing can be pulled from the server at runtime. With both
server avenues closed and the schema nonetheless present in the shipped JS, the
bundle is left as the only source — entailing
`claims.kb/bundle-is-only-schema-source.md`.
