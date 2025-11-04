# CLI Layer Design (M4-CLI)

**Status:** TODO - Will be designed after M1-CLAUDE and M2-VFS are complete

This document will describe:

- User-facing command design (chatfs-ls, chatfs-cat, chatfs-sync, etc.)
- Path parsing and resolution (absolute `//provider/...` vs relative paths)
- Progress bars and terminal UI
- Error messages and help text
- Shell completion
- How M4-CLI wraps M3-CACHE with human-friendly interface

**Note:** Subcommand interface (`chatfs ls` instead of `chatfs-ls`) is a future optional enhancement.

See
[../technical-design.md#cli-layer-m4-cli---future]
for architecture overview.
