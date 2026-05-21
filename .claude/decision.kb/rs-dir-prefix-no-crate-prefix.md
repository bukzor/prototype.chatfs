# `rs-` prefix on directories; no prefix on crate names

For the two Rust crates created during the har-browse port:

| Aspect | Name |
|---|---|
| Directory | `packages/rs-playwright-lite/`, `packages/rs-har-browse/` |
| Crate (`Cargo.toml` name) | `playwright-lite`, `har-browse` |

## Why

- The workspace is polyglot (Python, Rust, Node). `rs-` prefix on
  directory names disambiguates language at the filesystem level —
  matches the existing pattern (`chatfs-fuser` aside, future
  language-specific subprojects benefit from explicit prefixes).
- Crate names follow Rust ecosystem conventions and don't need the
  prefix once you're inside the crate. Avoids redundant `rs-` showing
  up in `Cargo.toml`, doc links, `use` statements, etc.

Decided 2026-05-21. Pending application at commit `0100` and the
skeleton-creation session.
