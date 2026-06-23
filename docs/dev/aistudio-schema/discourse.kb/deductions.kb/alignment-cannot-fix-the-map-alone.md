---
status: asserted
kind: entailment
conclusion: claims.kb/offline-decode-needs-curation.md
premises:
  - claims.kb/ordering-alignment-is-ambiguous.md
  - claims.kb/field-names-absent-client-side.md
depends: [claims.kb/field-numbers-are-literals.md]
tags: [rationale]
---

The naive offline path was: align one golden pair position-by-position, freeze
the derived map, decode forever. Two premises break the "derive" step. Field
names are absent client-side (`claims.kb/field-names-absent-client-side.md`), so
the only signal in a capture is *position* — and positional alignment is
ambiguous wherever a field is absent from the sample
(`claims.kb/ordering-alignment-is-ambiguous.md`). A map carrying those
mis-assignments would silently decode later captures wrong.

So the map cannot be trusted from alignment alone; it must be reconciled against
an independent source of field numbers — the bundle accessors, where the numbers
are integer literals (`claims.kb/field-numbers-are-literals.md`) — and curated by
hand. That reconciliation is reverse engineering, paid once. Hence
`claims.kb/offline-decode-needs-curation.md`: deterministic per-decode, but not
RE-free.
