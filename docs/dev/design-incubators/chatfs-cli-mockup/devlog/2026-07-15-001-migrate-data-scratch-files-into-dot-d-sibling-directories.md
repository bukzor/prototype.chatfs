# Devlog: 2026-07-15 — migrate `.data/` scratch files into `X.d/` siblings

## Focus

Closed
`.claude/todo.kb/2026-07-14-000-Migrate-data-scratch-files-into-dot-d-sibling-directories.md`:
implements `path-ownership.md`'s `.data/` `X.d/` scratch convention
(every top-level contract name `X` reserves the sibling `X.d/` for
scratch involved in producing or checking it — same shape as
`/etc/apt/sources.list.d/`). Moves AI Studio's pre-normalization pluck
from `.data/conversation.raw.json` to `.data/conversation.json.d/raw.json`,
and chatgpt/claude's incidental-capture cross-check dump from
`.data/index-pages.jsonl` to `.data/cdp.jsonl.d/index-pages.jsonl`.

Landed on top of the same-day `chatfs_layout.py` refactor (jq/sh port,
commit `0e1842b`) per the user's sequencing call — both touch
`chatfs_aistudio_layout.py:capture()`'s call shape and `find_index_item`
in the claude/chatgpt `conversation_url_browse.py` files, so landing the
port first settled the shape this migration edits on top of.

## Decisions

### `pluck()` creates `dst`'s parent, not each call site

**Rationale:** both scratch paths are now nested one level under `.data/`
(`conversation.json.d/raw.json`, `cdp.jsonl.d/index-pages.jsonl`), and
`pluck()` (added in the jq/sh port) is the one place that actually opens
`dst` for writing. Adding `dst.parent.mkdir(parents=True, exist_ok=True)`
there covers every current and future `.d/`-scratch call site uniformly,
rather than repeating a per-call-site mkdir. First tried it as an
explicit `conversation.parent.mkdir(...)` inside `chatfs_layout.capture()`
instead — reverted once `pluck()` grew the same line, since duplicating
the same mkdir in the one caller that always routes through `pluck()`
anyway added nothing.
**Alternatives considered:** mkdir at each of the four call sites
individually — rejected, exactly the "remembering to do it every time"
fragility `run_pluck`'s docstring already calls out as the reason for
centralizing pluck output at all.

### Correction to the todo's "three call sites" claim

The todo's Current Situation section claimed the cross-check dump has
"the same shape at three call sites, one per provider's
`conversation_url_browse.py`." Checked before editing
(`grep -rl find_index_item`): only `chatfs_claude_conversation_url_browse.py`
and `chatfs_chatgpt_conversation_url_browse.py` implement it — AI
Studio's `conversation_url_browse.py` only *mentions* `find_index_item`
in a contrastive docstring sentence ("no incidental-index capture ...
contrast chatgpt/claude's find_index_item"), it has no `find_index_item`
function of its own (matches that file's own docstring: AI Studio's
single `ResolveDriveResource` body carries identity directly, nothing to
cross-check). Two real call sites, not three; both migrated.

## Conventions Established

- `path-ownership.md`'s `.data/` section's `[!TODO] Not yet implemented`
  marker is dropped now that both scratch files described there are
  migrated — see path-ownership.md's own edit in this same commit.

## Open Questions

- None new. Per the todo's own note, no live end-to-end capture was run
  to verify AI Studio's `conversation.json.d/raw.json` round-trip in
  this sandboxed environment (no Chromium/network access) — verified
  instead via full existing test suite + basedpyright (both clean) and a
  direct unit-level check that `pluck()` creates a not-yet-existing
  `X.d/` parent on demand. A live capture against a real AI Studio
  prompt is still worth doing whenever this incubator is next driven
  interactively.

## References

- `.claude/todo.kb/2026-07-14-000-Migrate-data-scratch-files-into-dot-d-sibling-directories.md`
  — the closed todo (deleted after this entry landed).
- `docs/dev/technical-policy.kb/path-ownership.md` — the contract this
  implements; `[!TODO]` dropped.
- `chatfs_layout.py` (`pluck`, `capture`), `chatfs_aistudio_layout.py`
  (`capture`), `chatfs_aistudio_conversation_{url,path}_browse.py`,
  `chatfs_aistudio_conversation_massage_json.py`,
  `chatfs_{claude,chatgpt}_conversation_url_browse.py`
  (`find_index_item`).
- `design.kb/040-design.kb/cli-command-shape.kb/noun=conversation.kb/verb=browse.md`
  — updated AI Studio-divergence prose off the old top-level
  `conversation.raw.json` path.
- `devlog/2026-07-15-000-port-jq-sh-pluck-pipeline-to-python.md` — the
  same-day prerequisite this landed on top of.
