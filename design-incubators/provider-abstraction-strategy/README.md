# Provider Abstraction Strategy Investigation

## Problem Statement

How do we design M2-API (normalized layer) to support multiple data providers while keeping the abstraction useful and not overly generic?

## Current Status

- [ ] Category 1 (chat providers) research - need Claude API data from M1-CLAUDE
- [ ] Category 2 (non-chat providers) research - Linear, GitHub, GCP/AWS
- [ ] Decision on abstraction approach (chat-only, universal, or tiered)
- [ ] Normalized schema design for chosen approach

## Investigation Approach

1. **M1-CLAUDE first:** Get concrete Claude API data
2. **Research comparable providers:** ChatGPT, Gemini structure
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
- `DECISION.md` - Chosen abstraction approach with rationale
- `schema.md` - Normalized JSONL schema specification
- Update `technical-design.md` with M2-API design

## Related Incubators

- [fork-representation/] - Fork models vary significantly between providers
