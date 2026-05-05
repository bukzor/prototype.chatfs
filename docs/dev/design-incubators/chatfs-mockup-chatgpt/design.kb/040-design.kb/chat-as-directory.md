---
last-updated: "2026-05-05"
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
            chat.md                # ergonomic view
            meta.json              # captured (index endpoint item)
            conversation.json      # captured (conversation endpoint mapping doc)
            cdp.jsonl              # captured (raw CDP)
            messages/              # derived (chatgpt-splat output)
            conversations/         # derived (chatgpt-splat output)
    YYYY/MM/DD/HH:MM:SS±HH:MM/
        Quantum Gravity and UV Catastrophe.md -> ../../../../.chat/69dfa575-…/chat.md
        .chat -> ../../../../.chat/69dfa575-…
```

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
