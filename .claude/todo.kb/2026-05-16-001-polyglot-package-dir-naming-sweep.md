---
anthropic-skill-ownership: llm-subtask
depends:
  - 2026-05-16-000-execute-rust-port-kb-scope-refactor.md
---

# Polyglot package directory naming — sweep existing packages

**Priority:** Low (cleanup; deferred per Q4 resolution)
**Complexity:** Medium (mechanical renames + Cargo.toml + pyproject.toml + import-path updates + grep across project for path strings)
**Context:** Q4 of the rust-port kb scope refactor (2026-05-15) adopted a `rs-`/`py-`/`js-` directory-prefix convention for polyglot legibility, applied to new packages immediately. Existing packages remain bare for the moment; this todo tracks bringing them into convention.

## Problem Statement

`packages/` is intended as a polyglot concept. The Q4 convention is: directory prefix names the toolchain (`rs-`, `py-`, `js-`); the crate / package name in `Cargo.toml` / `pyproject.toml` / `package.json` stays bare.

Existing inconsistent state (pre-sweep):

- `packages/bukzor.chatgpt-export/` — Python; no prefix
- `packages/chatfs/` — Python; no prefix
- `packages/chatfs-fuser/` — Rust; no prefix
- `packages/har-browse/` — Node; no prefix (slated for retirement at rust-port commit 1300 anyway)

New (rust-port-introduced) packages will be:

- `packages/rs-har-browse/` — replaces `packages/har-browse/` at 1300
- `packages/rs-playwright-lite/` — new

## Proposed Solution

Rename each existing package directory to the prefixed form:

- `packages/bukzor.chatgpt-export/` → `packages/py-bukzor.chatgpt-export/`
- `packages/chatfs/` → `packages/py-chatfs/`
- `packages/chatfs-fuser/` → `packages/rs-chatfs-fuser/`
- `packages/har-browse/` — let it die at commit 1300; do not rename in flight.

## Per-package work

For each rename:

1. `git mv` the directory.
2. Update root `Cargo.toml` workspace members (Rust packages).
3. Update root `pnpm-workspace.yaml` / `pyproject.toml` / `uv.lock` workspace declarations (per toolchain).
4. Grep for the old path string across the repo (docs, scripts, READMEs, `.claude/focus.md` files, CLAUDE.md files, devlogs).
5. Update each occurrence.
6. Verify build (`cargo build`, `uv sync`, etc.) still passes.
7. Verify tests still pass.
8. Commit (one per rename, to keep diffs reviewable).

## Sequencing

Do AFTER `2026-05-16-000-execute-rust-port-kb-scope-refactor.md` lands (the workspace ADR
recording the convention is created there).

Order within sweep: do `chatfs-fuser` first (fewest dependents), then the Python ones.

## Acceptance

- [ ] Workspace ADR `2026-MM-DD-polyglot-package-dir-naming.md` exists (created by execute-rust-port todo)
- [ ] All non-retiring existing packages renamed
- [ ] Workspace manifests (`Cargo.toml`, `pyproject.toml`, etc.) updated
- [ ] No grep hits for old paths (other than in devlog / commit history, which is OK)
- [ ] All builds and tests green
- [ ] No symlinks created — direct renames only

## Out of scope

- Renaming `har-browse/` in flight (will be removed at rust-port commit 1300; don't churn it).
- Inventing prefixes for non-language toolchains (no `bash-`, `make-`, etc. — only language toolchains the convention covers).
- Buck2 BUCK-file changes (separate future work; see `ideas.kb/`).
