# Fork Representation in Lazy Filesystem

## The Core Problem

Claude.ai conversations support forking: at any message, you can branch to
explore alternative directions. Users often maintain 2-3 active forks per
conversation, switching between them for different perspectives.

**Challenge:** Represent this branching structure across three layers of abstraction:

1. **What does the Claude API return?** (M1-CLAUDE: claude-native layer)
2. **What should our normalized API provide?** (M2-API: standardized layer)
3. **How do we represent forks on disk?** (M3-CACHE: filesystem layer)

Each question builds on the previous answer. We can't normalize what we don't understand, and we can't persist what we haven't normalized.

## Three-Phase Investigation

### Phase 1: Claude API Investigation (M1-CLAUDE)

**Question:** What does claude.ai actually return for forked conversations?

**Critical unknowns:**
1. How does the API represent forks? (parent_uuid? fork_point? ancestry chain?)
2. What's in the conversation metadata for forked conversations?
3. Can we list all forks from a parent conversation?
4. How are forks identified? (separate UUID? same UUID + branch ID?)
5. Do forked conversations appear in `list_conversations()`?

**Action:** Investigate API responses for actual forked conversations (user has essential content on multiple forks)

**Deliverable:** Document exact API behavior in `api-findings.md`

### Phase 2: Normalized Schema Design (M2-API)

**Question:** What should our provider-agnostic API provide?

**Depends on:** Phase 1 findings + ChatGPT/other provider research

**Critical unknowns:**
1. What fork metadata is common across providers (Claude, ChatGPT, Linear)?
2. How do we represent provider-specific fork features in normalized schema?
3. What fork operations need to work across all providers?

**Deliverable:** Normalized JSONL schema for forks that works across providers

### Phase 3: Filesystem Representation (M3-CACHE)

**Question:** How do we represent forks on disk?

**Depends on:** Phase 2 normalized schema

**Critical unknowns:**
1. Flat naming? Nested directories? Git-like refs? (see candidate approaches below)
2. How to make fork navigation obvious with standard Unix tools?
3. How to support lazy loading while preserving fork relationships?

**Deliverable:** `DECISION.md` with chosen filesystem layout

## Design Constraints

**Must support:**

- Lazy creation (directories/files appear only when accessed)
- Multiple forks from same conversation point
- Fork navigation (list forks, switch between them, see ancestry)
- Standard POSIX operations (ls, cat, grep work naturally)
- Future write operations (appending may create new forks)

**Nice to have:**

- Obsidian compatibility (wikilinks, graph view)
- Git-like semantics (familiar mental model)
- Minimal filesystem clutter

## Candidate Approaches

### Option A: Flat Naming Convention

```
2025-10-29/
├── tshark-filtering.md                    # Original conversation
├── tshark-filtering.fork-try-python.md    # Fork 1
├── tshark-filtering.fork-use-wireshark.md # Fork 2
└── tshark-filtering.jsonl                 # Raw data (all forks?)
```

**Pros:**

- Simple, flat structure
- Easy to list all forks: `ls tshark-filtering*.md`
- Each fork is independently addressable file

**Cons:**

- Naming gets messy with deep fork trees
- Hard to represent fork-of-fork relationships
- Clutters date directories with many forks

### Option B: Nested Directories

```
2025-10-29/
└── tshark-filtering/
    ├── main.md
    ├── main.jsonl
    └── forks/
        ├── try-python/
        │   ├── thread.md
        │   └── thread.jsonl
        └── use-wireshark/
            ├── thread.md
            └── thread.jsonl
```

**Pros:**

- Clear hierarchy (fork-of-fork naturally nested deeper)
- Date directories stay clean
- Groups related forks together

**Cons:**

- Deeper paths for common operations
- `main.md` vs `thread.md` inconsistency
- More complex lazy loading logic

### Option C: Symlinks + Hidden Refs

```
2025-10-29/
├── tshark-filtering.md          # Symlink to .forks/main/thread.md
└── .tshark-filtering/
    ├── forks.index.json         # Fork metadata
    └── refs/
        ├── main/
        │   ├── thread.md
        │   └── thread.jsonl
        ├── try-python/
        │   ├── thread.md
        │   └── thread.jsonl
        └── use-wireshark/
            ├── thread.md
            └── thread.jsonl
```

**Pros:**

- Git-like mental model (refs, hidden .git-style dir)
- Date directory looks clean (one file per conversation)
- Fork isolation in hidden structure

**Cons:**

- Symlinks complicate lazy loading
- Hidden directories may surprise users
- More complex to implement

### Option D: Virtual Paths (No Real Forks Until Accessed)

```
2025-10-29/
└── tshark-filtering.md          # Contains all forks in frontmatter
                                 # Virtual commands expose forks:
                                 # chatfs-forks "tshark-filtering.md"
                                 # chatfs-cat "tshark-filtering.md#fork-2"
```

**Pros:**

- Minimal filesystem footprint
- Defer fork materialization until needed
- Fragment-style addressing (#fork-2)

**Cons:**

- Can't use standard ls/grep to discover forks
- Requires custom tooling for all fork operations
- Breaks "just files" philosophy

## Evaluation Criteria

**Score each approach (1-5):**

1. **Lazy-friendly:** Easy to implement lazy loading?
2. **CLI-natural:** Works with standard tools (ls/cat/grep)?
3. **Fork clarity:** Obvious how to navigate forks?
4. **Write-ready:** Supports future append/fork operations?
5. **Obsidian-friendly:** Works with [[wikilinks]] and graph view?

## Next Steps

**Immediate (M1-CLAUDE):**
1. Use existing unofficial-claude-api to inspect forked conversation responses
2. User has forked conversations with essential content - investigate those
3. Document exact JSON fields and relationships in `api-findings.md`
4. Implement M1-CLAUDE layer that outputs whatever Claude returns

**Later (M2-API):**
5. Research how other providers (ChatGPT, Linear) handle similar concepts
6. Design normalized schema that accommodates all providers
7. See separate incubator: `provider-abstraction-strategy/`

**Much Later (M3-CACHE):**
8. Prototype filesystem approaches (Option A, B, C) with normalized schema
9. User testing: which feels better for grep/navigation?
10. Write `DECISION.md` with chosen approach

## Success Criteria

The chosen approach should:

- Enable `grep -r "search term" ./chatfs/` across all forks
- Make it obvious when a conversation has forks (`ls` should reveal them)
- Support adding new forks without breaking existing structure
- Feel intuitive for someone familiar with file trees
