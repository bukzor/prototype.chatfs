# chatfs-cli

The hand-driven capture → splat → render pipeline for chat conversations
(claude.ai, chatgpt.com, AI Studio). Graduated from
`docs/dev/design-incubators/chatfs-cli-mockup/` (2026-08-07); this is the
CLI surface the future FUSE daemon will invoke under the hood.

To *use* it, read `docs/how-to-chatfs.md` at the repo root. This README
covers the package shape and the stage-by-stage anatomy.

## Install

From the repo root:

```bash
uv sync
```

The workspace root declares `chatfs-cli` as a default dependency, so this
installs the import package `chatfs` and puts one command per pipeline
stage on `PATH`. The bare `chatfs` command name is reserved for the future
Rust dispatcher (`design.kb/040-design.kb/package-division.md`).

## Command shape

Commands are named `chatfs-<provider>-<noun>-<verb>`, kebab-mapped from
the module path (`chatfs.provider.claude.conversation.url_browse` →
`chatfs-claude-conversation-url-browse`); see
`design.kb/040-design.kb/cli-command-shape.md` for the vocabulary
(noun, verb, locator sub-noun).

Every command runs from any directory. URL-addressed and index commands
take `--cache <dir>` — the per-provider cache root they read and write,
deliberately with no baked default (`technical-policy.kb/path-ownership.md`).
Path-addressed commands take an on-disk path, which itself says which
cache they're in.

## Cache layout

```
$CACHE/                                 # one root per provider
    .chat/$UUID/
        chat.md                         # rendered current-path with dead-branch asides
        messages/                       # per-message .md/.json
        conversations/                  # per-branch symlinks (when branches exist)
        .data -> ../../.data/$UUID/     # inspection symlink
    .data/$UUID/
        meta.json                       # one index item, verbatim
        conversation.json               # plucked conversation document
        cdp.jsonl                       # raw CDP exhaust from har-browse
    Created=YYYY/MM/DD/HH:MM:SS±HH:MM/
        $TITLE -> ../../../../.chat/$UUID/   # single directory-symlink per chat
    trash/$TIMESTAMP/                   # url-trash destination
```

Storage is flat and UUID-keyed; the date tree is a view of symlinks
pointing into storage. Ownership per subpath:
`docs/dev/technical-policy.kb/path-ownership.md`.

## Stages

Leaf stages read stdin and write stdout (data only; progress goes to
stderr). Orchestrators take an addressable target (URL or chat-dir path),
tee intermediates to disk for debuggability, and drive the leaves as
subprocesses (`design.kb/040-design.kb/driver-model.md`).

1. **`chatfs-<p>-index-browse --cache $C`** — drives `har-browse` against
   the provider's index page, tees raw CDP to `.data/index.cdp.jsonl`,
   plucks in-process, emits index pages on stdout.
2. **`chatfs-<p>-index-splat --cache $C`** — reads index pages on stdin;
   per item, writes `.data/$UUID/meta.json`, purges prior view symlinks
   for that UUID, places a fresh `$TITLE` directory-symlink under the
   date tree.
3. **`chatfs-<p>-conversation-url-browse --cache $C <url>`** — captures
   one chat by URL: one browse trip yields both the conversation document
   and (chatgpt/claude) an index page to derive `meta.json` from; places
   meta and delegates to path-render. Fails loudly if the sidebar didn't
   include the target.
4. **`chatfs-<p>-conversation-path-browse <chat-dir>`** — captures
   `cdp.jsonl` and `conversation.json` into an already-placed chat's
   `.data/$UUID/`, then delegates to path-render.
5. **`chatfs-<p>-conversation-path-render <chat-dir>`** — rebuilds the
   whole derived surface (splat + render) in a staged sibling and
   atomically swaps it into place.
6. **`chatfs-<p>-conversation-render <chat-dir>`** — walks the mapping
   tree from `current_node` back to root, streams turn headings linking
   to atomic `.md` files; dead branches render as nested blockquoted
   asides at their fork point. Markdown on stdout.

Every stage rebuilds its outputs from scratch (no freshness caches) and
regeneration is byte-deterministic; see
`design.kb/040-design.kb/deterministic-regeneration.md`.

## Layout

```
packages/chatfs-cli/
├── pyproject.toml        # [project.scripts]: one entry per stage
└── lib/chatfs/
    ├── provider/{claude,chatgpt,aistudio}/
    │   ├── conversation/ # url_browse, path_browse, *_render, splat, ...
    │   ├── index/        # browse, splat
    │   ├── layout.py     # provider-specific naming/url/time
    │   ├── pluck.py      # network-exhaust filters
    │   └── types.py
    ├── shell/            # impure kernel: capture, place, atomic, locks, sh
    └── *.py              # pure vocabulary: layout, json, pluck, render
```

Only `shell/` does I/O at import-reachable top level; everything else is
pure vocabulary the leaves compose.

## Design

- `docs/dev/design.kb/` — project-level layered design knowledge
- `design.kb/` — pipeline- and CLI-shape decisions, package-scoped
  (graduated with the code from the chatfs-cli-mockup incubator)
- `docs/dev/technical-policy.kb/` — cross-cutting invariants
