# chatfs-mockup — what should the filesystem *look* like?

A small, hand-driven prototype of the chatfs surface — built on real
captured data from chatgpt.com, but without any FUSE involvement yet.
The goal is to settle the directory layout and lazy-loading idioms by
materializing a static mockup we can `ls`, `tree`, `cd`, and `cat`.

## Pipeline

1. **Capture** (`chatgpt-index.sh`) — drives `har-browse` against
   `https://chatgpt.com`, stores the raw CDP event stream as
   `chatgpt.index.cdp.jsonl`. Re-uses the cached file if it is less
   than an hour old.
2. **Pluck** (same script, inline `jq`) — selects responses to
   `/backend-api/conversations?...` and emits one JSON page per line
   to `chatgpt.index.jsonl`.
3. **Splat** (`chatgpt-index-splat.py`) — reads the index pages on
   stdin and materializes a date tree under `chatfs.demo/chatgpt/`:

   ```
   chatfs.demo/chatgpt/YYYY/MM/DD/HH:MM:SS/
       meta.json                      # full item metadata
       $TITLE.md -> $TITLE.md         # broken self-symlink (ELOOP on read)
   ```

   The self-symlink is a placeholder — visible in `ls`, deliberately
   unreadable, signalling "not yet fetched." A future BB2 step will
   replace it with the rendered markdown.

## Run it

```bash
cd docs/dev/design-incubators/chatfs-mockup
./chatgpt-index.sh                              # capture + pluck
./chatgpt-index-splat.py < chatgpt.index.jsonl  # build the tree
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
- [x] Date-tree splat with self-symlink placeholders
- [ ] Per-conversation pluck (`/backend-api/conversation/{id}`)
- [ ] Render placeholder → `$TITLE.md` with actual content
- [ ] Multi-provider sketch (claude.ai under same tree?)
