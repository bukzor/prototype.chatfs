---
anthropic-skill-ownership: llm-subtask
status: done
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

- [x] `chatfs_chatgpt_layout.py`:
  - [x] `place_meta`: replace title-`.md` symlink + `.chat` shortcut
        with single `$TITLE → .chat/$UUID/` directory-symlink
  - [x] Write `meta.json` to `.chat/$UUID/.data/meta.json`
  - [x] `mkdir .chat/$UUID/.data/` if missing
  - [x] `CAPTURED_FILES` constant → `DATA_DIR_NAME = ".data"`;
        update consumers
  - [x] `_purge_view_symlinks` unchanged
  - [x] `resolve_chat_dir` simplified — walks up to `.chat`-parent;
        the `.chat`-shortcut branch goes away
- [x] `chatfs_chatgpt_index_splat.py`: unchanged (calls `place_meta`)
- [x] `chatfs_chatgpt_conversation_path_browse.py`:
  - [x] Read meta from `.data/meta.json`
  - [x] Write `cdp.jsonl` and `conversation.json` to `.data/`
- [x] `chatfs_chatgpt_conversation_url_browse.py`:
  - [x] Move staged captures into `.data/` (not chat-dir root)
- [x] `chatfs_chatgpt_conversation_path_render.py`:
  - [x] `purge_non_captured`: keep only `.data/`; rm everything else
  - [x] Read `conversation.json` from `.data/`
  - [x] Splat into `.data/conversation.splat/`; move `messages/` and
        `conversations/` up two levels into chat-dir root, then
        rmdir splat (Approach A from the open question)
- [x] `chatfs_chatgpt_conversation_render.py`:
  - [x] Read `conversation.json` from `.data/`
  - [x] `messages/` lookup unchanged (still at chat-dir root)
- [x] `chatfs_chatgpt_conversation_url_render.py`: meta-presence check
      now reads `.data/meta.json`
- [x] Design docs:
  - [x] `chat-as-directory.md` — updated layout block + textual-link
        explanation
  - [x] `chat-as-directory.kb/view-symlink.md` — rewritten for
        directory-symlink
  - [x] `chat-as-directory.kb/captured-vs-derived.md` — `.data/`
        allowlist
  - [x] `chat-as-directory.kb/pipeline-implications.md` — updated
  - [x] `chat-as-directory.kb/collision-tolerance.md` — wording
        updated for dir-symlink
  - [x] `deterministic-regeneration.md` — updated index-splat and
        path-render bullets
- [x] `README.md` — layout block + `Run it` references updated
- [x] Smoke test: rm-rf demo, re-splat from `chatgpt.index.jsonl`,
      `place_meta` test chat, copy captures into `.data/`, re-render,
      verify links resolve from view path textually; pyright clean
- [x] Live URL test (interactive `har-browse`; user-driven) — ran
      against `https://chatgpt.com/c/69de8f14-e80c-8329-b3a8-3e4046c10cb1`,
      262 messages → 206 turns, three-phrase content spot-check passed

## Open Questions (resolved)

- **Splat output location.** Resolved as Approach A: splat into
  `.data/conversation.splat/`, move `messages/` and `conversations/`
  up two levels into chat-dir root, rmdir the splat. Mirrors the
  prior pattern (one extra path component); no tmp-dir staging.
- **`.data/meta.json` readable through the view.** Yes —
  `view/$TITLE/.data/meta.json` resolves correctly. `.data/` is hidden
  from default `ls` but reachable via known path.
- **`chatgpt.index.cdp.jsonl` (incubator-level intermediate).** Out of
  scope — incubator exhaust, not chat-scoped. Left as-is.

## Success Criteria

- [x] View dir contains exactly one entry per chat (the dir-symlink).
- [x] `cat 2026/.../$TITLE/chat.md` reads chat content (via symlink
      resolution).
- [x] `cat 2026/.../$TITLE/messages/<stem>.md` reads atomic turn
      content textually (no symlink resolution required).
- [x] `ls 2026/.../$TITLE/` shows `chat.md`, `messages/`,
      `conversations/` (and `.data/` only with `-a`).
- [x] `path_render` allowlist purge keeps only `.data/`; everything
      else is rebuilt.
- [x] Live URL re-capture works end-to-end (verified against
      `https://chatgpt.com/c/69de8f14-…`; 262 messages → 206 turns).
- [x] Design docs and README reflect new layout.

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
