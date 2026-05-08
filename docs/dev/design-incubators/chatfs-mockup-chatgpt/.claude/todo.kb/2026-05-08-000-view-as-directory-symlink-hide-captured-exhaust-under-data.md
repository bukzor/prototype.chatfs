---
anthropic-skill-ownership: llm-subtask
---

# View as directory-symlink; hide captured exhaust under .data/

**Priority:** Medium (ergonomic + correctness improvement; doesn't block
other work but blocks any web-rendering use case)
**Complexity:** Medium (touches `place_meta`, all browse/render scripts,
design.kb, README; mostly mechanical once the shape is fixed)
**Context:**
- `design.kb/040-design.kb/chat-as-directory.md` — the storage/view split
- `design.kb/040-design.kb/chat-as-directory.kb/view-symlink.md` — current
  view-symlink mechanics (will be rewritten)
- `design.kb/040-design.kb/chat-as-directory.kb/captured-vs-derived.md` —
  current captured allowlist (will simplify to `{".data"}`)

## Problem Statement

Inline `messages/<stem>.md` links inside `chat.md` are valid when the
file is read via the real path (`.chat/$UUID/chat.md`) or via a
symlink-resolving reader (editors, POSIX file APIs). They break when a
path-textual renderer (web rendering — GitHub Pages, mkdocs, Obsidian
publish) reads `chat.md` via the view symlink at
`YYYY/.../$TITLE.md`: `messages/` doesn't exist alongside the symlink,
so the link 404s.

This is a real bug — we don't document bugs.

## Current Situation

View dir contains two symlinks per chat:

```
YYYY/MM/DD/HH:MM:SS±TZ/
    $TITLE.md   -> ../../../../.chat/$UUID/chat.md
    .chat       -> ../../../../.chat/$UUID
```

Inside `.chat/$UUID/`: 6 entries — 3 captured (`meta.json`,
`conversation.json`, `cdp.jsonl`), 3 derived (`chat.md`, `messages/`,
`conversations/`). Captured exhaust mingles with the user surface.

`chat.md` inline links are textual `messages/<stem>.md`.
`conversations/` is a sibling derived dir whose internal symlinks point
into `messages/` — not referenced from `chat.md`.

## Proposed Solution

**Collapse the view to a single directory-symlink, hide captured exhaust.**

```
chatfs.demo/chatgpt/
    .chat/$UUID/
        chat.md              # user surface
        messages/            # user surface
        conversations/       # user surface
        .data/               # captured exhaust (hidden)
            meta.json
            conversation.json
            cdp.jsonl
    YYYY/MM/DD/HH:MM:SS±TZ/
        $TITLE -> ../../../../.chat/$UUID
```

Why this works:
- The view-dir entry IS the chat dir (via symlink). Path-textual
  renderers reading `2026/.../$TITLE/messages/<stem>.md` resolve to
  `.chat/$UUID/messages/<stem>.md`. Links work everywhere.
- Single symlink per view dir (vs two today). `.chat` shortcut
  redundant — the view IS the chat.
