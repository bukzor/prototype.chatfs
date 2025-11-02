# M0 Documentation Completion - TODO

**Project:** chatfs - lazy filesystem for chat conversations
**Milestone:** M0 (Documentation Phase) - see [docs/dev/development-plan.md#milestone-0-documentation-phase]
**Current Status:** See [STATUS.md]
**Goal:** LLM-resumable documentation foundation before M1 implementation

**Approach:** Discussion-based validation → Develop certainty → Evaluate/Correct/Rewrite

**IMPORTANT:** Existing docs are rough drafts written by Claude with minimal oversight. Do NOT treat them as authoritative. Your task is to:

1. **Discuss** concepts with the user to develop deep understanding
2. **Validate** existing content for accuracy/completeness
3. **Correct** what's wrong or misleading
4. **Create** missing content with confidence

**NOT:** Mechanical fill-in-the-blanks. You must reach certainty before making changes.

**Editing Guideline:** Make edits at 80% confidence. Do NOT over-hedge or seek permission for edits when you have reasonable confidence. Edit first, discuss if uncertain.

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

## Phase 1: Validate Level 1 (Foundation - Main Doc Bodies)

**Goal:** Develop certainty about foundational concepts through discussion, then validate/correct main docs

### Workflow per topic:
1. **Discuss** with user to develop understanding
2. **Read** existing rough-draft content
3. **Evaluate** accuracy/completeness
4. **Correct/Rewrite** with confidence

### Topics to validate:

- [x] **Problem Statement** (`design-rationale.md` intro)
  - Discussion: What problem does chatfs solve? Why do existing solutions fail?
  - Validate: Does current text accurately represent the problem?
  - Correct: Fix any mischaracterizations or missing context

- [x] **Design Philosophy** (`design-rationale.md` core decisions)
  - Discussion: Are the four key decisions (plumbing/porcelain, JSONL, lazy, unofficial API) correct?
  - Validate: Is the rationale for each decision sound?
  - Correct: Fix weak reasoning, add missing tradeoffs

- [ ] **System Architecture** (`technical-design.md`)
  - Discussion: What are the actual components? How do they interact?
  - Validate: Does the architecture section match reality?
  - Correct: Fix component descriptions, data flow inaccuracies

- [ ] **Open Questions** (`design-incubators/README.md`)
  - Discussion: What are the actual unsolved problems?
  - Validate: Is fork-representation correctly characterized?
  - Correct: Add missing unknowns, remove resolved questions

## Phase 2: Validate Level 2 (Elaborate Foundations - Subdirectories)

**Goal:** Validate/correct detailed rationale and design docs through discussion

### Workflow per subdoc:
1. **Discuss** the concept in depth with user
2. **Read** existing rough-draft subdoc
3. **Evaluate** for technical accuracy, completeness, weak arguments
4. **Correct/Rewrite** OR **Delete** if unnecessary (per documentation-howto: subdocs only if >100-200 lines or independently referenced)

### Design Rationale Subdocs

- [ ] **Plumbing/Porcelain Split** (`design-rationale/plumbing-porcelain-split.md`)
  - Discussion: Why this decision? What alternatives exist? Real tradeoffs?
  - Validate: Are the arguments sound? Any strawman alternatives?
  - Correct: Strengthen weak arguments, add missing perspectives
  - Delete?: If <100 lines and fully covered in main doc

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
  - Validate: Does design match M1/M2 plans?
  - Correct: Clarify unofficial-claude-api wrapping vs future abstraction

- [ ] **Cache Layer** (`technical-design/cache-layer.md`)
  - Discussion: M1 scope? What's deferred? Directory structure?
  - Validate: Is M1 scope clearly bounded?
  - Correct: Mark staleness checking, lazy stubs as explicitly deferred

- [ ] **Porcelain Layer** (`technical-design/porcelain-layer.md`)
  - Discussion: What porcelain commands make sense? When to build them?
  - Validate: Is it clear this is mostly post-M1?
  - Correct: Add concrete examples, mark deferred scope

- [ ] **Markdown Format** (`technical-design/markdown-format.md`)
  - Discussion: Exact format spec? Frontmatter fields? Obsidian compat?
  - Validate: Is format well-specified enough for implementation?
  - Correct: Add missing details, clarify ambiguities

## Phase 3: Mark Deferred Details (Implementation Specifics for M1+)

**Goal:** Clearly mark what's intentionally deferred to implementation phase

### Workflow:
1. **Discuss** what level of detail is appropriate for M0 (design phase)
2. **Identify** implementation details that belong in M1 documentation
3. **Mark clearly** as "TBD M1" or similar
4. **Avoid** creating placeholder docs that add no value

### Deferred topics:

- [ ] **JSONL Schemas**
  - Discussion: Do we need placeholder now, or define during M1 implementation?
  - Action: Add note to `technical-design.md` that schemas will be documented during M1
  - Avoid: Creating empty `jsonl-schemas.md` with just "TODO"

- [ ] **Per-tool Implementation Details**
  - Discussion: How much detail about list-orgs, list-convos, etc. belongs in M0?
  - Action: Mark tool details as "documented during implementation"
  - Avoid: Speculative implementation docs that will be wrong

## Phase 4: Validate Against Success Criteria

**Goal:** Verify M0 achieves actual success criteria through critical evaluation, not mechanical checkbox completion

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

- [ ] **M0 Success Criteria** (from development-plan.md)
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
  - Acceptable: Implementation details marked "TBD M1"
  - Not acceptable: Unresolved design questions, vague placeholders in L1/L2
  - Action: Fix or remove unacceptable TODOs

- [ ] **Cross-reference verification**
  - Discussion: Did file moves/renames break any links?
  - Test: Click through major links in docs
  - Fix: Update any broken references

- [ ] **Python project baseline**
  - Discussion: What baseline configs are needed for M0 vs M1?
  - M0 scope: Entry points defined (for M1 implementation)
  - M1 scope: Actual tool installation/testing
  - Action: Add pyproject.toml entry points, verify uv structure

### Session Closeout (End of session)

- [ ] **Update STATUS.md**
  - Discussion: Is M0 actually complete? What blockers remain?
  - Document: Validation results, remaining work
  - Next actions: Either "Ready for M1" or "Continue M0 validation on X"

- [ ] **Create devlog entry**
  - Discussion: What was learned this session?
  - Document: Validation approach, corrections made, design clarifications
  - Record: Which docs were validated/corrected, acceptance test results

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
