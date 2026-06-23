---
status: asserted
kind: entailment
conclusion: claims.kb/schema-recoverable-from-bundle.md
premises:
  - claims.kb/schema-ships-to-browser.md
  - claims.kb/field-numbers-are-literals.md
  - claims.kb/accessor-names-survive-minification.md
  - claims.kb/primitive-encodes-type.md
depends: [claims.kb/primitive-legend-partial.md]
tags: [rationale]
---

Because the bundle uses immutable JS protos, each field is exposed through a
generated accessor that simultaneously reveals its number (integer literal),
its name (survives minification), and its type/cardinality plus submessage edge
(the primitive). Reading these across all accessors reconstructs the message
graph — entailing `claims.kb/schema-recoverable-from-bundle.md`.

Caveat: soundness is bounded by `claims.kb/primitive-legend-partial.md` — fields
whose primitive is not yet in the legend are recovered in number and name but
not in type. Recovery is therefore complete in structure, partial in typing.