- Visible chat-dir surface matches user intent: `chat.md`,
  `messages/`, `conversations/`. Captured exhaust hidden in `.data/`
  (out of `ls`'s default view).
- Allowlist purge simplifies: `keep = {".data"}` — one name, not
  three. New derived outputs need no allowlist update.
- Same-second collisions still handled — ts-dir stays a real
  directory, hosts one `$TITLE` per chat at that second.

Ergonomic cost: `cat date/$TITLE.md` → `cat date/$TITLE/chat.md`. One
extra path component. `chat.md` is stable across all chats — arguably
better for muscle memory than per-chat title-derived filenames.

## Implementation Steps

- [ ] `chatfs_chatgpt_layout.py`:
  - [ ] `place_meta`: replace title-`.md` symlink + `.chat` shortcut
        with single `$TITLE → .chat/$UUID/` directory-symlink
  - [ ] Write `meta.json` to `.chat/$UUID/.data/meta.json`
  - [ ] `mkdir .chat/$UUID/.data/` if missing
  - [ ] `CAPTURED_FILES` constant → `CAPTURED_DIR = ".data"` (or
        equivalent); update consumers
  - [ ] `_purge_view_symlinks` unchanged (still scans for symlinks
        whose target contains UUID)
- [ ] `chatfs_chatgpt_index_splat.py`: no change beyond the layout
      module (it just calls `place_meta`)
- [ ] `chatfs_chatgpt_conversation_path_browse.py`:
  - [ ] Read meta from `.data/meta.json`
  - [ ] Write `cdp.jsonl` and `conversation.json` to `.data/`
- [ ] `chatfs_chatgpt_conversation_url_browse.py`:
  - [ ] Move staged captures into `.data/` (not chat-dir root)
- [ ] `chatfs_chatgpt_conversation_path_render.py`:
  - [ ] `purge_non_captured`: keep only `.data/`; rm everything else
  - [ ] Read `conversation.json` from `.data/`
  - [ ] Splat unchanged (output to `.data/conversation.splat`?
        TBD — whether splat output goes through `.data/` or directly
        to chat dir; design decision)
- [ ] `chatfs_chatgpt_conversation_render.py`:
  - [ ] Read `conversation.json` from `.data/`
  - [ ] `messages/` lookup unchanged (still at chat-dir root)
- [ ] `chatfs_chatgpt_conversation_url_render.py`: no change
- [ ] Design docs:
  - [ ] `chat-as-directory.md` — update layout block
  - [ ] `chat-as-directory.kb/view-symlink.md` — rewrite for
        directory-symlink (drop `$TITLE.md` filename ergonomics
        section; emphasize that view IS chat dir via symlink)
  - [ ] `chat-as-directory.kb/captured-vs-derived.md` — simpler
        allowlist (`.data/`)
  - [ ] `chat-as-directory.kb/pipeline-implications.md` — update
        per-script descriptions
  - [ ] `chat-as-directory.kb/collision-tolerance.md` — same logic;
        verify wording still accurate
  - [ ] `deterministic-regeneration.md` — update purge example if it
        still references the old layout
- [ ] `README.md` — update layout block and `Run it` example
- [ ] Smoke test: rm-rf demo, re-splat from `chatgpt.index.jsonl`,
      migrate captures for the test chat into `.data/`, re-render,
      verify links resolve from view path textually
- [ ] Live URL test (interactive `har-browse`; user-driven)

## Open Questions

- **Splat output location.** `chatgpt-splat` writes
  `<src>.splat/{messages,conversations}` next to its input. If input
  moves to `.data/conversation.json`, splat writes to
  `.data/conversation.splat/`. Then we unpack `messages/` and
  `conversations/` up *two* levels (out of `.data/conversation.splat/`,
  out of `.data/`, into chat-dir root). Or we splat into a tmp dir and
  move outputs explicitly. Decide before coding.
- **Should `.data/meta.json` be readable through the view?** Currently
  it would be: `view/$TITLE/.data/meta.json` → `.chat/$UUID/.data/meta.json`.
  That's fine — `.data/` is hidden from `ls` but reachable via known path.
- **What about `chatgpt.index.cdp.jsonl` (the index-level debug
  intermediate at incubator root)?** Out of scope — it's incubator
  exhaust, not chat-scoped. Leaves as-is.

## Success Criteria

- [ ] View dir contains exactly one entry per chat (the dir-symlink).
- [ ] `cat 2026/.../$TITLE/chat.md` reads chat content (via symlink
      resolution).
- [ ] `cat 2026/.../$TITLE/messages/<stem>.md` reads atomic turn
      content textually (no symlink resolution required).
- [ ] `ls 2026/.../$TITLE/` shows `chat.md`, `messages/`,
      `conversations/` (and `.data/` only with `-a`).
- [ ] `path_render` allowlist purge keeps only `.data/`; everything
      else is rebuilt.
- [ ] Live URL re-capture works end-to-end.
- [ ] Design docs and README reflect new layout.

## Notes

This was prompted by a content-spot-check: the inline `messages/<stem>.md`
links in `chat.md` resolve from the real chat dir but break textually
from the view symlink. Three rejected alternatives:

1. Document the limitation — rejected: we don't document bugs.
2. Add `messages` (and originally `conversations`) symlinks beside
   `$TITLE.md` in each view dir — rejected: leaves a multi-symlink view
   shape and `conversations/` was overreach (not referenced from
   `chat.md`).
3. Make `chat.md` links absolute — rejected: messy, not relocatable.

A user-suggested fourth option ("ts-dir IS the symlink, no nesting") was
rejected because it loses title-in-path navigation and can't host
same-second-different-title collisions.
