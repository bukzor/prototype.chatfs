---
anthropic-skill-ownership: llm-subtask
---

# chatgpt-splat: parse_messages unit-factor and mutation-testing

**Priority:** Medium
**Complexity:** Medium
**Context:** `packages/bukzor.chatgpt-export/lib/bukzor/chatgpt_export/splat.py:148`

## Problem Statement

`parse_messages` is the most complex pure function in splat.py — handles root detection, timestamp extraction with fallback, role extraction through three nesting levels, and wires up `extract_text_content`. Zero direct test coverage. All behavior tested only transitively through e2e.

## Current Situation

The function is ~30 lines with multiple branches (no-message root case, timestamp present/absent, author present/absent). Currently covered only by the e2e test that runs the full pipeline.

## Proposed Solution

1. Factor `parse_messages` into smaller testable units (extract timestamp, extract role, etc.)
2. Write direct unit tests for each
3. Run `/mutation-testing` to verify test quality

## Implementation Steps

- [ ] Factor out timestamp extraction (handles None, 0, missing cases)
- [ ] Factor out role extraction (handles missing author, missing role)
- [ ] Write tests for each extracted function
- [ ] Write integration tests for `parse_messages` itself
- [ ] Run `/mutation-testing` against the refactored code

## Open Questions

- How granular should the factoring be? Some helpers may be 3-4 lines.

## Success Criteria

- [ ] `parse_messages` has direct test coverage for all branches
- [ ] `/mutation-testing` passes with high confidence
- [ ] Pyright still at 0 errors
