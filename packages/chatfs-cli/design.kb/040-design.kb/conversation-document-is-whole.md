---
why:
  - ../../../../docs/dev/design.kb/030-requirements.kb/canonical-conversation-graph.md
  - ../../../../docs/dev/design.kb/030-requirements.kb/pipeline-composability.md
---

# The Conversation Document Is Whole

`.data/$UUID/conversation.json` holds one complete conversation
document -- a single-rooted `mapping` in which every message is
reachable and `current_node` names a node that exists -- however many
HTTP responses the provider used to deliver it. Downstream stages
(splat, render) see a document, never a transport.

## Assembly is a named stage

chatgpt delivers a conversation over N responses: the conversation
endpoint carries the newest page of `messages` plus a `page_info`
cursor, and each older page is a separate `/messages?before=<cursor>`
response fired as the reader scrolls back. Pluck cannot flatten that
by itself, so the pipeline splits in two, following AI Studio's
massage precedent:

- pluck → `conversation.json.d/raw.jsonl`, one `{"url", "body"}`
  record per conversation-bearing response, in capture order
  (`path-ownership.md`'s `.d/` scratch convention: the contract name
  `conversation.json` reserves the sibling)
- assemble → `conversation.json`, the whole document

The record keeps the URL because the link between pages lives in the
*request* (`?before=<start_cursor>`), not in the body. Ordering pages
by their messages' timestamps instead would be a guess -- the oldest
page opens with system messages whose `create_time` is null.

## An incomplete page chain fails loudly

Assembly walks `has_previous_page` back from the conversation endpoint's
own page until a page reports `has_previous_page: false`. A missing link
in that chain means the capture stopped mid-conversation, and the stage
raises rather than emit a truncated document -- `no-partial-synthesis.md`
rule 3.

The reader's recovery is to scroll to the top of the conversation before
clicking **Done Capturing**. Scrolling on the reader's behalf is not
available to us: it would make the tool, not the human, the cause of the
provider's response (`policy-safe-automation-boundary.md`).

## Fork structure is only as rich as the capture

The assembled `mapping` carries exactly the branching the provider
served. chatgpt's paginated endpoints serve the current thread as a
linear sequence, so the mapping they assemble into is a chain: each
message parents the next, `current_node` is the last. Edited-and-
regenerated turns that the old single-response endpoint exposed as
sibling branches are not in these responses at all.

That is a loss of fidelity, and it is the provider's, not ours. What
the design forbids is disguising it: we do not invent branch structure,
and we do not rename the artifact to advertise a completeness we can't
check. `conversation.json` means "the conversation document, whole as
captured" -- a chain is a legitimate value of that, an assembled prefix
is not.

## Both response shapes assemble

A body that already carries `mapping` is a whole document as it stands
and passes through unchanged. Which shape a browse yields is the
provider's choice, per account and per rollout; the stage reads the
body rather than assuming.
