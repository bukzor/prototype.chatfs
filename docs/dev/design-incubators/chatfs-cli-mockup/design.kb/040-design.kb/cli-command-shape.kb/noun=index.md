# noun=index

`index` is the enumeration of conversations in the user's ChatGPT sidebar:
pages of `{id, title, create_time, update_time}` records served by
`/backend-api/conversations`.

## Lifecycle

- `chatgpt index browse` drives `har-browse` against
  `https://chatgpt.com`, captures the sidebar CDP traffic, plucks the
  conversations pages with `chatfs_chatgpt_layout.pluck_index_pages`, and
  emits one page per line on stdout (jsonl).
- `chatgpt index splat` reads that jsonl on stdin and, for each item,
  calls `place_meta` — writing `.chat/$UUID/meta.json` and creating the
  view dir-symlink `YYYY/MM/DD/HH-MM-SS-$TITLE → .chat/$UUID/`. Placement
  mechanics live in `../chat-as-directory.kb/`.

## Why the index matters

The index is one of two places title is captured. Chats reached via the
sidebar get `meta.json` through `index splat`. Chats reached by URL
(`chatgpt conversation url browse`) get `meta.json` through
*browse-incidental capture* — `har-browse` records the same
`/backend-api/conversations` request while loading the conversation
page, and the URL-browse pipeline plucks that side-capture to extract
the title. See `../browse-incidental-capture.md`.

Without one of these paths a chat has no human-readable title.
