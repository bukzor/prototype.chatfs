<anthropic-skill-ownership llm-subtask />

# Tactical Tasks — chatfs-mockup-chatgpt

Scope: this incubator only. Project-wide tactical work lives in
`../../../../.claude/todo.md`.

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
- [ ] End-to-end test against `https://chatgpt.com/c/69f21e0c-1cfc-83ea-b952-5e9d31022a31`
- [x] Devlog in `../../../devlog/2026-04-29-000-chatfs-mockup-chatgpt-url-flow-and-determinism.md`

## Loose ends

- `foo.py`, `bar.py` — moved to `~/trash/`.
- `chatfs_chatgpt_url_render.py` — capture-already-done convenience; not on
  either entry-point flow. Keep, fold into `path_render`, or delete?
- End-to-end test against the real chatgpt URL — `har-browse` is interactive
  (waits for "Done Capturing"); needs user to run it. Smoke test: render
  against existing 134-turn ts-dir reproduces previous bytes exactly.

## Pipeline shape (post-session)

Leaf scripts read stdin / write data to stdout / send progress to stderr.
Higher-level orchestrators take URL or ts-dir args, tee debug intermediates
(e.g. `chatgpt.index.cdp.jsonl`, `<ts-dir>/cdp.jsonl`), drive the leaves.
Later: gate the debug intermediates behind a flag (default off).
