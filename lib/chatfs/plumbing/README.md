# lib/chatfs/plumbing/ - Low-Level JSONL Tools

Plumbing commands provide raw, composable access to Claude.ai API operations.

## Contract

Every plumbing tool follows this contract:

**Input:** JSONL on stdin (one JSON object per line) **Output:** JSONL on stdout
(one JSON object per line) **Errors:** Human-readable messages on stderr **Exit
codes:** 0 for success, non-zero for failure

## Design Philosophy

Plumbing tools are:

- **Composable** - Pipe together for complex operations
- **Non-interactive** - No prompts, colors, or progress bars
- **Streaming** - Process input line-by-line when possible
- **Transparent** - Output includes all input fields plus additions

## What Belongs Here

Commands that perform single, well-defined API operations:

- List resources (organizations, conversations)
- Fetch resources (conversation details, messages)
- Transform data (render to different formats)

## What Doesn't Belong Here

- User-friendly CLI wrappers (goes in bin/porcelain/)
- Shared library code (goes in lib/chatfs/)
- Business logic beyond API operations

## See Also

- [../../HACKING.md#adding-a-new-plumbing-tool] - How to add a new
  plumbing tool
- [../../docs/dev/technical-design.md#plumbing-tools] -
  Architecture details
