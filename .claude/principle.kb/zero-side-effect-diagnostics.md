# Diagnostic emission must have zero observable side effects

When a system emits diagnostic / instrumentation / probe events
alongside its primary output, emitting (or not emitting) those events
must not change any other behavior:

- Same code flow regardless of whether the diagnostic stream is
  enabled.
- Same non-diagnostic output (byte-identical, ordering-identical).
- Same error / timing / resource behavior to a tolerance test-suite
  randomization can't distinguish.

## Why

If a test passes only when diagnostics are on (or only when off), the
diagnostic emission has become load-bearing — and you can no longer
trust the diagnostic events to be honest reports of what *would have
happened* without instrumentation. The probe has perturbed the
experiment.

## Enforcement

Mechanical, not by code review:

- A dedicated double-run gate test runs the same scenario twice (once
  with diagnostics on, once off) and asserts non-diagnostic output is
  byte-identical. CI fails if the gate trips.
- Tests at large run in randomized modes (seeded by test name), so
  any test that secretly depends on a specific mode tends to surface
  flakily over time.

See `decision.kb/uniform-emit-with-randomized-test-mode.md` for the
test-suite mechanism.

## Implementation guidance

- Gate diagnostics at the **sink** (drop or keep the stream), never
  at the **source** (always emit). No `if (diagnostics_enabled) emit()`
  in the production code path.
- Diagnostic emission should be a separate stream (per
  `decision.kb/separate-diagnostic-stream.md`) so it's filterable
  cleanly at the consumer.
- Diagnostic events express **observable invariants**, not internal
  state — they're proofs, not state dumps.

## Scope

This is a principle for any instrumentation/probe layer where the
probe is supposed to be observation-only — not specific to har-browse.

Surfaced 2026-05-21 during har-browse Rust-port meta-planning.
