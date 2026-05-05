# Pipeline Implications

Per-script consequences of the chat-as-directory layout.

## `place_meta(item, root)`

1. Writes `$root/.chat/$UUID/meta.json`.
2. Runs the view-symlink cleanup for `$UUID` (see
   `../deterministic-regeneration.md` — Identity-scoped cleanup).
3. Creates the date-view symlinks under `$root/<ts-dir>/`.

The `$UUID/` dir may already exist (re-place); only the captured files
inside it are overwritten. Derived files left from a prior render are
not touched here — that's path-render's job.

## `conversation_url_browse` and `conversation_path_browse`

Write `cdp.jsonl` and `conversation.json` directly into
`.chat/$UUID/`. URL browse derives `$UUID` from the URL; path browse
takes the `.chat/$UUID/` dir as its address.

## `conversation_path_render`

Takes a `.chat/$UUID/` dir as its argument (the canonical chat unit).

1. Cleans non-captured contents (see `captured-vs-derived.md`).
2. Runs `chatgpt-splat conversation.json`, which writes
   `conversation.splat/`.
3. Unpacks `conversation.splat/*` up one level into the chat dir, then
   `rmdir conversation.splat`.
4. Writes `chat.md` (with the `uuid:` frontmatter) at
   `.chat/$UUID/chat.md`.

## `conversation_render` (leaf)

Reads from a `.chat/$UUID/` dir and emits the rendered markdown —
including `uuid:` frontmatter — on stdout. No file output, no path
mutation.

## A future `view rebuild` verb (deferred)

Not on the critical path. Wipes a whole view tree (`rm -rf YYYY/`)
and rebuilds from `.chat/$UUID/*` for ad-hoc resync. Useful when the
view derivation logic changes (TZ format, new view shape) without a
re-browse.
