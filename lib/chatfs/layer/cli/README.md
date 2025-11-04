# lib/chatfs/layer/cli/ - M4-CLI Human-Friendly Commands

CLI commands provide user-friendly wrappers around cache/VFS operations.

## What Belongs Here

**User-facing command implementations** that:

- Wrap M3-CACHE layer with path-based interface
- Provide nice UX (progress bars, colors, error messages)
- Handle interactive workflows
- Format output for human consumption

These are Python modules/packages that will become CLI commands via packaging
(pyproject.toml entry points). Commands like `chatfs-ls`, `chatfs-cat`, `chatfs-sync`.

**Note:** Subcommand interface (`chatfs ls`) is a future optional enhancement.

## Contract

CLI commands:

- **May** use interactive features (prompts, colors, progress)
- **May** maintain state across invocations
- **Should** wrap M3-CACHE layer for core operations
- **Should** provide helpful error messages
- **No JSONL** - output for human consumption (not piping)

## What Doesn't Belong Here

- JSONL operations (goes in layer/vfs/ or layer/cache/)
- Provider-specific code (goes in layer/native/)
- Library code (goes in lib/chatfs/ root or other modules)

## Layer Dependencies

M4-CLI sits on top of:
- **M3-CACHE** (cache layer) - provides persistent storage
- Indirectly uses M2-VFS and M1-CLAUDE through cache layer

## Status

Not yet implemented. Will be created after M3-CACHE is complete.

## See Also

- [../cache/] - Cache layer that CLI wraps
- [../../../docs/dev/development-plan.md#m4-cli] - Implementation roadmap
