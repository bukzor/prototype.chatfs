---
status: observed
first-recorded: 2026-05-12
last-checked: 2026-05-12
evidence:
  - claude.index.complete.2026-05-11.jsonl  # index page containing the test UUID, 15-field item
  - claude.chat.b0f46746-e087-44de-9d34-ce0e15027d6b.jsonl  # conversation doc, 11 top-level fields
---

# claude conversation vs index endpoints — meta field shapes

The two claude endpoints expose overlapping but distinct field sets
for the same conversation.

## Index `/chat_conversations_v2?…` per item (15 fields)

`uuid, name, summary, model, created_at, updated_at, settings,
is_starred, is_temporary, project_uuid, session_id, platform,
current_leaf_message_uuid, user_uuid, project`

## Conversation `/chat_conversations/{id}` top-level (11 fields)

`uuid, name, summary, model, created_at, updated_at, settings,
is_starred, is_temporary, platform, current_leaf_message_uuid`

(plus `chat_messages: [...]`, which index doesn't carry)

## The four extras and why they don't bite (yet)

The index-only fields are `project_uuid`, `session_id`, `user_uuid`,
`project`. In the test data (a non-project personal chat) all four
were null. Hypothesis: project/session/user are null for non-project
solo chats and populated only for project-context conversations.

This is why `chatfs_claude_conversation_url_browse.py` uses
**null-tolerant** cross-check between conversation-derived and
index-derived meta: missing-on-one-side or null-on-either-side is
treated as match. Catches divergence where it'd matter (non-null
disagreement) without firing on the structural shape difference.

## See also

- `chatfs_claude_types.py` — `IndexItem` TypedDict (declares the
  three fields we actually read; the rest are pass-through).
- `chatfs_claude_conversation_url_browse.py:null_tolerant_mismatches`
- The four extras are a candidate test signal once we see a real
  project chat — if `project_uuid` is non-null in index but absent
  in conversation doc, the null-tolerant check still passes (one
  side null); we'd only fail if both sides have non-null values
  that disagree.
