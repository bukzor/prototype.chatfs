---
why:
  - unix-composability
  - pipeline-composability
---

# Stdio Pipeline Shape

Leaf scripts read stdin and write data to stdout. Higher-level
orchestrators take an addressable target (URL or ts-dir) and tee
debug intermediates to disk.

## Rule

A script with one logical input and one logical output uses stdin/stdout
for those — no file arguments, no hardcoded output paths. Progress and
status go to stderr; data goes to stdout. This applies to:

- `*-pluck.jq` filters — stdin: CDP, stdout: plucked records
- `chatfs_chatgpt_index_splat.py` — stdin: index pages jsonl
- `chatfs_chatgpt_conversation_render.py` — stdout: markdown
- `chatfs_chatgpt_index_browse.sh` — stdout: index pages jsonl

Multi-input or multi-output stages take addressable targets as
positional arguments (URL or ts-dir), not file paths to individual
inputs:

- `chatfs_chatgpt_conversation_path_browse.py <ts-dir>` — reads `meta.json`,
  writes `cdp.jsonl` + `$UUID.json` next to it
- `chatfs_chatgpt_conversation_path_render.py <ts-dir>` — reads
  `meta.json` + `$UUID.json`, runs splat, redirects render stdout to
  `$TITLE.md`

## Tee debug intermediates in orchestrators

Orchestrators that compose a capture step with downstream filters tee
the captured stream to a debug file before piping into the filter:

```
har-browse <url> | tee chatgpt.index.cdp.jsonl | chatfs_chatgpt_index_pluck.jq
```

The tee'd file is not consumed by any later stage — it exists so a
half-broken run is inspectable. When something looks wrong downstream,
the user can re-run pluck against the captured CDP without re-driving
Chromium.

This is currently default-on. A future flag will gate it default-off
once the pipeline stabilizes; keeping it on during incubation pays for
itself the first time a render produces something surprising.

## Why

- **Composability.** A user can substitute one leaf for another by
  changing pipe wiring, no code edit. `head -1`, `jq`, `wc -l`, `tee`
  all work without modification.
- **Single-purpose scripts.** Each leaf does one transformation; the
  orchestrators handle file placement and naming. No leaf knows about
  the date tree under `chatfs.demo/`.
- **Fail-loud composition.** `set -o pipefail` plus stderr-only
  progress means broken pipelines exit non-zero. Mixing data and
  progress on stdout would corrupt downstream JSON parsers.
- **Streaming.** Where the work allows it (e.g. emitting markdown
  sections one at a time), leaves emit incrementally rather than
  buffering. `"".join(parts)` after a recursive accumulation is a code
  smell signaling buffered output where streaming was possible.

## Why orchestrators take addressable targets

A `<ts-dir>` argument names a *target* — the script reads several files
from it and writes several files into it. There is no single input or
output stream to plumb. URL is similar: it addresses a remote
conversation that the orchestrator captures and places.

Orchestrators do not chain via stdio because their work is inherently
multi-file. They chain by *position* — `path_browse` writes the files
that `path_render` reads, both keyed off the same `<ts-dir>`.
