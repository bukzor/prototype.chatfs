# Commit 0700: skeleton

## What
Scaffold `har-browse-rs` crate; depend on `playwright-lite`; smoke launch + exit.

## Plan
- Add `packages/har-browse-rs/{Cargo.toml,src/main.rs}`.
- Register as workspace member.
- `main.rs`: parse `--profile <name>` argv, call `playwright_lite::launch(profile_dir)`, await SIGINT or window close, exit cleanly.

## Refs
- `../decisions.kb/crate-architecture.md`
- `0400-launch.md`

## Outcomes
- [ ] `cargo build -p har-browse-rs` passes
- [ ] Smoke test against `toy_server/`: binary launches Chrome, lets toy_server render, exits with status 0 on window close
- [ ] `--profile` argv flag resolves to a path under `${XDG_CACHE_HOME:-$HOME/.cache}/har-browse/profile/<name>` (full XDG logic deferred to `1100`)
