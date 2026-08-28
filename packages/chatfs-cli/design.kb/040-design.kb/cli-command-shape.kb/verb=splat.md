# verb=splat

`splat` names the operation of fanning a monolithic JSON document out
into a normalized tree of small files (one per message, plus indices).
Alternatives considered: `materialize`, `expand`, `unpack`. `splat` is
in-house jargon but precise — readers of this repo recognize it, and it
carries the connotation of "explode into many pieces" that the
alternatives lose.

Two splat operations in the pipeline, both top-level CLI verbs (as of
2026-08-16 -- `chatgpt conversation splat` previously ran via the
external `chatgpt-splat` command from `packages/bukzor.chatgpt-export`,
carved out of the uniform command surface; that carve-out was temporary
and has since expired -- see `package-division.md`):

- `chatgpt index splat` — reads the sidebar index jsonl on stdin, places
  per-UUID chat dirs via `place_meta`, and writes one placement record
  per chat placed to stdout. See `noun=index.md`.
- `chatgpt conversation splat` — invoked by `chatgpt conversation path
  render`. Splats `.data/conversation.json` into `messages/` and
  `conversations/` subtrees before the bare-leaf render walks the
  result, same as claude/aistudio's conversation splat.

The verb is shape-of-operation, not shape-of-input: index splat reads
jsonl-of-pages-from-stdin; conversation splat reads a single JSON file.
Both fan a single document out into a tree of small files; that's the
common shape `splat` names.

That input shape is also why neither splat has a provider-dispatching
form. Both take a document and a destination rather than an address, and
conversation splat's destination is a staged scratch sibling that need
not sit in a cache at all -- there is nothing in the arguments a provider
could be read off. See `../cli-command-shape.md`'s **dispatching form**.
