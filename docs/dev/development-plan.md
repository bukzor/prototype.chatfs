# Development Plan

**Last Updated:** 2025-11-01

**Read this when:**

- Understanding project roadmap
- Planning next implementation phase
- Prioritizing features
- Estimating project timeline

This document defines milestones and implementation order for chatfs.

## Milestones Overview

```
M0-DOCS: Documentation → M1-CLAUDE: Native → M2-VFS: Normalized → M3-CACHE: Cache → M4-CLI: UI → M5-WRITE: Write Ops
(1-2 sessions)           (2 weeks)           (2 weeks)             (1 week)          (1 week)     (TBD, Blocked)
```

**Layer evolution:**
- **M1-CLAUDE:** Learn what Claude API returns (concrete case)
- **M2-VFS:** Design normalization based on M1-CLAUDE findings (abstract schema)
- **M3-CACHE:** Add persistence layer
- **M4-CLI:** Add human-friendly UX
- **M5-WRITE:** Add write operations (blocked on fork representation)

## Milestone 0: Documentation Phase (M0-DOCS)

**Status:** In Progress (firming up design)

**Goal:** Establish project structure, design foundation, and documentation
before implementation

**Deliverables:**

- [x] Core documentation files rough draft (README, HACKING, CLAUDE, STATUS)
- [x] Design rationale document rough draft (plumbing/porcelain split, JSONL choice, lazy loading)
- [x] Technical design document rough draft (architecture, data flow, components)
- [x] Development plan rough draft (this document - high-level overview)
- [x] Devlog structure and first entry
- [x] Fork representation design incubator setup
- [ ] Populate placeholder docs (`git grep -l "TODO\|Status:.*TODO" docs/`)
  - [ ] Delete unnecessary detail placeholder docs
- [ ] Solidify technical design (API wrapper, data models, JSONL schemas)
- [ ] Apply template.python-project baseline configurations
  - [ ] pyproject.toml entry points for CLI commands
- [ ] Investigate fork representation via API
- [ ] Review and finalize M0 - ready for M1?

**Dependencies:** None

**Success Criteria:**

- All core docs exist and follow meta-documentation standard
- Design decisions explicitly documented with rationale
- Clear entry points for future sessions (STATUS.md, devlog/)
- LLM can resume work by reading CLAUDE.md → STATUS.md → latest devlog

**Estimated Effort:** 1-2 sessions

**Next Milestone:** M1-CLAUDE (Claude-native layer implementation)

## Milestone 1: Claude-Native Layer (M1-CLAUDE)

**Status:** Blocked (depends on M0-DOCS completion)

**Goal:** Build direct wrapper around claude.ai API. Output raw Claude data as JSONL with minimal abstraction. Learn what Claude API actually returns before designing normalized schema.

**Deliverables:**

- [ ] `chatfs-claude-list-orgs` command - List organizations (entry point from `lib/chatfs/layer/native/claude/list_orgs.py`)
- [ ] `chatfs-claude-list-convos` command - List conversations for org (entry point from `lib/chatfs/layer/native/claude/list_convos.py`)
- [ ] `chatfs-claude-get-convo` command - Get messages for conversation (entry point from `lib/chatfs/layer/native/claude/get_convo.py`)
- [ ] `chatfs-claude-render-md` command - Render messages to markdown (entry point from `lib/chatfs/layer/native/claude/render_md.py`)
- [ ] `lib/chatfs/client.py` - Claude API client wrapper (wraps unofficial-claude-api)
- [ ] Integration tests (full pipeline)
- [ ] Session key setup docs
- [ ] **Fork API investigation:** Document what Claude API returns for forked conversations

**Dependencies:** M0-DOCS (Documentation)

**Success Criteria:**

- Can pipe claude-native tools:
  `chatfs-claude-list-orgs | chatfs-claude-list-convos | chatfs-claude-get-convo | chatfs-claude-render-md`
- Output is valid JSONL (except render-md outputs markdown)
- Works with jq for filtering/transforming
- Manual testing with real claude.ai account works
- **Fork API behavior documented** in design-incubators/fork-representation/api-findings.md

**Estimated Effort:** 2 weeks

**Key Principle:** Output whatever Claude API returns. No normalization decisions. This layer exists to learn what the API does before designing M2-VFS normalized schema.

**Deferred to M2-VFS:**
- Normalized data models
- Provider abstraction
- Multi-provider support

**Deferred to M3-CACHE:**
- Filesystem writes
- Staleness checking
- Lazy stub file creation

**Implementation Notes:**

