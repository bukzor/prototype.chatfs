# Pipeline Implications

Per-script consequences of the chat-as-directory layout.

Each section is keyed by script; for the noun-verb-locator framing of
those scripts (which noun/verb/locator each implements, why each name
was chosen), see `../cli-command-shape.md` + `../cli-command-shape.kb/`.

## `place_meta(item, root)`

1. Ensures `$root/.chat/$UUID/.data/` exists, writes
   `$root/.chat/$UUID/.data/meta.json`.
2. Runs the view-symlink cleanup for `$UUID` (see
   `../deterministic-regeneration.md` — Identity-scoped cleanup).
3. Creates a single directory-symlink under `$root/<ts-dir>/$TITLE`
   pointing at `$root/.chat/$UUID/`.

The `$UUID/` dir may already exist (re-place); only the captured files
inside `.data/` are overwritten. Derived files left from a prior render
are not touched here — that's path-render's job.

## `conversation_url_browse` and `conversation_path_browse`

Write `cdp.jsonl` and `conversation.json` directly into
`.chat/$UUID/.data/`. URL browse derives `$UUID` from the URL; path
browse takes the `.chat/$UUID/` dir as its address.

## `conversation_path_render`

Takes a `.chat/$UUID/` dir as its argument (the canonical chat unit).

1. Cleans non-captured contents (allowlist `{".data"}`; see
   `captured-vs-derived.md`).
2. Runs `chatgpt-splat .data/conversation.json`, which writes
   `.data/conversation.splat/{messages,conversations}`.
3. Moves `messages/` and `conversations/` up two levels into the
   chat-dir root, then `rmdir .data/conversation.splat`.
4. Writes `chat.md` at `.chat/$UUID/chat.md`.

The visible chat-dir surface after render is `chat.md`, `messages/`,
`conversations/`. Captured exhaust stays out of the way under `.data/`.

## `conversation_render` (leaf)

Reads `.data/conversation.json` from a `.chat/$UUID/` dir, walks the
mapping, and emits the rendered markdown on stdout. No file output, no
path mutation. Inline links (`messages/<stem>.md`) are relative to
chat-dir root and resolve correctly under both real-path and
view-symlink reads.

## A future `view rebuild` verb (deferred)

Not on the critical path. Wipes a whole view tree (`rm -rf YYYY/`)
and rebuilds dir-symlinks from `.chat/$UUID/*` for ad-hoc resync.
Useful when the view derivation logic changes (TZ format, new view
shape) without a re-browse.
