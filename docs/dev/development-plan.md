# Development Plan

**Last Updated:** 2025-11-01

**Read this when:**

- Understanding project roadmap
- Planning next implementation phase
- Prioritizing features
- Estimating project timeline

This document defines milestones and implementation order for claifs.

## Milestones Overview

```
M0: Documentation   → M1: Plumbing     → M2: Multi-Provider → M3: Write Ops
    (1-2 sessions)     (2-3 weeks)        (2 weeks)            (TBD)
                                                               (Blocked)
```

## Milestone 0: Documentation Phase

**Status:** In Progress (firming up design)

**Goal:** Establish project structure, design foundation, and documentation
before implementation

**Deliverables:**

- [x] Core documentation files (README, HACKING, CLAUDE, STATUS)
- [x] Design rationale document (plumbing/porcelain split, JSONL choice, lazy loading)
- [x] Technical design document (architecture, data flow, components)
- [x] Development plan (this document - high-level overview)
- [x] Devlog structure and first entry
- [x] Fork representation design incubator setup
- [ ] Populate placeholder docs (`git grep -l "TODO\|Status:.*TODO" docs/`)
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

**Next Milestone:** M1 (Plumbing implementation) or continue design exploration

## Milestone 1: Read-Only Plumbing

**Status:** Blocked (depends on M0 completion)

**Goal:** Implement core JSONL-based tools for reading claude.ai conversations

**Deliverables:**

- [ ] `bin/plumbing/claifs-list-orgs` - List organizations
- [ ] `bin/plumbing/claifs-list-convos` - List conversations for org
- [ ] `bin/plumbing/claifs-get-convo` - Get messages for conversation
- [ ] `bin/plumbing/claifs-render-md` - Render messages to markdown
- [ ] `lib/claifs/api.py` - API client wrapper
- [ ] `lib/claifs/cache.py` - Filesystem cache (read-only)
- [ ] `lib/claifs/models.py` - Data structures
- [ ] Integration tests (full pipeline)
- [ ] Session key setup docs

**Dependencies:** M0 (Documentation)

**Success Criteria:**

- Can pipe plumbing tools:
  `claifs-list-orgs | claifs-list-convos | claifs-get-convo | claifs-render-md`
- Output is valid JSONL (except render-md outputs markdown)
- Works with jq for filtering/transforming
- Cache writes conversations to `./claudefs/` structure
- Manual testing with real claude.ai account works

**Estimated Effort:** 2-3 weeks

**Deferred:**

