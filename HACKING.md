# Hacking on chatfs

**Last Updated:** 2025-11-01

## Setup

**Prerequisites:**

- Python 3.10+
- uv (Python package manager)
- Claude.ai session key

**Install dependencies:**

```bash
cd claude-api
uv sync
```

**Get session key:**

1. Log into claude.ai in your browser
2. Open browser DevTools → Application → Cookies
3. Copy the `sessionKey` cookie value
4. Store in `.env`: `CLAUDE_SESSION_KEY=sk-ant-...`

## Project Structure

```
packages/
├── chatfs-fuser/            # Rust: idiomatic wrapper on fuser (FUSE library)
│   ├── src/
│   │   ├── lib.rs
│   │   ├── fuse_impl.rs     # FUSE operations
│   │   ├── filesystem.rs    # Filesystem abstraction
│   │   ├── inode_table/     # Inode management
│   │   └── resolve/         # Path resolution
│   └── examples/            # Static tree, dynamic, procfs demos
├── bukzor.chatgpt-export/   # Python: ChatGPT conversation export/splat
docs/
└── dev/
    ├── design.kb/           # Layered design knowledge
    ├── design-incubators/   # Active design explorations
    ├── background.kb/       # Technology primers
    ├── technical-policy.kb/ # Cross-cutting guidance
    └── devlog/              # Session history
```

See [docs/dev/design.kb/] for
architecture details.

## Running Tests

**Rust (chatfs-fuser):**

```bash
cd packages/chatfs-fuser
cargo test
cargo run --example static_tree  # mount a static demo tree
```

**Python (bukzor.chatgpt-export):**

```bash
cd packages/bukzor.chatgpt-export
uv sync
uv run pytest
```

### Understanding Data Flow

**Pipeline:** BB1 (capture) → BB2 (extract) → BB3 (render)

```
Browser session (Playwright sidecar)
  → capture artifact (HAR/trace)          [BB1]
  → canonical conversation graph (JSON)   [BB2]
  → markdown files + metadata in cache    [BB3]
  → served via FUSE mount
```

See [docs/dev/design.kb/040-design.kb/black-box-decomposition.md] for details.

### Working with the Cache

Sync is explicit — touch a conversation file to trigger refresh. Reads always serve from cache, never hit the network.

See [docs/dev/design.kb/040-design.kb/sync-control-plane.md] for cache structure and sync triggers.

## Architecture

**Rust FUSE daemon** mounts conversations as a filesystem. A **Node/Playwright sidecar** handles browser-driven capture.

**Pipeline:** BB1 (capture) → BB2 (extract) → BB3 (render)

- **BB1 (capture):** Browser automation produces capture artifacts (HAR/trace)
- **BB2 (extract):** Parses artifacts into canonical conversation graph
- **BB3 (render):** Writes markdown files and metadata to cache

**Key properties:**

- **No network on read:** All filesystem reads serve from cache
- **Explicit sync:** User triggers capture (e.g. `touch` a file), never a side effect of reading
- **Provider plugins:** Adding a provider means implementing BB1/BB2 — core is unchanged
- **Work enqueueing:** FUSE handlers stay fast; expensive work runs in a background job queue

See [docs/dev/design-rationale.md] for full reasoning and [docs/dev/design.kb/] for the layered design knowledge.

## Design Decisions

For detailed rationale on architectural choices, see:

- [docs/dev/design-rationale.md] - Core design
  decisions
- [docs/dev/design.kb/] - Layered design knowledge
  (mission → goals → requirements → design)
- [docs/dev/design-incubators/] - Unsolved problems being explored

## Contributing Workflow

1. Read relevant design docs in [docs/dev/design.kb/]
3. Implement changes
4. Test with JSONL layer pipeline
5. Update documentation if needed

**For major changes:**

- Discuss in docs/dev/design-incubators/ first
- Prototype multiple approaches
- Document decision rationale
