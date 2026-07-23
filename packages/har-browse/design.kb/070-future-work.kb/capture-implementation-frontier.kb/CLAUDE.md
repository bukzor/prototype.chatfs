# Capture Implementation Frontier — Candidates

One file per candidate implementation considered for a green-field BB1
capture, answering `../capture-implementation-frontier.md`. Every
candidate is evaluated against the same requirements
(`capture-everything`, `crash-durability`, `unblocked-sessions`); each
states its `status` (`frontier-optimal` or `dominated`) and an
`owned-loc` estimate.

## What belongs here

- One implementation candidate per file: what it is, its approximate
  owned-code cost, and why it's frontier-optimal or what vetoes it
- Dominated candidates, kept when the way they lose is instructive
  (not every rejected idea earns a file — only illustrative ones)

## What does NOT belong

- The question itself and the cross-candidate axes (→
  `../capture-implementation-frontier.md`)
- The currently shipped design (→ `../../040-design.kb/`)
