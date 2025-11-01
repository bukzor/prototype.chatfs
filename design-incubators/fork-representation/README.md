# Fork Representation Design

This subdirectory focuses on solving one critical problem: **How to represent
forked Claude.ai conversations in a lazy filesystem.**

## Why This Matters

Fork representation is a **foundation decision** that affects:

- Directory structure and file naming
- Data format (JSON schema, frontmatter fields)
- All write operations (append, fork, amend)
- CLI tool design (navigation, listing, diffing)

We must get this right before implementing write operations.

## Investigation Phase

### Step 1: Understand the API

**Run:** `./investigate-forks.py <uuid-of-forked-conversation>`

This will reveal:

- How Claude.ai API represents fork relationships
- What metadata is available (parent_uuid, fork_point, etc.)
- Whether forks are separate conversations or branches within one

**To create test data:**

1. Go to claude.ai
2. Start a conversation
3. At any message, click "fork" or edit a previous message
4. Copy the conversation UUID from the URL
5. Run the investigation script

### Step 2: Document Findings

Create `api-findings.md` with:

- Raw JSON examples of forked conversations
- Field descriptions
- Relationship model (tree? graph? linked list?)

### Step 3: Prototype Filesystem Layouts

Test the candidate approaches from CLAUDE.md:

- **Option A:** Flat naming (`conversation.fork-name.md`)
- **Option B:** Nested directories (`conversation/forks/name/`)
- **Option C:** Git-like refs (`.conversation/refs/fork-name/`)

Create mock directory trees and test:

```bash
# Can I list all forks easily?
ls -R

# Can I grep across all forks?
grep -r "search term"

# Is navigation intuitive?
cd into/various/forks

# How would append work?
# How would creating a new fork work?
```

### Step 4: Score and Decide

Use evaluation criteria from CLAUDE.md:

1. Lazy-friendly (implementation complexity)
2. CLI-natural (works with standard tools)
3. Fork clarity (obvious navigation)
4. Write-ready (supports future operations)
5. Obsidian-friendly (wikilinks, graph view)

### Step 5: Document the Decision

Create `DECISION.md` with:

- Chosen approach
- Rationale (scored evaluation)
- Implementation spec
- Migration considerations (if changing from initial approach)

## Current Status

- [ ] API investigation (need forked conversation UUIDs)
- [ ] Document API structure (`api-findings.md`)
- [ ] Prototype Option A
- [ ] Prototype Option B
- [ ] Prototype Option C
- [ ] Score approaches
- [ ] Make decision (`DECISION.md`)
- [ ] Update parent README with chosen approach

## Open Questions

1. **How does Claude.ai represent forks in the API?**

   - Separate conversation UUIDs?
   - Parent/child relationships?
   - Full ancestry chain?

2. **Can we list all forks from a parent?**

   - Is there an API endpoint for this?
   - Or do we need to track it ourselves?

3. **What happens when you fork a fork?**

   - Tree structure?
   - How deep can it go?

4. **Do forked conversations appear in date-based listings?**

   - Do they have their own created_at?
   - Or do they inherit from parent?

5. **How do we handle fork naming?**
   - User-provided names?
   - Auto-generated from first diverging message?
   - UUID-based references?

## Tools

- `investigate-forks.py` - Examine API structure of forked conversations
- (More to come as we prototype filesystem layouts)
