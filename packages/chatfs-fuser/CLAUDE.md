# chatfs-fuser

Idiomatic wrapper around the [`fuser`](https://docs.rs/fuser) crate.

## Building

```bash
cargo check -p chatfs-fuser
cargo test -p chatfs-fuser
cargo build -p chatfs-fuser
```

## Design context

Project-level docs (paths relative to repo root):

- `docs/technical-policy.kb/` — design rules (stateless re-evaluation, POSIX error semantics, inode lifecycle)
- `docs/design-incubators/dynamic-routing/` — lazy VFS design sketch and analysis

## Conventions

- Workspace member under `packages/` (see root `Cargo.toml`)
- Rust 2024 edition
