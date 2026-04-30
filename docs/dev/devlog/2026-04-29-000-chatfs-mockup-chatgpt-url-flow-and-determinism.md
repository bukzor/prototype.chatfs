# 2026-04-29: chatfs-mockup-chatgpt — URL-driven capture, streaming render, deterministic regen

## Focus

Make the mockup pipeline addressable by a chatgpt.com URL — the common
ad-hoc case ("someone shared a link, capture this one chat") — and
clean up the freshness caches and buffered-output idioms that had
crept in during hand-driven iteration.

Decisions captured in `design.kb/040-design.kb/`:
`cli-command-shape`, `deterministic-regeneration`, `no-partial-synthesis`,
`browse-incidental-capture`, `stdio-pipeline-shape`. The devlog is
session narrative — see those entries for the durable rationale.

## What Happened

**CLI rename to noun-verb shape.** Scripts are now named as if they
were subcommands of a future `chatfs` CLI. Module names use `_` for
sibling-import; the same path with `-` is the script-on-`$PATH` form.

**Shared layout helpers extracted.** `chatfs_chatgpt_layout.py` owns
`safe_filename`, `time_dir_for`, `place_meta`. `chatfs_chatgpt_types.py`
defines an `IndexItem` TypedDict for the fields read out of
`/backend-api/conversations` items; everything else passes through as
opaque payload into `meta.json`.

**Two render entry points, one shared core.** `path_render` takes a
ts-dir, `rm -rf`s `$UUID.splat/`, re-runs `chatgpt-splat`, then
redirects the leaf render's stdout to `$TITLE.md`. `url_render`
resolves a URL to an existing ts-dir for re-render-without-recapture.
Both `conversation_url_browse` and `conversation_path_browse` delegate
to `path_render` after capture.

**URL-driven browse.** `chatfs_chatgpt_conversation_url_browse.py
<url>` parses the UUID, browses to a tempdir, runs both pluck filters
against the same CDP capture, and uses the sidebar's
`/backend-api/conversations` page (which the browser fetches
incidentally) to derive `meta.json` byte-for-byte from the index
endpoint. From the matched item's `create_time` we pick the ts-dir,
`rm -rf` it, place files, and delegate to path_render. Sidebar miss
asserts loudly.

**Freshness caches removed everywhere.** `index_browse` no longer
reuses a <60-min CDP file; `path_browse` `unlink`s its prior
`cdp.jsonl` and `$UUID.json` before re-capturing; `path_render` no
longer mtime-gates the splat — it `rmtree`s `$UUID.splat/` and
re-splats every run. `is_newer_than` deleted from the layout module.

**Stdio pipeline shape.** Leaf scripts (`*_pluck.jq`,
`index_browse.sh`, `index_splat.py`, `conversation_render.py`) now
read stdin, write data on stdout, and progress on stderr — no file
output args. The conversation render in particular streams sections
to stdout as the recursion produces them, instead of accumulating in
a list and joining at the end. Higher-level orchestrators tee debug
intermediates (e.g. `chatgpt.index.cdp.jsonl`,
`<ts-dir>/cdp.jsonl`) for inspectable half-broken runs.

**pyright executionEnvironment for the incubator.** A scoped
`extraPaths` entry in `pyproject.toml` lets pyright resolve flat
sibling-importing scripts without polluting global module names.
Drop when an incubator graduates to `packages/*`.

## Lessons

**Design before reflex-implementing the obvious flow.** First
instinct on URL-driven capture was to synthesize `meta.json` from the
conversation document — `id`, `title`, `create_time` overlap with the
index payload, so it looks safe. Discovering that the sidebar
`/backend-api/conversations` request fires *incidentally* during a
conversation page load — and writing that down before coding —
unblocked the clean variant where `meta.json` is byte-for-byte from
the index endpoint. The synthesis flow would have produced two
different `meta.json` schemas under the same filename depending on
entry point, with downstream stages either silently degrading or
failing at a distance.

**The mtime gate on splat was the cache I almost kept.** Splat is
fast; the gate was for "iterate on render without re-running splat
each time." But `chatgpt-splat` is external code: an upgrade to that
tool wouldn't bump the input mtime, and the gate would silently serve
stale output. Writing down the deterministic-regeneration rule killed
it once articulated.

**`"".join(out_parts)` after a recursive accumulation is a code
smell.** The user pointed it out — the structure implied that work
could/should have been streaming. The render was buffering 11000+
lines of markdown into a list before writing once, when the recursive
walk could just emit each section as it produced it. Single-pass
refactor with `nonlocal seq, prev_depth` and direct `sys.stdout.write`
preserved bytes exactly while halving the in-memory representation.
The lesson generalizes: when a recursion fills a list and then a loop
walks the list to do something, ask whether the recursion can do that
something directly.

## Next Session

- End-to-end test the URL flow against a real conversation;
  `har-browse` is interactive (waits for "Done Capturing"), so this
  needs a human at the keyboard. Smoke test against the existing
  134-turn ts-dir reproduces previous bytes byte-for-byte.
- Decide fate of `chatfs_chatgpt_conversation_url_render.py` — the
  capture-already-done convenience that isn't on either main flow.
  Fold into `path_render`, document its niche, or delete.
- Multi-provider sketch — claude.ai under `chatfs.demo/claude/` with
  the same date-tree shape, or some other layout?
- Fold incubator lessons (CLI shape, deterministic regen,
  no-partial-synthesis, browse-incidental capture, stdio pipeline
  shape) back into the project-level design.kb where they generalize
  beyond chatgpt.
