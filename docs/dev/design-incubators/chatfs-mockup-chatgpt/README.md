# chatfs-mockup — what should the filesystem *look* like?

A small, hand-driven prototype of the chatfs surface — built on real
captured data from chatgpt.com, but without any FUSE involvement yet.
The goal is to settle the directory layout and lazy-loading idioms by
materializing a static mockup we can `ls`, `tree`, `cd`, and `cat`.

## Pipeline

End-to-end now runs capture → splat (per-conversation) → render. Per
timestamp directory:

```
chatfs.demo/chatgpt/YYYY/MM/DD/HH:MM:SS/
    meta.json                 # from index splat
    content.cdp.jsonl         # raw CDP from har-browse
    $UUID.json                # plucked conversation document
    $UUID.splat/              # chatgpt-splat output (per-message .md/.json)
    $TITLE.md                 # rendered current_node path with dead-branch asides
```

1. **Index capture** (`chatgpt-index.sh` + `chatgpt-index-pluck.jq`) —
   drives `har-browse` against `https://chatgpt.com`, stores the raw
   CDP event stream as `chatgpt.index.cdp.jsonl`, plucks
   `/backend-api/conversations?...` responses to `chatgpt.index.jsonl`.
   Re-uses the cached CDP file if it is less than an hour old.
2. **Index splat** (`chatgpt-index-splat.py`) — reads the index pages
   on stdin and materializes the date tree, including a `meta.json`
   per timestamp directory.
3. **Per-conversation capture** (`chatgpt-page-capture.py`) — drives
   `har-browse` against each conversation URL, writes
   `content.cdp.jsonl`, runs `chatgpt-conversation-pluck.jq` →
   `$UUID.json`, then `chatgpt-splat` → `$UUID.splat/` (one
   `.json`/`.md` pair per message, plus `conversations/` view).
4. **Render** (`chatgpt-render.py`) — walks the full mapping tree
   from `current_node` back to root, emits H1 turn headings
   `(seq · role · time, variant suffix)` linking to the atomic `.md`
   under `messages/`. Dead branches render as nested blockquoted
   asides at their fork point; depth = nesting in `> ` prefixes.

## Run it

```bash
cd docs/dev/design-incubators/chatfs-mockup
./chatgpt-index.sh                              # capture + pluck index
./chatgpt-index-splat.py < chatgpt.index.jsonl  # build the date tree
./chatgpt-page-capture.py <ts-dir>              # capture+splat one conversation
./chatgpt-render.py <ts-dir>                    # write $TITLE.md
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
