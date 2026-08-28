---
why:
  - black-box-decomposition
source:
  - user (bukzor)
---

# Path Ownership (v1, descriptive)

`black-box-decomposition.md` says the rest of the system depends on the
pipeline only through "command invocation, exit codes, file paths, atomic
outputs" — but stops short of saying which paths. This is that seam,
written down as of 2026-07-14: for each subpath under a cache root, which
component may write it, and which only read it.

**Scope:** describes on-disk reality in `packages/chatfs-cli` today.
Stage names (capture, index splat, path render, ...) match the package
README's "Stages" section — commands and arguments stay single-sourced
there and in each package; this doc names owners, not invocations.
Aspirational content (the not-yet-built daemon) is marked `[!TODO]`.

## Cache root

Every path below is relative to a *provider root*, `$cache/<provider>/`.
The cache is a required argument everywhere (2026-08-07, child 001):
url-addressed and index commands take `--cache <dir>`; path-addressed
commands resolve the provider root from the given path. No baked default
exists, so the daemon can point arbitrary mounts at arbitrary caches.

The provider segment is appended by `chatfs.cli.extract_cache`, never by
the caller (2026-08-28). One `--cache ~/chats` therefore serves every
provider, and `$CHATFS_CACHE` is settable once rather than per-provider.
The cache and the provider root are different things, and only the cache
is nameable on the command line: passing a provider root to `--cache`
nests a second one inside it (`~/chats/claude/claude/`).

Besides `.chat/`, `.data/`, and the view tree below, the root carries
`trash/` — the url-trash verb's destination (`trash/$TIMESTAMP/`, chat
dir plus its view symlinks). Sweeps and view-symlink purges skip it.

## `.chat/$UUID/` — canonical storage

Flat, UUID-keyed, owned end-to-end by the pipeline (`chatfs-cli`).
Nothing outside the pipeline writes here — see Future daemon, below, for
why that boundary holds even once a daemon exists.

### `.data/` — contract files vs. reserved scratch

The ownership question ("may X write path P?") has a fixed answer only
for three names — everything else under `.data/` is a stage's private
business, not a cross-stage contract.

| Subpath | Owner (writes) | Others | Notes |
|---|---|---|---|
| `.data/` | capture stages (index splat, url browse, path browse) | splat, path render (read `.data/conversation.json`) | Sole write-owner across the whole regeneration cycle. Path render's purge step allowlists `.data` explicitly — it is the one thing a render pass never touches. |
| `.data/meta.json` | index splat or url browse, via the shared `place_meta` helper | render (identity fields) | One entry's index-page item, verbatim. |
| `.data/conversation.json` | capture | splat | The canonical plucked conversation document — splat's sole input. Capture is not always a single step to produce it (some sources need an internal normalization pass first); that intermediate step is scratch, below, not a second contract name. |
| `.data/cdp.jsonl` | capture | — | Raw captured network exhaust; kept for inspectability and recovery, not read by any later stage in the ordinary path. |

**Verbatim is the contract, not an oversight.** Most of a claude index
entry's bytes are per-conversation feature-flag `settings` (~74%, mostly
`enabled_mcp_tools`), so a cache runs several times larger than its
identity fields need. Filtering would mean parsing a structure nothing
downstream has claimed yet — what is currently opaque stays opaque.
Ruled 2026-08-27; re-raise when a consumer needs the space, not before.

**Scratch:** a capture stage may need working files beyond the three
above — a pre-normalization pluck, a cross-check dump from a
single-browse-trip optimization, anything internal to producing or
cross-checking one contract file. No other stage may depend on a
scratch file's name or presence.

Every top-level contract name `X` reserves the sibling `X.d/` for scratch
related to producing or checking it — `ls`-legible by position, and the
reservation costs nothing for contract files that never need scratch.
Same pattern as `/etc/apt/sources.list.d/`; applies wherever a top-level
contract name exists, not just here. Implemented 2026-07-15: AI Studio's
pre-normalization pluck lives at `conversation.json.d/raw.json`;
chatgpt/claude's incidental-capture cross-check dump lives at
`cdp.jsonl.d/index-pages.jsonl`.

The same `.data/` idiom recurs one level up, at the provider root:
`$root/.data/index.cdp.jsonl` is index browse's debug CDP tee
(2026-07-17; previously a loose file next to the scripts). Same
ownership shape as `.data/cdp.jsonl` — capture writes it, no later stage
reads it — and `index.cdp.jsonl.d/` is reserved per the rule above.

### Derived members (`messages/`, `conversations/`, `chat.md`)

| Subpath | Owner (writes) | Others | Notes |
|---|---|---|---|
| `messages/`, `chat.md` | path render | view-tree readers | Regenerated from scratch every path-render run, atomically: built in a staged sibling and swapped whole (`chatfs.shell.atomic.staged`, landed 2026-07-18) — readers only ever see old-complete or new-complete; a crashed attempt is preserved as `.fail` and the next run self-heals. |
| `conversations/` | path render | view-tree readers | Splat-produced only when the source conversation has branches to represent; not every capture does today. |

## View tree (`Created=YYYY/MM/DD/HH:MM:SS±HH:MM/$TITLE`, etc.)

Owned entirely by `place_meta` (called from index splat and from url
browse). Pure symlinks pointing at `.chat/$UUID/` — never real files.
Every `place_meta` call purges prior view symlinks for that UUID by
identity (not by path) before placing the current one, so a labeled tree
can change shape (new label, new offset format) without a migration
step. `rm -rf` on any view subtree loses no data — see
`chat-as-directory.md`'s storage-vs-view split for the full argument.

No component other than `place_meta` writes under the view tree.

## Future daemon (not built yet)

> [!TODO] `chatfs mount` (child 003/004) adds a control plane per
> `sync-control-plane.md`: `control` (write-only trigger), `status`
> (read-only job state), `needs_sync/` (read-only staleness listing),
> and per-conversation `.sync`/`.SYNC` hint files. These paths don't
> exist today.
>
> The daemon **owns** those control-plane paths and nothing else. It
> **writes nothing under `.chat/`** — sync is performed by invoking the
> pipeline (`chatfs-cli`) as a subprocess per `work-enqueueing-model.md`
> (stage into `staging/<jobid>/`, atomic rename into place), and the
> pipeline remains the sole writer of `.chat/` content as described
> above. The daemon only reads `.chat/` trees to serve them over FUSE.

## See also

- `../design.kb/040-design.kb/black-box-decomposition.md` — the
  component seam this doc fills in with paths.
- `../design.kb/040-design.kb/work-enqueueing-model.md` — stage/rename
  discipline the future daemon side of this contract follows.
- `../design.kb/040-design.kb/sync-control-plane.md` — control-plane
  path names used above.
- `../../../packages/chatfs-cli/design.kb/040-design.kb/chat-as-directory.md` —
  storage-vs-view rationale behind the `.chat/` / view-tree split.
