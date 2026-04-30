# chatfs-mockup — what should the filesystem *look* like?

A small, hand-driven prototype of the chatfs surface — built on real
captured data from chatgpt.com, but without any FUSE involvement yet.
The goal is to settle the directory layout and lazy-loading idioms by
materializing a static mockup we can `ls`, `tree`, `cd`, and `cat`.

## Pipeline

End-to-end runs capture → splat (per-conversation) → render. Per
timestamp directory:

```
chatfs.demo/chatgpt/YYYY/MM/DD/HH:MM:SS/
    meta.json                 # one item from /backend-api/conversations
    cdp.jsonl                 # raw CDP from har-browse for this conversation
    $UUID.json                # plucked conversation mapping document
    $UUID.splat/              # chatgpt-splat output (per-message .md/.json)
    $TITLE.md                 # rendered current_node path with dead-branch asides
```

There are two entry points for capturing a single conversation:

- **By URL** (most common) — one browse fetches both the conversation
  document and the sidebar index page; we derive `meta.json` from the
  latter and place files under the right ts-dir.
- **By path** — used after `index browse` + `index splat` have already
  laid down ts-dirs, when iterating across many conversations.

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
   pages on stdin and materializes the date tree, placing `meta.json`
   and a broken `$TITLE.md` self-symlink per timestamp directory.
3. **Conversation URL browse**
   (`chatfs_chatgpt_conversation_url_browse.py <url>`) — captures one
   chat by URL: browses to a staging dir, runs both pluck filters,
   filters the index pluck to the matching item for `meta.json`,
   derives the ts-dir from `create_time`, rebuilds it, and delegates
   to path render. Fails loudly if the sidebar didn't include the
   target.
4. **Conversation path browse**
   (`chatfs_chatgpt_conversation_path_browse.py <ts-dir>`) — captures
   one chat into an existing ts-dir (which already has `meta.json`
   from index splat), then delegates to path render.
5. **Path render** (`chatfs_chatgpt_conversation_path_render.py <ts-dir>`) — splats
   `$UUID.json` and runs the conversation render, redirecting its
   stdout into `$TITLE.md`.
6. **Conversation render**
   (`chatfs_chatgpt_conversation_render.py <ts-dir>`) — walks the full
   mapping tree from `current_node` back to root, streams H1 turn
   headings `(seq · role · time, variant suffix)` linking to atomic
   `.md` files under `messages/`. Dead branches render as nested
   blockquoted asides at their fork point; depth = nesting in `> `
   prefixes. Markdown goes to stdout.

Every stage rebuilds its outputs from scratch (no freshness caches);
see `design.kb/040-design.kb/deterministic-regeneration.md`.

## Run it

```bash
cd docs/dev/design-incubators/chatfs-mockup-chatgpt

# single conversation by URL — common case
./chatfs_chatgpt_conversation_url_browse.py https://chatgpt.com/c/<uuid>

# bulk: index first, then iterate ts-dirs
./chatfs_chatgpt_index_browse.sh | ./chatfs_chatgpt_index_splat.py
./chatfs_chatgpt_conversation_path_browse.py <ts-dir>

tree chatfs.demo/ | head -20
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

Once the shape feels right, fold lessons back into design.kb and
delete or archive this incubator.

## Status

- [x] Index capture working against real chatgpt.com
- [x] Date-tree splat with `meta.json` per timestamp directory
- [x] Per-conversation pluck (`/backend-api/conversation/{id}`)
- [x] Render `$TITLE.md` from `current_node` walk
- [x] Dead-branch forks rendered as nested blockquoted asides
- [ ] Multi-provider sketch (claude.ai under same tree?)
