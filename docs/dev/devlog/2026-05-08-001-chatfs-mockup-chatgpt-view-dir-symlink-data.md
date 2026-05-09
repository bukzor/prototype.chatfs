# 2026-05-08: chatfs-mockup-chatgpt — view as directory-symlink, captured exhaust under .data/

## Focus

Land the directory-symlink + `.data/` refactor designed earlier today.
Two coupled changes:

1. **View-dir entry shape.** Replace the two-symlink view (`$TITLE.md`
   file-symlink + `.chat` dir-shortcut) with a single directory-symlink
   `$TITLE → .chat/$UUID/`. The view path *is* the chat directory.
2. **Captured exhaust under `.data/`.** Move `meta.json`,
   `conversation.json`, `cdp.jsonl` from chat-dir root into
   `.chat/$UUID/.data/`. Visible chat-dir surface becomes `chat.md`,
   `messages/`, `conversations/`.

Goal: fix the textual-link bug (inline `messages/<stem>.md` references
in `chat.md` 404 under web rendering when read via the view symlink)
and clean up the user surface.

## What Happened

**Docs first.** Updated `chat-as-directory.md` (layout block + textual
link explanation), rewrote `view-symlink.md` for the dir-symlink shape,
simplified `captured-vs-derived.md` to a `{".data"}` allowlist, updated
`pipeline-implications.md` per-script, updated `collision-tolerance.md`
wording, updated the purge example in `deterministic-regeneration.md`,
and the layout block + Run-it bullets in `README.md`.

**Code.** `chatfs_chatgpt_layout.py`: `CAPTURED_FILES` →
`DATA_DIR_NAME = ".data"`; `place_meta` writes
`.chat/$UUID/.data/meta.json` and creates a single
`view/$TITLE → .chat/$UUID/` directory-symlink (relative path);
`resolve_chat_dir` simplified to walk up to the `.chat`-parent (drops
the `.chat`-shortcut branch — view-symlinks now resolve straight to
the chat dir). Browse + render scripts read/write through `.data/`;
`conversation_render` reads `.data/conversation.json`. `path_render`
allowlist became `{DATA_DIR_NAME}`; splat lands in
`.data/conversation.splat/`, then `messages/` and `conversations/`
move up two levels to chat-dir root. `conversation_url_render`
checks `.data/meta.json` for the placement gate.

**Splat output location decided as Approach A.** Splat into `.data/`,
move outputs up two levels. Considered tmp-dir staging (Approach B);
A wins because the splat dir is removed within the same function so
`.data/` never externally contains transient state, and the move is
mechanical.

**Smoke test green.** `mv chatfs.demo trash/...`, re-splat 56 chats
from cached `chatgpt.index.jsonl`, called `place_meta` with the prior
`meta.json` for the URL-captured test chat (`69f21e0c-…`, not in the
sidebar at last index), copied `cdp.jsonl` + `conversation.json` into
`.data/`, ran `path_render` *via the view dir-symlink*
(`2026/04/29/.../Moral Duties in ChatFS`). Splat: 188 messages.
Render: 129 turns. `chat.md` byte-stable vs the prior render. Default
`ls` via view path shows `chat.md`, `conversations`, `messages` —
`.data/` hidden. `ls -la` shows `.data/` too. Re-splat symlink count
stable (374 → 374); re-render byte-stable. Pyright clean (0 errors).

**Textual link resolution verified.** Picked first
`messages/<stem>.md` link from `chat.md`, confirmed
`view/$TITLE/messages/<stem>.md` resolves textually as a real file —
the bug we set out to fix.

## Lessons

**Approach A's splat-into-`.data/` is fine.** The brief moment when
`.data/conversation.splat/` exists is invisible externally (the
function holds the only reference). Worry about purity at observable
boundaries, not at internal sub-steps. Tmp-dir staging would have been
two extra moves with no observable benefit.

**`resolve_chat_dir` got cleaner via the design change.** The old
shape needed special handling for the `.chat`-shortcut branch
(view-dir-with-shortcut → chat dir). The new shape lets
`Path.resolve()` do the work — view dir-symlinks resolve in one step,
and walking up the parent chain to `.chat` handles every other entry
point uniformly. The function shrank and got more general.

**One commit's bug-fix is the next commit's `tree` validation.**
Without the prior session's content spot-check, the textual-link
asymmetry would have shipped silently. The discipline of reading the
rendered output (not just running the pipeline) caught a real bug
that pyright and exit codes never would.

## Next Session

- `.claude/todo.kb/2026-05-05-002-…-noun-verb-model-sub-kb.md` —
  planning, discussion with user before any kb creation.
- Live URL re-capture (interactive `har-browse`; user-driven) to
  confirm the URL-browse flow against the live ChatGPT page under
  the new layout. Smoke covered the path-render flow; URL-browse
  was unit-exercised through the layout module and pyright but
  hasn't run end-to-end this session.
