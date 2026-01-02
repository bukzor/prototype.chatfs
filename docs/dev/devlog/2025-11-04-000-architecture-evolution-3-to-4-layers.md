# Devlog: 2025-11-04

## Focus

Architecture evolution: 3 layers → 4 layers with learn-then-abstract approach.

## Key Insight

Can't design good abstraction (M2-VFS) without understanding concrete case (M1-CLAUDE). Inserting claude-native layer makes this explicit.

## Architecture Change

**Old:** M1 (API) → M2 (Cache) → M3 (CLI)

**New:** M1-CLAUDE (native) → M2-VFS (normalized) → M3-CACHE (persistence) → M4-CLI (UX)

M1-CLAUDE outputs whatever Claude returns (no normalization decisions). M2-VFS designs normalization based on M1-CLAUDE findings.

## Other Decisions

- **Fork representation:** Split into 3 phases across M1/M2/M3 milestones (was conflating distinct questions)
- **Provider abstraction:** New design incubator, depends on M1-CLAUDE findings

## Commits

Session 1:
- docs: evolve architecture from 3 to 4 layers with phased milestones
- docs: Phase 1.25 Step 1 - evolve architecture to 4 layers

Session 2:
- docs: Phase 1.25 complete - milestone renaming and M1-CLAUDE references
- docs: update devlog for 2025-11-04 session 2
- docs: Phase 1.4 complete - integrate open questions understanding
- docs: update devlog for Phase 1.4 completion
- docs: remove commit SHAs from devlog

Session 3:
- refactor: Phase 1.5 Step 1 - restructure to 4-layer architecture
- docs: Phase 1.5 Step 2 - update design-rationale.md with 4-layer terminology
- docs: update TODO.md to reflect Phase 1.5 progress

## Sessions

**Session 1:** Phase 1.25 Step 1 - updated core architecture docs with 4-layer spec

**Session 2:** Phase 1.25 Steps 2-3 complete + Phase 1.4 complete:
- Step 2: Renamed all milestone references (worked backwards M3→M2→M1→M0 to avoid overwrites)
- Step 3: Added M1-CLAUDE quick reference examples to CLAUDE.md, updated README.md architecture overview
- Phase 1.4: Integrated open questions understanding into design-incubators/

**Session 3:** Phase 1.5 in progress - Terminology Cleanup (plumbing/porcelain → layer structure):
- Created lib/chatfs/layer/ directory structure (native/claude/, vfs/, cache/, cli/)
- Moved lib/chatfs/plumbing/ → lib/chatfs/layer/vfs/
- Moved lib/chatfs/porcelain/ → lib/chatfs/layer/cli/
- Created __init__.py files for all layers with docstrings
- Updated pyproject.toml with new command naming (chatfs-claude-*, chatfs-vfs-*, chatfs-cache-*, chatfs)
- Updated CLAUDE.md with 4-layer architecture overview and conventions
- Updated layer README files with M#-TOKEN terminology
- Renamed docs: plumbing-porcelain-split.md → layered-architecture.md
- Renamed docs: porcelain-layer.md → cli-layer.md
- Updated design-rationale.md with 4-layer terminology
- Updated TODO.md to track Phase 1.5 progress

**Session 3 - Phase 1.5 remaining work:**
- HACKING.md updates
- technical-design.md updates (major file)
- Rename milestone-1-plumbing.md → milestone-1-claude-native.md
- Create technical-design/vfs-layer.md
- Update lib/chatfs/__init__.py docstrings
- Update content in layered-architecture.md and cli-layer.md (files renamed but content not yet updated)
- Final verification with git grep

**Session 4:** Phase 1.5 complete - Terminology cleanup finalized:
- Completed remaining doc updates (HACKING.md, technical-design.md, lib/chatfs/__init__.py)
- Renamed milestone-1-plumbing.md → milestone-1-claude-native.md
- Added "Working on Documentation" section to CLAUDE.md (critical: TODO docs need discussion first)
- Updated TODO.md: replaced all bare M0-M4 references with full milestone names
- Clarified: Milestone names (M0-DOCS, M1-CLAUDE, etc.) ≠ Layer names (native/claude, vfs, cache, cli)

**Session 5:** Phase 1.5 final cleanup - Fixed remaining issues identified in TODO.md review:
- Fixed development-plan.md:374 - "porcelain features" → "M4-CLI features"
- Fixed CLAUDE.md:21 - api.py → client.py path reference
- Updated layered-architecture.md content and fixed anchor reference
- Updated cli-layer.md content (title, references, milestone context)
- Updated milestone-1-claude-native.md content (title, references, M1-CLAUDE scope)
- Fixed outdated paths in development-plan.md (lib/chatfs/plumbing → lib/chatfs/layer/vfs)
- Fixed vague "Milestone 1" reference in technical-design.md → "M1-CLAUDE"
- Verified and fixed all anchor references in subdocs
- Updated __init__.py docstrings in cli/ and vfs/ layers
- Updated CLAUDE.md and HACKING.md to use "JSONL layer" terminology
- Verified all remaining plumbing/porcelain references are historical
- Updated TODO.md to mark Phase 1.5 as complete

## Next Session

Phase 2: Validate Level 2 documentation through discussion (design-rationale and technical-design subdocs).

## Links

- [../../../TODO.md] - Phase 1.25 tracking
- [2025-11-02.md] - Previous session
