---
status: asserted
likelihood: 1.0
sources: [sources.kb/readme.md, sources.kb/bundle-audit.md]
depends: [claims.kb/primitive-encodes-type.md]
tags: [jspb, schema, incomplete]
---

The primitive→meaning legend is **only partially known**, and the gap is
larger than the four-row table suggests. The legend covers 4 primitives
(`_.l`, `_.Mj`, `_.X`, `_.xi`); `accessors.jsonl` contains **13 distinct
primitives across 140 fields**, so **~43 % of recovered fields (60/140) are
un-typed** — number and name only. (Bumped to 1.0: this is now a measured
fact, not a README hedge — see `sources.kb/bundle-audit.md`.)

The doubt is in completeness, not in the four observed rows: any field whose
primitive is outside the legend is currently un-typed by the pipeline. The
nine unknown primitives (`_.sm`, `_.tm`, `_.Do`, `_.An`, `_.Qi`, `_.jp`,
`_.Ii`, `_.Lm`, `_.Or`) are the concrete backlog.
