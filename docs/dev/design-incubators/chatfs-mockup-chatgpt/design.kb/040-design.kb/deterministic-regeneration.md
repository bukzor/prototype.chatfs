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

- `index browse` — re-runs har-browse and re-plucks; no mtime check on
  the cached CDP file.
- `conversation {url,path} browse` — removes any prior `content.cdp.jsonl`,
  `$UUID.json`, `$UUID.splat/`, and `$TITLE.md` for the target before
  capturing.
- `index splat` — overwrites `meta.json` and the `$TITLE.md` symlink for
  every item it sees.
- `conversation render` — replaces `$TITLE.md` (whether previously a
  broken symlink from index-splat or a rendered file).

## Why not freshness caches

The earlier `chatgpt-page-capture.py` kept a 1000-hour CDP cache and
`chatgpt-index.sh` kept a 60-minute one. Both were accelerators for
hand-driven iteration but contradict the rule that running a stage
twice in a row should produce the same bytes the second time as the
first.

Skipping a stage because its output looks fresh hides:

- Code changes to the stage itself (output is stale w.r.t. the new code)
- Upstream input changes (the conversation may have new turns since
  capture)
- Partial-write failures (a half-written cache survives the freshness
  check)

If browse latency becomes the bottleneck for a workflow, the answer is
a separate developer-only flag, not a default-on cache. The current
incubator has no such flag.
