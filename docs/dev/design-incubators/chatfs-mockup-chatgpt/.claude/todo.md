---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 10.0
    rationale: |
      Heavily-used incubator parent — residual is real, mixed with
      already-rated child .kb references. Unchecked items: 3 content-
      type renders (thinking, tool_use, tool_result) ~3h, har-browse
      has_more=false wait fix ~2h, branch enumeration ~1h, 2
      refactors (extract chatfs_layout.py, promote provider-plugin-
      model) ~3h, strategic items (claude-code provider, shared
      code) tracked as child .kb refs.
    confidence: tentative
  benefit-2w:
    "@value": 2.0
    rationale: |
      Active prototype with MVP landed for both chatgpt + claude
      providers. Content-type renders close last gap to full parity.
      Refactor unlocks third provider. Real forward momentum.
    confidence: tentative
  cost-of-delay-2w:
    "@value": 0.3
    rationale: |
      Active prototyping has high context-decay tax. Each 2w of
      delay forces re-learning the incubator's many design choices.
      (The "too-many-changes" freeze was drained 2026-05-19 —
      archive/too-many-changes; worktree removed.)
    confidence: tentative
---

# Tactical Tasks — chatfs-mockup-chatgpt

Scope: this incubator only. Project-wide tactical work lives in
`../../../../.claude/todo.md`.

## Next

- [ ] [pyright-clean sweep across the incubator](todo.kb/2026-07-05-000-pyright-clean-sweep-across-the-incubator.md)
      — TypedDict+TypeGuard house pattern, applied provider by provider; AI
      Studio and chatgpt done, claude next. See the file for the approach.
- [ ] [Cross-provider data-flow drift — pre-unification fixes vs unification scope](todo.kb/2026-07-03-000-cross-provider-data-flow-drift--pre-unification-fixes-vs-unification-scope.md)
      — from the 2026-07-03 three-provider review. All three "fix before
      unification" bugs landed 2026-07-03/04 (aistudio splat retarget,
      `create_time` mislabel, chatgpt failsoft→failfast) — the aistudio
      unification gate is clear. File stays open only for its "Solve by
      unification" section: five drift items recorded as requirements for
      the shared-code refactor, deliberately NOT fixed in place — see
      `~/.claude/sessions.kb/provider-code-reuse-stutter-step.md`
      (outside this repo; not a resolvable link).
- [ ] [Rename incubator to chatfs-cli-mockup](../../../../../.claude/todo.kb/2026-05-11-000-rename-incubator-to-chatfs-cli-mockup.md)
      — precursor to multi-provider sketch; current name encodes a single
      provider. Tracked at project level because the rename also touches
      `pyproject.toml` and the project ADR.
- [ ] Scan the rest of the incubator code for the implicit-match /
      `if X: return` … fall-through pattern and convert to explicit
      `match`/`case _:` (house exhaustive-case rule).
      `chatfs_claude_conversation_splat.py` already swept this session;
      remaining: the `chatfs_chatgpt_*.py` siblings and both `*_render.py` (e.g.
      `render.py:primary_child`). Also recheck for fail-soft `.get()` guards and
      `ensure_ascii` while there.
- [ ] [AI Studio provider — parity ladder](todo.kb/2026-06-20-000-aistudio-provider-parity-ladder.md)
      — third provider, first JSPB source. Pluck + splat landed 2026-06-20;
      layout/types 2026-06-22; massage_json + url_browse 2026-07-03 (writes
      conversation.raw.json + conversation.json + meta.json end-to-end,
      live-tested). Index rung, render/path_render, and browse automation
      remain — url_browse doesn't yet delegate to a render step.

## Claude provider — parity ladder

Each row extends the working surface. Check the first few for an MVP that
renders a single linear chat end-to-end; check all rows for full parity with the
chatgpt side (or better).

**MVP — single chat URL → `chat.md` (linear chats only):**

- [x] `chatfs_claude_index_pluck.jq` — extract `/chat_conversations_v2?…`
      response bodies from CDP
- [x] `chatfs_claude_index_splat.py` — place `.chat/$UUID/.data/meta.json` +
      view dir-symlink (uuid dedupe; empty-name → uuid fallback)
- [x] `chatfs_claude_conversation_pluck.jq` — extract
      `/chat_conversations/{id}?…` response body
