# noun=conversation, locator=url

URL addresses a conversation by the link its provider serves it at --
`https://chatgpt.com/c/$UUID`, `https://claude.ai/chat/$UUID`,
`https://aistudio.google.com/prompts/$ID`. Each provider's
`uuid_from_url` asserts its own path shape (chatgpt's checks
`parts[0] == "c"`), so a malformed link fails at parse rather than
producing a plausible wrong uuid.

The host names the provider, and is the only part that does: the paths
differ per provider and carry no such signal. Each `layout` declares its
`HOST` and builds `url_for` from it, so the map
`chatfs-conversation-url-<verb>` dispatches on cannot drift from the URLs
this codebase emits -- see `../../cli-command-shape.md`'s
**dispatching form**.

`url browse` is the first-capture entry point — used when the chat dir
doesn't yet exist or when only the URL is known. The conversation
capture is plucked once for `conversation.json` and a second time
through the index pluck filter, filtered to `.id == $UUID`, to populate
`.data/meta.json` (title, create_time → ts-dir). The match is required:
an admin-deleted or shared-link-only chat will not appear in the user's
sidebar pages and `url browse` fails loudly.

`url render` does not capture. It asserts `.data/meta.json` exists,
resolves the URL → `.chat/$UUID/` (via `chat_dir_for`), and delegates to
`path render`. Refusal-on-missing-meta is intentional: rendering without
a placed chat dir would orphan the output from the date-tree view.
