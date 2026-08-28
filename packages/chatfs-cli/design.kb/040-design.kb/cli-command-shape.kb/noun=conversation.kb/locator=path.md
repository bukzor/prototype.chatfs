# noun=conversation, locator=path

Path addresses a conversation by any filesystem path inside or
referencing the chat dir. `resolve_chat_dir` (in
`chatfs.shell.place`) normalizes input — accepts the chat dir itself,
a file inside it, the `.data/$UUID/` twin, the view dir-symlink under the
date tree, or any descendant — and walks up to canonical `.chat/$UUID/`.
It climbs by `p.parent.name` rather than `is_dir()`, and does **not**
assert the result exists: a chat dir legitimately does not, before its
first render.

The provider is a segment of that canonical form. `resolve_chat_dir`
yields `$cache/$provider/.chat/$UUID`, so `chatfs-conversation-path-<verb>`
reads the provider off the path instead of being told it -- see
`../../cli-command-shape.md`'s **dispatching form**.

The view dir-symlink (`Created=YYYY/MM/DD/HH:MM:SS±HH:MM/$TITLE →
.chat/$UUID/`, see `../../chat-as-directory.md`) is the user-facing entry point;
`resolve_chat_dir` is intentionally forgiving so the user can pass either
the view path or the storage dir interchangeably. Loose-then-strict:
ergonomic input shapes encapsulated inside `resolve_chat_dir`, downstream
code assumes the canonical post-condition.

`path browse` reads `.data/meta.json` from the resolved chat dir to
derive the URL, then re-captures CDP and re-plucks `conversation.json`.
Fails if `meta.json` is absent — run `url browse` or `index splat` first.

`path render` purges non-captured content (allowlist `{.data}`),
re-splats, re-renders. Both the bare-leaf
`chatgpt conversation render <chat-dir>` and the orchestrator
`chatgpt conversation path render <chat-dir>` accept path input; the
former emits markdown to stdout, the latter writes `chat.md`.