1. Wrap unofficial-claude-api in `lib/chatfs/client.py`
2. Implement `chatfs-claude-list-orgs` (simplest, no input needed)
3. Implement `chatfs-claude-list-convos` (takes org record)
4. Implement `chatfs-claude-get-convo` (takes convo record)
5. Implement `chatfs-claude-render-md` (formats messages to markdown)
6. **Investigate fork API:** Create forked conversations on claude.ai, inspect API responses
7. Document findings in design-incubators/fork-representation/api-findings.md
8. Test full pipeline end-to-end

**Next Milestone:** M2-VFS (Virtual filesystem layer with normalization)

## Milestone 2: Virtual Filesystem Layer (M2-VFS)

**Status:** Blocked (depends on M1-CLAUDE completion)

**Goal:** Build normalized JSONL schema across providers (Claude, ChatGPT, etc.). Design abstraction based on M1-CLAUDE findings. Still stateless (no filesystem writes).

**Deliverables:**

- [ ] `chatfs-vfs-list-orgs` command - List organizations (entry point from `lib/chatfs/layer/vfs/list_orgs.py`)
- [ ] `chatfs-vfs-list-convos` command - List conversations for org (entry point from `lib/chatfs/layer/vfs/list_convos.py`)
- [ ] `chatfs-vfs-get-convo` command - Get messages for conversation (entry point from `lib/chatfs/layer/vfs/get_convo.py`)
- [ ] `chatfs-vfs-render-md` command - Render messages to markdown (entry point from `lib/chatfs/layer/vfs/render_md.py`)
- [ ] `lib/chatfs/models.py` - Normalized data structures (Org, Conversation, Message)
- [ ] Provider abstraction design (based on M1-CLAUDE findings)
- [ ] **Optional:** M1-CHATGPT native layer for ChatGPT (if multi-provider desired)
- [ ] Integration tests (full pipeline)

**Dependencies:** M1-CLAUDE (Claude-native layer completed)

**Success Criteria:**

- Can pipe VFS tools:
  `chatfs-vfs-list-orgs | chatfs-vfs-list-convos | chatfs-vfs-get-convo | chatfs-vfs-render-md`
- Output uses normalized schema (provider-agnostic fields)
- Works with jq for filtering/transforming
- `--provider` flag supported (default: claude)
- If multi-provider: ChatGPT support works with same tools
- Manual testing with real claude.ai account works

**Estimated Effort:** 2 weeks

**Deferred to M3-CACHE:**

