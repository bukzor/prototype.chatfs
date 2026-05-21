# example.com baseline is a transition-only fixture

Pre-record a HAR (or equivalent capture) against `example.com` and
commit as a transition fixture for the har-browse Rust port.

## Scope

- **During Node→Rust transition:** run both implementations against
  this fixture, validate equivalence (alongside `toy_server`).
- **After commit `1300`:** the fixture is no longer routine. The
  toy_server suite suffices for ongoing testing. The fixture file
  may be retired or left in place as historical.

## Why a real-network capture during transition

- More realistic than `toy_server` — touches real HTTPS, real TLS,
  real DNS, real cache behavior.
- Adds confidence during the high-risk transition window where one
  implementation is being validated against the other.

## Why not as a permanent fixture

- Network-dependent oracles are unreliable in CI.
- Pre-recorded HARs drift (TLS certs expire, server fingerprints
  change) — ongoing maintenance tax we don't want post-cutover.
- After cutover there's only one implementation; there's nothing
  to cross-validate against.

## Execution

The capture happens once during the test-conversion / baseline-capture
session (commit `0010` or folded into `0050`). The fixture is committed
as a transition artifact with a planned retirement at `1300`.

Decided 2026-05-21.
