# Commit 1000: barrier-reentrant

## What
Port reentrant BARRIER logic and merge-into-`barrier_consumed` state.

## Plan
- Read existing `src/capture.mjs` BARRIER logic; identify the encoded invariants.
- Re-encode as a typed state machine in Rust (likely an enum with explicit transitions).
- Port associated tests verbatim.
- Begin `dev.kb/barrier-invariants.md` capturing the invariant set as a durable spec.

## Refs
- `../facts.kb/current-architecture.md` (BARRIER is load-bearing)
- Original commit: `ff1e8a0` (reentrant BARRIER + merge into barrier_consumed)

## Outcomes
- [ ] BARRIER state encoded as a Rust enum with explicit transitions (no implicit/string states)
- [ ] All BARRIER tests from the Node implementation pass after porting (one-to-one mapping in the Rust test file)
- [ ] Re-entry on an already-active barrier merges into `barrier_consumed` (test exercises this explicitly)
- [ ] `dev.kb/barrier-invariants.md` exists and enumerates the invariants this commit upholds

## Notes
May split (e.g., `1010`, `1020`) if the state-machine port reveals natural seams. Reassess at landing.
