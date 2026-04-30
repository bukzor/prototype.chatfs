---
why:
  - atomic-cache-updates
  - pipeline-composability
---

# Deterministic Regeneration

Every pipeline stage presumes its outputs are stale and rebuilds them
from scratch. There are no freshness caches in the user-facing scripts.

## Rule

Before a stage writes its outputs, it `rm -rf`s them. After the stage
runs, the outputs are a pure function of the inputs and the stage's
code — never a mixture of old and new.

This applies to:

- `index browse` — re-runs har-browse every time; no mtime check on
  the tee'd CDP debug file.
- `conversation url browse` — derives the ts-dir from the captured
  index page, then `rm -rf`s the entire ts-dir before placing files.
- `conversation path browse` — removes any prior `cdp.jsonl` and
  `$UUID.json` before capturing into the supplied ts-dir.
- `index splat` — overwrites `meta.json` and the `$TITLE.md` symlink
  for every item it sees.
- `path render` — `rm -rf`s `$UUID.splat/` and re-runs `chatgpt-splat`
  every time, then redirects `conversation render` stdout into
  `$TITLE.md` (unlinking any prior file or symlink first). The leaf
  `conversation render` only emits markdown to stdout; the file write
  is `path render`'s responsibility.

## Why not freshness caches

The earlier `chatgpt-page-capture.py` kept a 1000-hour CDP cache,
`chatgpt-index.sh` kept a 60-minute one, and `path render` mtime-gated
the splat. All three were accelerators for hand-driven iteration but
contradict the rule that running a stage twice in a row should produce
the same bytes the second time as the first.

Skipping a stage because its output looks fresh hides:

- Code changes to the stage itself (output is stale w.r.t. the new code)
- Code changes to *external tools* the stage shells out to —
  `chatgpt-splat`'s mtime won't bump even when the binary is rebuilt
- Upstream input changes (the conversation may have new turns since
  capture)
- Partial-write failures (a half-written cache survives the freshness
  check)

If browse latency becomes the bottleneck for a workflow, the answer is
a separate developer-only flag, not a default-on cache. The current
incubator has no such flag.
