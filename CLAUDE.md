--- # workaround: anthropics/claude-code#13003
depends:
  - Skill(llm-collab)
  - Skill(llm-subtask)
  - Skill(llm-kb)
  - Skill(llm-design-kb)
git-caution: personal
---

# chatfs - Development Guide for Claude

## Architecture Overview

chatfs provides lazy filesystem access to chat conversations (claude.ai, ChatGPT). Polyglot Python/Rust repo.

**Pipeline:** Browser-driven capture (BB1) → extraction (BB2) → rendering (BB3). See `docs/dev/design.kb/040-design.kb/black-box-decomposition.md`.

**Rust side:** `chatfs-fuser` crate — FUSE filesystem daemon. Cargo workspace at repo root.

**Node/Playwright side:** Browser automation for HAR capture (BB1). See `packages/har-browse/`.

**Why JSONL:** Streaming-friendly, works with Unix tools now, easy capnproto migration later.

## What Works Today

The README describes the destination (FUSE mount, `chatfs` command); neither
exists yet, and `packages/chatfs/`'s CLI is a stub. The pipeline that actually
runs end-to-end — capture a conversation URL, get markdown on disk, all three
providers — is the hand-driven CLI in
`docs/dev/design-incubators/chatfs-cli-mockup/`.

**To run anything, read `docs/how-to-chatfs.md` first.** It has the commands,
setup, output layout, and failure modes. Don't reconstruct them from source.

## Design Knowledge

- `docs/dev/design.kb/` — Layered design.kb (mission → goals → requirements → design → future work)
- `docs/dev/background.kb/` — Technology primers, prior art
- `docs/dev/technical-policy.kb/` — Cross-cutting normative guidance (7 invariants, opaque extractor boundary, etc.)
- `docs/dev/design-incubators/` — Active design explorations with prototypes

For how to create and maintain design knowledge, see `Skill(llm-design-kb)`.

## Key Files

- `packages/` — Polyglot workspace members (Python packages, Rust crates)
- `docs/dev/design.kb/` — Project-level design knowledge (design.kb)
- `packages/har-browse/` — BB1 capture (Playwright HAR)
- `docs/dev/design-incubators/chatfs-cli-mockup/` — **the working pipeline** (capture → splat → render, all three providers)
- `docs/dev/design-incubators/fuser-vfs/` — FUSE filesystem learning
- `docs/dev/design-incubators/fork-representation/` — Fork representation investigation
- `docs/dev/devlog/` — Session narrative history

## Conventions

**JSONL format:**

- One JSON object per line
- UTF-8 encoding
- Streaming-friendly (process line-by-line)
- Works with jq

**JSONL layer contract:**

- Read JSONL from stdin
- Write JSONL to stdout (except render-md → markdown)
- Log errors to stderr
- Exit 0 on success
- No terminal dependencies (colors, progress bars)
