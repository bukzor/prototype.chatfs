# Test split — `.spec.mjs` to blackbox CLI; `.test.mjs` to Rust units

For the har-browse port, classify tests by filename extension:

- **`*.spec.mjs`** (Playwright-driven integration tests) — convert to
  blackbox CLI form (subprocess invocation of the har-browse binary,
  assert on JSONL output streams). Same test runs against both Node and
  Rust implementations during transition.
- **`*.test.mjs`** (node:test unit tests for internal seams like
  `src/cache.mjs`, `src/user-agent.mjs`, `src/cdp_to_har.mjs`) — port to
  Rust unit tests inside the new crate. The internal seam still exists
  in Rust; the test moves with it.
- **`tests/typecheck.test.mjs`** — Node-specific; retires at commit
  `1300` along with the Node implementation.

## Why

- Blackbox CLI tests are language-agnostic regression gates — both
  implementations pass the same suite. Validates Rust output against
  Node output without writing a cross-language diff harness (which
  `decision.kb/separate-diagnostic-stream.md` and the testing strategy
  jointly obviate).
- Unit tests need to be re-written in Rust against the new internal
  structures — `cache.rs` doesn't share types with `cache.mjs`.
- The `.spec.mjs` / `.test.mjs` extension distinction already aligns
  with this split empirically — no new convention required.

## Execution

The conversion of `.spec.mjs` → blackbox CLI happens at the inserted
commit `0050`; see
`decision.kb/test-conversion-precedes-port-scaffold.md`. Per-test
unit-port to Rust happens as part of the relevant phase-2 commit (e.g.,
the cache port commit ports `cache.test.mjs` to a Rust `#[test]` in
`cache.rs`).

Decided 2026-05-21.
