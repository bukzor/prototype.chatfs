# View Entry as Directory-Symlink

The user-facing entry point for a chat is a single directory-symlink at
`YYYY/.../$TITLE`, whose target is `.chat/$UUID/`. The view path is
UUID-free; the storage path isn't, but users don't normally tread the
storage layer.

## Why a directory-symlink, not a file-symlink

The chat dir contains derived outputs that reference each other by
relative path: `chat.md` links to `messages/<stem>.md`. A file-symlink
to `chat.md` resolves the file fine, but the textual link
`messages/<stem>.md` doesn't exist alongside the symlink under the view
path — only beside the real `chat.md` under storage.

That asymmetry breaks path-textual renderers (web rendering — GitHub
Pages, mkdocs, Obsidian publish) that read `chat.md` via the view path.
Such renderers don't follow symlinks; they read text and resolve links
textually.

A directory-symlink solves this: the view-path entry *is* the chat dir
(via one symlink resolution). Walking from `view/$TITLE/chat.md` into
`view/$TITLE/messages/<stem>.md` is a textual descent — the
dir-symlink is followed once to reach `.chat/$UUID/`, and everything
inside that dir is reached by plain pathname lookup. Links work
everywhere.

## Single symlink per view dir

The earlier shape had two entries per chat (a `$TITLE.md` file-symlink
plus a `.chat` dir-shortcut). The directory-symlink folds both: the
view IS the chat dir. There's no longer a need for a separate
`.chat` shortcut — `cd 2026/.../$TITLE/` lands inside the chat.

## Pre-render dangling

Pre-render, `.chat/$UUID/` doesn't exist yet, so the view dir-symlink
itself dangles — not just `chat.md` inside it. Reading
`view/$TITLE/chat.md` returns ENOENT until the render completes and
promotes the chat dir into place. The dangling link is the deliberate
"not yet synced" signal; captured artifacts are meanwhile inspectable
at `.data/$UUID/`.

## Ergonomic tradeoff

`cat date/$TITLE.md` becomes `cat date/$TITLE/chat.md` — one extra
path component. `chat.md` is stable across all chats — arguably better
for muscle memory than per-chat title-derived filenames; tab-completion
to `chat.md` is identical everywhere.
