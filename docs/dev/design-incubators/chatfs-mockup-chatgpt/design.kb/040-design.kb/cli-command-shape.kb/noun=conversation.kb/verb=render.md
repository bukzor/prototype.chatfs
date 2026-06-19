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

## Fork-fact notation

When the tree forks, the render makes the fork legible from headings and
metadata alone. The governing audience is the *excerpt reader* (grep
window, partial read): no single fact may live in only one place if a
reader landing elsewhere would need it, so fork facts repeat across
positions.

- **Numbering** is branch-prefixed: a branch member is `head/seq`
  (`049/051`); trunk and branch-head turns render bare (`049`). Numbers
  are stable cross-reference handles, not chronology.
- **`(re: N)` backlink** on the heading when the parent isn't the turn
  directly above.
- **Metadata lines** sit in two zones around the body, by *direction*:
  - *Above* the body — version **status**, read before deciding to engage:
    `superseded by: <winner>` on each abandoned sibling (one hop to the
    live continuation from any excerpt); `prior revisions: …` on the
    winner (succession order — the revision chain recoverable in one
    canonical place, landing right after the superseded asides it names).
  - *Below* the body — forward **navigation**: `replies: …` on a fork
    parent, all children in render order with the live one marked `←live`.
- **Spelling is bare `*italics*`, not `<sub>`.** The primary consumers are
  LLMs and plaintext editors, to which `<sub>` tags are token cost and
  visual clutter; in-browser smallness would serve only the third-ranked
  consumer. Same reasoning that keeps **anchors** out: refs repeat the
  heading's number verbatim, so a search for a ref string finds the
  definition — the heading *is* the anchor, no `<a id>` needed.
- **`←live` is explicit, not positional.** Liveness must not rely on the
  unstated "last in the list is live" convention.
- A `---` divider at the *parent's* depth separates adjacent sibling
  branches, splitting their blockquotes into distinct islands.

This notation is **provider-agnostic** — it's a property of rendering a
forked conversation, not of any one provider's capture. Both provider
renderers must emit it identically.

The orchestrator forms prepare inputs and place outputs. `path render`
purges non-captured content (allowlist `{.data}`), splats
`.data/conversation.json` via `chatgpt-splat` (see `../../verb=splat.md`)
into `messages/` and `conversations/`, calls the bare leaf, and writes
the result to `chat.md`. `url render` thinly resolves the URL → chat dir
and delegates to `path render`.

Deterministic regen: orchestrator forms rebuild the splat tree and
`chat.md` from `.data/conversation.json` on every invocation. See
`../../deterministic-regeneration.md`.
