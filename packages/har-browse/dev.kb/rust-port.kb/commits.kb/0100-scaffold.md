# Commit 0100: scaffold

## What
Scaffold the `playwright-lite` crate in the Cargo workspace.

## Plan
- Add `packages/playwright-lite/{Cargo.toml,src/lib.rs}`.
- Register as workspace member in root `Cargo.toml`.
- `lib.rs`: empty `pub mod` declarations for `binary`, `flags`, `launch` (placeholders).
- No external deps yet.

## Refs
- `../decisions.kb/crate-architecture.md`

## Outcomes
- [ ] `cargo build -p playwright-lite` passes
- [ ] `cargo test -p playwright-lite` runs zero tests cleanly
- [ ] `cargo build` from workspace root still passes (no regression)
