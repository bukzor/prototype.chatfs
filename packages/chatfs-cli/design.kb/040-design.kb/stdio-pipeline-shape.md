---
why:
  - ../../../../docs/dev/design.kb/020-goals.kb/unix-composability.md
  - ../../../../docs/dev/design.kb/030-requirements.kb/pipeline-composability.md
---

# Stdio Pipeline Shape

Leaf scripts read stdin and write data to stdout. Higher-level
orchestrators take an addressable target (URL or ts-dir) and tee
debug intermediates to disk.

Orthogonal to the noun-verb-locator partition (see
`cli-command-shape.md` + `cli-command-shape.kb/`): every command sits
at some noun×verb partition AND has some stdio shape. "Leaf" and
"orchestrator" map to that doc's *bare-verb leaf* and *orchestrator
form* vocabulary.

## Rule

A script with one logical input and one logical output uses stdin/stdout
for those — no file arguments, no hardcoded output paths. Progress and
status go to stderr; data goes to stdout. This applies to:

- `chatfs-chatgpt-index-splat` — stdin: index pages jsonl
- `chatfs-chatgpt-conversation-render` — stdout: markdown
- `chatfs-chatgpt-index-browse` — stdout: index pages jsonl (pluck
  itself — `chatfs.pluck.iter_responses_matching` plus a provider's thin
  wrapper — is an in-process generator, not a standalone stdio leaf; see
  `driver-model.md`)

Multi-input or multi-output stages need parameterization other than
stdio — there is no single stream to plumb. Two patterns:

- **Positional target arg** when the target varies — URL or chat dir.
  - `chatfs-chatgpt-conversation-path-browse <chat-dir>` — reads
    `meta.json`, writes `cdp.jsonl` + `conversation.json` next to it.
  - `chatfs-chatgpt-conversation-path-render <chat-dir>` — reads
    `meta.json` + `conversation.json`, runs splat, writes `chat.md`.
- **Required `--cache <dir>`** when the stage places files into a cache
  root — `index-splat` and the url-addressed commands take it, with
  deliberately no default (see
  `docs/dev/technical-policy.kb/path-ownership.md`). This supersedes the
  incubator-era fixed-by-convention `chatfs.demo/` root.

Either way, never file paths to individual inputs.

## Tee debug intermediates in orchestrators

Orchestrators that compose a capture step with downstream plucking write
the captured stream to a debug file first, then pluck from that same
file as a second pass:

```python
browse(url, cdp_path)               # $CACHE/.data/index.cdp.jsonl
pluck(pluck_index_pages, cdp_path, dst)
```

(Pre-port, this was a shell `tee`: `har-browse <url> | tee
chatgpt.index.cdp.jsonl | chatfs_chatgpt_index_pluck.jq`. `browse()` then
`pluck()` write-then-read the same file sequentially rather than forking
the stream concurrently — the file's role as an inspectable debug
intermediate is unchanged.)

The debug file is not consumed by any later stage — it exists so a
half-broken run is inspectable. When something looks wrong downstream,
the user can re-run pluck against the captured CDP without re-driving
Chromium. (Since the 2026-07-15 jq→Python port that re-run is a library
affordance — `chatfs.shell.capture.pluck` over a provider pluck function,
from Python — not a shell one; a stdin→stdout pluck leaf was sketched
during the module-shape refactor but has not landed.)

This is currently default-on. A future flag will gate it default-off
once the pipeline stabilizes; keeping it on during incubation pays for
itself the first time a render produces something surprising.

## Why

- **Composability.** A user can substitute one leaf for another by
  changing pipe wiring, no code edit. `head -1`, `jq`, `wc -l`, `tee`
  all work without modification.
- **Single-purpose scripts.** Each leaf does one transformation; the
  orchestrators handle file placement and naming. No leaf knows about
  the date tree under the cache root.
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

Pipe composition and delegation composition are shape choices at this
level, not competing implementations underneath — see
`driver-model.md` for how both surfaces stay thin drivers over the
same importable stage functions.
