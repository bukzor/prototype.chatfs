# Provider Abstraction Design

This incubator focuses on: **How to design M2-VFS to abstract across different chat/project APIs while preserving their unique features.**

## Why This Matters

M2-VFS is the **normalized layer** that sits between provider-specific native layers (M1-CLAUDE, M1-CHATGPT) and the cache/UI layers. Getting the abstraction wrong would:

- Force awkward mappings from native APIs
- Lose important provider-specific features
- Make adding new providers difficult
- Create leaky abstractions that break composability

## Investigation Approach

### Step 1: Build Concrete Case (M1-CLAUDE)

**Don't design abstraction first.** Instead:

1. Build M1-CLAUDE as direct wrapper around Claude API
2. Output whatever Claude returns, make no normalization decisions
3. Document everything thoroughly

**Rationale:** We need to understand what APIs actually provide before designing how to normalize them.

### Step 2: Analyze Patterns

After M1-CLAUDE complete:

1. What patterns emerged?
2. What feels Claude-specific vs. universal?
3. Research other providers (ChatGPT, Linear)
4. Look for common abstractions

### Step 3: Design Normalized Schema

With concrete examples in hand:

1. Design JSONL schemas for normalized layer
2. Decide: pure abstraction vs. abstraction+extensions?
3. Define provider interface contract
4. Validate design works for planned providers

### Step 4: Document Decision

Create `DECISION.md` with:
- Chosen abstraction strategy
- Normalized JSONL schemas
- Provider interface specification
- Rationale and tradeoffs

## Current Status

- [ ] M1-CLAUDE implementation complete
- [ ] Claude API fully documented
- [ ] ChatGPT API research
- [ ] Pattern analysis across providers
- [ ] Normalized schema design
- [ ] Provider interface design
- [ ] DECISION.md created

## Related Incubators

- **fork-representation/** - Phase 2 (normalized fork schema) depends on this incubator
- **fork-representation/** - Phase 1 (Claude API investigation) informs this incubator

## Critical Questions

See [CLAUDE.md](./CLAUDE.md) for detailed questions, including:

1. Should M2-VFS support provider-specific extensions?
2. How do we normalize fork representation across providers?
3. Should Linear use the same VFS layer as chat providers?
4. Do we need provider capability detection?

## Files

- `CLAUDE.md` - Problem definition and investigation plan
- `README.md` - This file (workflow and status)
- `DECISION.md` - (TODO: create after M1-CLAUDE complete) Final design decision
