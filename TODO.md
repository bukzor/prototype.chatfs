# M0 Documentation Completion - TODO

**Project:** chatfs - lazy filesystem for chat conversations
**Milestone:** M0 (Documentation Phase) - see [docs/dev/development-plan.md#milestone-0-documentation-phase]
**Current Status:** See [STATUS.md]
**Goal:** LLM-resumable documentation foundation before M1 implementation
**Approach:** Breadth-first - build solid foundation (L1) before details (L3/4)

**Structure fixed:** Files moved, renamed, all links updated (2025-11-02)

## Documentation Dependency Tree

**Strategy:** Breadth-first traversal - complete each level before descending to next

```
Level 0 (Root): chatfs - What is this project?
│
├─ Level 1: Foundational Concepts (Phase 1)
│  ├─ Problem Space (why this exists)
│  ├─ Design Philosophy (guiding principles)
│  ├─ System Architecture (high-level structure)
│  └─ Open Questions (known unknowns)
│
├─ Level 2: Elaborate Each Foundation (Phase 2)
│  │
│  Problem Space branches:
│  ├─ Chat history trapped in web UIs
│  ├─ Need Unix tool composability
│  └─ Want local filesystem access (Obsidian, grep, etc)
│  │
│  Design Philosophy branches:
│  ├─ Plumbing/Porcelain split (why)
│  ├─ JSONL choice (why)
│  ├─ Lazy loading strategy (why)
│  └─ Unofficial APIs (why)
│  │
│  Architecture branches:
│  ├─ Data Flow (overall pipeline)
│  ├─ Component Structure (what parts exist)
│  └─ Data Formats (how things talk)
│  │
│  Open Questions branches:
│  ├─ Fork representation (blocked M3)
│  └─ Write operation semantics
│
└─ Level 3: Component Details (Phase 3 - mostly deferred to M1)
   │
   Data Flow branches:
   ├─ Provider → Models → JSONL pipeline
   └─ Cache interaction points
   │
   Component Structure branches:
   ├─ API/Provider Layer
   ├─ Cache Layer
   ├─ Plumbing Layer
   └─ Porcelain Layer
   │
   Data Formats branches:
   ├─ JSONL schemas
   └─ Markdown format

   Level 4: Implementation Specifics (deferred to M1+)
   │
   API Layer branches:
   ├─ Provider interface definition
   ├─ Claude provider specifics
   └─ ChatGPT provider specifics
   │
   Cache Layer branches:
   ├─ Directory structure
   ├─ Staleness checking
   └─ Lazy stub creation
   │
   Plumbing Layer branches:
   ├─ Tool contract (stdin/stdout)
   ├─ list-orgs implementation
   ├─ list-convos implementation
   ├─ get-convo implementation
   └─ render-md implementation
   │
   JSONL Schemas branches:
   ├─ Org record fields
   ├─ Conversation record fields
   └─ Message record fields
```

## Where Topics Live

All topics have natural homes in our doc structure:

| Topic Layer                  | Doc Location                                             | ✓   |
| ---------------------------- | -------------------------------------------------------- | --- |
| L0: Project concept          | README.md                                                | ✓   |
| L1: Problem Space            | design-rationale.md (intro)                              | ✓   |
| L1: Design Philosophy        | design-rationale.md (core decisions)                     | ✓   |
| L1: Architecture             | technical-design.md#architecture                         | ✓   |
| L1: Open Questions           | design-incubators/                                       | ✓   |
| L2: Rationale details        | design-rationale/rationale/\*.md                         | ✓   |
| L2: Architecture elaboration | technical-design.md (sections)                           | ✓   |
| L2: Data Formats             | technical-design/\*.md                                   | ✓   |
| L3: Component interfaces     | technical-design/\*.md subdocs                           | ✓   |
| L4: Implementation specifics | technical-design/_.md OR development-plan/milestone-_.md | ✓   |

**One gap identified:** JSONL schemas may need a new `technical-design/jsonl-schemas.md` (stub in Phase 3)

## Phase 1: Complete Level 1 (Foundation - Main Doc Bodies)

**Goal:** Solid foundation in main docs before elaborating subdirectories

- [x] Add Problem Statement to `design-rationale.md`

  - Why chatfs exists
  - What problem it solves
  - Current state of alternatives

- [ ] Strengthen Design Philosophy in `design-rationale.md`

  - Summarize the four key decisions (plumbing/porcelain, JSONL, lazy loading, unofficial APIs)
  - Brief rationale for each (1-2 sentences + link to subdoc)

- [ ] Review `technical-design.md` System Architecture section

  - Ensure architecture overview is clear
  - Verify component responsibilities are stated
  - Check data flow description exists

- [ ] Review `design-incubators/README.md`
  - Ensure fork-representation problem is listed
  - Add any other open questions discovered

## Phase 2: Complete Level 2 (Elaborate Foundations - Subdirectories)

**Goal:** Flesh out rationale and design subdocs with detail

### Design Rationale Subdocs

- [ ] Populate `design-rationale/plumbing-porcelain-split.md`

  - Remove TODOs
  - Add concrete examples
  - Document alternatives considered

- [ ] Create `design-rationale/jsonl-choice.md`

  - Why JSONL over other formats (CSV, msgpack, JSON arrays, capnproto)
  - Streaming benefits
  - jq composability
  - Future migration path

- [ ] Populate `design-rationale/lazy-filesystem.md`

  - Remove TODOs
  - Explain lazy vs eager tradeoffs
  - Document staleness handling strategy

- [ ] Populate `design-rationale/unofficial-api.md`
  - Remove TODOs
  - Document risks/mitigations
  - Explain why official API insufficient

### Technical Design Subdocs

- [ ] Review `technical-design/provider-interface.md` (was api-reference.md)

  - Clarify it's about wrapping unofficial-claude-api
  - Document provider abstraction concept
  - Stub ChatGPT provider for M2

- [ ] Review `technical-design/cache-layer.md` (was caching-strategy.md)

  - Clarify M1 scope (simple writes only)
  - Mark staleness checking as deferred
  - Mark lazy stubs as deferred

- [ ] Review `technical-design/porcelain-layer.md` (was porcelain-design.md)

  - Mark as mostly deferred post-M1
  - Clarify examples of future porcelain commands

- [ ] Review `technical-design/markdown-format.md`
  - Ensure format is well-specified
  - Document frontmatter fields
  - Show examples

## Phase 3: Stub Level 3 (Implementation Details - Defer to M1)

**Goal:** Acknowledge what's deferred, mark clearly

- [ ] Note in `technical-design.md` that JSONL schemas will be in `technical-design/jsonl-schemas.md`

  - Mark as "TBD in M1 implementation"
  - Placeholder: will document Org, Conversation, Message record schemas

- [ ] Note in `technical-design.md` that per-tool details defer to M1
  - list-orgs, list-convos, get-convo, render-md
  - Each will be documented as implemented

## Phase 4: Final Review & Validation

**Goal:** Verify M0 achieves its actual success criteria, not just checklist completion

### Acceptance Tests

- [ ] Test LLM entry point path (simulate fresh session)

  - [ ] Read CLAUDE.md → Can I understand architecture? Y/N
  - [ ] Read STATUS.md → Do I know what to do next? Y/N
  - [ ] Read development-plan.md M0 section → Can I see progress? Y/N
  - [ ] Can I start work without asking clarifying questions? Y/N

- [ ] Verify against documentation-howto.md standards

  - [ ] Each main doc has "Read this when" section at top
  - [ ] All links include context (not just bare URLs)
  - [ ] Tiered detail present (summary in main → link → deep dive in subdoc)
  - [ ] Subdirectories only used for >100-200 line content

- [ ] Check M0 success criteria explicitly (from development-plan.md)
  - [ ] All core docs exist and follow meta-documentation standard
  - [ ] Design decisions explicitly documented with rationale
  - [ ] Clear entry points for future sessions (STATUS.md, devlog/)
  - [ ] LLM can resume work by reading CLAUDE.md → STATUS.md → latest devlog

### Technical Cleanup

- [ ] Run `git grep -l "TODO\|Status:.*TODO" docs/` to find remaining TODOs

  - Acceptable: TODOs in Level 3/4 (implementation details, marked "TBD M1")
  - Not acceptable: TODOs in Level 1-2 (foundation/rationale)

- [ ] Verify all cross-references are correct after moves/renames

- [ ] Apply template.python-project baseline configurations
  - [ ] Add pyproject.toml entry points for CLI commands (chatfs-list-orgs, etc.)
  - [ ] Verify uv project structure matches template

### Session Closeout

- [ ] Update STATUS.md

  - Mark M0 complete or identify remaining blockers
  - List next actions for M1

- [ ] Create devlog entry for this session
  - Document restructuring decisions
  - Link to updated docs
  - Record acceptance test results

## Decision Points

### Should we investigate fork representation now?

**Option A:** Investigate API for fork representation before M0 completion

- Pro: Might inform design decisions
- Con: Not blocking M1 (read-only doesn't need forks)

**Option B:** Defer to parallel investigation during M1 or before M3

- Pro: Faster to working MVP
- Con: Might need refactoring later

**Recommendation:** Defer. M1 is read-only and doesn't need fork handling.

### Delete unnecessary placeholder docs?

If during Phase 3 review we find subdocs that add no value beyond the main doc summary:

- Delete them
- Keep just the summary in main doc
- Per documentation-howto.md: use subdocs only when >100-200 lines or frequently referenced independently
