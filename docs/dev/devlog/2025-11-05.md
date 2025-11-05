# Devlog: 2025-11-05

## Focus

Phase 2: Breadth-first documentation validation (Level 0 → Level 1).

## What Happened

### Completed

**Session 1: README.md and command consistency**

- Updated README.md command examples for consistency
- Added explicit path convention documentation (`//provider/...` = absolute, relative paths work like filesystem)
- Showed filesystem-like navigation (cd into directories, use relative paths)
- Global scan and fix for command naming consistency across all docs:
  - M4-CLI commands: `chatfs-ls`, `chatfs-cat`, `chatfs-sync` (not subcommands)
  - Updated development-plan.md, technical-design.md, cli-layer.md, lib/chatfs/layer/cli/README.md
  - Noted subcommand interface (`chatfs ls`) is future optional enhancement
- Files updated: README.md, CLAUDE.md, TODO.md, docs/dev/{development-plan,technical-design}.md, docs/dev/technical-design/cli-layer.md, lib/chatfs/layer/cli/README.md

**Session 2: design-rationale.md validation**

- Reviewed design-rationale.md - solid, no changes needed
- Problem statement clear, four core decisions well-explained with alternatives and tradeoffs
- Lazy filesystem section correctly describes explicit CLI calls vs FUSE

**Session 3: technical-design.md validation and fixes**

- Fixed architecture diagram to match data flow (reversed from dependency direction to data flow direction)
- Added inter-layer labels: "HTTP/TLS", "Raw API responses", "Virtual FS", "Lazy, Cached FS"
- Removed "Shared Libraries" box from diagram (conflated layers, incorrect module naming)
- Fixed layer vs milestone naming globally in technical-design.md:
  - Layers named by directory: `native/claude`, `vfs`, `cache`, `cli`
  - Milestones named: M1-CLAUDE, M2-VFS, M3-CACHE, M4-CLI
  - Added "Layer:" field to component headers
  - Updated all references: "M2-VFS layer" → "`vfs` layer", etc.
- Reorganized component sections:
  - Moved ClaudeClient to `native/claude` section
  - Moved models to `vfs` section
  - Moved CacheManager to `cache` section
  - Each layer owns its own utilities/models
- Removed redundant "Future Considerations" M2-M4 sections (content already covered in Components)
- Renamed "Future Considerations" → "Beyond the Four Layers (M5-WRITE+)"
- Fixed "Read this when" to use code-styled layer names

**Session 4: CLAUDE.md clarification**

- Clarified native family vs native/claude tension:
  - "native family" = umbrella term for all provider-specific layers
  - `native/claude` = specific Claude implementation (M1-CLAUDE)
  - Listed future: `native/chatgpt`, `native/gemini`

**Session 5: TODO.md updates**

- Added two global cleanup tasks for separate sessions:
  1. Fix layer naming globally (scan for milestone-named layers)
  2. Remove excessive bolding (use headers and emdashes instead)
- Updated Phase 2 progress tracking

**Session 6: design-incubators reorganization**

- Renamed incubator directories for clarity:
  - `provider-abstraction/` → `chat-provider-normalization/`
  - `provider-abstraction-strategy/` → `multi-domain-support/`
- Clarified distinct scopes:
  - **chat-provider-normalization/**: Technical problem - how to normalize across chat LLM providers (Claude/ChatGPT/Gemini). Blocks M2-VFS implementation.
  - **multi-domain-support/**: Strategic problem - whether to expand beyond chat providers to Linear/GitHub/AWS/GCP. Long-term architecture decision.
- Updated all cross-references (7 in fork-representation/, plus technical-design.md, development-plan.md)
- Fixed outdated "M2-API" terminology → "M2-VFS" throughout multi-domain-support/
- Added cross-references between the two incubators
- Updated design-incubators/README.md with both entries

## Decisions Made

### Layer Naming Convention

**Decision:** Layers are named by their directory path, not by milestone names.

**Naming:**
- Layer names: `native/claude`, `vfs`, `cache`, `cli`
- Milestone names: M1-CLAUDE, M2-VFS, M3-CACHE, M4-CLI (development phases)
- `native` acceptable as shorthand for the native family

**Usage:**
- ✓ "the `vfs` layer normalizes across providers"
- ✓ "implemented in milestone M1-CLAUDE"
- ✗ "the M1-CLAUDE layer" (wrong - that's a milestone, not a layer)

**Rationale:** Milestones are temporary development phases. Layers are permanent architecture. Conflating them causes confusion.

### Command Naming and Paths

**Decision:** M4-CLI uses hyphenated commands (`chatfs-ls`, `chatfs-cat`) with filesystem-like path semantics.

**Path conventions:**
- `//provider/...` = Absolute chatfs path (works anywhere)
- Regular paths = Relative to cwd (only works inside `chatfs-init` directory)
- Navigation works like filesystem: `cd` into directories, paths relative to cwd

**Subcommand interface** (`chatfs ls`) is a future optional enhancement, not the initial design.

**Rationale:** Hyphenated commands are simpler to implement initially. Subcommands require more infrastructure. Deferring optimization.

## Commits

- docs: update command examples for consistency with path conventions
- docs: update TODO.md to reflect Phase 2 progress
- docs: reverse architecture diagram to match data flow
- docs: fix layer vs milestone naming in technical-design.md
- docs: fix remaining layer naming references in technical-design.md
- docs: fix redundancy and styling in technical-design.md
- docs: clarify native family vs native/claude in CLAUDE.md
- docs: add global cleanup tasks to TODO.md
- docs: update TODO.md Phase 2 progress
- docs: reorganize design-incubators with clear scopes

## Next Session

Continue Phase 2:
- Move to Level 2: subdoc validation through discussion
- Start with design-rationale/ subdocs or technical-design/ subdocs

**Known work items:**
1. Global layer naming scan and fix (separate session)
2. Remove excessive bolding from docs (separate session)

## Links

- [../../../TODO.md] - Phase 2 tracking
- [2025-11-04.md] - Previous session
