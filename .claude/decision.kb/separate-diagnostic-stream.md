# Diagnostic events go in a separate stream from cdp-jsonl

For mutations that require defending an internal ordering invariant
(bucket (a) in the mutation-walk classification), augment har-browse to
emit auxiliary "diagnostic" events. These go in a **separate output
stream**, not interleaved into the cdp-jsonl stream.

## Mechanism

To-be-decided at schema-design time. Candidates:
- Separate file via `--diagnostics-out=<path>` flag.
- stderr (with structured JSONL framing).
- Sibling output handle.

## Interleavability concerns

If relative timing between a diagnostic event and specific cdp-jsonl
events is load-bearing for defending an invariant (e.g., "no body
event between two `Diagnostic.barrierConsumed` events"), the separate-
stream choice loses information unless mitigated. Mitigation options
(decide per-invariant during the mutation walk):

- **Sequence numbers** on both streams, monotonic across the run.
- **Timestamps** on both streams, monotonic at sufficient resolution.
- **Interleaved format** for the specific invariant that needs it
  (escape hatch from the separate-stream default).

## Why separate (not interleaved)

- Keeps the cdp-jsonl stream byte-stable for `chrome-har` consumption
  and downstream BB2 extraction. Charter line 57 ("byte-stable for
  fields we control") stays clean of qualifiers.
- Diagnostic schema can evolve independently of the CDP wire format.
- Downstream consumers (`toy_pluck.sh`, BB2) don't have to filter
  diagnostic events out of the main stream.

## Diagnostic-event design rule

Events express **observable invariants**, not internal state-machine
transitions. E.g., `Diagnostic.barrierConsumed` (the invariant: barrier
was merged into consumed state) — not `Diagnostic.barrierEnterPhase1`.
Both Node and Rust implementations satisfy the same observable
property regardless of internal structure.

Decided 2026-05-21.
