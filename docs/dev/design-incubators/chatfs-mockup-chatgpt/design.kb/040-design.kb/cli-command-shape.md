---
why:
  - unix-composability
  - pipeline-composability
---

# CLI Command Shape

Pipeline scripts are named as if they were subcommands of a future
`chatfs` CLI: noun-then-verb, with an explicit locator sub-noun where
the same action accepts multiple input shapes.

## Hierarchy

```
chatfs chatgpt index browse
chatfs chatgpt index splat

chatfs chatgpt conversation url browse <url>
chatfs chatgpt conversation path browse <ts-dir>
chatfs chatgpt conversation render <ts-dir>
```

- **Provider** (`chatgpt`) is the outermost grouping — multi-provider is
  a parent goal, and per-provider script families compose under it.
- **Nouns** are `index` and `conversation`. These are the only two
  artifacts the pipeline manipulates.
- **Verbs** are `browse`, `splat`, `render`. `browse` is preferred over
  `capture` or `fetch` because it accurately signals that a real browser
  window opens (har-browse drives Chromium); reducing user surprise
  matters more than CLI verb conventions here.
- **Sub-nouns** disambiguate locator type (`url` vs `path`) when the
  same verb applies to either. We prefer explicit sub-nouns over
  polymorphic single commands: a script that quietly accepts both a URL
  and a directory path is harder to read in a pipeline and harder to
  shell-complete.

## `splat` as a verb

`splat` names the unusual operation of fanning a monolithic JSON
document out into a normalized tree of small files (one per message,
plus indices). Alternatives considered: `materialize`, `expand`,
`unpack`. `splat` is in-house jargon but precise — readers of this
repo recognize it, and it carries the connotation of "explode into
many pieces" that the alternatives lose.

## Script names on `$PATH`

Each subcommand path translates to a single script with `-` separators:

| subcommand | script |
|---|---|
| `chatgpt index browse` | `chatfs-chatgpt-index-browse` |
| `chatgpt index splat` | `chatfs-chatgpt-index-splat` |
| `chatgpt conversation url browse` | `chatfs-chatgpt-conversation-url-browse` |
| `chatgpt conversation path browse` | `chatfs-chatgpt-conversation-path-browse` |
| `chatgpt conversation render` | `chatfs-chatgpt-conversation-render` |

Internal helpers (e.g. `*-pluck.jq` files) carry the same prefix so
that `ls chatfs-chatgpt-*` enumerates the family.

Python module names use `_` for the same path: `chatfs_chatgpt_layout`
for shared primitives.
