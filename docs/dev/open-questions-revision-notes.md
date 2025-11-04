# Open Questions - Revision Notes (Phase 1 Understanding)

**Created:** 2025-11-02
**Purpose:** Capture improved understanding of open questions before Phase 1.25 architecture updates
**Status:** Temporary scratchpad - integrate into design-incubators/ after Phase 1.25 completes

## Key Insight: Fork Representation Has 3 Phases, Not 1

The current fork-representation incubator treats this as a single question, but it's actually three distinct questions at different milestones:

### Phase 1: What does claude.ai API return? (M1-CLAUDE)

**Blocking:** M1-CLAUDE implementation
**Question:** What fork data exists in the Claude API?
**Investigation needed:**
- Create forked conversations on claude.ai
- Use unofficial-claude-api to inspect responses
- Document exact JSON structure

**Specific unknowns:**
- Do forks appear as separate conversation UUIDs in list_conversations()?
- What metadata exists? (parent_uuid, fork_point, ancestry chain?)
- How are fork relationships represented?
- What happens when you fork a fork?

**Deliverable:** `design-incubators/fork-representation/claude-api-findings.md` documenting raw API behavior

**M1-CLAUDE scope:** Output whatever Claude returns as JSONL, no decisions needed

### Phase 2: How do we normalize across providers? (M2-VFS)

**Blocking:** M2-VFS implementation
**Question:** What should the normalized fork schema look like?
**Design needed:**
- How do Claude's forks map to normalized schema?
- How would ChatGPT forks map to same schema?
- How would Linear task relationships map?
- What's the common abstraction?

**Specific unknowns:**
- Do all providers support forks, or is this Claude-specific?
- Should VFS expose provider-specific features, or lowest common denominator?
- How do we represent fork relationships in JSONL?

**Deliverable:** `design-incubators/provider-abstraction/fork-normalization.md`

**M2-VFS scope:** Define normalized data model for forks that works across providers

### Phase 3: How do we represent forks on disk? (M3-CACHE)

**Blocking:** M3-CACHE implementation
**Question:** What filesystem layout for cached forked conversations?
**This is the current fork-representation incubator focus**

**Candidate approaches:**
- Flat naming: `conversation.fork-name.md`
- Nested directories: `conversation/forks/name/`
- Git-like refs: `.conversation/refs/fork-name/`
- Virtual paths: frontmatter-only, materialized on demand

**Deliverable:** `design-incubators/fork-representation/DECISION.md`

**M3-CACHE scope:** Choose filesystem representation based on M2-VFS's normalized schema

## New Open Question: Provider Abstraction Strategy

**Current location:** Nowhere (needs new incubator)
**Recommended location:** `design-incubators/provider-abstraction/`

### The Core Question

How do we design M2-VFS to abstract across fundamentally different APIs?

**Chat providers (Claude, ChatGPT):**
- Organizations → Conversations → Messages
- Forks/branches
- Streaming responses

**Project tracking (Linear, GitHub):**
- Projects → Tickets/Issues → Comments
- Relationships: blocks, depends-on, relates-to
- State transitions

### Why This Matters

If we try to design M2-VFS before building M1-CLAUDE, we're guessing at the abstraction. We need concrete cases (Claude API behavior) to inform good abstraction design.

### Investigation Needed

1. **M1-CLAUDE:** Build claude-native layer, learn what's actually there
2. **Analysis:** What patterns exist? What's provider-specific vs universal?
3. **M2-VFS design:** Create abstraction informed by M1-CLAUDE reality

### Specific Questions

- Should M2-VFS support provider-specific extensions, or pure abstraction?
- How do we handle features only some providers have (forks, streaming)?
- Should Linear even use the same VFS layer, or is it too different?
- Do we need provider capability detection?

**Deliverable:** `design-incubators/provider-abstraction/DECISION.md`

## Updates Needed to design-incubators/

### design-incubators/README.md

**Status:** Probably OK as-is
**Possible addition:** Add example showing multi-phase incubators (like fork-representation split across 3 milestones)

### design-incubators/fork-representation/CLAUDE.md

**Changes needed:**
- Add section: "This question has 3 phases across 3 milestones"
- Clarify: "This incubator focuses on Phase 3 (M3-CACHE filesystem representation)"
- Add: "See Phase 1 (M1-CLAUDE API investigation) in api-investigation.md"
- Add: "See Phase 2 (M2-VFS normalization) in ../provider-abstraction/"

### design-incubators/fork-representation/README.md

**Changes needed:**
- Update "Current Status" to show this is Phase 3 of 3
- Add Phase 1 checklist: API investigation (M1-CLAUDE scope)
- Add Phase 2 reference: Normalization design (M2-VFS scope)
- Keep existing Phase 3 checklist: Filesystem design (M3-CACHE scope)

**Add note:**
> Fork representation is split across 3 milestones:
> - M1-CLAUDE: Investigate what Claude API returns (design-incubators/fork-representation/api-investigation.md)
> - M2-VFS: Define normalized fork schema (design-incubators/provider-abstraction/)
> - M3-CACHE: Choose filesystem layout (this incubator's primary focus)

### design-incubators/fork-representation/ (new files)

**Create:** `api-investigation.md`
- Template for documenting Claude API fork behavior
- Checklist: create test forks, run unofficial-claude-api, document JSON structure
- This gets filled during M1-CLAUDE implementation

## Other Open Questions (Uncovered During Discussion)

### Cache Invalidation Strategy (M3-CACHE)

**Question:** How do we handle staleness checking?
- mtime-based comparison?
- ETag-style versioning?
- Explicit refresh commands only?

**Status:** Deferred to M3-CACHE implementation, probably doesn't need incubator (straightforward decision)

### Markdown Format Specifics (M2-VFS or M3-CACHE?)

**Question:** Exact frontmatter fields, Obsidian compatibility details
**Current location:** `docs/dev/technical-design/markdown-format.md`
**Status:** Needs review - is this VFS concern or Cache concern?

## Integration Plan (After Phase 1.25)

Once technical-design.md shows 4-layer architecture with M#-TOKEN milestones:

1. **Create:** `design-incubators/provider-abstraction/` incubator
2. **Update:** `design-incubators/fork-representation/CLAUDE.md` with 3-phase structure
3. **Update:** `design-incubators/fork-representation/README.md` with milestone mapping
4. **Create:** `design-incubators/fork-representation/api-investigation.md` template
5. **Update:** `design-incubators/README.md` to reference multi-phase incubators
6. **Mark:** Phase 1 Open Questions validation as complete

## Notes for Future Me

**Key realization:** We kept saying "fork representation blocks M1-CLAUDE" but actually:
- M1-CLAUDE doesn't need to represent forks, just output what API gives us
- M2-VFS needs to normalize fork schema across providers
- M3-CACHE needs to choose filesystem layout

These are three distinct decisions at three milestones. Conflating them caused confusion about when/how to resolve "fork representation."

**User's critical insight:** "We have no idea what we WANT from the normalized layer until we know what we CAN HAVE from the native layer."

This is why M1-CLAUDE (native) must come before M2-VFS (normalized abstraction).
