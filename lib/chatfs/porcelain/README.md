# lib/chatfs/porcelain/ - High-Level User Commands

Porcelain commands provide user-friendly wrappers around plumbing operations.

## What Belongs Here

**User-facing command implementations** that:

- Compose multiple plumbing operations
- Provide nice UX (progress bars, colors, error messages)
- Handle interactive workflows
- Format output for human consumption

These are Python modules/packages that will become CLI commands via packaging
(pyproject.toml entry points).

## Contract

Porcelain commands:

- **May** use interactive features (prompts, colors, progress)
- **May** maintain state across invocations
- **Should** compose plumbing tools for core operations
- **Should** provide helpful error messages

## What Doesn't Belong Here

- Low-level API operations (goes in lib/chatfs/plumbing/)
- Library code (goes in lib/chatfs/ root or other modules)
- Raw JSONL pipelines (that's plumbing's job)

## Status

Not yet implemented. Will be created after Milestone 1 (plumbing tools) is
complete.

## See Also

- [lib/chatfs/plumbing/](../plumbing/) - Low-level tools that porcelain wraps
- [../../../docs/dev/development-plan.md] -
  Implementation roadmap
