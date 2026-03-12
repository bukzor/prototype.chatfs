---
anthropic-skill-ownership: llm-subtask
---

# chatgpt-splat: fork semantics discussion and tests

**Priority:** Low
**Complexity:** Low (resolved in session 2026-03-12)

## Resolution

The fork semantics were resolved by refactoring `enumerate_conversation_links`
to a children-first, stack-based traversal. Key decisions:

- **Fork link is sole representative.** The multi-message ConversationLink
  holds the fork children. No separate single-message links are emitted for
  those children. Branches continue from each child's children.

- **Fork write creates symlinks.** `ConversationLink.write()` for forks now
  creates branch subdirectories AND symlinks for each child message (not just
  directories). Each branch dir gets `{link_name}.json` and optional
  `{link_name}.md` symlinks pointing to the message in `messages/`.

- **No dual representation.** A message appears in exactly one ConversationLink.
  Consumers iterating all links see each message exactly once.

- **ConversationLink is the stack item.** The traversal uses ConversationLink
  directly as its stack type — no separate _StackItem needed. `_child_links`
  takes a parent link and yields child links.

## Remaining

- [ ] Could add more fork-specific tests (nested forks, forks with mixed leaf/non-leaf children)
- [x] ~~Discuss design tradeoffs with user~~ (done)
- [x] ~~Add tests that make fork behavior explicit~~ (done: `it_yields_fork_link_at_branch_point`, `it_nests_branch_paths`)
- [x] ~~Decide on and implement structural changes~~ (done)
