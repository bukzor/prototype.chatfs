# Fork Representation in Lazy Filesystem

## The Core Problem

Claude.ai conversations support forking: at any message, you can branch to
explore alternative directions. Users often maintain 2-3 active forks per
conversation, switching between them for different perspectives.

**Challenge:** Represent this branching structure in a filesystem that:

- Supports lazy loading (don't fetch until accessed)
- Feels natural for CLI tools (grep, cat, ls)
- Preserves fork relationships and navigation
- Enables future write operations (append, fork, amend)

## What We Need to Learn First

**Critical unknowns about Claude.ai fork API:**

1. How does the API represent forks? (parent_uuid? fork_point? ancestry chain?)
2. What's in the conversation metadata for forked conversations?
3. Can we list all forks from a parent conversation?
4. How are forks identified? (separate UUID? same UUID + branch ID?)

**Action:** Investigate API responses for forked conversations before committing
to filesystem design.

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
                                 # claifs-forks "tshark-filtering.md"
                                 # claifs-cat "tshark-filtering.md#fork-2"
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

1. **API Investigation:** Use existing unofficial-claude-api to inspect forked
   conversation responses
2. **Create test data:** Find or create forked conversations on claude.ai
3. **Document API structure:** Write down exact JSON fields for forks
4. **Prototype approaches:** Implement Option A and Option B with real data
5. **User testing:** Which feels better for grep/navigation?

## Success Criteria

The chosen approach should:

- Enable `grep -r "search term" ./claudefs/` across all forks
- Make it obvious when a conversation has forks (`ls` should reveal them)
- Support adding new forks without breaking existing structure
- Feel intuitive for someone familiar with file trees
