# Pipeline Implications

Per-script consequences of the chat-as-directory layout.

Each section is keyed by script; for the noun-verb-locator framing of
those scripts (which noun/verb/locator each implements, why each name
was chosen), see `../cli-command-shape.md` + `../cli-command-shape.kb/`.

## `place_meta(item, root)`

1. Stages `meta.json` into `$root/.data/$UUID/` (`chatfs_atomic.staged`,
   under `.data/$UUID/`'s write lock).
2. Stages the view dir-symlink under `$root/<ts-dir>/$TITLE`, pointing
   at `$root/.chat/$UUID/` — placed *before* the identity-scoped purge
   below runs, so the chat never vanishes from every view.
3. Runs the view-symlink cleanup for `$UUID`, excluding the symlink
   just placed (see `../deterministic-regeneration.md` — Identity-scoped
   cleanup).

All three steps share one outer write lock on `.data/$UUID/`, so a
cooperating reader (`chatfs_locks.read_locked`) sees them as a single
transition. The `$UUID/` dirs may already exist (re-place); derived
files under `.chat/$UUID/` from a prior render are not touched here —
that's path-render's job.

## `conversation_url_browse` and `conversation_path_browse`

Both delegate to shared `capture()`: `cdp.jsonl` and the conversation
document are each staged into `.data/$UUID/` and atomically promoted,
under one outer write lock spanning both. A failed browse leaves the
prior `cdp.jsonl` untouched; a failed pluck leaves the prior
conversation document untouched even though a successful browse's new
`cdp.jsonl` is kept. URL browse derives `$UUID` from the URL and
delegates to path-render at the end; path browse takes the
`.chat/$UUID/` dir as its address and does not re-derive the URL.

## `conversation_path_render`

Takes a `.chat/$UUID/` dir as its argument (the canonical derived
unit).

1. Opens a staged scratch sibling (`chatfs_atomic.staged`, under
   `.data/$UUID/`'s write lock).
2. Creates the scratch dir and its `.data` inspection symlink
   (`link_data_dir`, pointing at `.data/$UUID/`).
3. Runs the provider's splat with an explicit output-dir argument,
   writing `messages/`/`conversations/` straight into the scratch — no
   move-up step.
4. Runs render, piping stdout to `chat.md` inside the scratch.
5. On success, the whole scratch is atomically promoted over
   `.chat/$UUID/` in one swap; on failure, the partial scratch is
   preserved as a `.fail` sibling instead.

No pre-clean allowlist: captured and derived artifacts live in separate
trees (`captured-vs-derived.md`), so there's nothing to purge in
advance. New derived outputs need no path-render change.

## `conversation_render` (leaf)

Reads `.data/conversation.json` through the chat dir's `.data`
inspection symlink, walks the mapping, and emits the rendered markdown
on stdout. No file output, no path mutation beyond the caller's own
scratch. Path-render invokes this leaf against the staged scratch
sibling (not yet promoted), so it reads via the `.data` symlink rather
than computing `.data/$UUID/` directly — the symlink is valid from both
the scratch and the final chat dir, since `link_data_dir` takes the
uuid explicitly rather than inferring it from the containing dir's
name. Inline links (`messages/<stem>.md`) are relative to chat-dir root
and resolve correctly under both real-path and view-symlink reads.

## A future `view rebuild` verb (deferred)

Not on the critical path. Wipes a whole view tree (`rm -rf YYYY/`)
and rebuilds dir-symlinks from `.chat/$UUID/*` for ad-hoc resync.
Useful when the view derivation logic changes (TZ format, new view
shape) without a re-browse.
