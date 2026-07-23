---
why:
  - capture-cut-completeness
---

# Marks: Page-Facing Checkpoint Stamps

Pages and injected helpers can stamp the record via a page-facing
binding, `window.harBrowseMark(payload)`, which appears in the record
as a `Runtime.bindingCalled` event. Payloads beginning `BARRIER:` carry
a causal guarantee: every response the page had consumed before the
mark appears in the record before the mark, letting a caller (test or
tool) verify that capture-cut-completeness actually held at that
checkpoint. Non-anchored payloads (any prefix other than exactly
`BARRIER:`) pass through at their natural position — no deferral.

Marks are a verification hook, not a mission-required capability:
capture-everything's "verify downstream" corollary means the extractor,
not the capture stage, ultimately judges sufficiency. Marks exist so
that judgment — here, in this codebase's own test suite — has
something precise to check against.
