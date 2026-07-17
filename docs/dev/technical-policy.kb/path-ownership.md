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

**Scope:** describes `$PWD` reality in the `chatfs-cli-mockup` incubator
today. Stage names (capture, index splat, path render, ...) match the
incubator README's "Stages" section — commands and arguments stay
single-sourced there and in each package; this doc names owners, not
invocations. Aspirational content (the not-yet-built daemon, the
not-yet-argument cache root) is marked `[!TODO]`.

## Cache root

Every path below is relative to a cache root, one per provider.

> [!TODO] Today the root is a baked default (`<incubator-dir>/chatfs.demo/
> $provider/`), not a parameter — every entry point (index splat, url
> browse) hardcodes it. Promotion (child 000/001) makes it a required
> argument everywhere, with no baked default, so the daemon can point
> arbitrary mounts at arbitrary cache roots.

## `.chat/$UUID/` — canonical storage

Flat, UUID-keyed, owned end-to-end by the pipeline (today: the incubator
scripts; post-promotion: `chatfs-cli`). Nothing outside the pipeline
writes here — see Future daemon, below, for why that boundary holds even
once a daemon exists.

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
| `messages/`, `chat.md` | path render | view-tree readers | Regenerated destructively every path-render run: purge everything except `.data/`, re-splat, re-render. **Not yet atomic** — a crash mid-run can strand the chat dir incomplete (tracked: incubator todo `2026-07-13-000-Atomic-chat-dir-regeneration...`). |
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
- `../design-incubators/chatfs-cli-mockup/design.kb/040-design.kb/chat-as-directory.md` —
  storage-vs-view rationale behind the `.chat/` / view-tree split.
- `../design-incubators/chatfs-cli-mockup/.claude/todo.kb/2026-07-13-000-Atomic-chat-dir-regeneration---stage-and-rename--never-rewrite-in-place.md` —
  closes the non-atomicity gap noted above.
