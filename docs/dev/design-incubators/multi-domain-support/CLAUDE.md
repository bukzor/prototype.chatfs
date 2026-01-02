# Provider Abstraction Strategy

## The Core Problem

chatfs started as "claude.ai conversations as filesystem" but the concept generalizes: **any structured API data could benefit from Unix tool composability**.

**Question:** Should we expand chatfs beyond chat providers, and if so, how?

**Note:** This is a strategic/scope question. For technical details on normalizing chat providers specifically, see `../chat-provider-normalization/`.

## Two Categories of Providers

### Category 1: Chat Providers (Easy)

**Similar data models:** Organizations, conversations, messages with roles

**Candidates:**
- Claude (claude.ai)
- ChatGPT (chat.openai.com)
- Google AI Studio (aistudio.google.com)

**Challenge:** Subtle differences (fork models, message types, metadata fields)

**Abstraction difficulty:** Moderate - mostly alignment of field names and schemas

### Category 2: Non-Chat Providers (Hard)

**Different data models:** Projects/tickets, repos/issues, resources/instances

**Candidates:**
- Linear (projects → tickets → comments)
- GitHub (repos → issues/PRs → comments)
- GCP (projects → resources → configs)
- AWS (accounts → services → resources)

**Challenge:** Fundamentally different hierarchies and relationships

**Abstraction difficulty:** High - may need provider-specific schemas with minimal commonality

## Key Questions

### 1. Should we support both categories?

**Option A: Chat-only abstraction**
- M2-VFS normalizes across Claude/ChatGPT/Google AI Studio only
- Non-chat providers get separate projects (linear-fs, github-fs, gcp-fs)
- Pro: Focused, clean abstraction for one problem domain
- Con: Misses opportunity for code/tool reuse

**Option B: Universal abstraction**
- M2-VFS provides generic "entity/relationship" schema
- All providers map to common model
- Pro: Maximum reuse, one set of cache/CLI tools
- Con: Abstraction likely too generic to be useful (lowest common denominator)

**Option C: Tiered abstraction**
- M2-VFS-Chat for conversation providers (Claude, ChatGPT, Google AI Studio)
- M2-VFS-Issues for ticket/issue providers (Linear, GitHub)
- M2-VFS-Cloud for resource providers (GCP, AWS)
- Each tier has appropriate abstraction, shares cache/CLI infrastructure
- Pro: Right level of abstraction per domain
- Con: More upfront design, multiple schemas to maintain

### 2. What belongs in the normalized layer?

**Must normalize:**
- Primary entity types (conversation, message, etc.)
- Timestamps, identifiers
- Hierarchical relationships

**Might normalize:**
- Metadata fields (tags, labels, status)
- Search/filtering capabilities
- Permission models

**Should NOT normalize:**
- Provider-specific features that don't map well
- Complex computed fields
- Provider-specific optimizations

### 3. How do we handle provider-specific extensions?

**Approach A: Strict schema**
- M2-VFS defines exact fields
- Provider layers must fit into schema or drop data
- Pro: Consistent, predictable
- Con: Loses valuable provider-specific features

**Approach B: Extension fields**
- Core schema + `extensions: {provider_name: {...}}`
- Tools can access provider-specific data if needed
- Pro: Preserves all data
- Con: Tools need provider-specific logic to use extensions

**Approach C: Capability flags**
- Providers declare what features they support
- Tools query capabilities and adapt
- Pro: Graceful degradation
- Con: Complex capability system to maintain

## Investigation Tasks

### For Category 1 (Chat providers):

- [ ] Document Claude API structure (from M1-CLAUDE investigation)
- [ ] Research ChatGPT API/unofficial client for conversation structure
- [ ] Research Google AI Studio API for conversation structure
- [ ] Identify common fields vs provider-specific
- [ ] Design normalized conversation/message schema (see chat-provider-normalization/)
- [ ] Prototype M2-VFS with 2 chat providers to validate

### For Category 2 (Non-chat providers):

- [ ] Research Linear API (projects/tickets/comments model)
- [ ] Research GitHub API (repos/issues/PRs model)
- [ ] Identify if useful abstraction exists across domains
- [ ] Decide: Separate projects vs unified abstraction
- [ ] If unified: Design generic entity schema
- [ ] If separate: Define boundaries (what code is shared?)

## Success Criteria

The chosen approach should:

1. **Enable adding providers without breaking existing tools** - New provider = new layer, no cache/CLI changes
2. **Preserve useful provider-specific features** - Not just lowest common denominator
3. **Make common operations natural** - List/get/search work the same way across providers
4. **Allow specialization when needed** - Tools can detect provider and use specific features
5. **Minimize abstraction overhead** - Don't normalize for the sake of normalizing

## Blocking Relationships

**This incubator blocks:**
- Long-term architecture decisions (what domains to support)
- Non-chat provider development (if we decide to support them)

**This incubator depends on:**
- M1-CLAUDE findings (need concrete data from at least one provider)
- chat-provider-normalization experience (how hard is Category 1 abstraction?)
- fork-representation Phase 1 (forks are a key differentiator between providers)

## Related

See also:
- [fork-representation/] - Fork models differ significantly between providers
- [technical-design.md] - Overall architecture decisions
