# M0-DOCS Documentation Completion - TODO

**Project:** chatfs - lazy filesystem for chat conversations
**Milestone:** M0-DOCS (Documentation Phase) - see [docs/dev/development-plan.md#milestone-0-documentation-phase]
**Current Status:** See [STATUS.md]
**Goal:** LLM-resumable documentation foundation before M1-CLAUDE implementation

**Approach:** Discussion-based validation → Develop certainty → Evaluate/Correct/Rewrite

**IMPORTANT:** Existing docs are rough drafts written by Claude with minimal oversight. Do NOT treat them as authoritative. Your task is to:

## Global Cleanup Tasks (Separate Sessions)

- [x] Fix Layer Naming Globally

  **Issue:** Docs inconsistently use milestone names (M1-CLAUDE, M2-VFS) when referring to layers instead of layer names (`native`, `vfs`).

  **Completed:** Fixed all instances across docs/, CLAUDE.md, HACKING.md, development-plan.md, fork-representation/CLAUDE.md
  - Replaced "M1-CLAUDE layer" → "`native/claude` layer"
  - Replaced "M2-VFS layer" → "`vfs` layer"
  - Replaced "M3-CACHE layer" → "`cache` layer"
  - Milestone names kept only for: section headers, development phases, "implemented in M1-CLAUDE"

- [ ] Remove Excessive Bolding

  **Issue:** Too much bold text reduces impact and readability.

  **Action needed:**
  - [ ] Replace bolded section headers with section headers: `##`, `###`
  - [ ] Replace bolded line-item headers/labels with emdash-delimiting
  - [ ] Remove most bolding from documentation
      - Keep/restore bolding only for: critical warnings, key terms on first use


## Documentation Dependency Tree

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
│  ├─ Layered architecture (why)
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
│  ├─ Fork representation (blocked M3-CACHE)
│  └─ Write operation semantics
│
└─ Level 3: Component Details (Phase 3 - mostly deferred to M1-CLAUDE)
   │
   Data Flow branches:
   ├─ Provider → Models → JSONL pipeline
   └─ Cache interaction points
   │
   Component Structure branches:
   ├─ native layer family
   ├─ vfs layer
   ├─ cache layer
   └─ cli layer
   │
   Data Formats branches:
   ├─ JSONL schemas
   └─ Markdown format

   Level 4: Implementation Specifics (deferred to M1-CLAUDE+)
   │
   native layer branches:
   ├─ Provider interface definition
   ├─ native/claude specifics
   └─ native/chatgpt specifics
   │
   cache layer branches:
   ├─ Directory structure
   ├─ Staleness checking
   └─ Lazy stub creation
   │
   vfs layer branches:
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

See [CLAUDE.md#working-on-documentation] for documentation topic locations.

## Phase 1: Validate Level 1 (Foundation - Main Doc Bodies)

### Topics to validate:

- [x] **Problem Statement** (`design-rationale.md` intro)
  - Discussion: What problem does chatfs solve? Why do existing solutions fail?
  - Validate: Does current text accurately represent the problem?
  - Correct: Fix any mischaracterizations or missing context

- [x] **Design Philosophy** (`design-rationale.md` core decisions)
  - Discussion: Are the four key decisions (plumbing/porcelain, JSONL, lazy, unofficial API) correct?
  - Validate: Is the rationale for each decision sound?
  - Correct: Fix weak reasoning, add missing tradeoffs

- [x] **System Architecture** (`technical-design.md`)
  - Discussion: Defined three-layer architecture, then evolved to four-layer (native/vfs/cache/cli)
  - Validate: Corrected architecture to show layered structure
  - Correct: Updated component descriptions, data flows (will complete in Phase 1.25)

- [x] **Open Questions** (`docs/dev/design-incubators/README.md`)
  - Discussion: Fork representation splits into 3 phases (M1-CLAUDE/M2-VFS/M3-CACHE), new provider-abstraction question
  - Validate: Current docs conflate 3 distinct questions
  - Correct: Captured understanding in `docs/dev/open-questions-revision-notes.md` for integration after Phase 1.25

## Phase 1.25: Architecture Evolution (3 layers → 4 layers)

**Goal:** Update architecture from 3 layers to 4 layers with M#-TOKEN milestone format

**Why now:** Locks in architecture before terminology cleanup, minimizes total work

**Rationale:** Can't design good abstraction (M2-VFS) without understanding concrete case (M1-CLAUDE). Inserting claude-native layer lets us learn what the API does before deciding how to normalize it.

### Four-Layer Architecture Specification

**Milestones:**
- **M0-DOCS:** Documentation phase (current)
- **M1-CLAUDE:** Claude-native layer - direct API wrapper, minimal abstraction
- **M2-VFS:** Virtual filesystem layer - normalized view across providers
- **M3-CACHE:** Cache/filesystem layer - persistent storage
- **M4-CLI:** CLI layer - human-friendly UX

**Directory structure:**
```
lib/chatfs/layer/
├── native/
│   └── claude/      # M1-CLAUDE
├── vfs/             # M2-VFS
├── cache/           # M3-CACHE
└── cli/             # M4-CLI
```

**Command naming conventions:**
- M1-CLAUDE: `chatfs-claude-list-orgs`, `chatfs-claude-list-convos`, `chatfs-claude-get-convo`, `chatfs-claude-render-md`
- M2-VFS: `chatfs-vfs-list-orgs`, `chatfs-vfs-list-convos`, `chatfs-vfs-get-convo`, `chatfs-vfs-render-md`
- M3-CACHE: `chatfs-cache-list-orgs`, `chatfs-cache-list-convos`, `chatfs-cache-get-convo`, `chatfs-cache-render-md`
- M4-CLI: `chatfs-ls`, `chatfs-cat`, `chatfs-sync` (human-friendly, no JSONL)

**Layer responsibilities:**
- **M1-CLAUDE:** Stateless, outputs whatever claude.ai API returns as JSONL. No normalization, no decisions.
- **M2-VFS:** Normalized JSONL schema across providers. Takes `--provider` flag. No persistence.
- **M3-CACHE:** Wraps M2-VFS, adds filesystem writes and staleness checking.
- **M4-CLI:** Wraps M3-CACHE, adds colors, progress bars, path-based interface.

**Shared libraries:**
- `chatfs.client` - Wraps unofficial-claude-api (used by M1-CLAUDE)
- `chatfs.models` - Normalized data models (defined at M2-VFS layer)
- `chatfs.cache` - Filesystem cache manager (M3-CACHE)

### Step 1: Update core architecture docs with 4-layer spec

- [x] **technical-design.md** - REWRITE architecture section:
  - Replace 3-layer diagram (API/Cache/CLI) with 4-layer diagram (native/vfs/cache/cli)
  - Update "Components" section to show all 4 layers with M#-TOKEN milestones
  - Update "Data Flow" to show M1-CLAUDE (native) → M2-VFS → M3-CACHE → M4-CLI
  - Update all command examples: chatfs-api-* → chatfs-vfs-*, add chatfs-claude-* examples
  - Update shared libraries section: api.py → client.py, clarify models defined at M2-VFS

- [x] **development-plan.md** - Insert M1-CLAUDE milestone:
  - Add new M1-CLAUDE section BEFORE current M1 content
  - M1-CLAUDE scope: claude-native layer, investigate fork API, output raw JSONL
  - Renumber subsequent milestones in this file only (M2-VFS, M3-CACHE, M4-CLI, M5-WRITE)

- [x] **STATUS.md** - Update current milestone reference to M0-DOCS

### Step 2: Milestone renaming across all docs (work backwards M3→M2→M1→M0)

**Important:** Work backwards to avoid overwriting. After each step, verify the change worked.

- [x] **Find M3 references:** `git grep -l 'M3[^-]' docs/`
  - Update each file: `M3` → `M4-CLI`
  - Verify: `git grep 'M3[^-]' docs/` should show nothing (except devlogs)

- [x] **Find M2 references:** `git grep -l 'M2[^-]' docs/`
  - Update each file: `M2` → `M3-CACHE`
  - Verify: `git grep 'M2[^-]' docs/` should show nothing (except devlogs)

- [x] **Find M1 references:** `git grep -l 'M1[^-]' docs/`
  - Update each file: `M1` → `M2-VFS`
  - Context: Old M1 was "API layer", now called "VFS layer"
  - Verify: `git grep 'M1[^-]' docs/` should show nothing (except devlogs)

- [x] **Find M0 references:** `git grep -l 'M0[^-]' docs/`
  - Update each file: `M0` → `M0-DOCS`
  - Verify: `git grep 'M0[^-]' docs/` should show nothing (except devlogs)

- [x] **Final verification:** Run `git grep -E 'M[0-9]([^-]|$)' docs/`
  - Should find nothing except devlogs (historical refs are OK)
  - If found elsewhere, update those files

### Step 3: Add M1-CLAUDE references where needed

- [x] **technical-design.md** - Already updated in Step 1
- [x] **development-plan.md** - Already updated in Step 1
- [x] **CLAUDE.md** - Add M1-CLAUDE quick reference examples
- [x] **README.md** - Update architecture overview to mention M1-CLAUDE

**Deliverable:** technical-design.md shows 4 layers with M#-TOKEN milestones, ready for Phase 1.5 terminology cleanup

## Phase 1.4: Integrate Open Questions Understanding

**Goal:** Apply insights from Phase 1 Open Questions discussion to docs/dev/design-incubators/

**Why now:** Architecture is locked (4 layers), now we can map open questions to correct milestones

**Source:** `docs/dev/open-questions-revision-notes.md` (created during Phase 1)

### Updates needed:
- [x] **docs/dev/design-incubators/fork-representation/CLAUDE.md** - Add 3-phase structure (M1-CLAUDE/M2-VFS/M3-CACHE split)
- [x] **docs/dev/design-incubators/fork-representation/README.md** - Update with milestone mapping
- [x] **Create:** `docs/dev/design-incubators/fork-representation/api-investigation.md` template for M1-CLAUDE
- [x] **Create:** `docs/dev/design-incubators/provider-abstraction/` new incubator
- [x] **Create:** `docs/dev/design-incubators/provider-abstraction/CLAUDE.md` - define the question
- [x] **Create:** `docs/dev/design-incubators/provider-abstraction/README.md` - investigation workflow
- [x] **Update:** `docs/dev/design-incubators/README.md` - add note about multi-phase incubators
- [x] **Delete:** `docs/dev/open-questions-revision-notes.md` (integrated)

**Deliverable:** docs/dev/design-incubators/ reflects split fork question and new provider abstraction question

## Phase 1.5: Terminology Cleanup (Plumbing/Porcelain → Layer Structure) ✓ COMPLETE

**Completed:** 2025-11-04 (Session 5)

**Outcome:** All code and docs use 4-layer terminology consistently. Command examples updated for path conventions (absolute `//provider/...` vs relative paths).

## Phase 2: Breadth-First Documentation Validation

**Goal:** Validate all existing docs breadth-first (Level 0 → Level 1 → Level 2), correcting rough drafts through discussion

**Current Status:** In progress - validating Level 1 docs

**Completed:**
- [x] **Level 0: README.md** - Updated command examples, added path convention docs (absolute vs relative)
- [x] **Level 1: Core Documentation** - Main doc bodies
  - [x] design-rationale.md - Problem Space + Design Philosophy (solid, no changes needed)
  - [x] technical-design.md - System Architecture (fixed diagram flow, layer vs milestone naming, reorganized components)

**In Progress:**
- [ ] **Level 1: Core Documentation** - Remaining doc
  - [ ] docs/dev/design-incubators/README.md - Open Questions

**Pending:**
- [ ] **Level 2: Subdocs** - Elaborate foundations through discussion

### Level 2 Workflow (after Level 1 complete):
1. **Discuss** the concept in depth with user
2. **Read** existing rough-draft subdoc
3. **Evaluate** for technical accuracy, completeness, weak arguments
4. **Correct/Rewrite** OR **Delete** if unnecessary (per documentation-howto: subdocs only if >100-200 lines or independently referenced)

### Design Rationale Subdocs

- [ ] **Layered Architecture** (`design-rationale/layered-architecture.md`)
  - Discussion: Why four layers? Why learn-then-abstract approach?
  - Validate: Currently has TODO status, needs content discussion
  - Create/Correct: Fill in with rationale for 4-layer architecture evolution
  - Delete?: If <100 lines and fully covered in design-rationale.md main doc

- [ ] **JSONL Choice** (currently in main `design-rationale.md`, may need subdoc)
  - Discussion: Why JSONL specifically? What about msgpack, CSV, protobuf?
  - Validate: Is current rationale complete?
  - Create?: Only if detailed analysis needed (>100 lines)

- [ ] **Lazy Filesystem** (`design-rationale/lazy-filesystem.md`)
  - Discussion: Lazy vs eager tradeoffs? Staleness handling strategy?
  - Validate: Does existing content match actual design intent?
  - Correct: Fix mischaracterizations of lazy loading behavior
  - Delete?: If simple enough for main doc

- [ ] **Unofficial API** (`design-rationale/unofficial-api.md`)
  - Discussion: Real risks? Mitigations? Why official API truly insufficient?
  - Validate: Are risks accurately stated? Mitigations realistic?
  - Correct: Fix any overconfidence or understatement of risks

### Technical Design Subdocs

- [ ] **Provider Interface** (`technical-design/provider-interface.md`)
  - Discussion: What's the actual abstraction? How will multi-provider work?
  - Validate: Does design match M1-CLAUDE/M2-VFS plans?
  - Correct: Clarify unofficial-claude-api wrapping vs future abstraction

- [ ] **Cache Layer** (`technical-design/cache-layer.md`)
  - Discussion: M3-CACHE scope? What's deferred? Directory structure?
  - Validate: Is M3-CACHE scope clearly bounded?
  - Correct: Mark staleness checking, lazy stubs as explicitly deferred

- [ ] **CLI Layer** (`technical-design/cli-layer.md`)
  - Discussion: What CLI commands make sense? When to build them?
  - Validate: Currently has TODO status, needs content discussion
  - Correct/Create: Add concrete examples, mark deferred scope (milestone M4-CLI)
  - Delete?: If <100 lines and fully covered in technical-design.md main doc

- [ ] **VFS Layer** (`technical-design/vfs-layer.md`)
  - Discussion: Does this need separate doc or covered in technical-design.md?
  - Decision: May not need this subdoc at all
  - Action: Discuss during Phase 2 subdoc review, create only if needed

- [ ] **Markdown Format** (`technical-design/markdown-format.md`)
  - Discussion: Exact format spec? Frontmatter fields? Obsidian compat?
  - Validate: Is format well-specified enough for implementation?
  - Correct: Add missing details, clarify ambiguities

## Phase 3: Mark Deferred Details (Implementation Specifics for M1-CLAUDE+)

### Deferred topics:

- [ ] **JSONL Schemas**
  - Discussion: Do we need placeholder now, or define during M1-CLAUDE implementation?
  - Action: Add note to `technical-design.md` that schemas will be documented during M1-CLAUDE
  - Avoid: Creating empty `jsonl-schemas.md` with just "TODO"

- [ ] **Per-tool Implementation Details**
  - Discussion: How much detail about list-orgs, list-convos, etc. belongs in M0-DOCS?
  - Action: Mark tool details as "documented during implementation"
  - Avoid: Speculative implementation docs that will be wrong

## Phase 4: Validate Against Success Criteria

**Goal:** Verify M0-DOCS achieves actual success criteria through critical evaluation, not mechanical checkbox completion

### Acceptance Tests (User-driven validation)

- [ ] **LLM Entry Point Test** (simulate fresh session)
  - Discussion: Would a new LLM understand the project from docs alone?
  - Test: Read CLAUDE.md → STATUS.md → development-plan.md
  - Evaluate: Can LLM start work without clarifying questions?
  - Criteria: Architecture clear, next actions obvious, design rationale accessible

- [ ] **Documentation Standards Check**
  - Discussion: Do docs follow documentation-howto.md principles?
  - Validate:
    - "Read this when" sections present and useful
    - Links include context (not bare URLs)
    - Tiered detail (summary → link → deep dive)
    - Subdocs only for >100-200 lines
  - Correct: Fix any violations

- [ ] **M0-DOCS Success Criteria** (from development-plan.md)
  - Discussion: Have we achieved the actual goals, not just checkboxes?
  - Validate:
    - Core docs exist AND are accurate (not just present)
    - Design decisions explicitly documented WITH sound rationale
    - Entry points clear AND actually helpful
    - LLM can resume AND make progress without user handholding

### Technical Cleanup (After validation complete)

- [ ] **Remaining TODOs audit**
  - Run: `git grep -l "TODO\|Status:.*TODO" docs/`
  - Discussion: Which TODOs are acceptable vs problematic?
  - Acceptable: Implementation details marked "TBD M1-CLAUDE"
  - Not acceptable: Unresolved design questions, vague placeholders in L1/L2
  - Action: Fix or remove unacceptable TODOs

- [ ] **Cross-reference verification**
  - Discussion: Did file moves/renames break any links?
  - Test: Click through major links in docs
  - Fix: Update any broken references

- [ ] **Python project baseline**
  - Discussion: What baseline configs are needed for M0-DOCS vs M1-CLAUDE?
  - M0-DOCS scope: Entry points defined (for M1-CLAUDE implementation)
  - M1-CLAUDE scope: Actual tool installation/testing
  - Action: Add pyproject.toml entry points, verify uv structure

### Session Closeout (End of session)

- [ ] **Update STATUS.md**
  - Discussion: Is M0-DOCS actually complete? What blockers remain?
  - Document: Validation results, remaining work
  - Next actions: Either "Ready for M1-CLAUDE" or "Continue M0-DOCS validation on X"

- [ ] **Create devlog entry**
  - Discussion: What was learned this session?
  - Document: Validation approach, corrections made, design clarifications
  - Record: Which docs were validated/corrected, acceptance test results

## Decision Points

### Should we investigate fork representation now?

**Option A:** Investigate API for fork representation before M0-DOCS completion

- Pro: Might inform design decisions
- Con: Not blocking M1-CLAUDE (read-only doesn't need forks)

**Option B:** Defer to parallel investigation during M1-CLAUDE or before M3-CACHE

- Pro: Faster to working MVP
- Con: Might need refactoring later

**Recommendation:** Defer. M1-CLAUDE is read-only and doesn't need fork handling.

### Delete unnecessary placeholder docs?

If during Phase 3 review we find subdocs that add no value beyond the main doc summary:

- Delete them
- Keep just the summary in main doc
- Per documentation-howto.md: use subdocs only when >100-200 lines or frequently referenced independently
