# Commit 0300: vendor-flags

## What
Vendor `chrome-launcher` `DEFAULT_FLAGS` + add upstream-drift assertion.

## Plan
- Create `playwright-lite/src/flags.rs` with `pub const DEFAULT_FLAGS: &[&str] = &[…]` copied verbatim from `chrome-launcher/src/flags.ts`.
- Record `pub const UPSTREAM_SHA: &str = "…"` (source commit at vendor time).
- Drift test (gated on `network-tests` feature) queries GitHub for latest commit touching `chrome-launcher/src/flags.ts`.

## Refs
- `../facts.kb/ecosystem-survey.md` (chrome-launcher upstream)
- `../decisions.kb/dependency-choices.md`
- `../decisions.kb/assertion-strategy.md`

## Outcomes
- [ ] `DEFAULT_FLAGS` array compiles and is `pub`-accessible
- [ ] `UPSTREAM_SHA` matches the commit the array was copied from
- [ ] Drift test passes against pinned `UPSTREAM_SHA`
- [ ] On simulated drift (test with stale SHA), test fails with a message naming `decisions.kb/assertion-strategy.md` and the deferred CI-diff work
