# Defer implementation work behind a precise runtime assertion

When implementation work can be deferred behind a known limitation,
add a runtime (or test-time) assertion that detects when reality
crosses into the limitation's scope.

## The pattern

For each known limitation:

1. Record it as a deferred future-work item.
2. Add an assertion (runtime or test-time) precise enough to fire only
   when the deferred work becomes necessary.
3. When the assertion fires, the deferred work moves to active.

Trades pre-emptive code for monitoring. Ensures we don't pay for
solutions to problems we may never hit, but also ensures that when
we *do* hit the problem we discover it at the precise moment of
encounter, not at the moment of debugging a downstream symptom.

## Examples

Three live instances in `packages/rs-playwright-lite/` (per the Rust
port):

- **Flag drift.** Vendor records the upstream SHA; a periodic check
  queries GitHub for the latest commit touching the vendored file.
  Failure if it post-dates `UPSTREAM_SHA`.
- **Iframe-URL gap (chromiumoxide #280).** On
  `Target.attachedToTarget`, if `targetInfo.type == "iframe"`, assert
  non-empty `targetInfo.url`. Asserts in real captures.
- **Chrome version drift.** After launch, compare
  `Browser.getVersion` product string to the CfT-fetched version.
  Warn or fail on mismatch.

(Full descriptions:
`packages/har-browse/dev.kb/rust-port.kb/decisions.kb/assertion-strategy.md`,
the file this principle was promoted from.)

## Failure mode this guards against

Deferred limitations forgotten until they cause a production issue
with no proximate cause. The assertion is a tripwire that converts
"silent drift" into "loud, located failure."

## Provenance

Promoted from
`packages/har-browse/dev.kb/rust-port.kb/decisions.kb/assertion-strategy.md`.
The original was classified as a decision (specific fork choice); it's
actually a generalizable principle, because:

- It applies beyond the three current instances.
- Future deferred-limitation moments will benefit from following the
  same pattern.
- The original "the pattern" section is itself the principle statement.

Surfaced 2026-05-21 during har-browse Rust-port meta-planning.
