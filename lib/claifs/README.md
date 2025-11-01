# lib/claifs/ - Core claifs Library

Python package providing shared functionality for all claifs commands.

## What Belongs Here

**Python modules** that implement core claifs functionality:

- API client wrappers (interface to unofficial-claude-api)
- Cache layer (filesystem operations, mtime tracking)
- Data models (Organization, Conversation, Message)
- Serialization (JSONL encoding/decoding)
- Common utilities

Each module should:

- Be importable: `from claifs.module import function`
- Have no CLI dependencies (no argparse, click, etc.)
- Focus on library-style APIs (return values, not print statements)
- Be testable independently

## What Doesn't Belong Here

- Command-line interface logic
- Main program entry points
- One-time scripts or experiments

## See Also

- [docs/dev/technical-design.md](../../docs/dev/technical-design.md) -
  Architecture overview
