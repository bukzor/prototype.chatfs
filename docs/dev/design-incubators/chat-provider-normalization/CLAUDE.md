# Chat Provider Normalization Strategy

## The Core Problem

How do we design M2-VFS to normalize across chat LLM providers?

**Chat providers (Claude, ChatGPT, Gemini):**
- Organizations → Conversations → Messages
- Forks/branches (Claude-specific?)
- Streaming responses
- Message types and metadata

## Why This Matters

If we try to design M2-VFS before building M1-CLAUDE, we're guessing at the abstraction. We need concrete cases (Claude API behavior) to inform good abstraction design.

**Key insight:** "We have no idea what we WANT from the normalized layer until we know what we CAN HAVE from the native layer."

This is why M1-CLAUDE (native) must come before M2-VFS (normalized abstraction).

## Critical Questions

### 1. Should M2-VFS support provider-specific extensions?

**Option A: Pure abstraction**
- Only expose features common to all providers
- Lowest common denominator approach
- Simple, but loses provider-specific features

**Option B: Abstraction + extensions**
- Core schema common across providers
- Provider-specific extensions in separate fields
- More complex, but preserves unique features

**Question:** How do we handle features only some providers have (forks, streaming)?

### 2. How do we normalize fork representation?

**Depends on:**
- M1-CLAUDE findings (what does Claude return?)
- ChatGPT research (how do they handle forks?)
- Gemini research (fork support?)

**Questions:**
- Do all chat providers support forks, or is this Claude-specific?
- Should VFS expose provider-specific features?
- How do we represent fork relationships in JSONL?

### 3. Do we need provider capability detection?

If providers have different features, M2-VFS might need:
- Capability flags (supports_forks, supports_streaming, etc.)
- Runtime feature detection
- Graceful degradation for missing features

## Investigation Plan

### Phase 1: Build M1-CLAUDE (concrete case)

1. Implement claude-native layer
2. Document everything the Claude API provides
3. Understand what's actually there (not what we think should be there)

**Deliverable:** Working M1-CLAUDE with complete API documentation

### Phase 2: Analyze Patterns

1. What patterns exist in Claude API?
2. What's Claude-specific vs. likely universal across chat providers?
3. How do other chat providers (ChatGPT, Gemini) structure similar data?

**Deliverable:** Pattern analysis document

### Phase 3: Design M2-VFS

1. Create normalized schema informed by M1-CLAUDE findings
2. Design provider abstraction based on real use cases
3. Validate design against chat providers (Claude, ChatGPT, Gemini)

**Deliverable:** M2-VFS specification and implementation

## Specific Unknowns (M1-CLAUDE will answer)

- How does Claude represent organizations?
- What conversation metadata exists?
- How are forks represented? (see ../fork-representation/)
- What message types exist?
- How is streaming handled?
- What's the pagination model?

## Deferred Decisions (Until M1-CLAUDE complete)

- Exact normalized JSONL schemas for chat providers
- Provider capability detection strategy
- Extension mechanism for provider-specific features

## Success Criteria

The M2-VFS abstraction should:

- Support multiple chat providers (Claude, ChatGPT minimum)
- Preserve essential provider-specific features (if abstraction+extensions approach)
- Be informed by reality (M1-CLAUDE findings), not speculation
- Enable M3-CACHE to work with any provider
- Feel natural to implement new providers against

## Next Steps

**Immediate (during M1-CLAUDE):**
1. Build claude-native layer
2. Document Claude API thoroughly
3. Note what feels universal vs. Claude-specific

**After M1-CLAUDE:**
4. Research ChatGPT API structure
5. Analyze patterns across providers
6. Design M2-VFS normalized schema
7. Write DECISION.md with chosen abstraction strategy
