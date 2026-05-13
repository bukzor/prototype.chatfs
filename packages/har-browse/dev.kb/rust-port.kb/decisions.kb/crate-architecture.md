# Decision: two-crate split

`playwright-lite` (foundation) + `har-browse-rs` (consumer) instead of a single crate.

## Rationale

- **Forced contract.** A crate boundary forces us to freeze "what a CDP-capable Chrome session looks like" early, separately from "how har-browse uses it."
- **Independent testing.** `playwright-lite` testable against any fixture (`toy_server/`); `har-browse-rs` testable against the JSONL contract.
- **Reusable substrate.** If something else in chatfs ever needs a CDP-capable Chrome session, `playwright-lite` is ready. No design effort spent on that future, but the option exists.

## Names

Working names: `playwright-lite`, `har-browse-rs`. Final names decided at commit `0100`.

## Workspace placement

Cargo workspace at repo root already exists (`chatfs-fuser` is there). Add both crates as workspace members under `packages/` to match the existing polyglot layout.

## Out of scope

Publishing `playwright-lite` to crates.io. Defer until the crate has stabilized in-tree usage.
