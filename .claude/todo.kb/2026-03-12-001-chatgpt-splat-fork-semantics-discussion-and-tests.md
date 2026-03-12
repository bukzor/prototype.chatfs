---
anthropic-skill-ownership: llm-subtask
---

# chatgpt-splat: fork semantics discussion and tests

**Priority:** Low
**Complexity:** Medium
**Context:** `packages/bukzor.chatgpt-export/lib/bukzor/chatgpt_export/splat.py:191`

## Problem Statement

Two related issues with fork representation need discussion:

### #12: Child message appears in two ConversationLinks

At a fork, child message `a` appears in:
1. The fork link's `messages` list (creates branch directory via `ConversationLink.write()`)
2. Its own single-message link inside the branch (creates symlinks)

This means a consumer iterating all links would see message `a` twice. The fork link creates "scaffolding" (directories) while the branch link creates "content" (symlinks). This works but is an implicit contract — `ConversationLink` doesn't distinguish these roles.

### #2: Fork write naming

`ConversationLink.write()` for forks creates directories + subdirectories, but "write" undersells the scaffolding role. May warrant clearer naming or documentation.

## Open Questions

- Should `ConversationLink` have a `kind` field (e.g., "link" vs "fork") to make the dual role explicit?
- Should consumers be expected to filter fork links, or should the API prevent double-counting?
- Would splitting into separate types (Link vs Fork) be cleaner than one type with implicit roles?
- Are there downstream use cases that would break with the current design?

## Implementation Steps

- [ ] Discuss design tradeoffs with user
- [ ] Add tests that make fork behavior explicit (verify what appears where)
- [ ] Decide on and implement any naming/structural changes
