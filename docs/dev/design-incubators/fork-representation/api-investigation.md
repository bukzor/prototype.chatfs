# Claude API Fork Investigation

**Status:** TODO (fill during M1-CLAUDE implementation)
**Purpose:** Document actual Claude API behavior for forked conversations

## Investigation Checklist

- [ ] Create test forked conversations on claude.ai
- [ ] Use unofficial-claude-api to inspect API responses
- [ ] Document JSON structure for forked conversations
- [ ] Test fork-of-fork scenarios
- [ ] Document fork metadata fields

## Critical Questions

### 1. How does Claude.ai represent forks in the API?

**Unknown:**
- Do forks appear as separate conversation UUIDs?
- Is there a parent_uuid field?
- How is fork ancestry represented?

**Findings:** (TODO: fill during investigation)

### 2. What fork metadata exists?

**Unknown:**
- fork_point (message ID where fork occurred)?
- created_at for forks?
- fork_name or auto-generated identifier?
- Full ancestry chain?

**Findings:** (TODO: fill during investigation)

### 3. How are fork relationships represented?

**Unknown:**
- Tree structure with parent references?
- Graph with bidirectional links?
- Linear linked list?

**Findings:** (TODO: fill during investigation)

### 4. What happens when you fork a fork?

**Unknown:**
- Multiple levels of nesting supported?
- How is multi-level ancestry tracked?

**Findings:** (TODO: fill during investigation)

### 5. Do forked conversations appear in list_conversations()?

**Unknown:**
- Separate entries for each fork?
- Grouped with parent somehow?
- Special filter/flag needed?

**Findings:** (TODO: fill during investigation)

## Raw API Examples

### Example 1: Simple Fork

```json
TODO: Add actual JSON response from unofficial-claude-api
```

### Example 2: Fork of Fork

```json
TODO: Add actual JSON response showing nested forks
```

### Example 3: Multiple Forks from Same Parent

```json
TODO: Add actual JSON showing sibling forks
```

## Data Model Summary

(TODO: After examples collected, summarize the data model)

**Relationship type:** (tree? graph? list?)

**Key fields:**
- conversation_uuid: ...
- parent_uuid: ...
- fork_point: ...
- other fields: ...

## Implications for M2-VFS

(TODO: After investigation complete, note what this means for normalized schema design)

**For M2-VFS normalization:**
- What fields are Claude-specific vs. universal?
- What should the normalized fork schema look like?
- How does this compare to other providers?

## Next Steps

After completing this investigation:

1. Use findings to inform M2-VFS normalized schema design
2. See `../chat-provider-normalization/` for cross-provider normalization
3. Eventually inform M3-CACHE filesystem layout decisions
