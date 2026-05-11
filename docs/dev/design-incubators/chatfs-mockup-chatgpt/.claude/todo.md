<anthropic-skill-ownership llm-subtask />

# Tactical Tasks — chatfs-mockup-chatgpt

Scope: this incubator only. Project-wide tactical work lives in
`../../../../.claude/todo.md`.

## Next

- [ ] [Rename incubator to chatfs-cli-mockup](../../../../../.claude/todo.kb/2026-05-11-000-rename-incubator-to-chatfs-cli-mockup.md) — precursor to multi-provider sketch; current name encodes a single provider. Tracked at project level because the rename also touches `pyproject.toml` and the project ADR.

## Claude provider — parity ladder

Each row extends the working surface. Check the first few for an MVP
that renders a single linear chat end-to-end; check all rows for full
parity with the chatgpt side (or better).

**MVP — single chat URL → `chat.md` (linear chats only):**

- [x] `chatfs_claude_index_pluck.jq` — extract `/chat_conversations_v2?…` response bodies from CDP
- [x] `chatfs_claude_index_splat.py` — place `.chat/$UUID/.data/meta.json` + view dir-symlink (uuid dedupe; empty-name → uuid fallback)
- [x] `chatfs_claude_conversation_pluck.jq` — extract `/chat_conversations/{id}?…` response body
- [x] `chatfs_claude_conversation_splat.py` (text-only first) — walk `chat_messages`, write one `messages/<stem>.md` per message with concatenated text-block content; skip thinking/tool blocks; skip `conversations/` symlinks
- [x] `chatfs_claude_conversation_render.py` — DFS from root via `parent_message_uuid` index; live path (root → `current_leaf_message_uuid`) inline; dead branches as nested blockquoted asides (mirrors chatgpt-render structure)
- [ ] `chatfs_claude_conversation_path_render.py` — orchestrator: splat `.data/conversation.json` into `.data/conversation.splat/`, move outputs up two levels, render → `chat.md`

**Same end-user entry points as chatgpt:**

- [ ] `chatfs_claude_conversation_url_browse.py` — capture by URL; pluck both index + conversation; place files; delegate to `path_render`
- [ ] `chatfs_claude_conversation_path_browse.py` — capture by chat-dir path (bulk iteration after index)
- [ ] `chatfs_claude_conversation_url_render.py` — URL → resolve to `.chat/$UUID/`, delegate to `path_render`

**All content types rendered (this capture exercises all four):**

- [ ] Render `thinking` blocks (proposed: blockquoted, marked `[thinking]`)
- [ ] Render `tool_use` blocks (proposed: fenced JSON with tool name + input)
- [ ] Render `tool_result` blocks (proposed: fenced text; truncate huge)

**Browse-side automation:**

