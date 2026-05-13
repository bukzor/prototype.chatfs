# Commit 1050: causal-watermark

## What
Port causal-watermark logic: multi-witness, range, body-integrity.

## Plan
- Re-encode the three tightenings from original Node commit `0de80cd` as typed Rust invariants.
- Port tests verbatim, one per invariant where feasible.
- Extend `dev.kb/barrier-invariants.md` (or split out as `dev.kb/causal-watermark.md`) with the three invariants + their interactions with BARRIER.

## Refs
- `../facts.kb/current-architecture.md`
- Original commit: `0de80cd` (multi-witness + range + body-integrity)
- `1000-barrier-reentrant.md`

## Outcomes
- [ ] Multi-witness invariant encoded with at least one targeted test (watermark only advances with N witnesses, N>1)
- [ ] Range invariant encoded with at least one targeted test (out-of-range witnesses rejected)
- [ ] Body-integrity invariant encoded with at least one targeted test (mismatched body rejected)
- [ ] All causal-watermark tests from the Node implementation pass after porting
- [ ] `dev.kb/` doc (extended `barrier-invariants.md` or new `causal-watermark.md`) covers the three invariants and their interactions with BARRIER

## Notes
The three sub-invariants may want individual commits (`1025` / `1050` / `1075`) if porting reveals them as independently verifiable. Reassess before starting.
