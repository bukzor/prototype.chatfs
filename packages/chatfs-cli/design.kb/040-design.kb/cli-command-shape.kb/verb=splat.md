# verb=splat

`splat` names the operation of fanning a monolithic JSON document out
into a normalized tree of small files (one per message, plus indices).
Alternatives considered: `materialize`, `expand`, `unpack`. `splat` is
in-house jargon but precise — readers of this repo recognize it, and it
carries the connotation of "explode into many pieces" that the
alternatives lose.

Two splat operations in the pipeline:

- `chatgpt index splat` — top-level CLI verb. Reads the sidebar index
  jsonl on stdin, places per-UUID chat dirs via `place_meta`. See
  `noun=index.md`.
- `chatgpt-splat` — internal helper invoked by
  `chatgpt conversation path render`. Splats `.data/conversation.json`
  into `messages/` and `conversations/` subtrees before the bare-leaf
  render walks the result. Not a user-facing top-level CLI verb.

The verb is shape-of-operation, not shape-of-input: index splat reads
jsonl-of-pages-from-stdin; conversation splat reads a single JSON file.
Both fan a single document out into a tree of small files; that's the
common shape `splat` names.
