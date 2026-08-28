# Devlog: 2026-08-28 — chatgpt paginates conversations; conversation.json becomes an assembled document

## Focus

`chatfs-chatgpt-conversation-url-browse` started dying on a zero-byte
`conversation.json`:

    json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

The pluck matched nothing. Diagnosis, then adaptation.

## What happened

1. **The endpoint moved and split.** Comparing captures either side of the
   break (2026-08-17 works, 2026-08-27 is the first zero-byte one) shows
   chatgpt.com replaced

       GET /backend-api/conversation/{uuid}      -> {..., mapping, current_node}

   with

       GET /backend-api/conversations/{uuid}?num_turns=10
           -> {..., messages: [...], current_node, page_info}
       GET /backend-api/conversations/{uuid}/messages?before={cursor}&num_turns=10
           -> {messages: [...], page_info}

   Singular to plural, one document to N pages, and `mapping` is gone:
   the pages carry flat message objects with no `parent`/`children`. The
   pluck's `/conversation/[0-9a-f-]+$` matched only the old shape, and its
   `$` anchor also excluded the new shape's query string.

2. **Assemble is a stage.** `conversation.json` keeps its meaning -- one
   whole document, `mapping` plus `current_node` -- and gains a stage that
   builds it: pluck now writes `conversation.json.d/raw.jsonl` (one
   `{"url", "body"}` per conversation-bearing response) and
   `chatfs-chatgpt-conversation-assemble` chains the pages into the
   document. AI Studio's `massage_json` already set this shape; chatgpt is
   the second user, which is why `run_module` and `capture`'s
   `conversation_filename` are now documented as a pattern rather than an
   AI Studio quirk.

   The record keeps the response URL because the page link lives in the
   request (`?before=`), not the body. Ordering by message timestamp was
   the alternative and it's a guess: the oldest page opens with system
   messages whose `create_time` is null.

3. **Assembly is staged, so a bad capture is not destructive.** The
   original symptom was a *zero-byte* `conversation.json` -- `run_module`
   truncates its destination before the subprocess can fail. Assembly runs
   inside `atomic.staged`, so the incomplete-capture failure below leaves
   the last whole document intact.

4. **Recovered both broken captures without re-browsing.** Everything
   needed was already in `cdp.jsonl`; the two conversations that had
   failed since the change re-rendered from bytes on disk (160 messages /
   125 turns, zero `type="unmodeled"` markers).

## Decisions

### Forks are lost, and that stays visible

**Rationale:** The new endpoints serve one linear thread. The assembled
`mapping` is therefore a chain -- each message parents the next. We don't
invent branch structure we didn't receive, and we don't rename the
artifact to advertise a completeness we can't check.

**Alternatives considered:** Fetching the old endpoint ourselves with the
browser's session, or auto-scrolling the page to force the older pages to
load. Both make the tool the cause of the provider's response, which
`policy-safe-automation-boundary.md` forbids. Working on already-captured
bytes is the part of that boundary we're allowed inside.

### An incomplete page chain raises

**Rationale:** `no-partial-synthesis.md` rule 3. chatgpt sends older pages
only as the reader scrolls back, so a capture taken from the bottom of a
long conversation is a suffix. The error names the recovery ("scroll to
the top of the conversation before clicking Done Capturing") because the
reader is the only actor allowed to perform it.

### A body carrying `mapping` still passes through

**Rationale:** Which shape a browse gets is the provider's choice, per
account and per rollout. The stage reads the body rather than assuming a
migration completed.

## Conventions Established

- `iter_responses` (url + body) is the pluck primitive;
  `iter_response_bodies` is the common case built on it. Renamed from
  `iter_responses_matching`.
- A provider whose pluck output needs a stage before it earns the contract
  name writes `conversation.json.d/raw.*` -- AI Studio's massage,
  chatgpt's assemble.

## Postscript: the fork markers survive

Asked whether the data says *where* a fork went missing. It does, and
checking beat the assumption twice:

- **`metadata.has_versions: true`** marks a message with siblings the
  response didn't carry -- 6 of 160 here, every one a user message. It's
  what `?include_has_versions=true` buys, and it arrived with the
  pagination change: the old-format captures carry it on zero nodes
  because their requests never asked. So the branch *locations* survive
  even though the branch *content* doesn't.

  Corroborated by the one capture that still has a true `mapping`
  (`696bf4b5`, 2026-08-17): all 6 of its fork points are
  `assistant -> [user, user]`, i.e. user-turn edits -- exactly the shape
  a `has_versions` user message marks.

- **`metadata.parent_id` is not structure**, though 139 of 160 messages
  carry it. Same old-format capture, where the real graph is available to
  check against: of 91 nodes bearing a `parent_id`, 31 match the node's
  actual parent and 60 name an id absent from the conversation entirely.
  Generation-time bookkeeping. The commit message's "no parent/children
  anywhere" was too strong as stated; the operative claim -- that no
  usable edge survives -- holds, and now has a measurement behind it.

`canonical-conversation-graph.md`'s fork guarantee still holds for claude
and not for chatgpt: we can say a fork was here, not what was in it.

## Open Questions

- Whether a fork's *content* is reachable at all under
  `policy-safe-automation-boundary.md` -- clicking a `<` arrow is the
  reader navigating, which is allowed, but whether that fires a
  capturable response is unmeasured.

## References

- `packages/chatfs-cli/design.kb/040-design.kb/conversation-document-is-whole.md`
- `packages/chatfs-cli/design.kb/040-design.kb/no-partial-synthesis.md`
- `docs/dev/technical-policy.kb/policy-safe-automation-boundary.md`
