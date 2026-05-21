# Insert a `0050` blackbox-conversion commit before `0100` scaffold

Before the Rust crate scaffold lands at commit `0100`, insert a `0050`
commit (or block) that converts the existing `.spec.mjs` tests to
blackbox CLI form (subprocess invocation, assertions on JSONL output).

## Why

- The regression suite must exist **before** any Rust output appears,
  so that the `0100` scaffold and every subsequent Rust commit lands
  against a live oracle.
- Doing the conversion on Node-only ground is cheaper than mid-port:
  any Node-specific output quirks the existing tests rely on get
  discovered now, when fixing them is local to one implementation.
- This precedes the diagnostic-event work; the blackbox tests start
  asserting only on the cdp-jsonl stream and grow diagnostic assertions
  later (per `decision.kb/separate-diagnostic-stream.md`).

## Scope of `0050`

- Convert `.spec.mjs` files to subprocess form. See
  `decision.kb/test-split-by-extension.md` for what stays as a
  `.test.mjs` unit test (those don't convert; they port to Rust later).
- Capture a baseline JSONL run against `toy_server` (and possibly
  `example.com` per
  `decision.kb/example-com-baseline-transition-only.md`) as committed
  fixtures, used as the oracle.
- Set up the test-runner's randomized-mode infrastructure scaffold
  (per `decision.kb/uniform-emit-with-randomized-test-mode.md`), even
  if no diagnostic events are emitted yet.

## Numbering

The charter (`packages/har-browse/dev.kb/rust-port.md`) reserves `0N00`
spacing for `0150`/`0250` inserts; `0050` is "before any phase-1
commit." If diagnostic-design or baseline-capture wants its own
commit, use `0025`/`0075` for further subdivision.

Decided 2026-05-21.
