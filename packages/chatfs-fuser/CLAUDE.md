# chatfs-fuser

Idiomatic wrapper around the [`fuser`](https://docs.rs/fuser) crate.

## Building

```bash
cargo check -p chatfs-fuser
cargo test -p chatfs-fuser
cargo build -p chatfs-fuser
```

## Conventions

- Workspace member under `packages/` (see root `Cargo.toml`)
- Rust 2024 edition
