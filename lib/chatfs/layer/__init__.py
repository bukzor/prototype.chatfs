"""chatfs layered architecture.

Four layers:
- native/: Provider-specific wrappers (M1-CLAUDE, M1-CHATGPT, etc.)
- vfs/: Normalized virtual filesystem layer (M2-VFS)
- cache/: Persistent storage with staleness tracking (M3-CACHE)
- cli/: Human-friendly UX commands (M4-CLI)
"""