- Staleness checking (read from cache, don't refresh)
- Lazy stub file creation
- Porcelain commands
- Write operations

**Implementation Notes:**

See [plan/milestone-1-plumbing.md](plan/milestone-1-plumbing.md) for task
breakdown.

**Key tasks:**

1. Wrap unofficial-claude-api in `lib/claifs/api.py`
2. Implement data models in `lib/claifs/models.py`
3. Implement `claifs-list-orgs` (simplest, no input needed)
4. Implement `claifs-list-convos` (takes org UUID)
5. Implement `claifs-get-convo` (takes convo UUID)
6. Implement `claifs-render-md` (formats messages)
7. Implement cache writes in `lib/claifs/cache.py`
8. Test full pipeline end-to-end

## Milestone 2: Multi-Provider Support

**Status:** Blocked (depends on M1 completion)

**Goal:** Add ChatGPT support, refactor for provider abstraction

**Deliverables:**

- [ ] `lib/claifs/providers/` module structure
- [ ] `lib/claifs/providers/claude.py` - Claude provider
- [ ] `lib/claifs/providers/chatgpt.py` - ChatGPT provider
- [ ] Plumbing tools accept `--provider` flag
- [ ] Cache structure: `./claudefs/chatgpt/`, `./claudefs/claude.ai/`
- [ ] ChatGPT unofficial API integration (TBD which library)
- [ ] Tests for both providers

**Dependencies:** M1 (Plumbing working for Claude)

**Success Criteria:**

- Same plumbing tools work for both Claude and ChatGPT
- `echo '{"provider":"chatgpt"}' | claifs-list-orgs` works
- Cache keeps providers separate
- Provider-specific quirks abstracted in provider modules

**Estimated Effort:** 2 weeks

**Deferred:**

- Gemini support (lower priority)
- Provider auto-detection
- Cross-provider search

**Implementation Notes:**

**Provider abstraction:**

```python
# lib/claifs/providers/base.py
class Provider(ABC):
    @abstractmethod
    def list_organizations(self) -> List[Org]: ...

    @abstractmethod
    def list_conversations(self, org_uuid: str) -> List[Conversation]: ...

    @abstractmethod
    def get_conversation(self, convo_uuid: str) -> List[Message]: ...

# lib/claifs/providers/claude.py
class ClaudeProvider(Provider):
    def __init__(self, session_key: str):
        self.client = Client()  # unofficial-claude-api

# lib/claifs/providers/chatgpt.py
class ChatGPTProvider(Provider):
    # TBD: Which unofficial ChatGPT API to use?
```

**Plumbing changes:**

```bash
# Before
claifs-list-orgs

# After
claifs-list-orgs --provider claude
echo '{"provider":"chatgpt"}' | claifs-list-convos
```

## Milestone 3: Write Operations

**Status:** Blocked (fork representation undecided)

**Goal:** Support appending, forking, amending conversations

**Deliverables:**

- [ ] Fork representation decision (see design-incubators/fork-representation/)
- [ ] `bin/plumbing/claifs-append` - Add message to conversation
- [ ] `bin/plumbing/claifs-fork` - Fork conversation at message
- [ ] `bin/plumbing/claifs-amend` - Edit message in conversation
- [ ] Cache write operations with fork tracking
- [ ] Tests for write operations

**Dependencies:**

- M1 (Read-only plumbing)
- Fork representation design resolved

**Blockers:**

- Fork representation undecided (flat naming? nested dirs? git-like refs?)
- Need real API investigation of how claude.ai represents forks

**Success Criteria:**

- Can append message:
  `echo '{"convo_uuid":"...", "text":"..."}' | claifs-append`
- Can fork conversation:
  `echo '{"convo_uuid":"...", "fork_name":"try-alt"}' | claifs-fork`
- Filesystem reflects fork structure (per chosen design)
- Cache maintains fork relationships

**Estimated Effort:** TBD (depends on fork complexity)

**Deferred:**

- Merge forks (unclear if API supports)
- Rename forks
- Delete messages

**Implementation Notes:**

Must resolve
[design-incubators/fork-representation/](../../design-incubators/fork-representation/)
first.

## Tier 2: Maybe Soon, Maybe Later

Features identified but not scheduled:

### Obsidian Integration

- Verify markdown + YAML frontmatter compatibility
- Test wikilinks between conversations
- Graph view support

**Effort:** Low (may be free if format already compatible)

### Frontmatter CLI Suite

- `claifs-frontmatter-read` - Extract YAML frontmatter
- `claifs-frontmatter-write` - Update frontmatter fields
- `claifs-frontmatter-edit` - Modify while preserving formatting

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

**Rationale:** Nice-to-have, not core functionality. Re-evaluate after M1-M2
complete.

## Decision Points

### After M0: Start Implementation or Continue Design?

**Option A: Start M1 immediately**

- Pros: Working code sooner, learn from implementation
- Cons: Fork representation unresolved (will need refactor later)

**Option B: Resolve fork representation first**

- Pros: Better architecture, avoid refactoring later
- Cons: Slower to working MVP, may over-design

**Recommendation:** Start M1 (read-only doesn't need forks). Resolve forks in
parallel or defer to M3.

### After M1: Multi-Provider or Porcelain?

**Option A: M2 (Multi-provider)**

- Pros: Validates abstraction early, more useful (ChatGPT + Claude)
- Cons: More complex before basics work well

**Option B: Build porcelain first**

- Pros: Better UX sooner, easier to use
- Cons: Doesn't teach us about provider abstraction

**Recommendation:** Depends on user needs. If primarily using Claude, build
porcelain first. If want both providers, do M2.

### After M1/M2: Capnshell Integration?

If capnshell exists by then:

1. Define capnproto schemas
2. Add `--output-format capnp` to plumbing tools
3. Test in capnshell
4. Deprecate JSONL? (Or keep both)

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

- [design-rationale.md](design-rationale.md) - Why these milestones and order
- [technical-design.md](technical-design.md) - What we're building
- [plan/milestone-1-plumbing.md](plan/milestone-1-plumbing.md) - Detailed M1
  tasks
