# noun=conversation, verb=render

Render emits markdown for a conversation. The bare leaf
(`chatgpt conversation render <chat-dir>`) walks `mapping` from root
toward `current_node` in `.data/conversation.json`:

- Live-path turns render unprefixed.
- Dead-branch turns appear immediately after their fork point,
  blockquote-prefixed at fork depth — they read as quoted asides between
  the parent turn and the live continuation.
- Each turn is `# [seq · role · time](messages/<stem>.md)` — H1 backref
  to the atomic turn-file under `messages/`.

The bare leaf reads `.data/conversation.json` and `messages/*.json` to
find each turn's stem; it does not manage placement and writes markdown
to stdout.

The orchestrator forms prepare inputs and place outputs. `path render`
purges non-captured content (allowlist `{.data}`), splats
`.data/conversation.json` via `chatgpt-splat` (see `../../verb=splat.md`)
into `messages/` and `conversations/`, calls the bare leaf, and writes
the result to `chat.md`. `url render` thinly resolves the URL → chat dir
and delegates to `path render`.

Deterministic regen: orchestrator forms rebuild the splat tree and
`chat.md` from `.data/conversation.json` on every invocation. See
`../../deterministic-regeneration.md`.
