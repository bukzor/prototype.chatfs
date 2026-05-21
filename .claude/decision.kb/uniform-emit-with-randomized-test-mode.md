# Diagnostic events emit uniformly; tests sample on/off mode randomly

For diagnostic events (the auxiliary JSONL events that defend ordering
invariants — see `decision.kb/separate-diagnostic-stream.md`):

- **Production emission is uniform.** No `if CI`-gated emission paths in
  the code. Diagnostic events are always emitted at the *source*; the
  *sink* decides whether to keep or drop the stream (default: drop in
  production unless explicitly enabled).
- **Tests randomize mode per test.** Each test's mode (diagnostics on
  vs off) is determined by hashing the test name into a seed —
  deterministic across runs, but the suite samples both modes in steady
  state without doubling cost.
- **Slow tests sample only one mode if passing.** Quickcheck/hypothesis
  discipline: if the single sample passes, don't re-run with the other
  mode. If it fails, the failure mode (on or off) is part of the report.
- **One dedicated double-run gate test** explicitly pays the 2× cost:
  runs the same scenario with diagnostics on and off, asserts the
  non-diagnostic output is byte-identical. This is the enforcement
  mechanism for `principle.kb/zero-side-effect-diagnostics.md`.

## Why

- Uniform emit avoids divergent code paths between test and production,
  which `principle.kb/zero-side-effect-diagnostics.md` requires.
- Random per-test sampling gets coverage of both modes across the suite
  without exponential test-count blowup.
- Singling out the explicit double-run gate localizes the 2× cost to
  the one place the property actually needs to be checked.

Decided 2026-05-21.
