# chatfs - Lazy Filesystem for Chat Conversations

Browse your chat conversations (claude.ai, ChatGPT) as files and directories, with on-demand lazy loading.

## Status

⚠️ **Pre-Alpha:** Not ready for use. Documentation and design phase.

See [STATUS.md] for current development state.

## What This Will Do

```bash
# Browse conversations by date
chatfs-ls "Buck Evan/2025-10-29"
# conversation-title-1.md
# conversation-title-2.md

# Read a conversation
chatfs-cat "Buck Evan/2025-10-29/tshark-filtering.md"
# (Fetches from claude.ai if stale, shows cached content if fresh)

# Search across conversations
grep -r "authentication" ./chatfs/
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

chatfs creates a lazy filesystem where directories and files appear on-demand:

- **Lazy loading:** Fetch only when accessed, never eagerly
- **Staleness tracking:** Filesystem mtime tracks when conversations need refresh
- **Plain files:** Just markdown - use cat/grep/ls normally when offline
- **Git-like UX:** Familiar init/sync workflow

## Architecture

Built on **plumbing/porcelain** split:

- **Plumbing:** Small JSONL-based tools for raw API operations
- **Porcelain:** (Future) Nice CLI wrappers for human UX

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
