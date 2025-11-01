# claifs - Lazy Filesystem for Claude.ai Conversations

Browse your claude.ai conversations as files and directories, with on-demand lazy loading.

## Status

⚠️ **Pre-Alpha:** Not ready for use. Documentation and design phase.

See [STATUS.md](STATUS.md) for current development state.

## What This Will Do

```bash
# Browse conversations by date
claifs-ls "Buck Evan/2025-10-29"
# conversation-title-1.md
# conversation-title-2.md

# Read a conversation
claifs-cat "Buck Evan/2025-10-29/tshark-filtering.md"
# (Fetches from claude.ai if stale, shows cached content if fresh)

# Search across conversations
grep -r "authentication" ./claudefs/
```

## The Problem

You have hundreds of conversations on claude.ai, but:

- Official Anthropic API cannot access claude.ai conversations (separate systems)
- Browser extensions only do manual one-shot exports
- No tool exists for incremental, on-demand, CLI-friendly conversation access

## The Solution

claifs creates a lazy filesystem where directories and files appear on-demand:

- **Lazy loading:** Fetch only when accessed, never eagerly
- **Staleness tracking:** Filesystem mtime tracks when conversations need refresh
- **Plain files:** Just markdown - use cat/grep/ls normally when offline
- **Git-like UX:** Familiar init/sync workflow

## Architecture

Built on **plumbing/porcelain** split:

- **Plumbing:** Small JSONL-based tools for raw API operations
- **Porcelain:** (Future) Nice CLI wrappers for human UX

See [docs/dev/technical-design.md](docs/dev/technical-design.md) for details.

## Contributing

See [HACKING.md](HACKING.md) for development setup and architecture.

## Design Documentation

- [docs/dev/design-rationale.md](docs/dev/design-rationale.md) - Why decisions were made
- [docs/dev/technical-design.md](docs/dev/technical-design.md) - How the system works
- [docs/dev/development-plan.md](docs/dev/development-plan.md) - Implementation milestones

## Related Projects

This project explores ideas that may feed into:

- **capnshell:** A shell using capnproto for structured data (like nushell)
- **aider-ng:** Modular, composable AI coding assistant (like aider/claude-code)

claifs serves as a test case for composable tool design.