- [ ] `chatfs_claude_index_browse.sh` — drive `har-browse` against `/recents`, tee CDP, pluck
- [ ] Solve har-browse "wait until `has_more=false`" — active scroll or longer idle? (`/recents` doesn't fire `chat_conversations_v2` until the user scrolls)

**Branches:**

- [x] Forked claude chat for test data — the founder-self-sabotage chat is forked (user edited their second message), discovered while rendering
- [x] Render dead-branch asides (nested blockquotes, depth = nesting; mirror chatgpt-side) — landed with `conversation_render.py`
- [ ] Branch enumeration in splat — emit `conversations/<branch>.md` symlinks per leaf

**Refactor (after both providers run end-to-end):**

- [ ] Extract provider-agnostic helpers into shared `chatfs_layout.py`; both `chatfs_chatgpt_layout.py` and `chatfs_claude_layout.py` reduce to provider-shaped `place_meta` + shared imports
- [ ] Promote `provider-plugin-model.md` symlink to a real incubator entry, with two-provider lessons (what's truly provider-shaped, what's universal)

## Today — URL-driven capture + CLI rename

Design persisted in `design.kb/040-design.kb/`. Decisions: noun-verb CLI
shape, deterministic regen (no freshness caches), no partial synthesis,
browse-incidental meta capture.

- [x] Refactor: extract shared `chatfs_chatgpt_layout.py` (`IndexItem` TypedDict, `safe_filename`, `time_dir_for`, `place_meta`); splat + render now import from it
- [x] Rename scripts to noun-verb shape — underscores + `.py`/`.sh`/`.jq` for sibling-import (use `git mv`):
  - [x] `chatgpt-index.sh` → `chatfs_chatgpt_index_browse.sh`
  - [x] `chatgpt-index-splat.py` → `chatfs_chatgpt_index_splat.py`
  - [x] `chatgpt-page-capture.py` → `chatfs_chatgpt_conversation_path_browse.py`
  - [x] `chatgpt-render.py` → `chatfs_chatgpt_conversation_render.py`
  - [x] `chatgpt-index-pluck.jq` → `chatfs_chatgpt_index_pluck.jq`
  - [x] `chatgpt-conversation-pluck.jq` → `chatfs_chatgpt_conversation_pluck.jq`
- [x] Drop freshness caches; rm-rf expected outputs before each regen
  - [x] `index_browse`: drop 60min CDP cache
  - [x] `conversation_path_browse`: rm cdp.jsonl + $UUID.json before browse (splat + $TITLE.md handled by path_render / conversation_render)
  - [x] `path_render`: drop is_newer_than gate; always rm-rf $UUID.splat/ and re-splat
- [x] Add `chatfs_chatgpt_conversation_url_browse.py <url>`:
  - [x] parse UUID from URL
  - [x] browse to staging tempdir, run both pluck.jq filters
  - [x] index pluck filtered to matching `.id` → meta (fail loudly if no match)
  - [x] derive ts-dir from `create_time`; rm -rf and rebuild; place files; delegate to path_render
- [x] Update incubator `README.md` with new command names + URL flow
- [x] End-to-end test against `https://chatgpt.com/c/69f21e0c-1cfc-83ea-b952-5e9d31022a31` — 2026-05-08, 188 messages / 129 turns rendered
- [x] Devlog in `../../../devlog/2026-04-29-000-chatfs-mockup-chatgpt-url-flow-and-determinism.md`

## Strategic

- [x] [chat-as-directory layout — propagate to other docs](todo.kb/2026-05-05-000-chat-as-directory-layout--propagate-to-other-docs.md)
- [x] [Scan design.kb for promotion signals](todo.kb/2026-05-05-001-scan-designkb-for-promotion-signals.md)
- [x] [Plan and create noun-verb model sub-kb](todo.kb/2026-05-05-002-plan-and-create-noun-verb-model-sub-kb.md)
- [x] [View as directory-symlink; hide captured exhaust under .data/](todo.kb/2026-05-08-000-view-as-directory-symlink-hide-captured-exhaust-under-data.md)
- [ ] [claude-code as next provider](todo.kb/2026-05-11-000-claude-code-as-next-provider.md) — after claude.ai parity; datasource `~/.claude/`, no BB1
- [ ] [shared code among providers](todo.kb/2026-05-11-001-shared-code-among-providers.md) — strategic placement of the parity-ladder Refactor entry

Directory-symlink + `.data/` refactor landed 2026-05-08:
`place_meta` writes `meta.json` to `.chat/$UUID/.data/` and places a
single `$TITLE → .chat/$UUID/` directory-symlink under the date tree;
`path_render` allowlists `{".data"}`, splats into `.data/`, moves
`messages/`/`conversations/` up two levels into the chat-dir root,
writes `chat.md`. Smoke: 56 chats re-splat, test chat (188 messages /
129 turns) re-rendered byte-stable; `messages/<stem>.md` links resolve
textually under the view path; re-splat symlink count stable
(374 → 374).

noun-verb model sub-kb landed 2026-05-11 at
`design.kb/040-design.kb/cli-command-shape.kb/` (10 entries, partition-
prefix scope, Hive-style `key=value` naming). Summary
`cli-command-shape.md` reshaped: listings out (subcommand-path block,
script-name table), partition-vocabulary glossary + explicit-locator
policy + naming-conventions rule in. "Cell" terminology renamed to
"command" throughout. Sibling-doc cross-links added to
`stdio-pipeline-shape.md` and
`chat-as-directory.kb/pipeline-implications.md`.

## Loose ends

- `foo.py`, `bar.py` — moved to `~/trash/`.
- `chatfs_chatgpt_conversation_url_render.py` — kept as the
  noun-verb-locator command `conversation × url × render`; updated to
  resolve URL → `.chat/$UUID/` directly and delegate to `path_render`.

## Pipeline shape (post-session)

Leaf scripts read stdin / write data to stdout / send progress to stderr.
Higher-level orchestrators take URL or ts-dir args, tee debug intermediates
(e.g. `chatgpt.index.cdp.jsonl`, `<ts-dir>/cdp.jsonl`), drive the leaves.
Later: gate the debug intermediates behind a flag (default off).
