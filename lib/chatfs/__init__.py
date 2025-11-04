"""
chatfs - Lazy filesystem for chat conversations

This package provides programmatic access to chat conversations through a
four-layer architecture:

- M1-CLAUDE (native): Direct Claude API wrapper, outputs raw JSONL
- M2-VFS (normalized): Provider-agnostic JSONL interface
- M3-CACHE (persistence): Filesystem caching with staleness tracking
- M4-CLI (UX): Human-friendly commands with colors and progress

Each layer is independently useful and composable with Unix tools.
"""

__version__ = "0.1.0"
