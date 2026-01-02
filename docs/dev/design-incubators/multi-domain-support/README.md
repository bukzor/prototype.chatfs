# Multi-Domain Provider Support

## Problem Statement

**Strategic decision:** Should chatfs support only chat LLM providers (Claude/ChatGPT/Google AI Studio), or also extend to other domains (Linear/GitHub/AWS/GCP)?

This is about scope and architecture strategy, not the technical details of normalization (see `chat-provider-normalization/` for that).

## Current Status

- [ ] Category 1 (chat providers) research - need Claude API data from M1-CLAUDE
- [ ] Category 2 (non-chat providers) research - Linear, GitHub, GCP/AWS
- [ ] Decision on abstraction approach (chat-only, universal, or tiered)
- [ ] Normalized schema design for chosen approach

## Investigation Approach

1. **M1-CLAUDE first:** Get concrete Claude API data
2. **Research comparable providers:** ChatGPT, Google AI Studio structure
3. **Research non-chat providers:** Linear, GitHub, cloud APIs
4. **Evaluate abstraction approaches:** Chat-only vs universal vs tiered
5. **Design schema:** Based on concrete provider data
6. **Prototype:** Implement M2-API for 2+ providers to validate

## Key Questions

1. Should we support chat + non-chat providers, or focus on chat-only?
2. What belongs in normalized layer vs provider-specific extensions?
3. How do we handle provider-specific features (forks, threads, labels, etc.)?

## Deliverables

When resolved:
- `DECISION.md` - Chosen scope strategy with rationale (chat-only, universal, or tiered)
- Update `technical-design.md` with long-term architecture strategy
- If tiered: Define tier boundaries and shared infrastructure

## Related Incubators

- **chat-provider-normalization/** - Technical design for normalizing chat providers (Category 1)
- **fork-representation/** - Fork models vary significantly between providers