- Filesystem writes
- Staleness checking (read from cache, don't refresh)
- Lazy stub file creation

**Deferred to M4-CLI:**

- Porcelain commands
- Colors, progress bars

**Deferred to M5-WRITE:**

- Write operations

**Implementation Notes:**

**Key design decision:** Based on M1-CLAUDE findings, design normalized schema.

**Key tasks:**

1. Review M1-CLAUDE output, identify normalization needs
2. Define `lib/chatfs/models.py` normalized data structures
3. Implement `chatfs-vfs-*` tools that wrap `chatfs-claude-*` and normalize output
4. Add `--provider` flag support
5. **Optional:** Implement M1-CHATGPT native layer for ChatGPT
6. **Optional:** Implement normalization for ChatGPT → VFS schema
7. Test full pipeline end-to-end with both providers
8. Resolve design-incubators/provider-abstraction-strategy/ decisions

**Next Milestone:** M3-CACHE (Cache/filesystem layer)

## Milestone 3: Cache/Filesystem Layer (M3-CACHE)

**Status:** Blocked (depends on M2-VFS completion)

**Goal:** Add filesystem persistence, staleness checking, and lazy loading. Wrap M2-VFS layer with caching.

**Deliverables:**

- [ ] `chatfs-cache-list-orgs` command - Cached list organizations (entry point from `lib/chatfs/layer/cache/list_orgs.py`)
- [ ] `chatfs-cache-list-convos` command - Cached list conversations (entry point from `lib/chatfs/layer/cache/list_convos.py`)
- [ ] `chatfs-cache-get-convo` command - Cached get conversation (entry point from `lib/chatfs/layer/cache/get_convo.py`)
- [ ] `chatfs-cache-render-md` command - Render from cache (entry point from `lib/chatfs/layer/cache/render_md.py`)
- [ ] `lib/chatfs/cache.py` - Filesystem cache manager
- [ ] Cache structure: `./chatfs/claude.ai/`, `./chatfs/chatgpt/` (provider-specific)
- [ ] Staleness checking via mtime comparison
- [ ] Lazy directory/file creation
- [ ] Tests for cache operations

**Dependencies:** M2-VFS (Virtual filesystem layer)

**Success Criteria:**

- Same interface as M2-VFS tools, but with caching:
  `chatfs-cache-list-orgs | chatfs-cache-list-convos | chatfs-cache-get-convo`
- Filesystem writes to `./chatfs/` directory structure
- Staleness checking works (compares mtime to remote `updated_at`)
- Cache invalidation based on `updated_at` fields
- Lazy directory creation on first access
- Manual testing shows cache working correctly

**Estimated Effort:** 1 week

**Deferred to M4-CLI:**

- Human-friendly path interface (org names instead of UUIDs)
- Progress bars, colors
- Interactive prompts

**Deferred to M5-WRITE:**

- Write operations
- Fork handling

**Implementation Notes:**

**Key tasks:**

1. Implement `lib/chatfs/cache.py` filesystem cache manager
2. Define cache directory structure (see technical-design.md#filesystem-cache-structure)
3. Implement `chatfs-cache-*` tools that wrap `chatfs-vfs-*` with caching
4. Add staleness checking logic (mtime vs remote `updated_at`)
5. Implement lazy directory creation
6. Test cache hits, misses, and invalidation

**Filesystem structure:**

```
./chatfs/
├── .config.json
└── claude.ai/
    └── Buck Evan/
        ├── org.jsonl
        ├── 2025-10-29/
        │   ├── tshark-filtering.md
        │   └── tshark-filtering.jsonl
        └── .uuid-index.json
```

**Next Milestone:** M4-CLI (CLI layer)

## Milestone 4: CLI Layer (M4-CLI)

**Status:** Blocked (depends on M3-CACHE completion)

**Goal:** Build human-friendly CLI wrappers with rich UX. Wrap M3-CACHE layer with colors, progress bars, path-based interface.

**Deliverables:**

- [ ] `chatfs ls` command - List conversations in org
- [ ] `chatfs cat` command - Display conversation
- [ ] `chatfs sync` command - Force refresh cache
- [ ] Path parsing (org name → org UUID lookup)
- [ ] Progress bars for slow operations
- [ ] Colors/formatting for terminal output
- [ ] Friendly error messages
- [ ] Interactive prompts (if needed)
- [ ] Tests for CLI commands

**Dependencies:** M3-CACHE (Cache/filesystem layer)

**Success Criteria:**

- Human-friendly commands work:
  `chatfs ls "Buck Evan"`, `chatfs cat "path/to/convo.md"`, `chatfs sync "Buck Evan/2025-10"`
- Path parsing works (org names, date ranges, conversation titles)
- Progress bars show for slow operations
- Colors/formatting work in terminal
- Friendly error messages guide user
- Manual testing with real account works smoothly

**Estimated Effort:** 1 week

**Deferred to M5-WRITE:**

- Write operations (`chatfs append`, `chatfs fork`, `chatfs amend`)

**Implementation Notes:**

**Key tasks:**

1. Design CLI interface (subcommands, arguments, flags)
2. Implement path parsing (org name → UUID, date ranges, conversation titles)
3. Wrap M3-CACHE tools with `chatfs` CLI
4. Add progress bars using rich/tqdm
5. Add colors/formatting using rich
6. Add friendly error messages
7. Test CLI UX with real users

**Next Milestone:** M5-WRITE (Write operations, blocked on fork representation)

## Milestone 5: Write Operations (M5-WRITE)

**Status:** Blocked (fork representation undecided)

**Goal:** Support appending, forking, amending conversations

**Deliverables:**

- [ ] Fork representation decision (see design-incubators/fork-representation/)
- [ ] `chatfs-append` command - Add message to conversation (entry point from `lib/chatfs/plumbing/append.py`)
- [ ] `chatfs-fork` command - Fork conversation at message (entry point from `lib/chatfs/plumbing/fork.py`)
- [ ] `chatfs-amend` command - Edit message in conversation (entry point from `lib/chatfs/plumbing/amend.py`)
- [ ] Cache write operations with fork tracking
- [ ] Tests for write operations

**Dependencies:**

- M1-CLAUDE (Fork API investigation completed)
- M2-VFS (Normalized schema includes fork representation)
- M3-CACHE (Cache layer exists for persistence)
- Fork representation design resolved (3 phases: M1/M2/M3 investigations complete)

**Blockers:**

- Fork representation undecided (see design-incubators/fork-representation/)
- Phase 1 (M1-CLAUDE): What does Claude API return for forks?
- Phase 2 (M2-VFS): How to normalize fork representation across providers?
- Phase 3 (M3-CACHE/M5-WRITE): How to represent forks on disk?

**Success Criteria:**

- Can append message:
  `chatfs append "convo-path" "message text"`
- Can fork conversation:
  `chatfs fork "convo-path" --name "try-alt"`
- Filesystem reflects fork structure (per chosen design)
- Cache maintains fork relationships
- Works across providers (if multi-provider implemented)

**Estimated Effort:** TBD (depends on fork complexity)

**Deferred:**

- Merge forks (unclear if API supports)
- Rename forks
- Delete messages

**Implementation Notes:**

Must resolve design-incubators/fork-representation/ (all 3 phases) first.

**Next Milestone:** TBD (polish, additional features, or maintenance)

## Tier 2: Maybe Soon, Maybe Later

Features identified but not scheduled:

### Obsidian Integration

- Verify markdown + YAML frontmatter compatibility
- Test wikilinks between conversations
- Graph view support

**Effort:** Low (may be free if format already compatible)

### Frontmatter CLI Suite

- `chatfs-frontmatter-read` - Extract YAML frontmatter
- `chatfs-frontmatter-write` - Update frontmatter fields
- `chatfs-frontmatter-edit` - Modify while preserving formatting

**Effort:** Medium (1 week) **Priority:** Low (only needed for advanced
porcelain features)

## Tier 3: Maybe Later, Maybe Never

Ideas deferred indefinitely:

- Gemini provider support
- Vector database / knowledge store integration
- LLM-assisted conversation analysis
- Collaborative second-brain features (wiki articles + chats)
- Graph analysis on conversation links
- Persistent watch command for eager updates

**Rationale:** Nice-to-have, not core functionality. Re-evaluate after M1-CLAUDE through M4-CLI complete.

## Decision Points

### After M0-DOCS: Start Implementation or Continue Design?

**Option A: Start M1-CLAUDE immediately**

- Pros: Working code sooner, learn what Claude API returns (concrete case informs M2-VFS design)
- Cons: Fork representation Phase 1 (API investigation) will happen during M1-CLAUDE

**Option B: Investigate fork API before starting M1-CLAUDE**

- Pros: May inform M1-CLAUDE implementation
- Cons: Fork investigation is part of M1-CLAUDE scope anyway

**Recommendation:** Start M1-CLAUDE immediately. Fork API investigation is part of M1-CLAUDE deliverables. Read-only doesn't need fork representation decisions.

### After M1-CLAUDE: Full M2-VFS or MVP First?

**Option A: Full M2-VFS (multi-provider)**

- Pros: Validates abstraction early, supports Claude + ChatGPT
- Cons: More complex before basics work

**Option B: M2-VFS Claude-only, skip multi-provider**

- Pros: Faster to working stack (M1-CLAUDE → M2-VFS → M3-CACHE → M4-CLI)
- Cons: Need to add multi-provider support later

**Recommendation:** M2-VFS Claude-only first (normalize Claude data). Add ChatGPT support later as needed.

### After M2-VFS: Add Cache or Skip to CLI?

**Option A: M3-CACHE before M4-CLI**

- Pros: Persistence layer before UX, more complete stack
- Cons: Slower to human-friendly interface

**Option B: Skip M3-CACHE, build M4-CLI directly on M2-VFS**

- Pros: Human-friendly UX sooner
- Cons: No persistence (always fresh API calls), slower operations

**Recommendation:** Follow planned order (M3-CACHE then M4-CLI). Persistence is important for usability.

### Capnshell Integration?

If capnshell exists:

1. Define capnproto schemas for Org, Conversation, Message
2. Add `--output-format capnp` to M1-CLAUDE/M2-VFS tools
3. Test in capnshell
4. Keep JSONL for human debugging

**Timeline:** TBD (depends on capnshell progress)

## Maintenance Plan

**After each milestone:**

1. Update STATUS.md
2. Create devlog entry summarizing progress
3. Update technical-design.md if architecture changed
4. Add lessons learned to design-rationale.md

**Regular reviews:**

- Monthly: Reassess tier 2/3 priorities
- Per milestone: Validate next milestone still correct direction

## Related Documents

- [design-rationale.md] - Why these milestones and order
- [technical-design.md] - What we're building
- [milestone-1-claude-native] - Detailed M1-CLAUDE tasks (to be created)

[design-rationale.md]: design-rationale.md
[technical-design.md]: technical-design.md
[milestone-1-claude-native]: development-plan/milestone-1-claude-native.md
