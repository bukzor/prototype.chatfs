# Commit 1300: retire-node

## What
Delete the Node implementation; update docs; sweep the transient kb.

## Plan
- Delete `src/har_browse.mjs`, `src/capture.mjs`, `package.json` entries, node_modules-pinning.
- Update `packages/har-browse/CLAUDE.md` and any READMEs: Rust as entry point.
- Check root `CLAUDE.md` for Node BB1 capture references; update or remove.
- Sweep transient kb: promote anything worth preserving out of `rust-port.kb/`, then `rm -rf dev.kb/rust-port.md dev.kb/rust-port.kb/`.

## Refs
- `../rust-port.md` (end state)
- `../CLAUDE.md` (rust-port.kb lifecycle)
- `../procedures.kb/consume-handoff.md` (promote-vs-delete heuristic; applies to any residual handoffs)

## Outcomes
- [ ] `src/har_browse.mjs` and `src/capture.mjs` removed
- [ ] `package.json` Node-driver entries removed (or whole `package.json` removed if no longer needed)
- [ ] `packages/har-browse/CLAUDE.md` reflects Rust as the entry point (no stale Node references)
- [ ] Root `CLAUDE.md` BB1 references checked; updated where stale
- [ ] End-to-end pipeline (toy_server → har-browse-rs → toy_pluck.sh) is green
- [ ] `handoffs.kb/` is empty (all hand-offs consumed or promoted; per `consume-handoff.md`)
- [ ] Durable contracts (`dev.kb/jsonl-schema.md`, BARRIER/causal-watermark docs) present at `dev.kb/` root
- [ ] `dev.kb/rust-port.md` and `dev.kb/rust-port.kb/` removed
