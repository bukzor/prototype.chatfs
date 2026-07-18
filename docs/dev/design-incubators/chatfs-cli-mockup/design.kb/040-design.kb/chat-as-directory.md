---
last-updated: "2026-07-18"
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
    .data/
        69dfa575-c0e0-832c-99c2-4e1919ab50de/
            meta.json          # captured (index endpoint item)
            conversation.json  # captured (conversation endpoint mapping doc)
            cdp.jsonl          # captured (raw CDP)
    .chat/
        69dfa575-c0e0-832c-99c2-4e1919ab50de/
            chat.md            # derived (rendered current_node walk)
            messages/          # derived (chatgpt-splat output)
            conversations/     # derived (chatgpt-splat output)
            .data -> ../../.data/69dfa575-…   # inspection symlink
    Created=YYYY/MM/DD/HH:MM:SS±HH:MM/
        Quantum Gravity and UV Catastrophe -> ../../../../.chat/69dfa575-…
```

Captured exhaust lives in a parallel UUID-keyed tree, `.data/$UUID/`,
leaving `.chat/$UUID/` 100% derived -- a pure function of `.data/$UUID/`,
and the unit of atomic regeneration: built complete in a sibling scratch
(`.chat/.$UUID.tmp/`), promoted into place by rename (mechanism:
`chatfs_atomic.py`).

Readers see the previous complete chat dir or the new one -- never
partial, never mixed (requirement: `atomic-cache-updates`), with no
reader cooperation required. The `.data` symlink keeps captured
artifacts addressable through view paths
(`view/$TITLE/.data/meta.json`) while taking exhaust out of recursive
grep. `.data/$UUID/` never moves and doubles as the per-chat flock
anchor. `.chat/$UUID/` does not exist before first render; the view
symlink dangles until then -- the honest "not yet synced" signal.

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

- **`.data/$UUID/` and `.chat/$UUID/` are canonical storage.** Flat,
  UUID-keyed, and never relocate. `.data/` holds captured artifacts
  (source of truth, not locally re-derivable); `.chat/` holds derived
  outputs, wholly a pure function of `.data/` (see
  `chat-as-directory.kb/captured-vs-derived.md`).
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

The UUID is the chat's identity. The storage paths (`.data/$UUID/` and
`.chat/$UUID/`) are a pure function of identity and never move.
Everything else is derived from `meta.json` content (`create_time`,
`title`): the view path, the title-named symlink, the offset suffix.

If derivation logic changes (new TZ rendering, new view shape), storage
doesn't move; the view rebuilds. There's no migration story for
`.chat/` or `.data/`.

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
