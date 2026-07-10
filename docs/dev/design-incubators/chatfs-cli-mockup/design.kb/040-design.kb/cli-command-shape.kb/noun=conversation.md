# noun=conversation

A `conversation` is the unit of chat data for one ChatGPT thread: a fork
tree of messages, per-turn content, and metadata. Each conversation has a
canonical UUID and lives at `.chat/$UUID/` in the chatfs root; the
user-facing entry point is a view dir-symlink at
`YYYY/MM/DD/HH-MM-SS-$TITLE → .chat/$UUID/`. Storage layout is defined in
`../chat-as-directory.md` and `../chat-as-directory.kb/`.

## Addressing

Two locators target a conversation:

- **URL** — `https://chatgpt.com/c/$UUID`. Canonical; the entry point
  when the chat dir doesn't yet exist (first capture). See
  `noun=conversation.kb/locator=url.md`.
- **Path** — any filesystem path inside or referencing the chat dir.
  Used to refresh an existing chat. See
  `noun=conversation.kb/locator=path.md`.

Both locators resolve to the same canonical `.chat/$UUID/` (via
`resolve_chat_dir` for paths, `chat_dir_for` for URLs).

## Verbs

- **browse** — capture conversation state from chatgpt.com (see
  `noun=conversation.kb/verb=browse.md`).
- **render** — emit `chat.md` from captured state (see
  `noun=conversation.kb/verb=render.md`).

No top-level `splat` command at the conversation noun: the splatting inside
`path render` (`chatgpt-splat`) is an internal helper, not a user-facing
verb. See `../verb=splat.md`.
