# lib/chatfs/layer/vfs/ - M2-VFS Normalized Layer

VFS commands provide normalized, composable JSONL operations across providers (Claude, ChatGPT, etc.).

## Contract

Every VFS tool follows this contract:

**Input:** JSONL on stdin (one JSON object per line) **Output:** JSONL on stdout
(one JSON object per line) **Errors:** Human-readable messages on stderr **Exit
codes:** 0 for success, non-zero for failure

## Design Philosophy

VFS tools are:

- **Composable** - Pipe together for complex operations
- **Non-interactive** - No prompts, colors, or progress bars
- **Streaming** - Process input line-by-line when possible
- **Transparent** - Output includes all input fields plus additions

## What Belongs Here

Normalized operations that work across providers:

- List resources (organizations, conversations) in normalized schema
- Fetch resources (conversation details, messages) in normalized schema
- Transform data (render to different formats)

Takes `--provider` flag (claude, chatgpt, etc.) and outputs provider-agnostic JSONL.

## What Doesn't Belong Here

- Provider-specific code (goes in layer/native/claude/, layer/native/chatgpt/)
- User-friendly CLI wrappers (goes in layer/cli/)
- Persistent storage (goes in layer/cache/)

## Layer Dependencies

M2-VFS sits between:
- **M1-CLAUDE** (native layer) - provides raw API data
- **M3-CACHE** (cache layer) - adds persistence

## See Also

- [../../../HACKING.md#vfs-layer] - How to work with VFS layer
- [../../../docs/dev/technical-design.md#m2-vfs-layer] - Architecture details
