# chatfs-mockup — what should the filesystem *look* like?

A small, hand-driven prototype of the chatfs surface — built on real
captured data from chatgpt.com, but without any FUSE involvement yet.
The goal is to settle the directory layout and lazy-loading idioms by
materializing a static mockup we can `ls`, `tree`, `cd`, and `cat`.

## Pipeline

End-to-end runs capture → splat (per-conversation) → render. Storage
is flat and UUID-keyed; the date tree is a view of symlinks pointing
into storage (see `design.kb/040-design.kb/chat-as-directory.md`).

```
chatfs.demo/chatgpt/
    .chat/$UUID/
        chat.md                   # rendered current_node path with dead-branch asides
        messages/                 # chatgpt-splat output (per-message .md/.json)
        conversations/            # chatgpt-splat output (per-branch symlinks)
        .data/                    # captured exhaust (hidden from default ls)
            meta.json             # one item from /backend-api/conversations
            conversation.json     # plucked conversation mapping document
            cdp.jsonl             # raw CDP from har-browse for this conversation
    YYYY/MM/DD/HH:MM:SS±HH:MM/
        $TITLE -> ../../../../.chat/$UUID/      # single directory-symlink per chat
```

The view entry is a directory-symlink — `view/$TITLE/` *is* the chat
dir. `cat 2026/.../$TITLE/chat.md` reads chat content;
`cat 2026/.../$TITLE/messages/<stem>.md` reads atomic turn content
textually (web renderers and editors both work).

There are two entry points for capturing a single conversation:

- **By URL** (most common) — one browse fetches both the conversation
  document and the sidebar index page; we derive `meta.json` from the
  latter and place files into `.chat/$UUID/`.
- **By path** — used after `index browse` + `index splat` have already
  laid down chat dirs, when iterating across many conversations.

### Stages

Leaf stages read stdin and write stdout (data only; progress goes to
stderr). Higher-level orchestrators take an addressable target (URL or
ts-dir), tee intermediate streams to disk for debuggability, and drive
the leaves.

1. **Index browse** (`chatfs_chatgpt_index_browse.sh`) — drives
   `har-browse` against `https://chatgpt.com`, tees the raw CDP to
   `chatgpt.index.cdp.jsonl` (debug intermediate), pipes through
   `chatfs_chatgpt_index_pluck.jq`, emits index pages on stdout.
2. **Index splat** (`chatfs_chatgpt_index_splat.py`) — reads index
   pages on stdin; per item, writes `.chat/$UUID/.data/meta.json`,
   purges any prior view symlinks for that UUID, and places a fresh
   `$TITLE` directory-symlink under the date tree.
3. **Conversation URL browse**
   (`chatfs_chatgpt_conversation_url_browse.py <url>`) — captures one
   chat by URL: browses to a staging dir, runs both pluck filters,
   filters the index pluck to the matching item for `meta.json`,
   moves captures into `.chat/$UUID/.data/`, calls `place_meta`, and
   delegates to path render. Fails loudly if the sidebar didn't
   include the target.
4. **Conversation path browse**
   (`chatfs_chatgpt_conversation_path_browse.py <chat-dir>`) — writes
   `cdp.jsonl` and `conversation.json` directly into
   `.chat/$UUID/.data/` (which already has `meta.json` from index
   splat), then delegates to path render.
5. **Path render** (`chatfs_chatgpt_conversation_path_render.py <chat-dir>`) —
   purges non-captured contents (allowlist `{".data"}`), splats
   `.data/conversation.json`, moves `messages/` and `conversations/`
   from `.data/conversation.splat/` up two levels into the chat-dir
   root, and runs the conversation render, redirecting its stdout
   into `chat.md`.
6. **Conversation render**
   (`chatfs_chatgpt_conversation_render.py <chat-dir>`) — walks the
   full mapping tree from `current_node` back to root, streams H1 turn
   headings `(seq · role · time, variant suffix)` linking to atomic
   `.md` files under `messages/`. Dead branches render as nested
   blockquoted asides at their fork point; depth = nesting in `> `
   prefixes. Markdown goes to stdout.

Every stage rebuilds its outputs from scratch (no freshness caches);
see `design.kb/040-design.kb/deterministic-regeneration.md`.

## Run it

```bash
cd docs/dev/design-incubators/chatfs-cli-mockup

# single conversation by URL — common case
./chatfs_chatgpt_conversation_url_browse.py https://chatgpt.com/c/<uuid>

# bulk: index first, then iterate chat dirs
./chatfs_chatgpt_index_browse.sh | ./chatfs_chatgpt_index_splat.py
./chatfs_chatgpt_conversation_path_browse.py chatfs.demo/chatgpt/.chat/<uuid>/

tree chatfs.demo/chatgpt/ | head -20
```

## Why this incubator

The pipeline `BB1 (capture) → BB2 (extract) → BB3 (render)` is
specified in the design.kb in terms of JSONL streams. This incubator
asks the perpendicular question: **what does the user-facing surface
look like?** Decisions to settle here:

- Hierarchy: by date? by title? by provider/account/conversation? Mix?
- Lazy markers: broken symlink? empty file? extended attribute?
- Filename collisions (titles, timestamps): suffix scheme? UUID fallback?
- Per-conversation layout: single file? `messages/`, `forks/` subdirs?

This is a prototype of a future `chatfs-cli` that will be load-bearing
for the final chatfs — the same CLI surface FUSE invokes lazily under
the hood. Lessons settled here get folded back to project-level
`design.kb/`; the code itself graduates to `lib/chatfs/` once
libraryized.

## Status

- [x] Index capture working against real chatgpt.com
- [x] Date-tree splat with `meta.json` per timestamp directory
- [x] Per-conversation pluck (`/backend-api/conversation/{id}`)
- [x] Render `$TITLE.md` from `current_node` walk
- [x] Dead-branch forks rendered as nested blockquoted asides
- [x] Multi-provider: claude.ai (2026-05-11) and AI Studio (2026-06-20..07-03) landed under the same tree
