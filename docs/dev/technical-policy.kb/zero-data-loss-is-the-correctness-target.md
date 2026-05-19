# Zero data loss is the correctness target

Once data is accepted into the pipeline, it is preserved through to the
consumer. Loss at the capture or transport layer is a binary correctness
failure, not a quality-of-service knob.

The asymmetry that makes this absolute: capture is the irreversible
step. Everything downstream — pluck, splat, render, render-md — can be
redone from a captured artifact. Nothing downstream can recover data we
never captured. So a moment of capture-side loss is permanent for every
future invocation of every future tool on that capture.

## Default trade-offs that follow

When the choice is between completeness and something else, completeness
wins:

- **Completeness over performance.** Synchronous syscalls, FIFO
  queues, while-loop drains — fine, even when faster paths exist.
- **Completeness over downstream convenience.** Emit bodyless events
  the consumer must filter; don't filter at the source for the
  consumer's benefit.
- **Loud failure over silent loss.** Process exits non-zero when the
  pipeline's drain-mismatch invariant fails (har-browse adjustment B);
  it does not log-and-continue. A loud signal is recoverable; silent
  loss is forever.
- **"Accept and write through" over "filter at capture for
  downstream's benefit."** The capture layer's job is faithfulness to
  what it received, not opinion about what downstream wants. Opinions
  live at the consumer.

## Where load-shedding does live

This principle is about the *middle* of the pipeline — between accepting
data and writing it out. Load-shedding belongs at the boundaries:

- **At the boundary (don't accept).** Refusing to start a capture
  against an unreasonable URL, declining oversized requests, etc.
- **At the consumer (filter on read).** A jq pluck that drops events
  it doesn't care about, a renderer that skips entries by predicate.

What's not allowed: silently dropping in the middle. If we accepted it,
it reaches the consumer.

## Manifestations from the 2026-05-12 har-browse session

- Drain-mismatch detector exits hard on mismatch rather than warning
  (`packages/har-browse/src/har_browse.mjs:49-55`).
- `PassThrough` fix chosen over a minimal in-band-sentinel patch
  because the primitive's contract makes the loss class structurally
  inexpressible.
- Held-drain (proposed): on shutdown, emit bare `responseReceived`
  events for in-flight requests rather than silently dropping them.
- chatfs pluckers updated to filter `body != null` at consume time, so
  capture can emit bodyless events without breaking downstream.

## When the principle is wrong

Genuinely never, *within scope* (capture-and-transport of accepted
data). Outside that scope — at boundaries where we choose what to
accept, or at consumers choosing what to render — load-shedding is
routine and correct.