- [x] `chatfs_claude_conversation_splat.py` (text-only first) — walk
      `chat_messages`, write one `messages/<stem>.md` per message with
      concatenated text-block content; skip thinking/tool blocks; skip
      `conversations/` symlinks
- [x] `chatfs_claude_conversation_render.py` — DFS from root via
      `parent_message_uuid` index; live path (root →
      `current_leaf_message_uuid`) inline; dead branches as nested blockquoted
      asides (mirrors chatgpt-render structure)
- [x] `chatfs_claude_conversation_path_render.py` — orchestrator: splat
      `.data/conversation.json` into `.data/conversation.splat/`, move outputs
      up two levels, render → `chat.md`

**Same end-user entry points as chatgpt:**

- [x] `chatfs_claude_conversation_url_browse.py` — capture by URL; pluck both
      index + conversation; place files; delegate to `path_render`. Adds a
      null-tolerant cross-check between conversation-doc and index-item meta
      fields (claude-side only; chatgpt doesn't have this guard yet)
- [x] `chatfs_claude_conversation_path_browse.py` — capture by chat-dir path
      (bulk iteration after index)
- [x] `chatfs_claude_conversation_url_render.py` — URL → resolve to
      `.chat/$UUID/`, delegate to `path_render`

**All content types rendered (this capture exercises all four):**

- [x] Render `thinking` blocks — collapsible `<details type="thinking">`,
      summary from Claude's own `summaries`
- [x] Render `tool_use` + `tool_result` — fused into one
      `<details type="tool_call" tool="<name>">` pair; web_search/web_fetch
      special-cased (🔍 query / 🕷️ url, request omitted), others 🛠️
      request+result
- [x] Dispatch fails loud — unknown content type raises; non-ASCII renders
      literally (`ensure_ascii=False`)

**Browse-side automation:**

- [x] `chatfs_claude_index_browse.sh` — drive `har-browse` against `/recents`,
      tee CDP, pluck
- [ ] Solve har-browse "wait until `has_more=false`". Observation: pressing
      "Done Capturing" shortly after the sidebar becomes interactable yields a
      CDP stream missing later index pages — cause underdetermined. Plan: a
      stop-when filter downstream of pluck breaks on `has_more=false`;
      har-browse receives EPIPE and shuts down cleanly (per
      `packages/har-browse/.claude/todo.md` 2026-04-24-003).

**Branches:**

- [x] Forked claude chat for test data — the founder-self-sabotage chat is
      forked (user edited their second message), discovered while rendering
- [x] Render dead-branch asides (nested blockquotes, depth = nesting; mirror
      chatgpt-side) — landed with `conversation_render.py`
- [ ] Branch enumeration in splat — emit `conversations/<branch>.md` symlinks
      per leaf
- [x] Amend section headings to indicate branch points — landed in
      `chatfs_claude_conversation_render.py`. Full notation contract persisted
      in `design.kb/…/noun=conversation.kb/verb=render.md` (§ Fork-fact
      notation): two-zone italic metadata (status above body, navigation below),
      bare `*italics*` not `<sub>`, explicit `←live` marker, no anchors.
      Verified against the 28-fork test conversation
      (`trash/check_render_notation.py`).
- [ ] Bring `chatfs_chatgpt_conversation_render.py` to parity with the claude
      side's fork-fact notation (now the canonical contract in
      `verb=render.md` § Fork-fact notation). The chatgpt renderer predates
      these decisions and emits **no** fork facts at all — it blockquotes dead
      branches but adds no branch-prefixed numbering, `(re:)` backlinks,
      `replies`/`superseded by`/`prior revisions` lines, or `←live` marker.
      The claude renderer (`chatfs_claude_conversation_render.py`) is the
      reference implementation; the notation is provider-agnostic. Likely wants
      the shared-`chatfs_layout.py` refactor (Refactor entries above) first, so
      the notation is written once, not twice.

**Refactor (after both providers run end-to-end):**

- [x] Extract provider-agnostic helpers into shared `chatfs_layout.py`; both
      `chatfs_chatgpt_layout.py` and `chatfs_claude_layout.py` reduce to
      provider-shaped `place_meta` + shared imports
- [ ] Promote `provider-plugin-model.md` symlink to a real incubator entry, with
      two-provider lessons (what's truly provider-shaped, what's universal)

## Today — URL-driven capture + CLI rename

Design persisted in `design.kb/040-design.kb/`. Decisions: noun-verb CLI shape,
deterministic regen (no freshness caches), no partial synthesis,
browse-incidental meta capture.

