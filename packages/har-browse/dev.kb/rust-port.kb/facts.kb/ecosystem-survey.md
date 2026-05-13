# Rust ecosystem — what's available

Research findings (May 2026) on Rust libraries covering the three concerns the port needs.

## Binary acquisition

- **`chrome-for-testing-manager` (lpotthast)** — thin Rust client over Google's [Chrome-for-Testing JSON manifest](https://googlechromelabs.github.io/chrome-for-testing/). Downloads, caches, version-pins. Decoupled from any CDP framework (its `thirtyfour` glue is optional). Single maintainer, v0.5 (2025). Only Rust crate purpose-built for the CfT pipeline.
- Known gap: arm64/macOS coverage less battle-tested than x86_64-linux.

## Launch flags

- **`GoogleChrome/chrome-launcher` (npm, not Rust)** — exports `DEFAULT_FLAGS: ReadonlyArray<string>` at `src/flags.ts`. Pure data, not embedded in launcher logic. ~27 entries. Better-curated than Playwright's list; companion `docs/chrome-flags-for-tools.md` explains each flag. Google-maintained.
- Rust crate `chrome_launcher` (chouzz) — stale verbatim port (2 commits ever). Skip as dependency.

## CDP / target lifecycle

- **`chromiumoxide` (mattsse)** — most-active CDP crate in Rust (~1.3k stars, releases through Feb 2026). Calls `SetAutoAttach { auto_attach: true, flatten: true }` automatically per target *and recursively* on each newly-attached target. Per-session typed event streams. Async/Tokio.
- Known open issues to watch:
  - [#280](https://github.com/mattsse/chromiumoxide/issues/280) — cross-origin iframes return `None` URLs.
  - [#228](https://github.com/mattsse/chromiumoxide/issues/228) — iframe lifecycle navigation timeouts.
  - [#312](https://github.com/mattsse/chromiumoxide/issues/312) — no high-level worker eval API (raw events still surface).

## Non-fits

- `headless_chrome` — 142+ open issues, worse iframe/worker coverage.
- `fantoccini` — WebDriver, no CDP / no response bodies.
- `playwright-rust` (forks) — wraps the Node Playwright driver over RPC; defeats the port's purpose.
- `playhard` / `patchright` — closest "playwright-lite" attempt, but locates pre-installed Chrome (not CfT) and rolls its own CDP (not on chromiumoxide).

## Combination gap

Zero crates on crates.io depend on both `chrome-for-testing-manager` and `chromiumoxide`. The "playwright-lite for Rust" niche is empty; building it locally is justified.
