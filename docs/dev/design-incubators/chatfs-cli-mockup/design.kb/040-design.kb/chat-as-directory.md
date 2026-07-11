---
last-updated: "2026-05-08"
why:
  - opaque-extractor-boundary
  - canonical-conversation-graph
  - atomic-cache-updates
---

# Chat as Directory

A chat is a directory in a flat, UUID-keyed canonical store. Everything
else under `chatfs.demo/chatgpt/` is a *view* — a tree of symlinks
derived from that store.

## Layout

```
chatfs.demo/chatgpt/
    .chat/
        69dfa575-c0e0-832c-99c2-4e1919ab50de/
            chat.md                # derived (rendered current_node walk)
            messages/              # derived (chatgpt-splat output)
            conversations/         # derived (chatgpt-splat output)
            .data/                 # captured exhaust (hidden from default ls)
                meta.json          # captured (index endpoint item)
                conversation.json  # captured (conversation endpoint mapping doc)
                cdp.jsonl          # captured (raw CDP)
    Created=YYYY/MM/DD/HH:MM:SS±HH:MM/
        Quantum Gravity and UV Catastrophe -> ../../../../.chat/69dfa575-…
```

## Multiple labeled date-trees

The year segment carries a `Label=` prefix (`time_dir_for`'s `label`
param, default `Created`) naming what the timestamp actually is —
uniformly, not just for the exceptional case — so multiple date-based
views can coexist under `root` without colliding or implying a claim
the underlying data can't back up:

- `Created=YYYY/…` — true creation time (the default; every provider
  that can supply it uses this).
- `LastModified=YYYY/…` — AI Studio's index rung (`ListPrompts`) has no
  turn content, so it can't derive a first-chunk creation time; rather
  than launder its `lastModified` timestamp into a false `Created=`
  claim (see `no-partial-synthesis.md`), it gets its own honestly
  labeled tree. Once the same chat is later fetched in full (real
  `create_time` known), re-`place_meta` purges the `LastModified=`
  symlink by uuid and re-places it under `Created=` — it "graduates."

Same mechanism as future by-tag/by-model/by-starred views: a differently
labeled tree, still just symlinks into `.chat/`.

The view entry is a single directory-symlink: the named view path *is*
the chat directory. `cat 2026/.../$TITLE/chat.md` resolves to
`.chat/$UUID/chat.md`; `cat 2026/.../$TITLE/messages/<stem>.md` resolves
textually (no symlink resolution required after the dir-symlink is
followed once). Inline `messages/<stem>.md` links inside `chat.md` work
under both real-path and view-path reads — including from path-textual
renderers (web rendering, mkdocs, Obsidian publish).

## Storage vs view

The two halves of the tree have different jobs:

- **`.chat/$UUID/` is canonical storage.** Flat, UUID-keyed, written
  once and only once per chat. Source of truth for everything about
  that chat — captured artifacts and derived outputs alike.
- **`YYYY/MM/…/` is a view.** A tree of symlinks pointing into
  `.chat/`. Wholly derivable from the storage layer — `rm -rf YYYY/`
  loses no data.

Other views can be added later (by-tag, by-model, by-starred, etc.)
without touching the storage layer. They are all `ln -s .chat/$UUID/…`
from a single source.

Decoupling storage from view means:
- `time_dir_for` semantics can change without moving data.
- Multiple views coexist without duplicating storage.
- A pathological view (broken symlink, stale title) is repaired by
  rebuild, not by re-capture.

## Identity is primary; storage is canonical

The UUID is the chat's identity. The storage path
(`.chat/$UUID/`) is a pure function of identity and never moves.
Everything else is derived from `meta.json` content (`create_time`,
`title`): the view path, the title-named symlink, the offset suffix.

If derivation logic changes (new TZ rendering, new view shape), storage
doesn't move; the view rebuilds. There's no migration story for
`.chat/`.

The cleanup rule that supports this — every verb removes prior
artifacts it is about to replace, identified by what they supersede
rather than by where they live — is articulated in
`deterministic-regeneration.md` ("Identity-scoped cleanup").

## See also

- `chat-as-directory.kb/` — sub-points: captured-vs-derived discipline,
  the front-door symlink mechanics, collision tolerance, pipeline
  script-by-script implications.
- `deterministic-regeneration.md` — the broader rule that `place_meta`'s
  symlink-purge implements.
- `no-partial-synthesis.md` — why `meta.json` and `conversation.json`
  stay separate files even though both describe the same chat.
