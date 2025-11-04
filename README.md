# chatfs - Lazy Filesystem for Chat Conversations

Browse your chat conversations (claude.ai, ChatGPT) as files and directories, with on-demand lazy loading.

## Status

⚠️ **Pre-Alpha:** Not ready for use. Documentation and design phase.

See [STATUS.md] for current development state.

## What This Will Do

```bash
# Use absolute paths anywhere (// prefix)
chatfs-ls //claude.ai/Buck\ Evan/2025-10-29
# conversation-title-1.md
# conversation-title-2.md

# Optional: Initialize cache directory to enable grep and relative paths
chatfs-init ~/my-chats
cd ~/my-chats

# Paths work like filesystem - relative to current directory
chatfs-cat claude.ai/Buck\ Evan/2025-10-29/tshark-filtering.md

# Navigate deeper, paths stay relative
cd claude.ai/Buck\ Evan/2025-10-29/
chatfs-cat tshark-filtering.md
chatfs-ls .

# Search across cached conversations with standard tools
cd ~/my-chats
grep -r "authentication" .
```

**Path conventions:**
- `//provider/...` = Absolute chatfs path (works anywhere)
- Regular paths = Relative to cwd (only works inside `chatfs-init` directory)
- Behaves like normal filesystem navigation

## The Problem

Your conversations on claude.ai are trapped in a web UI. You can't:

- grep across conversation history
- pipe conversations to other tools (analysis, LLMs, scripts)
- use them as data sources
- work with them offline using standard tools

They're in browser tabs, not files - locked away from the Unix toolchain.

**Technical constraints:** The official Anthropic API cannot access claude.ai conversations (separate systems). Browser extensions only do manual one-shot exports. chatfs solves this with lazy filesystem access.

## The Solution

chatfs provides lazy access to conversations via CLI commands, with optional caching:

- **Lazy loading:** Fetch only when you run `chatfs-ls` or `chatfs-cat`, never eagerly
- **Optional caching:** `chatfs-init` creates cache directory where files are written as markdown
- **Staleness tracking:** Cached file mtime tracks when conversations need refresh
- **Standard tools:** Cached files work with grep/cat/ls - no special tools needed
- **Git-like UX:** Familiar init/sync workflow (see [docs/dev/development-plan.md])

## Architecture

Built on **four-layer architecture** (learn-then-abstract approach):

- **M1-CLAUDE (native):** Direct claude.ai API wrapper (unofficial API), outputs raw JSONL
- **M2-VFS (normalized):** Provider-agnostic schema based on M1-CLAUDE findings
- **M3-CACHE (persistence):** Writes markdown files to cache directory, staleness tracking
- **M4-CLI (UX):** Human-friendly commands (`chatfs-init`, `chatfs-ls`, `chatfs-cat`, etc.)

**Key principle:** Learn what the claude.ai API gives us (M1-CLAUDE) before designing normalization (M2-VFS).

**Implementation:** JSONL pipelines under the hood (M1-M3) produce markdown files (M3-CACHE output). Commands work without cache (stdout only) or with cache (persistent files).

See [docs/dev/technical-design.md] for details.

## Contributing

See [HACKING.md] for development setup and architecture.

## Design Documentation

- [docs/dev/design-rationale.md] - Why decisions were made
- [docs/dev/technical-design.md] - How the system works
- [docs/dev/development-plan.md] - Implementation milestones

## Related Projects

This project explores ideas that may feed into:

- **capnshell:** A shell using capnproto for structured data (like nushell)
- **aider-ng:** Modular, composable AI coding assistant (like aider/claude-code)

chatfs serves as a test case for composable tool design.
