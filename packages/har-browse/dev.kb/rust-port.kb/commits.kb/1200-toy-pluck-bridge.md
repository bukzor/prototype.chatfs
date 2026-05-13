# Commit 1200: toy-pluck-bridge

## What
Wire `toy_pluck.sh` to consume Rust output. Node and Rust coexist for the transition window.

## Plan
- Update `toy_pluck.sh` to invoke `har-browse-rs` (with a flag to select Node vs Rust during transition, if useful).
- Both implementations remain in tree until `1300`.

## Refs
- `../facts.kb/current-architecture.md` (toy_pluck.sh interface)

## Outcomes
- [ ] `toy_pluck.sh` end-to-end against Rust `har-browse-rs` produces a valid JSON `/api/conversation` body
- [ ] `toy_pluck.sh` end-to-end against Node implementation still produces the same body (coexistence verified)
- [ ] Mode-selector (flag, env var, or default) for choosing Node vs Rust is documented in the script's usage output
