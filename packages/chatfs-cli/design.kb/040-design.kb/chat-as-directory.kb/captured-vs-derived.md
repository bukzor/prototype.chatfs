# Captured vs Derived

Split by lifecycle, split by tree:

- **Captured.** `meta.json`, `conversation.json`, `cdp.jsonl`. Written
  by browse stages directly from provider data. Expensive to regenerate
  (requires Chromium). Lives in the parallel tree `.data/$UUID/`.
- **Derived.** `chat.md`, `messages/`, `conversations/`. Written by
  render stages from captured state. Cheap to regenerate. Lives in
  `.chat/$UUID/` — the user surface.

```
.data/$UUID/
    meta.json
    conversation.json
    cdp.jsonl
.chat/$UUID/
    chat.md            # derived
    messages/          # derived
    conversations/     # derived
    .data -> ../../.data/$UUID   # inspection symlink
```

## Staged promotion, not an allowlist

Captured and derived artifacts no longer share a directory, so
path-render needs no advance purge at all: `conversation_path_render`
builds the entire derived surface (`chat.md`, `messages/`, the `.data`
inspection symlink) in a staged scratch sibling and atomically promotes
it over `.chat/$UUID/` in one swap (see
`../deterministic-regeneration.md`). New derived outputs need no
path-render change — whatever the splat tool emits into the scratch is
what gets promoted.

The `.data` symlink (inside `.chat/$UUID/`, pointing at `.data/$UUID/`)
has two jobs:

1. **Hidden from default `ls`.** The user-visible chat surface is
   `chat.md`, `messages/`, `conversations/` — what they came for.
   `ls -a` reveals `.data` for inspection.
2. **Reachable through the view symlink.** `view/$TITLE/.data/meta.json`
   resolves through `.chat/$UUID/.data -> .data/$UUID/` to
   `.data/$UUID/meta.json`. Captured artifacts stay addressable for
   debugging, just out of the way for normal browsing.
