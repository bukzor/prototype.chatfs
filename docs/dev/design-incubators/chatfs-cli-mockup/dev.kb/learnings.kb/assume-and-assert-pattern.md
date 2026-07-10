# Assume-and-assert: encode a live-behavior assumption as code

When facing an empirical question that can only be settled by real
behavior (a service's response shape, a tool's edge case, a timing
property), neither blocking on investigation nor coding for the
worst case is the right move. The pattern:

1. **Encode the assumption directly in the code path.** Write the
   happy path that depends on it; don't add fallback machinery.
2. **Surround the assumption with a tight assertion.** When the
   property is violated, fail loud with a recovery message that
   describes the symptom and the fallback procedure.
3. **Let real-world invocation be the empirical test.** First run
   either confirms the assumption (no action needed) or surfaces the
   failure with a documented data point.

## Worked example (from this session)

`chatfs_claude_conversation_url_browse.py` assumes the claude.ai
sidebar fires `/chat_conversations_v2` on chat pages (yielding
incidental index capture).

- Code uses one browse trip; calls `find_index_item` on the captured
  CDP.
- Assertion in `find_index_item` raises with a recovery message
  ("run `index_browse.sh | index_splat.py` then use `path_browse`")
  if no index page mentioned the target UUID.
- A second null-tolerant cross-check asserts conversation-doc and
  index-item agree on overlapping fields — catches schema drift
  independently of the first assumption.

## When this dominates the alternatives

- **vs. blocking on investigation:** investigation often costs more
  than the first-run discovery, especially when the empirical answer
  may itself be probabilistic or version-dependent.
- **vs. defensive worst-case design:** coding for "all three possible
  behaviors" obscures intent and creates dead branches. The
  assume-and-assert version is the simplest code that could possibly
  work; if the assumption breaks, the recovery branch belongs in a
  separate command anyway (here: the two-step recovery).

## When this is wrong

- **Destructive on failure.** If the failed-assumption path damages
  state, the loud assertion is too late. Invest in investigation
  first.
- **The recovery path doesn't yet exist.** Assume-and-assert assumes
  there's a documented fallback. If not, build the fallback first;
  it's the more important path.
