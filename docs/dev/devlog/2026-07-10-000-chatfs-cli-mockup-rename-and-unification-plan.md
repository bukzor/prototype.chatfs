# Devlog: 2026-07-10 — chatfs-cli-mockup rename and unification plan

## Focus

Orient on outstanding work across the incubator (session-start heuristic
match, no argument file), then execute the one item the user judged
worth doing immediately: rename `chatfs-mockup-chatgpt` ->
`chatfs-cli-mockup`. Along the way, settled two strategic decisions that
had been blocking the unification todo, and recorded a four-step
execution plan for the rest.

## Decisions

### Rename executed now, not deferred behind unification

The user's rationale: the "chatgpt" name has been false since AI Studio
landed as the third provider (2026-06-20), and fixing it first makes
"everything afterward just a bit more clear and easy" — a small,
low-risk win worth taking before the bigger unification work. Landed as
three commits: the `git mv` + full repo-wide reference sweep ("Rename
incubator chatfs-mockup-chatgpt -> chatfs-cli-mockup"), the plan/decision
recording ("chatfs-cli-mockup: record the agreed execution plan and
decisions"), and an unrelated fork's `.claude/focus.md` cleanup that had
accreted in the same working tree ("Remove dead .claude/focus.md
convention", kept separate since it's a different concern).

**Scope note:** the original rename plan (`todo.kb/2026-05-11-000-...`)
targeted graduation to `packages/chatfs-cli/`. The user corrected this
mid-session: the code's actual destination is `$REPO/lib/chatfs/` once
libraryized — the incubator stays `-mockup-` until then. README closing
paragraph and the shared-code todo.kb file both updated to match.

### Driver model: not pipe-vs-delegation either/or

The cross-provider-drift file's last open "solve by unification" item
asked to decide between the index flow's user-composed pipe
(`index_browse.sh | index_splat.py`) and the conversation flow's nested
delegation (`url_browse -> path_render -> splat + render`). The user's
answer: this is a false dichotomy if the CLI is well-decomposed —
importable generator functions give both surfaces for free, with pipe
and delegation as thin drivers over the same library functions.

**Rationale:** a generator-function-per-stage design means "pipe" and
"delegate" are just two ways of calling the same code (stdin/stdout
plumbing vs. direct Python calls), not two competing architectures.
**Alternatives considered:** picking one uniformly (either delegation
everywhere or pipes everywhere) — both were on the table as poll options
before the user pointed out the false dichotomy. Recorded as resolved in
`todo.kb/2026-07-03-000-...`; the remaining subtask is documenting the
pattern in `cli-command-shape.kb/` during the actual unification work.

### Shared-lib destination: `$REPO/lib/chatfs/`, not `packages/chatfs-core/`

Settled in passing while discussing the rename's "why not now" rationale
(the incubator can't drop `-mockup-` until code, paths, and design
knowledge all graduate together). Recorded in
`todo.kb/2026-05-11-001-shared-code-among-providers.md`.

## Conventions Established

- When a todo item's own wording encodes an assumption that's since been
  superseded (here: "graduates to `packages/chatfs-cli/`"), don't
  silently follow it — the rename plan's proposed README text was
  amended in place before use, not after.
- A rename commit's dry-run (`git commit-staged -n`) is the right gate
  for confirming both sides of every `git mv` pair landed in one
  commit — used here to catch that the two todo.kb files with pending
  decision-annotations needed to be split into a second commit rather
  than folded into the rename.

## Open Questions

- None blocking. Session ended by explicit user request after the
  rename; the four-step plan (rename -> AI Studio index live-capture ->
  AI Studio conversation-side rungs -> unification) is recorded in
  `.claude/todo.md`'s new "Immediate plan" section and needs no further
  design discussion to start.

## References

- `.claude/todo.md` — "Immediate plan (agreed 2026-07-10)" section
- `.claude/todo.kb/2026-05-11-000-rename-incubator-to-chatfs-cli-mockup.md`
  — full rename plan, now closed out with verification notes
- `docs/dev/design-incubators/chatfs-cli-mockup/.claude/todo.kb/2026-07-03-000-cross-provider-data-flow-drift--pre-unification-fixes-vs-unification-scope.md`
  — driver-model decision
- `docs/dev/design-incubators/chatfs-cli-mockup/.claude/todo.kb/2026-05-11-001-shared-code-among-providers.md`
  — lib-destination decision
- Commits (by title, since this branch has since been rebased and hashes
  no longer resolve): "Rename incubator chatfs-mockup-chatgpt ->
  chatfs-cli-mockup", "chatfs-cli-mockup: record the agreed execution
  plan and decisions", "Remove dead .claude/focus.md convention"
- `~/.claude/sessions.kb/penguin/chatfs-cli-mockup-open-todo-sweep.md` —
  session tracking note, renamed and updated this session
