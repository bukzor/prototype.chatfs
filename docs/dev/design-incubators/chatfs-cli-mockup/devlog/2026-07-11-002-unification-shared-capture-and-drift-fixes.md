# Devlog: 2026-07-11 — Unification: shared capture(), pluck persistence, chatgpt cross-check, details contract, driver model

## Focus

Immediate plan step 4 (`../.claude/todo.md`): execute
`../.claude/todo.kb/2026-07-03-000-cross-provider-data-flow-drift--pre-unification-fixes-vs-unification-scope.md`
§ "Solve by unification" — all five requirements — plus AI Studio's
still-missing `path_browse`/`url_render` entry points, built against
the newly-shared `capture()`. This closes that todo.kb file and the
shared-code-among-providers file's tactical half.

## Decisions

### chatgpt's endpoint cross-check needed normalization, not a verbatim port

Claude's `null_tolerant_mismatches(conversation_doc, index_item)` works
unmodified because claude's two endpoints share literal key names and
representations (`uuid`/`name`/`created_at`, both ISO strings) —
verified directly against a real captured `conversation.json`/
`meta.json` pair. chatgpt's don't: the conversation doc names the id
field `conversation_id` (not `id`) and carries `create_time` as a unix
float where the index returns an ISO string. A verbatim port would
null-tolerantly skip the `id` comparison entirely (missing key on one
side reads as "ok") and *always* flag `create_time` as mismatched
(same value, different representation, forever) — the second failure
mode would make chatgpt's `url_browse` fail-hard on every real
capture. `_index_shaped()` (`chatfs_chatgpt_conversation_url_browse.py`)
projects the conversation doc into `IndexItem` shape first, reparsing
`create_time` through `chatfs_chatgpt_layout.created_at` (promoted from
private `_created` to public, since it's now a second module's call
site) so both sides compare as normalized ISO strings. Verified against
a real captured pair: zero mismatches.

**Alternative considered:** comparing only `title` (the one field that
genuinely matches byte-for-byte without normalization) — rejected,
since it would silently drop the create_time cross-check's actual
value (catching real data-integrity drift between the two endpoints),
not just a naming difference.

### `capture()` generalized by two parameters, not a provider callback

`chatfs_layout.py::capture(url, chat_dir, pluck_script, *,
conversation_filename="conversation.json")` — the only two axes of
variation found across all three providers' capture logic were *which*
pluck script runs and *what* the pluck output gets named (AI Studio's
`conversation.raw.json`, since its pluck output still needs a massage
pass). No provider needed a callback or a subclass; each
`chatfs_<provider>_layout.py::capture()` is a one-line partial
application. `run_pluck(script, src, dst)` — the "run a filter, tee
stdout to disk" primitive `capture()`'s conversation-pluck step already
needed — got extracted too, since the same shape was needed for the
incidental-index pluck (now persisting `.data/index-pages.jsonl`
instead of `capture_output=True`-only) and AI Studio's massage stage.

### `null_tolerant_mismatches` went to a new module, not `chatfs_layout.py`

`chatfs_layout.py` is storage/view-tree concerns (where a chat lives on
disk, how the view tree symlinks to it); the endpoint cross-check is a
url-browse-orchestration concern with no storage-layer dependency.
Rather than let `chatfs_layout.py` become a catch-all for "shared code,
whatever kind," it got its own `chatfs_url_browse.py`. This answers
`shared-code-among-providers.md`'s open "what moves vs. stays" question
concretely: not every shared function belongs in the same module just
because it's shared.

## Conventions Established

- A provider's `capture()`/`place_meta()` wrapper is the seam: a
  one-to-three-line partial application of a shared function, never a
  reimplementation. `capture()` joins `place_meta()` as an instance of
  this shape (see `design.kb/040-design.kb/provider-plugin-model.md`).
- "Shared" doesn't mean "one module." Shared code sorts into modules by
  what it's *about* (storage layout vs. url-browse orchestration vs.
  rendering), not by "used by more than one provider."
- New: `design.kb/040-design.kb/driver-model.md` records the
  pipe-vs-delegation resolution (thin drivers over one library) and
  explicitly scopes what's landed (capture/pluck) vs. deferred (splat/
  render orchestration still subprocess-composed, not yet
  function-imported by orchestrators) via a `[!TODO]` block.

## Mistakes and Recovery

Used `git stash` mid-session to check basedpyright's warning baseline
against the chatgpt-export package before/after the `<details>`-wrapping
change — a documented "never do this" in
`~/.claude/reference.kb/git/conventions.md` (stash is unscoped and
destructive; the project convention is a throwaway-branch commit
instead). `basedpyright` exits 1 whenever there are *any* warnings (not
just errors), which under the Bash tool's `set -e` silently skipped the
subsequent `git stash pop` in the same compound command — the stash sat
un-popped (`stash@{0}`) for one turn before being caught (`git stash
list` was non-empty, `git diff --stat` showed no changes even though
files had just been edited). Recovered cleanly with a lone `git stash
pop` in its own command; nothing was lost, but it's a reminder that
`set -e` plus a multi-line git-stash dance is exactly the failure mode
the house convention exists to avoid.

Separately, an isolated `har-browse` stub written to smoke-test AI
Studio's new `path_browse.py` initially cat'd its replay source from
the *same path* `capture()` was about to `unlink()` — clobbering the
only real captured AI Studio demo fixture (`cdp.jsonl`,
`conversation.json`, `conversation.raw.json` all went to 0 bytes).
`chatfs.demo/` is gitignored, so there was no git history to restore
from; recovered using `aistudio.cdp.jsonl` (a root-level capture of the
same prompt, from the original 2026-06-20 reverse-engineering session)
by re-running the real pluck → massage → place_meta → path_render
pipeline by hand. Verified restored: `chat.md` back to the expected
439 lines / 15 turns. Lesson: a stand-in for a live external tool
(`har-browse`) must read from a path outside anything the code under
test is about to write to — an isolated scratch chat-dir (a `.chat/`
tree under the session scratchpad, not the fixture in place) is the
safe shape, used for the rest of the session's smoke tests.

## Open Questions

- `design.kb/040-design.kb/driver-model.md`'s `[!TODO]` — should
  splat/render orchestration (`path_render.py` et al.) move from
  subprocess composition to direct in-process function calls? Not
  decided; flagged as a further move under shared-code boundary
  refinement, not blocking anything today.

## References

- `../.claude/todo.md` — Immediate plan step 4
- `../.claude/todo.kb/2026-07-03-000-cross-provider-data-flow-drift--pre-unification-fixes-vs-unification-scope.md`
- `../.claude/todo.kb/2026-05-11-001-shared-code-among-providers.md`
- `../.claude/todo.kb/2026-06-20-000-aistudio-provider-parity-ladder.md`
- `chatfs_layout.py`, `chatfs_url_browse.py`
- `chatfs_claude_layout.py`, `chatfs_chatgpt_layout.py`, `chatfs_aistudio_layout.py`
- `chatfs_chatgpt_conversation_url_browse.py`, `chatfs_chatgpt_conversation_path_browse.py`
- `chatfs_aistudio_conversation_url_browse.py`,
  `chatfs_aistudio_conversation_path_browse.py`,
  `chatfs_aistudio_conversation_url_render.py`
- `../../../../packages/bukzor.chatgpt-export/lib/bukzor/chatgpt_export/splat.py`
- `design.kb/040-design.kb/driver-model.md`
