# Devlog: 2026-07-11 — AI Studio conversation_render/path_render: linear-chain confirmed

## Focus

Immediate plan step 3 (`../.claude/todo.md`): finish AI Studio's
conversation side — `conversation_render`, `path_render`, and
`url_browse` delegating to it. Step 2 (index rung) was accepted
done-for-now by the user mid-session ("as done as we can get it at the
present time") without the three index scripts themselves landing —
tracked as a deliberate deferral, not an oversight.

## Decisions

### AI Studio's turn history is linear — no fork tree, ever

Checked before writing the renderer, per the plan's explicit
"verify the linear/no-forks assumption first." `chunkedPrompt.chunks`
is a flat array; `Turn` (`chatfs_aistudio_types.py`) has no
parent/child/sibling field at all, unlike claude's
`parent_message_uuid` or chatgpt's `mapping`. The demo capture's 15
turns run in strictly increasing `createTime` (user → thought →
answer, repeating) with no duplicate indices. `[0][13]` is a 2-slot
`[live_turns, draft]` pair — no third slot for abandoned branches.
Recorded as a new section in
`dev.kb/claims.kb/aistudio-jspb-prompt-shape.md` ("Turn order is
linear"): `status: observed` (inferred from data shape, not a captured
edit/regenerate round-trip) — promote to `settled` if a future capture
of an edited prompt confirms the prior version is discarded rather
than preserved as a dead fork.

**Consequence:** `chatfs_aistudio_conversation_render.py::build_tree`
produces a straight predecessor chain (each turn's parent is the one
before it; `current` is always the chain's last turn) and hands it to
the *same* `chatfs_render.render_tree` claude/chatgpt use, rather than
writing a bespoke linear renderer. Verified against the live-rendered
15-turn `chat.md`: zero occurrences of `re:`, `replies:`, or
`superseded` — the fork-fact machinery degenerates to a no-op on every
node, by construction (every node has ≤1 child), not by a special
case bolted on.

**Alternatives considered:** a bespoke flat-list-to-markdown renderer,
skipping `chatfs_render` entirely — rejected: reusing the shared
machinery costs nothing extra (a degenerate tree *is* a valid input)
and keeps heading/numbering format uniform across all three providers
for free, which also future-proofs against AI Studio ever adding real
fork support later.

### Turn identity is the splat basename, not a synthesized id

AI Studio turns have no native id (per
`chatfs_aistudio_conversation_splat.py`'s own docstring) and can share
a `createTime`, so the render module keys everything off the already
zero-padded-index-led splat basename (`{index}.{role}[.thought]`)
rather than inventing a uuid. `render_conversation` sorts loaded turns
by the numeric index prefix, so dict insertion order never matters.

### Heading time is computed at render time, not baked at splat time

Unlike claude/chatgpt (whose message filenames already embed a
local-time string computed once, at splat time), AI Studio's basenames
carry only index+role — deliberately, since turns can share a
timestamp and have no id (see splat's docstring). So
`chatfs_aistudio_conversation_render.py::_time` converts each turn's
raw `createTime` (epoch seconds) to local wall-clock time on every
render invocation, via `.astimezone()`. This is a real (minor)
divergence from the other two providers: re-rendering on a machine in
a different timezone than the original capture would show a different
wall-clock hour, whereas claude/chatgpt's baked-in filename offset
never drifts. Accepted as-is: `chat.md` is a gitignored, freely
regenerated artifact, and there's no way to bake local time into
AI Studio's basenames without either abandoning the deliberate
index-led naming or writing a synthetic field into the otherwise-raw
per-turn `.json` (which the splat's docstring is explicit that it
does not do). Test coverage pins the conversion with a monkeypatched
`TZ` rather than asserting an environment-independent value.

## Conventions Established

- A provider whose wire shape has no branch representation should
  still be rendered through `chatfs_render.render_tree` via a
  degenerate single-child-chain `ConversationTree`, not a bespoke
  renderer — the shared fork-fact machinery is a no-op cost on a
  fork-less input, and keeps output format uniform across providers.
- `path_render.py` orchestration (purge non-`.data` contents → splat →
  move `messages/` up → render `chat.md`) is duplicated near-verbatim
  across providers, matching existing chatgpt/claude precedent —
  deliberately not shared yet; folds into the Immediate-plan step 4
  unification.

## Open Questions

- The "editing discards history, doesn't fork" claim is an inference
  from data shape, not a captured edit/regenerate round-trip. Revisit
  if a future AI Studio capture (live sitting) contradicts it.
- Render-time-local (vs. capture-time-local) heading timestamps: a
  latent inconsistency with claude/chatgpt, accepted for now (see
  above) — revisit if it ever causes a confusing `chat.md` diff.

## References

- `../.claude/todo.md` — Immediate plan steps 2 and 3
- `../.claude/todo.kb/2026-06-20-000-aistudio-provider-parity-ladder.md`
- `dev.kb/claims.kb/aistudio-jspb-prompt-shape.md`
- `chatfs_aistudio_conversation_render.py`,
  `chatfs_aistudio_conversation_render_test.py`,
  `chatfs_aistudio_conversation_path_render.py`
