# noun=conversation, verb=browse

Browse fetches a conversation's current state from chatgpt.com via a real
browser. `har-browse` opens a Chromium window pointed at
`https://chatgpt.com/c/$UUID`; the CDP stream is captured to
`.data/cdp.jsonl`, then reduced through
`chatfs_chatgpt_layout.pluck_conversation` to `.data/conversation.json`.

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

## AI Studio divergence

`chatfs_aistudio_conversation_url_browse.py` follows the same
capture-and-pluck shape, but two things differ from chatgpt/claude:

- **An extra file and stage.** AI Studio's wire format is JSPB (positional
  arrays), not native keyed JSON, so pluck's output isn't yet "good" —
  it's written verbatim to `conversation.json.d/raw.json` (audit copy,
  scratch under the eventual contract file's `.d/` sibling — see
  `path-ownership.md`), then `chatfs_aistudio_conversation_massage_json.py`
  names it into `conversation.json`. chatgpt/claude have no `.raw.json`:
  their pluck output is already the final shape.
- **No incidental-index capture.** There's no reverse-engineered AI Studio
  index endpoint yet (see the parity-ladder todo.kb), so there's nothing to
  cross-check against. Identity (`metadata.displayName`/`lastModified`)
  arrives in the *same* `ResolveDriveResource` body that becomes
  `conversation.json`, so `chatfs_aistudio_layout.index_item` derives
  `meta.json` straight from it — no second endpoint, no cross-check, no
  `find_index_item`-style fallback.

`url_browse.py` delegates to `path render` like the other two providers
(landed 2026-07-11; see `verb=render.md`'s AI Studio divergence note).
