# Devlog: 2026-08-28 — Uncaptured forks render as 'prior revisions: not captured'

## Focus

Landing the `[!TODO]` filed in `conversation-document-is-whole.md` the same
day: chatgpt tells us where an edited turn forked
(`metadata.has_versions`) without sending the superseded text, and
`chat.md` was rendering those turns as an unremarkable straight line.

Done on a branch in a `git worktree` -- another agent was working the
main checkout at the time, and landed a cache-layout change (`befa423`)
while this was in flight.

## Decisions

### The gap reuses the `prior revisions:` key

**Rationale:** A reader who has seen `prior revisions: 031, 032` reads
`prior revisions: not captured` without being taught anything new, and
one grep (`prior revisions:`) enumerates every superseded version in any
provider's `chat.md` -- the numbered ones you can jump to and the absent
ones you can only be told about. Vocabulary is the expensive part of a
notation; this adds none.

The key is honest here specifically because the paginated endpoints only
ever serve the live path: every message we receive is the surviving
version, so the siblings we're missing are always *priors*. That is what
licenses the word, not convenience.

**Alternatives considered:** A new key (`other versions:`, `fork here:`)
would have split the grep and taught a second word for the same fact.

### `uncaptured_versions` is a tree field, not a chatgpt detail

**Rationale:** `ConversationTree` is the provider-neutral seam, and "the
source named a fork it didn't ship" is a property any provider's wire
format can develop. It defaults empty, so claude and aistudio are
untouched -- their golden renders are byte-identical.

### Both version facts can hold at once

**Rationale:** `version_status` previously returned `superseded by: N` or
`prior revisions: ...` as converses, one node being exactly one of them.
A captured dead branch that *itself* has uncaptured siblings is both, so
the two items now join with ` · ` rather than one displacing the other.
No provider can currently produce that node -- chatgpt's tree is a chain
where every node is primary -- but the alternative was code that silently
drops a true fact the moment one can, which is the failure mode this
whole entry exists to prevent.

## Verification

- 204 tests (9 new). Each new assertion driven to red by mutation:
  dropping the `not captured` prior (5 red), collapsing the ` · ` join
  back to `or` (1 red), and dropping the flag set from
  `normalize_turnless`'s reconstruction (2 red).
- Real capture end to end: 6 markers in `chat.md`, on the 6 flagged user
  turns, matching the 6 `has_versions` messages in the raw responses.

## Open Questions

- A fresh `uv sync` produces a venv whose `pytest` cannot start:
  `pytest-pyright`'s pydantic models fail to build under
  Python 3.14.0rc2 (`typing._eval_type() got an unexpected keyword
  argument 'prefer_fwd_module'`). Worked around here with
  `-p no:pyright`. The repo-root `.venv` predates the offending
  resolution and is unaffected, which is why it hasn't bitten before.

## References

- `packages/chatfs-cli/design.kb/040-design.kb/conversation-document-is-whole.md`
- `2026-08-28-000-chatgpt-paginates-conversations--conversation-json-becomes-an-assembled-document.md`
