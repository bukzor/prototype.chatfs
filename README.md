# chatfs - Lazy Filesystem for Chat Conversations

Browse your chat conversations (claude.ai, ChatGPT) as files and directories, with on-demand lazy loading.

## Status

⚠️ **Pre-Alpha:** Not ready for use. Documentation and design phase.

## What This Will Do

```bash
# Conversations appear as a mounted filesystem
ls /mnt/llmfs/claude.ai/Buck\ Evan/2025-10/
# conversation-title-1.md
# conversation-title-2.md

# Standard tools just work
cat /mnt/llmfs/claude.ai/Buck\ Evan/2025-10/tshark-filtering.md
grep -r "authentication" /mnt/llmfs/

# Sync is explicit — touch a file to update it
touch /mnt/llmfs/claude.ai/Buck\ Evan/2025-10/conversation-xyz.md
```

## The Problem

Your conversations on claude.ai are trapped in a web UI. You can't:

- grep across conversation history
- pipe conversations to other tools (analysis, LLMs, scripts)
- use them as data sources
- work with them offline using standard tools

They're in browser tabs, not files - locked away from the Unix toolchain.

**Technical constraints:** The official Anthropic API cannot access claude.ai conversations (separate systems). Browser extensions only do manual one-shot exports. chatfs solves this with lazy filesystem access.

## The Solution

chatfs mounts conversations as a FUSE filesystem, with browser-driven capture:

- **FUSE mount:** Conversations appear as files at `/mnt/llmfs/<provider>/`
- **No network on read:** All reads serve from cache — grep, ls, editors work instantly
- **Explicit sync:** User triggers capture via control files, never as a side effect
- **Browser-driven capture:** Playwright sidecar attaches to your browser session
- **Standard tools:** Mounted files work with grep/cat/ls/find — no special tools needed

## Architecture

**Rust FUSE daemon** mounts conversations as a filesystem. A **Node/Playwright sidecar** handles browser-driven capture.

**Pipeline:** BB1 (capture) → BB2 (extract) → BB3 (render)

- **BB1 (capture):** Browser automation produces capture artifacts (HAR/trace)
- **BB2 (extract):** Parses artifacts into canonical conversation graph
- **BB3 (render):** Writes markdown files and metadata to cache

**Key principles:**
- Reads serve from cache — no network on read
- Sync is always user-triggered (control files, not side effects)
- Providers are plugins — adding one requires only BB1/BB2 implementation

See [docs/dev/design.kb/] for the full layered design knowledge.

## Contributing

See [HACKING.md] for development setup and architecture.

## Design Documentation

- [docs/dev/design.kb/] - Layered design knowledge (mission → goals → requirements → design). Decision rationale lives inline with the relevant entries (e.g. `040-design.kb/capture-pattern.md`, `040-design.kb/user-interface.md`).

## Related Projects

This project explores ideas that may feed into:

- **capnshell:** A shell using capnproto for structured data (like nushell)
- **aider-ng:** Modular, composable AI coding assistant (like aider/claude-code)

chatfs serves as a test case for composable tool design.
