# 2026-04-29: chatfs-mockup-chatgpt — URL-driven capture and deterministic regeneration

## Focus

Make the mockup pipeline addressable by a chatgpt.com URL — the common
ad-hoc case ("someone shared a link, capture this one chat") — and
clean up the freshness caches that had crept in to accelerate
hand-driven iteration.

## What Happened

**CLI rename to noun-verb shape.** Scripts are now named as if they
were subcommands of a future `chatfs` CLI:

- `chatgpt-index.sh` → `chatfs_chatgpt_index_browse.sh`
- `chatgpt-index-splat.py` → `chatfs_chatgpt_index_splat.py`
- `chatgpt-page-capture.py` → `chatfs_chatgpt_conversation_path_browse.py`
- `chatgpt-render.py` → `chatfs_chatgpt_conversation_render.py`
- pluck filters renamed in lockstep

Module names use `_` for sibling-import; the same path with `-` is
the script-on-`$PATH` form. Captured in
`design.kb/040-design.kb/cli-command-shape.md`.

**Shared layout helpers extracted.** `chatfs_chatgpt_layout.py` now
owns `safe_filename`, `time_dir_for`, `place_meta`; the index splat
and the new URL browse import from it. `chatfs_chatgpt_types.py`
defines an `IndexItem` TypedDict for the fields we actually read out
of `/backend-api/conversations` items. The rest pass through as
opaque dict payload into `meta.json`.

**Two render entry points.** Splat + render are factored into a
shared `chatfs_chatgpt_path_render.py` that takes a ts-dir; both
`conversation_path_browse` and `conversation_url_browse` delegate to
it after their own capture step. There is also a
`chatfs_chatgpt_url_render.py` that resolves a URL to an existing
ts-dir for re-render-without-recapture.

**URL-driven browse.** `chatfs_chatgpt_conversation_url_browse.py
<url>` parses the UUID, browses to a `tempfile.TemporaryDirectory`,
runs both pluck filters against the same CDP capture, and uses the
sidebar's `/backend-api/conversations` page (which the browser fetches
incidentally during the conversation page load) to derive `meta.json`
byte-for-byte from the index endpoint — no synthesis. From the matched
item's `create_time` we pick the ts-dir, `rm -rf` it, place the meta
via `place_meta`, move the staged cdp + `$UUID.json` in, and delegate
to path render. If the sidebar happened to omit the target (long-tail
archived chat), the script asserts and tells the user to fall back to
`index browse` + `conversation path browse`.

**Freshness caches removed.** `index_browse` no longer reuses a
<60-min CDP file; `conversation_path_browse` `unlink`s its prior
`cdp.jsonl` and `$UUID.json` before re-capturing; `path_render` no
longer mtime-gates the splat — it `rmtree`s `$UUID.splat/` and
re-splats every run. `is_newer_than` deleted from the layout module
since nothing imports it.

## Decisions

**Browse-incidental capture for `meta.json`.** Loading
`https://chatgpt.com/c/<uuid>` fires the sidebar's
`/backend-api/conversations` request as a side effect. We exploit this
to avoid synthesizing a partial `meta.json` from the conversation
document — the index endpoint's full schema is in the same CDP file
the conversation pluck reads. Captured in
`design.kb/040-design.kb/browse-incidental-capture.md` and
`no-partial-synthesis.md`. Failure mode (sidebar didn't include the
target) is a loud assert, not a silent fallback.

**No freshness caches in user-facing scripts.** Skipping a stage
because its output looks fresh hides three failure modes that bit us
during development: code changes to the stage itself, upstream
provider changes (the chat may have new turns since capture), and
half-written caches that survive the freshness check. The rule is now
explicit: every stage `rm -rf`s its outputs and rebuilds from scratch.
Captured in `design.kb/040-design.kb/deterministic-regeneration.md`.
If browse latency becomes the bottleneck for some workflow we'll add
an opt-in developer flag, not a default-on cache.

**Two URL entry points, not a polymorphic one.** A single script
that quietly accepts either a URL or a directory path is harder to
read in a pipeline and harder to shell-complete than two scripts
named after their locator type. `conversation_url_browse` and
`conversation_path_browse` share the splat+render tail via
`path_render`.

## Lessons

**Design before reflex-implementing the obvious flow.** First
instinct on "URL-driven capture" was to synthesize `meta.json` from
whatever the conversation document had — `id`, `title`, `create_time`
overlap with the index payload, so it looks safe. It isn't:
`meta.json` ends up with a different shape depending on which entry
point produced it, and downstream readers either tolerate the
difference (silently degrading) or fail at a distance from the
synthesis site. Discovering the sidebar request happens incidentally
during the page load — and writing that down before coding —
unblocked the clean variant.

**The mtime gate in `path_render` was the cache I almost kept.**
Splat is fast; the gate was for "iterate on render without re-running
splat each time." But `chatgpt-splat` is external code: an upgrade to
that tool wouldn't bump the input mtime, and the gate would silently
serve stale output. The deterministic-regeneration rule killed it
once written down.

## Next Session

- End-to-end test the URL flow against a real conversation; record
  any rough edges (e.g. UUID-in-path parsing for non-`/c/` URL shapes,
  creator-vs-participant accounts).
- Decide fate of `chatfs_chatgpt_url_render.py` — capture-already-done
  convenience that isn't on either entry-point path. Either fold it
  into `path_render` somehow, document its niche, or delete.
- Multi-provider sketch — claude.ai under `chatfs.demo/claude/` with
  the same date-tree shape, or some other layout?
- Fold incubator lessons (CLI shape, deterministic regen,
  no-partial-synthesis, browse-incidental capture) back into the
  project-level design.kb where they generalize beyond chatgpt.
