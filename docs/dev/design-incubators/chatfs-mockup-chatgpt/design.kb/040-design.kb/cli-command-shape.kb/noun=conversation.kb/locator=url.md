# noun=conversation, locator=url

URL addresses a conversation by its ChatGPT URL:
`https://chatgpt.com/c/$UUID`. `uuid_from_url` parses with
`assert parts[0] == "c"` — the URL must match that shape.

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
