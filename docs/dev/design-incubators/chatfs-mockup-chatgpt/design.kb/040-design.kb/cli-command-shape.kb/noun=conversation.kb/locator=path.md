# noun=conversation, locator=path

Path addresses a conversation by any filesystem path inside or
referencing the chat dir. `resolve_chat_dir` (in
`chatfs_chatgpt_layout`) normalizes input — accepts the chat dir itself,
a file inside it, the view dir-symlink under the date tree, or any
descendant — and walks up to canonical `.chat/$UUID/`. Post-condition
asserted: result is a real directory whose parent is named `.chat`.

The view dir-symlink (`YYYY/MM/DD/HH-MM-SS-$TITLE → .chat/$UUID/`, see
`../../chat-as-directory.md`) is the user-facing entry point;
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
