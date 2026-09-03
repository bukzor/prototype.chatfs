# noun=index

`index` is the enumeration of conversations in the user's ChatGPT sidebar:
pages of `{id, title, create_time, update_time}` records served by
`/backend-api/conversations`.

## Lifecycle

- `chatgpt index browse` drives `har-browse` against
  `https://chatgpt.com`, captures the sidebar CDP traffic, plucks the
  conversations pages with `chatfs.provider.chatgpt.pluck.pluck_index_pages`,
  and emits one page per line on stdout (jsonl).
- `chatgpt index splat` reads that jsonl on stdin and, for each item,
  calls `place_meta` — writing `.data/$UUID/meta.json` and creating the
  view dir-symlink `YYYY/MM/DD/HH-MM-SS-$TITLE → .chat/$UUID/`. Placement
  mechanics live in `../chat-as-directory.kb/`.
- `chatgpt index` (bare noun) runs those two as a subprocess pipe over
  one `--cache`. The whole lifecycle is browse-then-splat with no
  branch point, which is what earns the noun a driver at all -- see
  `../cli-command-shape.md`'s "Why a bare-noun driver".

## What index splat emits

Splat's stdout is one **placement record** per chat placed --
`{id, title, chat_dir, view}` -- not an echo of its input. The stream
answers "what landed, and where", which is what a consumer of a fresh
index actually acts on; re-emitting the provider's index pages would
just be `tee` of the bulkiest thing in the pipeline.

Identity is the normalized pair `place_meta` already takes, not the
provider's own field names (claude's `uuid`/`name`, chatgpt's
`id`/`title`, AI Studio's synthesized pair). One `jq` works against
every provider's stream.

`chat_dir` is the machine handle -- it's what `conversation path
browse` and `conversation path render` take as their argument, so
`index | jq -r .chat_dir | xargs` is the whole bulk-capture loop.
`view` is the human handle, the titled symlink a person navigates to.

Deliberately absent: `created`. It's already in `meta.json` and already
encoded in `view`'s path segments, and emitting it uniformly would mean
re-deriving AI Studio's create_time/last_modified fallback outside the
`place_meta` wrapper that owns that choice.

Present, and none of those objections apply to it: `updated` -- when
the provider last saw the conversation change, ISO 8601, or `null`
where the provider's payload doesn't say. It is not recoverable from
`view`'s path (which encodes creation, or AI Studio's honest
`LastModified=` stand-in for it), and it is not recoverable from
`meta.json` either at the moment a consumer needs it: splat rewrites
`meta.json` from the fresh index item before the record reaches
anyone, so the value it would be compared against is already
overwritten. Nor does it face the fallback problem `created` has --
AI Studio's `last_modified` *is* the updated timestamp, always present,
with no choice to re-derive.

What it buys is the whole basis for `refresh`: recency (is this chat
inside the window?) and staleness (is our capture older than the
provider's last change?) are both answered from the stream, without a
second pass over storage. See `verb=refresh.md`.

The driver (`chatfs-provider-<provider>-index`) does not compose this stream
itself: it emits whatever its last stage emits, because it *is* the
pipe (`../driver-model.md`). A driver with stdout of its own would be
a third implementation of the index flow rather than a way to run the
existing one.

## Why the index matters

The index is one of two places title is captured. Chats reached via the
sidebar get `meta.json` through `index splat`. Chats reached by URL
(`chatgpt conversation url browse`) get `meta.json` through
*browse-incidental capture* — `har-browse` records the same
`/backend-api/conversations` request while loading the conversation
page, and the URL-browse pipeline plucks that side-capture to extract
the title. See `../browse-incidental-capture.md`.

Without one of these paths a chat has no human-readable title.
