# noun=conversation, verb=browse

Browse fetches a conversation's current state from chatgpt.com via a real
browser. `har-browse` opens a Chromium window pointed at
`https://chatgpt.com/c/$UUID`; the CDP stream is captured to
`.data/cdp.jsonl`, then reduced through
`chatfs_chatgpt_conversation_pluck.jq` to `.data/conversation.json`.

Both locator variants (`url`, `path`) follow the same capture-and-pluck
shape and delegate to `path render` for final materialization (splat →
`messages/` + `conversations/` → `chat.md`). Both unlink prior
`.data/cdp.jsonl` and `.data/conversation.json` before re-capturing
(deterministic regen; see `../../deterministic-regeneration.md`).

The variants differ only in how the target URL is obtained:
`url browse` parses it from the argument; `path browse` reads
`.data/meta.json` from the resolved chat dir. Per-locator semantics
(failure modes, addressing details) live in `locator=url.md` and
`locator=path.md`.

## Browse-incidental capture

While the conversation page loads, `har-browse` also records the
`/backend-api/conversations` requests that the sidebar uses. `url browse`
exploits this to populate `meta.json` without a separate `index browse`
step: the same CDP stream is plucked twice (once for the conversation,
once for the index record matching `.id == $UUID`). See
`../../browse-incidental-capture.md`.
