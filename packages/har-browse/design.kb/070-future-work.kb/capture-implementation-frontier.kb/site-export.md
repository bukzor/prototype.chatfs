---
why:
  - capture-implementation-frontier
status: dominated
owned-loc: "~50"
middleware: "none"
silent-miss: "fatal (fork/tree structure dropped)"
crash-durable: "n/a (not a live capture)"
stealth: "n/a"
bb1-purity: "leaks all (relies entirely on the provider's export logic)"
---

# Provider's Official Data Export

If a provider's official export (or unofficial API) contained
everything chatfs needs, this candidate deletes the entire capture
stage: unzip and go.

**Why it's dominated, not frontier:** fails on fidelity. Exports drop
exactly the structure chatfs cares most about — fork/tree
relationships between messages — which is what makes reconstructing a
conversation graph from an export lossy in the one dimension this
project can't tolerate losing.

Worth an occasional empirical recheck per provider — export formats
change, and if one ever becomes complete, it obsoletes every other
candidate in this document, not just the capture stage.