- [x] Refactor: extract shared `chatfs_chatgpt_layout.py` (`IndexItem`
      TypedDict, `safe_filename`, `time_dir_for`, `place_meta`); splat + render
      now import from it
- [x] Rename scripts to noun-verb shape — underscores + `.py`/`.sh`/`.jq` for
      sibling-import (use `git mv`):
  - [x] `chatgpt-index.sh` → `chatfs_chatgpt_index_browse.sh`
  - [x] `chatgpt-index-splat.py` → `chatfs_chatgpt_index_splat.py`
  - [x] `chatgpt-page-capture.py` → `chatfs_chatgpt_conversation_path_browse.py`
  - [x] `chatgpt-render.py` → `chatfs_chatgpt_conversation_render.py`
  - [x] `chatgpt-index-pluck.jq` → `chatfs_chatgpt_index_pluck.jq`
  - [x] `chatgpt-conversation-pluck.jq` → `chatfs_chatgpt_conversation_pluck.jq`
- [x] Drop freshness caches; rm-rf expected outputs before each regen
  - [x] `index_browse`: drop 60min CDP cache
  - [x] `conversation_path_browse`: rm cdp.jsonl + $UUID.json before browse
        (splat + $TITLE.md handled by path_render / conversation_render)
  - [x] `path_render`: drop is_newer_than gate; always rm-rf $UUID.splat/ and
        re-splat
- [x] Add `chatfs_chatgpt_conversation_url_browse.py <url>`:
  - [x] parse UUID from URL
  - [x] browse to staging tempdir, run both pluck.jq filters
  - [x] index pluck filtered to matching `.id` → meta (fail loudly if no match)
  - [x] derive ts-dir from `create_time`; rm -rf and rebuild; place files;
        delegate to path_render
- [x] Update incubator `README.md` with new command names + URL flow
- [x] End-to-end test against
      `https://chatgpt.com/c/69f21e0c-1cfc-83ea-b952-5e9d31022a31` — 2026-05-08,
      188 messages / 129 turns rendered
- [x] Devlog in
      `../../../devlog/2026-04-29-000-chatfs-mockup-chatgpt-url-flow-and-determinism.md`

## Strategic

- [ ] [claude-code as next provider](todo.kb/2026-05-11-000-claude-code-as-next-provider.md)
      — after claude.ai parity; datasource `~/.claude/`, no BB1
- [ ] [shared code among providers](todo.kb/2026-05-11-001-shared-code-among-providers.md)
      — strategic placement of the parity-ladder Refactor entry

Directory-symlink + `.data/` refactor landed 2026-05-08: `place_meta` writes
`meta.json` to `.chat/$UUID/.data/` and places a single `$TITLE → .chat/$UUID/`
directory-symlink under the date tree; `path_render` allowlists `{".data"}`,
splats into `.data/`, moves `messages/`/`conversations/` up two levels into the
chat-dir root, writes `chat.md`. Smoke: 56 chats re-splat, test chat (188
messages / 129 turns) re-rendered byte-stable; `messages/<stem>.md` links
resolve textually under the view path; re-splat symlink count stable (374 →
374).

noun-verb model sub-kb landed 2026-05-11 at
`design.kb/040-design.kb/cli-command-shape.kb/` (10 entries, partition- prefix
scope, Hive-style `key=value` naming). Summary `cli-command-shape.md` reshaped:
listings out (subcommand-path block, script-name table), partition-vocabulary
glossary + explicit-locator policy + naming-conventions rule in. "Cell"
terminology renamed to "command" throughout. Sibling-doc cross-links added to
`stdio-pipeline-shape.md` and `chat-as-directory.kb/pipeline-implications.md`.

## Loose ends

- `foo.py`, `bar.py` — moved to `~/trash/`.
- `chatfs_chatgpt_conversation_url_render.py` — kept as the noun-verb-locator
  command `conversation × url × render`; updated to resolve URL → `.chat/$UUID/`
  directly and delegate to `path_render`.

## Pipeline shape (post-session)

Leaf scripts read stdin / write data to stdout / send progress to stderr.
Higher-level orchestrators take URL or ts-dir args, tee debug intermediates
(e.g. `chatgpt.index.cdp.jsonl`, `<ts-dir>/cdp.jsonl`), drive the leaves. Later:
gate the debug intermediates behind a flag (default off).
