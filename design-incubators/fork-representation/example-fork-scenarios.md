# Example Fork Scenarios

These examples illustrate common forking patterns to test filesystem design
against.

## Scenario 1: Simple Fork (Two Alternative Approaches)

**User workflow:**

1. Ask Claude about implementing authentication
2. Claude suggests OAuth
3. User forks at message #4, asks about JWT instead
4. Now has two threads: OAuth approach, JWT approach

**Expected filesystem behavior:**

```bash
chatfs-ls "Buck Evan/2025-10-30"
# Should show: authentication-design.md (or both forks?)

chatfs-forks "Buck Evan/2025-10-30/authentication-design.md"
# oauth-approach
# jwt-approach

chatfs-cat "Buck Evan/2025-10-30/authentication-design.md"
# Which fork do we show? Main? Most recent? Ask user?
```

## Scenario 2: Multiple Forks at Different Points

**User workflow:**

1. Discussion about database design (10 messages)
2. Fork at message #4: Try NoSQL instead of SQL
3. Fork at message #8: Explore caching strategies
4. Now has three threads branching at different points

**Questions:**

- Do we show this as three separate conversations?
- Or one conversation with two forks?
- How do we represent the fork points?

## Scenario 3: Fork-of-Fork (Nested Forks)

**User workflow:**

1. Main thread: Python web framework discussion
2. Fork 1: Try FastAPI approach (5 more messages)
3. Fork 1.1: FastAPI with async/await
4. Fork 1.2: FastAPI with threading
5. Main thread continues separately

**Tree structure:**

```
main
├── [continues independently]
└── fork-1: fastapi
    ├── [continues]
    ├── fork-1.1: async
    └── fork-1.2: threading
```

**Questions:**

- How deep can this nesting go?
- Should filesystem mirror the tree structure?
- How do we navigate "up" the tree?

## Scenario 4: Intentional Perspective Switching

**User workflow (common pattern):**

1. Create "optimistic" fork: Assume system works perfectly
2. Create "pessimistic" fork: Assume system faces constraints
3. Switch between them frequently to check both perspectives
4. Never merge - both views stay active

**User expectations:**

- Easy switching: `chatfs-switch-fork optimistic`
- Compare forks: `diff fork1.md fork2.md`
- Grep both: `grep "database" *.md`

## Scenario 5: Abandoned Forks

**User workflow:**

1. Create fork to explore dead-end idea
2. Realize it won't work after 2 messages
3. Return to main thread, forget about fork

**Questions:**

- Do abandoned forks clutter the filesystem?
- Should they auto-hide after N days of inactivity?
- Or always visible (user decides what to keep)?

## Scenario 6: Late Fork Discovery

**User workflow:**

1. Browse old conversations with `chatfs-ls "Buck Evan/2024-06-15"`
2. See `database-design.md`
3. `cat database-design.md` - reads main thread
4. Doesn't realize there were 2 forks until running `chatfs-forks`

**Questions:**

- Should forks be visually obvious in `ls` output?
- Or hidden by default (don't clutter)?
- Compromise: `ls -a` shows all, `ls` shows main only?

## Design Test: Score Each Approach

For each candidate filesystem layout (A/B/C from CLAUDE.md), walk through these
scenarios and ask:

1. **Is the fork structure obvious?**
2. **Is navigation intuitive?**
3. **Does `grep` work naturally?**
4. **Would write operations (fork/append) fit naturally?**
5. **Does it scale to 10 forks? 50 forks?**

## Real-World Usage Patterns to Support

Based on user's stated behavior ("I use forking a ton"):

**High priority:**

- List all forks at a glance
- Switch between 2-3 active forks quickly
- Grep across all forks of a conversation
- Diff two forks

**Medium priority:**

- Navigate fork-of-fork hierarchies
- See fork points (where conversation diverged)
- Identify abandoned forks

**Low priority:**

- Merge forks (probably not supported by API?)
- Rename forks (if API allows)
- Archive old forks (hide from default view)
