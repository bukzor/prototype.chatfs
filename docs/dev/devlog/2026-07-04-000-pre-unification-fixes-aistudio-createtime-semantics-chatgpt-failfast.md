# Devlog: 2026-07-04 — Pre-unification fixes: aistudio create_time semantics, chatgpt failfast

## Focus

Work the "Fix before unification" list in
`.claude/todo.kb/2026-07-03-000-cross-provider-data-flow-drift--pre-unification-fixes-vs-unification-scope.md`
(from the 2026-07-03 three-provider review), item by item, in priority
order (user: "first thing first"). Item 1 (aistudio splat/index_item
retarget) had already landed 2026-07-03; this session closed items 2
and 3.

## Decisions

### aistudio `create_time` anchors on first-chunk `createTime`, not `lastModified.revisionTime`

`chatfs_aistudio_layout.index_item` was reading
`metadata.lastModified.revisionTime` into `create_time` — verified live
against the demo capture that this is a *modification* timestamp
(`12:53:25`) that trails the conversation's actual creation
(`chunks[0].createTime`, `12:42:40`) by ~11 minutes, and would drift
further with every future re-capture of an active chat. Switched to
`chunkedPrompt.chunks[0].createTime`, matching chatgpt (`create_time`)
and claude (`created_at`), both genuine creation timestamps — all three
providers' date trees now bucket by the same semantic.

**Rationale:** unification will build one shared date-tree bucketing
function; baking a wrong (modification-time) semantic into aistudio
before that landed would have meant fixing it twice, or worse, fixing
it once and silently changing the other two providers' semantics to
match the wrong one.
**Alternatives considered:** keep `revisionTime` but rename the field
honestly (e.g. `modified_time`) — rejected because neither chatgpt's
nor claude's `IndexItem` carries a modified-time field, so adding one
to aistudio alone would be asymmetric, and the actual need (a
comparable creation-time bucket) is what all three date trees use.

Corrected the same mislabel in
`dev.kb/claims.kb/aistudio-jspb-prompt-shape.md` (added a
`previously-claimed:` entry per that collection's correction
convention, plus the turn-level `[32] createTime` field to the table).

### chatgpt failsoft → failfast: two sites, two different fixes

`packages/bukzor.chatgpt-export/lib/bukzor/chatgpt_export/splat.py`
`extract_text_content`'s terminal `else: return None` on an unrecognized
`content_type` now raises `ValueError`, mirroring claude's `extract_text`.
Grepped every captured export in the repo: only 6 content_types have
ever been observed (text/thoughts/code/reasoning_recap/
user_editable_context/model_editable_context) — this is latent-bug
coverage, not a currently-live bug.

`chatfs_chatgpt_conversation_render.py` was the harder call. The plan
(recorded in the todo file before this session) was to mirror claude's
`prune_bodiless_leaves` + `assert set(turns) == set(by_uuid)`
body-coverage pattern. Built it, then ran it end-to-end against a real
188-message capture — it failed with 58 "missing bodies", all
legitimate: chatgpt's tree is full of **non-leaf** bodiless pass-through
nodes (blank system-context messages, empty thought summaries) that
claude's tree structurally doesn't have. Claude's prune list only
excludes *childless* leaves because for claude that's the only
legitimately-bodiless case; for chatgpt it's the common case, not an
edge case, so a leaf-only prune list produces false positives on real
data.

**Rationale for the actual fix:** the real "vanishing" risk render.py
can independently catch is a stem-parsing bug in its own directory
scan (a message id silently dropped from `by_uuid` because its stem
didn't split into exactly 4 dot-separated parts) — landed as
`assert set(by_uuid) == set(mapping)`. The "unknown content_type"
risk claude's assertion also catches is already fully covered
upstream, at the source, by splat's raise (which runs before any
message in the file gets written, so render.py can assume every
`.json` it finds came from a fully-recognized content_type).
**Alternatives considered:** broaden the prune-list criteria to accept
non-leaf bodiless nodes too — rejected as pointless: once you accept
that most bodiless nodes are legitimate regardless of leaf-ness, the
"prune list" degenerates into "assert nothing", providing zero
signal while adding a function's worth of complexity. Removed it.

Verified end-to-end: `git stash` the two edited files to get pre-edit
baseline behavior, ran the full `path_render` pipeline on the
188-message capture both before and after, diffed `chat.md` —
byte-identical. Swept every demo chat with a captured
`conversation.json` (2 of ~57 demo chats have one downloaded); both
clean under the new asserts. `uv run pyright` (the user has since
switched to `basedpyright-as-pyright`, notably stricter) clean on both
files, module the 2 pre-existing `reportMissingTypeArgument` (bare
`dict`) warnings in render.py that predate this session's edits.

## Conventions Established

- When mirroring another provider's failsafe/assertion pattern, verify
  it against real captured data for *this* provider before trusting the
  analogy — provider trees can differ structurally (chatgpt's ubiquitous
  bodiless mid-tree nodes vs. claude's rare bodiless leaves) in ways
  that invalidate a design that looks reusable on paper.
- Repo-root basedpyright (no scoping `pyrightconfig.json` for this
  incubator dir) is stricter than `packages/bukzor.chatgpt-export`'s own
  scoped config — expect `reportAny`/`reportMissingTypeArgument` noise
  here that the package itself doesn't surface. Not this session's to
  fix; flagged in `.claude/sessions.kb/provider-code-reuse-stutter-step.md`
  as a small future cleanup.

## Open Questions

- None outstanding for the pre-unification scope — the aistudio
  unification gate (todo file's items 1-3) and the independent chatgpt
  bug (item 4) are both closed. The "Solve by unification" section of
  that same todo file remains open by design (5 requirements for the
  shared-code refactor, not to be fixed in place).

## References

- `.claude/todo.kb/2026-07-03-000-cross-provider-data-flow-drift--pre-unification-fixes-vs-unification-scope.md`
- `.claude/todo.kb/2026-05-11-001-shared-code-among-providers.md`
- `dev.kb/claims.kb/aistudio-jspb-prompt-shape.md`
- `chatfs_claude_conversation_render.py` (`prune_bodiless_leaves`,
  line ~281) — the pattern investigated and found not to transfer
- `~/.claude/sessions.kb/provider-code-reuse-stutter-step.md` — the
  broader line of work this unblocks
